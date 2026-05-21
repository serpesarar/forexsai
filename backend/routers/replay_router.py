"""
Replay endpoints — drive the 2026-05-20 historical TP/SL correction
operation.

Two endpoints:
  POST /api/replay/run     → kick off a batch replay; persists corrections
  GET  /api/replay/report  → aggregate diff between original and corrected
                             outcomes (per symbol × model_type × direction)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.signal_replay_1m import run_replay_batch, inspect_signal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/replay", tags=["Replay & Correction"])


@router.post("/run")
async def run_replay(
    since: str = Query("2026-02-10",
                        description="ISO date — replay signals created on/after this date"),
    symbol: Optional[str] = Query(None),
    model_type: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=50000),
    dry_run: bool = Query(False, description="Skip DB writes — preview the batch summary only"),
    concurrency: int = Query(6, ge=1, le=32),
    purge_existing: bool = Query(False,
                                  description="Delete prior corrections for these symbols "
                                              "before persisting — use when re-running"),
):
    """Walk every prediction_log since `since` against 1m bars from
    candle_cache, re-decide TP/SL outcome via the same rules as
    signal_lifecycle.py, and persist to prediction_replay_corrections.

    Heavy operation — narrow with `symbol` / `model_type` / `limit` first
    to validate, then run the full sweep.
    """
    try:
        since_iso = datetime.fromisoformat(since).replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        raise HTTPException(400, f"Invalid `since` date: {since}")

    summary = await run_replay_batch(
        since_iso=since_iso, symbol=symbol, model_type=model_type,
        limit=limit, dry_run=dry_run, concurrency=concurrency,
        purge_existing=purge_existing,
    )
    if summary.get("status") == "error":
        raise HTTPException(500, summary.get("error", "replay failed"))
    return summary


@router.get("/sample-ids")
async def sample_ids(
    symbol: Optional[str] = Query(None),
    flipped_only: bool = Query(True),
    limit: int = Query(10, ge=1, le=100),
):
    """Return a handful of prediction_ids from prediction_replay_corrections —
    handy for feeding /api/replay/inspect/{id} during a spot-check audit."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        raise HTTPException(503, "db_unavailable")
    client = get_supabase_client()

    q = (client.table("prediction_replay_corrections")
         .select("prediction_id,symbol,model_type,direction,original_status,"
                 "corrected_status,corrected_resolution_reason,outcome_flipped,"
                 "pnl_delta_pips,replay_status")
         .eq("replay_status", "ok")
         .order("replayed_at", desc=True)
         .limit(800))
    if symbol:
        q = q.eq("symbol", symbol)
    res = q.execute() if hasattr(q, "execute") else q
    rows = res.data if hasattr(res, "data") else (
        res.get("data") if isinstance(res, dict) else []) or []
    if flipped_only:
        rows = [r for r in rows if r.get("outcome_flipped")]
    return {"status": "ok", "count": len(rows[:limit]), "samples": rows[:limit]}


@router.get("/inspect/{prediction_id}")
async def inspect(prediction_id: str):
    """Audit one signal's correction — full bar-by-bar walk.

    Returns: original vs corrected outcome, the measured EODHD→MT5 price
    offset, every TP/SL price level, and each 1m bar's decision (which TP
    crossed, whether SL was touched, in-bar ambiguity flag) until the
    signal resolved. Use this to verify a correction is sound."""
    result = await inspect_signal(prediction_id)
    if result.get("status") == "error":
        raise HTTPException(404 if "not found" in str(result.get("error")) else 500,
                            result.get("error", "inspect failed"))
    return result


@router.get("/report")
async def replay_report(
    batch_id: Optional[str] = Query(None,
                                      description="Filter to one batch (defaults: most recent batch per row)"),
    symbol: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=180,
                       description="Window for original signal created_at"),
):
    """Per (symbol, model_type, direction) diff: original vs replay-corrected
    outcomes. Surfaces the operation's impact — how many WINs/LOSSES flipped,
    which scopes had the biggest pnl_delta, etc."""
    from database.supabase_client import get_supabase_client, is_db_available
    from datetime import timedelta

    if not is_db_available():
        raise HTTPException(503, "db_unavailable")
    client = get_supabase_client()

    since_iso = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Paginate past the 1000-row PostgREST cap — the corrections table holds
    # ~87k rows, a single select would silently truncate to 1000.
    PAGE = 1000
    rows: list = []
    page_offset = 0
    try:
        while True:
            q = (client.table("prediction_replay_corrections").select(
                "prediction_id,symbol,model_type,direction,"
                "original_status,corrected_status,corrected_resolution_reason,"
                "outcome_flipped,pnl_delta_pips,replay_status,replayed_at")
                .gte("signal_created_at", since_iso)
                .order("replayed_at", desc=False)
                .range(page_offset, page_offset + PAGE - 1))
            if batch_id:
                q = q.eq("replay_batch_id", batch_id)
            if symbol:
                q = q.eq("symbol", symbol)
            res = q.execute() if hasattr(q, "execute") else q
            page = res.data if hasattr(res, "data") else (
                res.get("data") if isinstance(res, dict) else []) or []
            if not page:
                break
            rows.extend(page)
            if len(page) < PAGE:
                break
            page_offset += PAGE
    except Exception as e:
        raise HTTPException(500, f"report fetch failed: {str(e)[:120]}")

    if not rows:
        return {"status": "ok", "rows": 0, "scopes": []}

    # Group by (symbol, model_type, direction)
    scopes: dict = {}
    for r in rows:
        if r.get("replay_status") != "ok":
            continue
        key = (r.get("symbol"), r.get("model_type"), r.get("direction"))
        s = scopes.setdefault(key, {
            "symbol": key[0], "model_type": key[1], "direction": key[2],
            "n": 0, "flipped": 0,
            "orig_completed": 0, "orig_stopped": 0, "orig_expired": 0,
            "corr_completed": 0, "corr_stopped": 0, "corr_expired": 0,
            "pnl_delta_pips_total": 0.0,
        })
        s["n"] += 1
        if r.get("outcome_flipped"):
            s["flipped"] += 1
        os_ = (r.get("original_status") or "").lower()
        cs_ = (r.get("corrected_status") or "").lower()
        if os_ in ("completed", "stopped", "expired"):
            s[f"orig_{os_}"] += 1
        if cs_ in ("completed", "stopped", "expired"):
            s[f"corr_{cs_}"] += 1
        s["pnl_delta_pips_total"] += float(r.get("pnl_delta_pips") or 0)

    scope_list = sorted(scopes.values(),
                         key=lambda s: -abs(s["pnl_delta_pips_total"]))
    for s in scope_list:
        s["pnl_delta_pips_total"] = round(s["pnl_delta_pips_total"], 2)
        s["flip_rate_pct"] = round(100.0 * s["flipped"] / s["n"], 2) if s["n"] else 0
        # Honest win-rate before/after among resolved (completed+stopped)
        orig_resolved = s["orig_completed"] + s["orig_stopped"]
        corr_resolved = s["corr_completed"] + s["corr_stopped"]
        s["orig_win_rate"] = round(100.0 * s["orig_completed"] / orig_resolved, 2) if orig_resolved else None
        s["corr_win_rate"] = round(100.0 * s["corr_completed"] / corr_resolved, 2) if corr_resolved else None

    return {
        "status": "ok",
        "rows": len(rows),
        "scopes": scope_list,
        "filter": {"batch_id": batch_id, "symbol": symbol, "days": days},
    }
