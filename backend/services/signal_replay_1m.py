"""
Signal replay engine — walk every historical signal against 1m bars and
re-decide TP/SL outcome using the EXACT production rule logic.

Pipeline
--------
1. Load resolved (or all) prediction_logs since a cutoff date.
2. For each signal:
     - Fetch 1m bars from candle_cache between created_at and
       (created_at + evaluation_window_minutes(timeframe)).
     - Compute TP levels and SL price via the same helpers production uses
       (target_config.calculate_target_prices / calculate_stoploss_price).
     - Walk bar-by-bar:
         * In-bar TP/SL hit check using the bar's high/low (per direction).
         * Tie-break rule mirrors signal_lifecycle.py:
              - TP4 hit → completed (tp4_hit), final
              - SL hit AND tp1_3 already hit by this bar → completed
                (tp1_3_hit_then_sl), TP wins the ambiguity
              - SL hit alone → stopped (sl_hit), final
              - any TP hit short-circuits forward walk
         * Track true MFE/MAE from bar highs/lows.
     - If neither TP nor SL fires within the window → expired (window_expired).
3. Write a row to prediction_replay_corrections — never touches prediction_logs.

The output table is the source of truth for the dashboard's "corrected
mode" toggle and for AI-Ops re-mining once the leak-era data is rebuilt.

Public API
----------
    await replay_signal_row(signal_row, batch_id) → dict (corrected outcome)
    await run_replay_batch(since_iso, symbol=None, model_type=None,
                             limit=None, dry_run=False) → batch summary
"""
from __future__ import annotations

import asyncio
import bisect
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

REPLAY_TIMEFRAME = "1m"
RULE_VERSION = "v1"
DEFAULT_FETCH_BATCH = 2000
SUPABASE_PAGE_SIZE = 1000   # Supabase caps a single select at 1000 rows


# ─── Helpers ────────────────────────────────────────────────────────────────

