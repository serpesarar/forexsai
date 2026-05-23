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
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.signal_replay_1m import (
    run_replay_batch, inspect_signal,
    apply_corrections_to_prediction_logs, revert_corrections,
)

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


@router.get("/walkforward")
async def walkforward(
    symbol: Optional[str] = Query(None, description="One symbol, or omit for all"),
    direction: Optional[str] = Query(None, description="BUY | SELL | omit for both"),
    model_type: Optional[str] = Query(None),
    train_cutoff: str = Query("2026-04-20T00:00:00+00:00",
                               description="Signals before this = train, after = test"),
    days: int = Query(120, ge=30, le=200),
    tp_pct: float = Query(50, ge=10, le=95,
                           description="TP at this percentile of the MFE distribution"),
    sl_pct: float = Query(85, ge=50, le=99,
                           description="SL beyond this percentile of winners' MAE"),
):
    """Distribution-based, overfit-resistant TP/SL design with an honest
    out-of-sample check.

    Derives TP/SL from the MFE/MAE distribution of TRAIN signals (before
    train_cutoff), then scores both the current config and the derived
    config on the untouched TEST signals (after the cutoff). If the
    derived config still wins out-of-sample it is real; if not it was
    overfit. This is the honest 'try both systems' comparison."""
    from services.tp_sl_walkforward import walk_forward_test, walk_forward_all
    if symbol:
        result = await walk_forward_test(
            symbol, direction=direction, model_type=model_type,
            train_cutoff=train_cutoff, days=days, tp_pct=tp_pct, sl_pct=sl_pct)
        if result.get("status") == "error":
            raise HTTPException(500, result.get("error", "walkforward failed"))
        return result
    return {"status": "ok",
            "results": await walk_forward_all(
                train_cutoff=train_cutoff, days=days, tp_pct=tp_pct, sl_pct=sl_pct)}


@router.post("/apply-corrections")
async def apply_corrections(
    since: str = Query("2026-02-10", description="Apply corrections for signals on/after this date"),
    dry_run: bool = Query(True, description="Preview counts only — pass dry_run=false to write"),
):
    """Overwrite prediction_logs' outcome fields (status, resolution_reason,
    exit_price, highest_profit_pips, lowest_drawdown_pips) with the
    1m-replay corrected values. Every panel reads prediction_logs, so this
    makes ALL panels show the honest signals at once.

    Reversible — originals are snapshotted in prediction_replay_corrections;
    POST /api/replay/revert-corrections restores them."""
    try:
        since_iso = datetime.fromisoformat(since).replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        raise HTTPException(400, f"bad since date: {since}")
    res = await apply_corrections_to_prediction_logs(since_iso, dry_run=dry_run)
    if res.get("status") == "error":
        raise HTTPException(500, res.get("error", "apply failed"))
    return res


@router.post("/revert-corrections")
async def revert_corrections_endpoint(
    since: str = Query("2026-02-10"),
    dry_run: bool = Query(True),
):
    """Undo apply-corrections — restore prediction_logs from the original_*
    snapshot in prediction_replay_corrections."""
    try:
        since_iso = datetime.fromisoformat(since).replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        raise HTTPException(400, f"bad since date: {since}")
    res = await revert_corrections(since_iso, dry_run=dry_run)
    if res.get("status") == "error":
        raise HTTPException(500, res.get("error", "revert failed"))
    return res


@router.get("/derived-config-status")
async def derived_config_status():
    """Show the walk-forward 'side system' — the derived TP/SL configs and
    whether they are currently active (env TP_SL_DERIVED_OVERRIDES)."""
    from services.target_config import (
        DERIVED_OVERRIDES_ACTIVE, _DERIVED_OVERRIDES, get_effective_config,
    )
    scopes = []
    for sym, (direction, ov) in _DERIVED_OVERRIDES.items():
        eff = get_effective_config(sym, direction)
        scopes.append({
            "symbol": sym, "direction": direction,
            "derived_tp_ladder": [t.pips for t in ov.targets],
            "derived_sl": ov.stoploss_pips,
            "provenance": ov.source,
            "currently_applied": bool(DERIVED_OVERRIDES_ACTIVE),
            "live_tp1": eff.targets[0].pips if eff.targets else None,
            "live_sl": eff.stoploss_pips,
        })
    return {
        "status": "ok",
        "side_system_active": bool(DERIVED_OVERRIDES_ACTIVE),
        "env_flag": "TP_SL_DERIVED_OVERRIDES",
        "note": ("Set TP_SL_DERIVED_OVERRIDES=1 and redeploy to apply the "
                  "derived configs to these 3 robust scopes; set to 0 to revert."),
        "scopes": scopes,
    }


@router.get("/expectancy")
async def expectancy(days: int = Query(90, ge=14, le=180)):
    """Sembol bazlı gerçek R-multiple ve beklenti hesabı.
    Cevap: avg_win_pips, avg_loss_pips, R-multiple (win/loss), expectancy/trade."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        raise HTTPException(503, "db_unavailable")
    client = get_supabase_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows: list = []
    offset = 0
    while True:
        q = (client.table("prediction_replay_corrections")
             .select("symbol,model_type,direction,entry_price,"
                      "corrected_status,corrected_exit_price,replay_status")
             .gte("signal_created_at", since)
             .order("signal_created_at", desc=False)
             .range(offset, offset + 999))
        res = q.execute() if hasattr(q, "execute") else q
        page = res.data if hasattr(res, "data") else (
            res.get("data") if isinstance(res, dict) else []) or []
        if not page: break
        rows.extend(page)
        if len(page) < 1000: break
        offset += 1000
    try:
        from services.target_config import pips_from_price_change
    except Exception:
        pips_from_price_change = None

    def _pips(sym, direction, e, x):
        if not e or not x: return 0.0
        diff = (x - e) if direction == "BUY" else (e - x)
        if pips_from_price_change:
            try:
                return abs(pips_from_price_change(abs(diff), sym)) * (1 if diff >= 0 else -1)
            except Exception:
                pass
        return diff

    from collections import defaultdict
    agg: dict = defaultdict(lambda: {"wins": 0, "losses": 0,
                                       "win_pips": 0.0, "loss_pips": 0.0})
    for r in rows:
        if r.get("replay_status") != "ok": continue
        sym = r["symbol"]; d = r["direction"]
        status = r["corrected_status"]
        e = float(r.get("entry_price") or 0)
        x = float(r.get("corrected_exit_price") or 0)
        p = _pips(sym, d, e, x)
        a = agg[sym]
        if status == "completed" and p > 0:
            a["wins"] += 1; a["win_pips"] += p
        elif status == "stopped" and p < 0:
            a["losses"] += 1; a["loss_pips"] += abs(p)

    out = {}
    for sym, a in agg.items():
        avg_w = a["win_pips"] / a["wins"] if a["wins"] else 0
        avg_l = a["loss_pips"] / a["losses"] if a["losses"] else 0
        total = a["wins"] + a["losses"]
        wr = a["wins"] / total if total else 0
        # R-multiple = avg_win / avg_loss
        r_mult = avg_w / avg_l if avg_l > 0 else None
        # Expectancy/trade = WR*avg_win − (1-WR)*avg_loss
        exp_pips = wr * avg_w - (1 - wr) * avg_l if total else 0
        # Expectancy in R units (win_avg as 1R proxy reference)
        exp_R = (wr * 1.0 - (1 - wr) * (avg_l / avg_w)) if avg_w > 0 else 0
        out[sym] = {
            "wins": a["wins"], "losses": a["losses"], "resolved": total,
            "win_rate_pct": round(100 * wr, 2),
            "avg_win_pips": round(avg_w, 3),
            "avg_loss_pips": round(avg_l, 3),
            "reward_to_risk": round(r_mult, 2) if r_mult else None,
            "expectancy_pips_per_trade": round(exp_pips, 3),
            "expectancy_R_per_trade": round(exp_R, 4),
        }
    return {"status": "ok", "days": days, "per_symbol": out}


@router.get("/walkforward-rolling")
async def walkforward_rolling(
    symbol: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    model_type: Optional[str] = Query(None),
    days: int = Query(120, ge=30, le=200),
    test_window_days: int = Query(12, ge=5, le=45),
    min_train_days: int = Query(40, ge=20, le=90),
    tp_pct: float = Query(50, ge=10, le=95),
    sl_pct: float = Query(85, ge=50, le=99),
):
    """Proper walk-forward analysis — rolls multiple non-overlapping test
    windows forward in time, re-deriving TP/SL on the expanding train set
    for each. Validates the derivation METHOD, not one lucky config."""
    from services.tp_sl_walkforward import rolling_walk_forward, rolling_walk_forward_all
    if symbol:
        result = await rolling_walk_forward(
            symbol, direction=direction, model_type=model_type, days=days,
            test_window_days=test_window_days, min_train_days=min_train_days,
            tp_pct=tp_pct, sl_pct=sl_pct)
        if result.get("status") == "error":
            raise HTTPException(500, result.get("error", "rolling walk-forward failed"))
        return result
    return {"status": "ok",
            "results": await rolling_walk_forward_all(
                days=days, test_window_days=test_window_days,
                min_train_days=min_train_days, tp_pct=tp_pct, sl_pct=sl_pct)}


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