def _utc_iso(dt: Optional[datetime] = None) -> str:
    return (dt or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()


def _parse_iso(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _max_hold_minutes(timeframe: Optional[str]) -> int:
    """Maximum minutes to walk a signal forward looking for TP/SL.

    NOT the live lifecycle's short evaluation window (2-60 min) — that
    cherry-picks only fast movers and biases the win rate upward. For an
    honest "did the direction prove right" verdict we walk until TP1 or SL
    is actually hit, capped at a generous, realistic holding horizon per
    timeframe. Over these spans virtually every signal resolves; whatever
    is still 'expired' genuinely never reached TP1 or SL.

    Override any value with env REPLAY_MAXHOLD_<TF> (minutes), e.g.
    REPLAY_MAXHOLD_5M=600.
    """
    import os as _os
    table = {"1m": 240, "5m": 720, "15m": 1440, "20m": 1440,
             "30m": 2160, "1h": 2880, "4h": 5760, "1d": 10080}
    tf = (timeframe or "").lower()
    base = table.get(tf, 1440)
    override = _os.getenv(f"REPLAY_MAXHOLD_{tf.upper()}")
    if override:
        try:
            return max(10, int(override))
        except ValueError:
            pass
    return base


def _target_rank(name: str) -> Optional[int]:
    if not name:
        return None
    n = name.upper().replace("TP", "")
    try:
        return int(n)
    except (TypeError, ValueError):
        return None


# ─── 1m bar loading — full paginated load per symbol ─────────────────────────

def _load_all_1m_bars_sync(symbol: str) -> list[dict]:
    """Load EVERY 1m bar for a symbol from candle_cache, paginating past the
    Supabase 1000-row cap. Returns a list sorted ascending by `ts`.

    This is loaded ONCE per symbol per batch and shared across all that
    symbol's signals — avoids 75k individual range queries and the old
    5000-bar window bug (5000 1m bars = only ~3.5 days of coverage)."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return []
    client = get_supabase_client()

    out: list[dict] = []
    offset = 0
    while True:
        try:
            q = (client.table("candle_cache")
                 .select("candle_time,open,high,low,close,volume")
                 .eq("symbol", symbol)
                 .eq("timeframe", REPLAY_TIMEFRAME)
                 .order("candle_time", desc=False)
                 .range(offset, offset + SUPABASE_PAGE_SIZE - 1))
            res = q.execute() if hasattr(q, "execute") else q
        except Exception as e:
            logger.warning("[replay] candle page fetch failed @%d for %s: %s",
                           offset, symbol, e)
            break
        page = res.data if hasattr(res, "data") else (
            res.get("data") if isinstance(res, dict) else []) or []
        if not page:
            break
        for row in page:
            ct = row.get("candle_time")
            ts = _parse_iso(ct)
            if ts is None:
                continue
            out.append({
                "ts": ts,
                "open": float(row.get("open") or 0),
                "high": float(row.get("high") or 0),
                "low": float(row.get("low") or 0),
                "close": float(row.get("close") or 0),
                "volume": float(row.get("volume") or 0),
            })
        if len(page) < SUPABASE_PAGE_SIZE:
            break
        offset += SUPABASE_PAGE_SIZE

    out.sort(key=lambda c: c["ts"])
    logger.info("[replay] loaded %d 1m bars for %s", len(out), symbol)
    return out


def _slice_bars(symbol_bars: list[dict], ts_keys: list,
                 start: datetime, end: datetime) -> list[dict]:
    """Binary-search slice of a pre-sorted bar list to [start, end]."""
    lo = bisect.bisect_left(ts_keys, start)
    hi = bisect.bisect_right(ts_keys, end)
    return symbol_bars[lo:hi]


# ─── Core: replay a single signal ────────────────────────────────────────────

async def replay_signal_row(signal_row: dict,
                              symbol_bars: list[dict],
                              ts_keys: list,
                              batch_id: Optional[str] = None,
                              trace: Optional[list] = None) -> dict:
    """Walk-forward replay of one signal against a pre-loaded, sorted bar list.

    Args:
      signal_row:  a prediction_logs row
      symbol_bars: ALL 1m bars for this signal's symbol, sorted by `ts`
      ts_keys:     parallel list of just the `ts` values (for bisect)
      batch_id:    groups this row under one /api/replay/run pass
      trace:       if a list is passed, every walked bar's decision is
                   appended to it (audit mode — used by /api/replay/inspect)

    Returns the dict to write to prediction_replay_corrections.
    """
    from services.target_config import (
        calculate_target_prices, calculate_stoploss_price,
        pips_from_price_change, get_symbol_config,
    )

    sid = signal_row.get("id")
    symbol = signal_row.get("symbol") or ""
    direction = (signal_row.get("ml_direction") or signal_row.get("direction") or "").upper()
    timeframe = signal_row.get("timeframe") or "15m"
    # recorded_entry is kept ONLY for transparency reporting — it is NOT used
    # to compute the outcome (it was found unreliable: variable 5-25 pip gap
    # vs the live MT5 quote). Per user spec 2026-05-21: match by date+time+
    # direction only, take the entry from the MT5 1m chart itself.
    recorded_entry = float(signal_row.get("ml_entry_price")
                            or signal_row.get("entry_price") or 0)
    created_at = _parse_iso(signal_row.get("created_at"))

    base = {
        "prediction_id": sid,
        "symbol": symbol,
        "model_type": signal_row.get("model_type"),
        "direction": direction or None,
        "timeframe": timeframe,
        "entry_price": None,   # set below from the MT5 1m bar
        "signal_created_at": _utc_iso(created_at) if created_at else None,
        "original_status": signal_row.get("status"),
        "original_resolution_reason": signal_row.get("resolution_reason"),
        "original_exit_price": signal_row.get("exit_price"),
        "original_highest_profit_pips": signal_row.get("highest_profit_pips"),
        "original_lowest_drawdown_pips": signal_row.get("lowest_drawdown_pips"),
        "rule_version": RULE_VERSION,
        "replay_batch_id": batch_id,
    }

    # ── Validation — only direction + timestamp are needed from the DB ──────
    if direction not in ("BUY", "SELL") or not created_at:
        return {**base, "replay_status": "no_entry",
                "replay_notes": "missing direction/created_at"}

    if not symbol_bars:
        return {**base, "replay_status": "no_candles",
                "replay_notes": "candle_cache empty for symbol/1m"}

    window_minutes = _max_hold_minutes(timeframe)
    # Walk forward up to the full holding horizon — the loop short-circuits
    # the instant TP or SL is hit, so a fast signal still resolves in 1 bar.
    window_end = created_at + timedelta(minutes=window_minutes + 2)

    # Bars from created_at forward — bars[0] is the ENTRY bar.
    bars = _slice_bars(symbol_bars, ts_keys, created_at, window_end)
    if not bars:
        return {**base, "replay_status": "no_candles",
                "replay_notes": (f"no 1m bars at/after created_at "
                                   f"[{created_at.isoformat()}, {window_end.isoformat()}]")}

    # ── Entry = the MT5 1m bar price at signal time (NOT the DB entry) ──────
    # Open of the first 1m bar at/after created_at = the real market price
    # the moment the signal fired. The entry bar is INCLUDED in the walk so
    # its own high/low can trigger TP/SL within the entry minute.
    entry_bar = bars[0]
    entry = float(entry_bar.get("open") or 0)
    if entry <= 0:
        return {**base, "replay_status": "no_candles",
                "replay_notes": "entry bar has no open price"}
    base["entry_price"] = round(entry, 5)
    anchor_bar = entry_bar   # kept for diagnostics

    # ── TP/SL ladder computed fresh from the MT5 entry ─────────────────────
    try:
        target_prices = calculate_target_prices(entry, direction, symbol, timeframe)
        sl_price = calculate_stoploss_price(entry, direction, symbol, timeframe)
    except Exception as e:
        return {**base, "replay_status": "exception",
                "replay_notes": f"target_calc_failed: {str(e)[:120]}"}
    if not target_prices or sl_price is None or sl_price <= 0:
        return {**base, "replay_status": "no_entry",
                "replay_notes": "tp/sl prices unresolved"}

    # Transparency only: how far the DB-recorded entry sat from the MT5 entry.
    raw_offset = 0.0
    offset_pct = 0.0
    if recorded_entry > 0:
        raw_offset = entry - recorded_entry
        offset_pct = abs(raw_offset) / recorded_entry

    # ── Walk forward ────────────────────────────────────────────────────────
    cfg = get_symbol_config(symbol)
    is_pct = bool(getattr(cfg, "is_percentage", False))
    pip_val = float(getattr(cfg, "pip_value", 1.0)) or 1.0

    def _px_to_pips(diff: float) -> float:
        if entry <= 0:
            return 0.0
        if is_pct:
            return (diff / entry) * 100.0
        return diff / pip_val if pip_val > 0 else diff

    # Track which TPs have been hit at any point during the walk.
    hit_targets: dict[str, bool] = {name: False for name in target_prices.keys()}
    # MFE/MAE tracked as cumulative bests.
    mfe_pips = 0.0
    mae_pips = 0.0

    resolution = None  # dict: {status, reason, exit_price, exit_at, bar_index, target_hit}
    bars_walked = 0

    for idx, bar in enumerate(bars):
        bars_walked = idx + 1
        h = float(bar["high"])
        l = float(bar["low"])
        o = float(bar.get("open") or 0)
        c = float(bar.get("close") or 0)
        bts: datetime = bar["ts"]

        # Update MFE/MAE
        if direction == "BUY":
            fav_excursion = _px_to_pips(h - entry)
            adv_excursion = _px_to_pips(entry - l)
        else:  # SELL
            fav_excursion = _px_to_pips(entry - l)
            adv_excursion = _px_to_pips(h - entry)
        if fav_excursion > mfe_pips:
            mfe_pips = fav_excursion
        if adv_excursion > mae_pips:
            mae_pips = adv_excursion

        # 1) Which TPs got crossed by this bar?
        newly_hit = []
        for tp_name, tp_px in target_prices.items():
            if hit_targets[tp_name]:
                continue
            if direction == "BUY" and h >= tp_px:
                hit_targets[tp_name] = True
                newly_hit.append(tp_name)
            elif direction == "SELL" and l <= tp_px:
                hit_targets[tp_name] = True
                newly_hit.append(tp_name)

        # 2) SL check
        if direction == "BUY":
            hit_sl = l <= sl_price
        else:
            hit_sl = h >= sl_price

        # Audit trace — one record per walked bar.
        if trace is not None:
            trace.append({
                "bar": idx + 1,
                "ts": _utc_iso(bts),
                "high": round(h, 5),
                "low": round(l, 5),
                "newly_hit_tp": newly_hit,
                "sl_touched": bool(hit_sl),
                "in_bar_ambiguous": bool(hit_sl and newly_hit),
                "mfe_pips": round(mfe_pips, 2),
                "mae_pips": round(mae_pips, 2),
            })

        # 3) Resolution — FIRST bar that touches TP or SL ends the trade.
        #    The walk short-circuits here, so MFE/MAE/time stay clean and a
        #    fast signal resolves in 1 bar while a slow one walks the full
        #    holding horizon. Tie-break: if a single bar spans both a TP and
        #    the SL, TP wins (matches signal_lifecycle's tp_*_then_sl).
        tp_hit_this_bar = bool(newly_hit)
        if tp_hit_this_bar or hit_sl:
            deepest = None
            if any(hit_targets.values()):
                deepest = max((n for n in hit_targets if hit_targets[n]),
                               key=lambda n: _target_rank(n) or 0)

            if tp_hit_this_bar and hit_sl:
                # In-bar ambiguity — a single 1m bar spanned both a TP and
                # the SL; true order is unknowable without tick data. Resolve
                # it with the standard OHLC bar-path heuristic: a bullish bar
                # (close>=open) is assumed to travel open→low→high→close, a
                # bearish one open→high→low→close. That tells us which side
                # was reached first. Flagged `ambiguous` so the batch reports
                # how many verdicts rest on this heuristic.
                bullish = c >= o
                if direction == "BUY":
                    # TP is above (high side), SL below (low side).
                    tp_first = not bullish    # bearish → high(TP) reached first
                else:  # SELL
                    # TP is below (low side), SL above (high side).
                    tp_first = bullish        # bullish → low(TP) reached first
                if tp_first:
                    if deepest == "TP4" and all(hit_targets.values()):
                        reason = "all_targets_hit"
                    elif deepest == "TP4":
                        reason = "tp4_hit"
                    else:
                        reason = "tp1_3_hit_then_sl"
                    resolution = {
                        "status": "completed", "reason": reason,
                        "exit_price": target_prices.get(deepest), "exit_at": bts,
                        "target_hit": deepest, "ambiguous": True,
                    }
                else:
                    resolution = {
                        "status": "stopped", "reason": "sl_hit_ambiguous",
                        "exit_price": sl_price, "exit_at": bts,
                        "target_hit": None, "ambiguous": True,
                    }
            elif tp_hit_this_bar:
                # Clean TP touch, no SL this bar → WIN at the deepest TP hit.
                if deepest == "TP4" and all(hit_targets.values()):
                    reason = "all_targets_hit"
                else:
                    reason = f"{deepest.lower()}_hit"
                resolution = {
                    "status": "completed", "reason": reason,
                    "exit_price": target_prices.get(deepest), "exit_at": bts,
                    "target_hit": deepest, "ambiguous": False,
                }
            else:
                # SL touched, no TP ever → clean LOSS.
                resolution = {
                    "status": "stopped", "reason": "sl_hit",
                    "exit_price": sl_price, "exit_at": bts,
                    "target_hit": None,
                }
            break

    # Neither TP nor SL touched within the full holding horizon → genuinely
    # expired (no decisive move in, e.g., 12-48h).
    if resolution is None:
        resolution = {
            "status": "expired", "reason": "window_expired",
            "exit_price": float(bars[-1]["close"]),
            "exit_at": bars[-1]["ts"],
            "target_hit": None,
        }

    # ── Build the corrections row ───────────────────────────────────────────
    exit_at: datetime = resolution["exit_at"]
    time_to_res = max(0, int((exit_at - created_at).total_seconds() // 60))

    # PnL delta vs original (in pips, signed favorable)
    def _signed_realized_pips(status: str, reason: str, exit_px: Optional[float]) -> float:
        if exit_px is None or entry <= 0:
            return 0.0
        diff = (exit_px - entry) if direction == "BUY" else (entry - exit_px)
        return _px_to_pips(diff)

    corrected_pnl = _signed_realized_pips(resolution["status"], resolution["reason"],
                                            resolution["exit_price"])
    original_exit = signal_row.get("exit_price")
    original_pnl = _signed_realized_pips(signal_row.get("status") or "",
                                           signal_row.get("resolution_reason") or "",
                                           float(original_exit) if original_exit else None)

    # Two distinct notions of "changed":
    #  - status_flipped: the win/loss/neutral VERDICT changed
    #    (completed↔stopped↔expired) — this is the metric that matters for
    #    win-rate honesty.
    #  - reason_changed: only the granular resolution_reason string differs
    #    (e.g. original 'window_resolve_positive' vs corrected 'tp1_hit').
    #    Almost always true since the old system used different reason
    #    vocabulary — NOT a meaningful signal on its own.
    status_flipped = (signal_row.get("status") != resolution["status"])
    reason_changed = (signal_row.get("resolution_reason") != resolution["reason"])

    notes_bits = []
    if recorded_entry > 0 and abs(raw_offset) > 0:
        notes_bits.append(f"db_entry_gap={raw_offset:+.3f}({offset_pct*100:.2f}%)")

    diagnostics = {
        "entry_source": "mt5_1m_bar_open",
        "mt5_entry": round(entry, 5),
        "db_recorded_entry": round(recorded_entry, 5),
        "db_entry_gap": round(raw_offset, 5),
        "db_entry_gap_pct": round(offset_pct * 100, 3),
        "entry_bar_ts": _utc_iso(entry_bar["ts"]),
        "tp_prices": {k: round(v, 5) for k, v in target_prices.items()},
        "sl_price": round(sl_price, 5),
        "window_minutes": window_minutes,
        "bars_in_window": len(bars),
        "tie_break_rule": "TP wins when a single bar spans both TP and SL",
    }
    return {
        **base,
        "_diagnostics": diagnostics,
        "corrected_status": resolution["status"],
        "corrected_resolution_reason": resolution["reason"],
        "corrected_target_hit": resolution["target_hit"],
        "corrected_exit_price": resolution["exit_price"],
        "corrected_exit_at": _utc_iso(exit_at),
        "corrected_time_to_resolution_minutes": time_to_res,
        "corrected_mfe_pips": round(mfe_pips, 3),
        "corrected_mae_pips": round(mae_pips, 3),
        "bars_walked": bars_walked,
        "replay_status": "ok",
        # outcome_flipped stores the MEANINGFUL verdict change (status).
        "outcome_flipped": bool(status_flipped),
        "_reason_changed": bool(reason_changed),   # summary-only, not persisted
        "_ambiguous": bool(resolution.get("ambiguous", False)),  # summary-only
        "pnl_delta_pips": round(corrected_pnl - original_pnl, 3),
        "replay_notes": "; ".join(notes_bits) if notes_bits else None,
    }


# ─── Batch runner ────────────────────────────────────────────────────────────

async def run_replay_batch(since_iso: str,
                            symbol: Optional[str] = None,
                            model_type: Optional[str] = None,
                            limit: Optional[int] = None,
                            dry_run: bool = False,
                            concurrency: int = 6,
                            purge_existing: bool = False) -> dict:
    """Replay every prediction_log since `since_iso`, persisting corrections.

    Returns a summary: counts by replay_status and outcome flip counts.
    `dry_run=True` skips the DB write — useful for spot checks.
    `purge_existing=True` deletes prior corrections for the batch's symbols
    first — use when re-running so the report doesn't double-count.
    """
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "error", "error": "db_unavailable"}
    client = get_supabase_client()

    batch_id = str(uuid.uuid4())

    # Fetch resolved + active signals (replay can still produce a result for
    # active ones since the 1m bar history extends past their lifecycle).
    # Supabase caps a select at 1000 rows — paginate with .range().
    rows: list[dict] = []
    page_offset = 0
    hard_cap = int(limit) if limit else 200000
    try:
        while len(rows) < hard_cap:
            page_size = min(SUPABASE_PAGE_SIZE, hard_cap - len(rows))
            q = (client.table("prediction_logs").select(
                "id,symbol,model_type,ml_direction,ml_entry_price,timeframe,status,"
                "resolution_reason,exit_price,highest_profit_pips,lowest_drawdown_pips,"
                "created_at")
                .gte("created_at", since_iso)
                .order("created_at", desc=False)
                .range(page_offset, page_offset + page_size - 1))
            if symbol:
                q = q.eq("symbol", symbol)
            if model_type:
                q = q.eq("model_type", model_type)
            res = q.execute() if hasattr(q, "execute") else q
            page = res.data if hasattr(res, "data") else (
                res.get("data") if isinstance(res, dict) else []) or []
            if not page:
                break
            rows.extend(page)
            if len(page) < page_size:
                break
            page_offset += page_size
    except Exception as e:
        logger.exception("replay: prediction_logs fetch failed: %s", e)
        return {"status": "error", "error": f"fetch_failed: {str(e)[:120]}"}

    if not rows:
        return {"status": "ok", "batch_id": batch_id, "scanned": 0,
                 "note": "no prediction_logs in window"}

    # ── Pre-load 1m bars ONCE per symbol (shared across that symbol's signals).
    symbols_in_batch = sorted({(r.get("symbol") or "") for r in rows if r.get("symbol")})

    # ── Optional purge — clear prior corrections for these symbols so a
    #    re-run doesn't leave stale rows the report would double-count.
    purged: dict[str, str] = {}
    if purge_existing and not dry_run:
        for sym in symbols_in_batch:
            try:
                # Wrapper: filters FIRST, then .delete() executes immediately.
                res = client.table("prediction_replay_corrections").eq(
                    "symbol", sym).delete()
                err = res.get("error") if isinstance(res, dict) else None
                purged[sym] = f"failed: {err}" if err else "ok"
            except Exception as e:
                logger.warning("replay purge failed for %s: %s", sym, e)
                purged[sym] = f"failed: {str(e)[:80]}"

    bars_by_symbol: dict[str, list[dict]] = {}
    tskeys_by_symbol: dict[str, list] = {}
    bar_coverage: dict[str, dict] = {}
    for sym in symbols_in_batch:
        sym_bars = await asyncio.to_thread(_load_all_1m_bars_sync, sym)
        bars_by_symbol[sym] = sym_bars
        tskeys_by_symbol[sym] = [b["ts"] for b in sym_bars]
        bar_coverage[sym] = {
            "bars": len(sym_bars),
            "from": _utc_iso(sym_bars[0]["ts"]) if sym_bars else None,
            "to": _utc_iso(sym_bars[-1]["ts"]) if sym_bars else None,
        }

    sem = asyncio.Semaphore(max(1, concurrency))

    async def _one(sig: dict):
        async with sem:
            sym = sig.get("symbol") or ""
            try:
                return await replay_signal_row(
                    sig,
                    symbol_bars=bars_by_symbol.get(sym, []),
                    ts_keys=tskeys_by_symbol.get(sym, []),
                    batch_id=batch_id,
                )
            except Exception as e:
                logger.debug("replay error for %s: %s", sig.get("id"), e)
                return {
                    "prediction_id": sig.get("id"),
                    "symbol": sig.get("symbol"),
                    "model_type": sig.get("model_type"),
                    "direction": sig.get("ml_direction"),
                    "timeframe": sig.get("timeframe"),
                    "entry_price": sig.get("ml_entry_price"),
                    "signal_created_at": sig.get("created_at"),
                    "replay_status": "exception",
                    "replay_notes": str(e)[:200],
                    "rule_version": RULE_VERSION,
                    "replay_batch_id": batch_id,
                }

    results = await asyncio.gather(*[_one(s) for s in rows])

    # ── Summary ─────────────────────────────────────────────────────────────
    summary = {
        "status": "ok",
        "batch_id": batch_id,
        "scanned": len(rows),
        "bar_coverage": bar_coverage,
        "by_replay_status": {},
        "status_flipped": 0,        # win/loss VERDICT changed — the real metric
        "reason_changed": 0,        # only the granular reason string differs
        "in_bar_ambiguous": 0,      # verdicts resting on the TP-wins tie-break
        "by_corrected_status": {},
        "by_corrected_reason": {},
        "by_original_status": {},
    }
    for r in results:
        rs = r.get("replay_status") or "unknown"
        summary["by_replay_status"][rs] = summary["by_replay_status"].get(rs, 0) + 1
        if r.get("outcome_flipped"):
            summary["status_flipped"] += 1
        if r.get("_reason_changed"):
            summary["reason_changed"] += 1
        if r.get("_ambiguous"):
            summary["in_bar_ambiguous"] += 1
        cs = r.get("corrected_status")
        if cs:
            summary["by_corrected_status"][cs] = summary["by_corrected_status"].get(cs, 0) + 1
        cr = r.get("corrected_resolution_reason")
        if cr:
            summary["by_corrected_reason"][cr] = summary["by_corrected_reason"].get(cr, 0) + 1
        os_ = r.get("original_status")
        if os_:
            summary["by_original_status"][os_] = summary["by_original_status"].get(os_, 0) + 1

    # ── Persist (batched upsert) ────────────────────────────────────────────
    if not dry_run:
        BATCH = 200
        persisted = 0
        for i in range(0, len(results), BATCH):
            # Strip summary-only keys the table has no column for.
            chunk = [{k: v for k, v in r.items() if not k.startswith("_")}
                     for r in results[i:i + BATCH]]
            try:
                # on_conflict on (prediction_id, replay_batch_id) — since
                # batch_id is fresh, this is effectively insert. Using
                # upsert anyway so the call shape stays consistent if a
                # batch is re-run.
                upd = client.table("prediction_replay_corrections").upsert(
                    chunk, on_conflict="prediction_id,replay_batch_id"
                )
                # Custom wrapper auto-executes; result handling is best-effort.
                persisted += len(chunk)
            except Exception as e:
                logger.warning("replay persist chunk failed: %s", e)
        summary["persisted"] = persisted
        if purge_existing:
            summary["purged"] = purged
    else:
        summary["dry_run"] = True

    return summary


# ─── Single-signal inspector (audit) ─────────────────────────────────────────

async def inspect_signal(prediction_id: str) -> dict:
    """Re-run the replay for ONE signal with full bar-by-bar trace.

    Lets a human audit a correction: see the recorded entry, the measured
    EODHD→MT5 price offset, every TP/SL price, and each 1m bar's decision
    until resolution. Used by GET /api/replay/inspect/{id}."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "error", "error": "db_unavailable"}
    client = get_supabase_client()

    try:
        q = (client.table("prediction_logs").select(
            "id,symbol,model_type,ml_direction,ml_entry_price,timeframe,status,"
            "resolution_reason,exit_price,highest_profit_pips,lowest_drawdown_pips,"
            "created_at").eq("id", prediction_id).limit(1))
        res = q.execute() if hasattr(q, "execute") else q
        rows = res.data if hasattr(res, "data") else (
            res.get("data") if isinstance(res, dict) else []) or []
    except Exception as e:
        return {"status": "error", "error": f"fetch_failed: {str(e)[:120]}"}
    if not rows:
        return {"status": "error", "error": "prediction_id not found"}

    sig = rows[0]
    symbol = sig.get("symbol") or ""
    sym_bars = await asyncio.to_thread(_load_all_1m_bars_sync, symbol)
    ts_keys = [b["ts"] for b in sym_bars]

    trace: list = []
    result = await replay_signal_row(sig, symbol_bars=sym_bars, ts_keys=ts_keys,
                                      batch_id=None, trace=trace)

    return {
        "status": "ok",
        "prediction_id": prediction_id,
        "original": {
            "status": sig.get("status"),
            "resolution_reason": sig.get("resolution_reason"),
            "entry_price": sig.get("ml_entry_price"),
            "exit_price": sig.get("exit_price"),
            "highest_profit_pips": sig.get("highest_profit_pips"),
            "lowest_drawdown_pips": sig.get("lowest_drawdown_pips"),
            "direction": sig.get("ml_direction"),
            "timeframe": sig.get("timeframe"),
            "created_at": sig.get("created_at"),
        },
        "corrected": {
            "status": result.get("corrected_status"),
            "resolution_reason": result.get("corrected_resolution_reason"),
            "target_hit": result.get("corrected_target_hit"),
            "exit_price": result.get("corrected_exit_price"),
            "exit_at": result.get("corrected_exit_at"),
            "mfe_pips": result.get("corrected_mfe_pips"),
            "mae_pips": result.get("corrected_mae_pips"),
            "time_to_resolution_minutes": result.get("corrected_time_to_resolution_minutes"),
        },
        "replay_status": result.get("replay_status"),
        "outcome_flipped": result.get("outcome_flipped"),
        "diagnostics": result.get("_diagnostics"),
        "bar_trace": trace,
    }
