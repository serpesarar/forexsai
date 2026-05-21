"""
Candle-based replay of resolved signals — honest MFE/MAE + post-resolution drift.

Why this exists
---------------
The original TP/SL optimizer (services/tp_sl_optimizer.py) builds its win/loss
distribution from the `highest_profit_pips` and `lowest_drawdown_pips` columns
on prediction_logs. Those columns are written by signal_lifecycle.py while the
signal is alive — and were corrupted by the pre-entry wick leak (commit 32033c6
fix). Even now, they only describe "from open to close" and miss two things
the user explicitly asked for:

  1. **Pre-resolution candle truth** — recompute MFE/MAE from the actual 5m
     candle stream between `created_at` and the resolution timestamp. This
     ignores any junk stored on the row.
  2. **Post-resolution drift** — what did price do in the N candles AFTER
     TP or SL fired? Tells us whether we exited too early (price kept
     extending in our favor → widen TP) or just in time (price reversed
     immediately → current TP is right).

Granularity note
----------------
MT5 bridge persists 5m bars to candle_cache; 1m is optional and not stored
historically. We use 5m as the replay primitive — 20 post-resolution bars =
100 minutes of forward look, which captures the local extension/reversal the
user wants to study without needing 1m archives we don't have.

Public API
----------
    await replay_signal(signal_row, post_bars=20) → dict
    await enrich_signals_with_replay(signals, post_bars=20) → list[dict]
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 5m bridges to 1 bar = 5 minutes. 20 bars = 100 minutes post-resolution.
DEFAULT_REPLAY_TIMEFRAME = "5m"
DEFAULT_POST_BARS = 20
BAR_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600}


def _parse_iso(s: Any) -> Optional[datetime]:
    if not s:
        return None
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _pip_unit(symbol: str) -> tuple[float, bool]:
    """Return (pip_value, is_percentage)."""
    try:
        from services.target_config import get_symbol_config
        cfg = get_symbol_config(symbol)
        return float(getattr(cfg, "pip_value", 1.0)) or 1.0, bool(getattr(cfg, "is_percentage", False))
    except Exception:
        return 1.0, False


def _price_to_pips(diff: float, entry: float, pip_val: float, is_pct: bool) -> float:
    if entry <= 0:
        return 0.0
    if is_pct:
        return (diff / entry) * 100.0
    return diff / pip_val if pip_val > 0 else diff


async def _load_window_candles(symbol: str, timeframe: str,
                                start: datetime, end: datetime) -> list[dict]:
    """Pull candles for [start, end] inclusive. Uses candle_cache via
    candle_cache_store.load_candles, then time-filters in Python.

    Note: load_candles returns the most recent N — for old signals we may
    need to over-fetch and filter. We compute the needed bar count from
    the window size with 50% headroom.
    """
    try:
        from services.candle_cache_store import load_candles
    except Exception as e:
        logger.debug("[replay] candle_cache_store unavailable: %s", e)
        return []

    span_s = max(BAR_SECONDS.get(timeframe, 300), 60)
    needed = int(((end - start).total_seconds() / span_s) * 1.5) + 20
    # Cap to a sane upper bound to avoid hammering Supabase.
    needed = max(50, min(needed, 5000))

    # candle_cache_store.load_candles is sync; run in thread to avoid blocking.
    candles = await asyncio.to_thread(load_candles, symbol, timeframe, needed)
    if not candles:
        return []

    out = []
    for c in candles:
        ts_ms = c.get("timestamp")
        if not ts_ms:
            continue
        ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
        if start <= ts <= end:
            out.append({**c, "ts": ts})
    return out


async def replay_signal(signal_row: dict,
                         post_bars: int = DEFAULT_POST_BARS,
                         timeframe: str = DEFAULT_REPLAY_TIMEFRAME) -> dict:
    """Replay a single resolved signal against real candles.

    Returns a dict with:
      mfe_true_pips           — max favorable excursion DURING signal life
      mae_true_pips           — max adverse excursion DURING signal life
      replayed_bars           — bar count actually consumed (sanity check)
      post_extension_pips     — best favorable move in `post_bars` after exit
      post_reversal_pips      — worst adverse move in same window
      post_close_drift_pips   — close-to-close drift over the window
      post_bars_consumed      — actual post-resolution bars found
      replay_status           — 'ok' | 'no_entry' | 'no_candles' | 'incomplete'

    Pips are computed against the entry direction so positive=favorable.
    """
    sid = signal_row.get("id")
    symbol = signal_row.get("symbol") or ""
    direction = signal_row.get("ml_direction") or signal_row.get("direction") or ""
    entry = float(signal_row.get("ml_entry_price") or signal_row.get("entry_price") or 0)
    created_at = _parse_iso(signal_row.get("created_at"))
    # Resolution time — prefer outcome_results.updated_at if present, else
    # fall back to whatever the caller passed in (status_changed_at or
    # signal_lifecycle's last check). For now: best-effort.
    resolved_at = _parse_iso(
        signal_row.get("resolved_at")
        or signal_row.get("updated_at")
        or signal_row.get("closed_at")
    )

    result = {
        "id": sid,
        "mfe_true_pips": 0.0,
        "mae_true_pips": 0.0,
        "replayed_bars": 0,
        "post_extension_pips": 0.0,
        "post_reversal_pips": 0.0,
        "post_close_drift_pips": 0.0,
        "post_bars_consumed": 0,
        "replay_status": "ok",
    }

    if entry <= 0 or direction not in ("BUY", "SELL") or not created_at:
        result["replay_status"] = "no_entry"
        return result

    pip_val, is_pct = _pip_unit(symbol)
    span_s = BAR_SECONDS.get(timeframe, 300)

    # If we don't have a resolved_at, assume now (active) — caller should skip
    # active rows, but guard anyway.
    end_window = resolved_at or datetime.now(timezone.utc)
    post_end = end_window + timedelta(seconds=span_s * post_bars + span_s)

    candles = await _load_window_candles(symbol, timeframe, created_at, post_end)
    if not candles:
        result["replay_status"] = "no_candles"
        return result

    pre_bars = [c for c in candles if c["ts"] <= end_window]
    post_window = [c for c in candles if c["ts"] > end_window][:post_bars]

    if not pre_bars:
        result["replay_status"] = "incomplete"
        return result

    # ── Pre-resolution: true MFE/MAE ─────────────────────────────────────────
    mfe_price = entry
    mae_price = entry
    for c in pre_bars:
        h, l = c["high"], c["low"]
        if direction == "BUY":
            if h > mfe_price:
                mfe_price = h
            if l < mae_price:
                mae_price = l
        else:  # SELL
            if l < mfe_price or mfe_price == entry:
                # For SELL, favorable = price down. Track the lowest low.
                if l < mfe_price:
                    mfe_price = l
            if h > mae_price:
                mae_price = h

    if direction == "BUY":
        mfe_pips = _price_to_pips(mfe_price - entry, entry, pip_val, is_pct)
        mae_pips = _price_to_pips(entry - mae_price, entry, pip_val, is_pct)
    else:
        mfe_pips = _price_to_pips(entry - mfe_price, entry, pip_val, is_pct)
        mae_pips = _price_to_pips(mae_price - entry, entry, pip_val, is_pct)

    result["mfe_true_pips"] = round(max(0.0, mfe_pips), 3)
    result["mae_true_pips"] = round(max(0.0, mae_pips), 3)
    result["replayed_bars"] = len(pre_bars)

    # ── Post-resolution: extension / reversal over N bars ────────────────────
    if post_window:
        # Anchor = close of the last pre-resolution bar (best proxy for exit
        # price when exit_price column is missing or unreliable).
        anchor = pre_bars[-1]["close"]
        post_high = max(c["high"] for c in post_window)
        post_low = min(c["low"] for c in post_window)
        post_close = post_window[-1]["close"]

        if direction == "BUY":
            ext = _price_to_pips(post_high - anchor, entry, pip_val, is_pct)
            rev = _price_to_pips(anchor - post_low, entry, pip_val, is_pct)
            drift = _price_to_pips(post_close - anchor, entry, pip_val, is_pct)
        else:
            ext = _price_to_pips(anchor - post_low, entry, pip_val, is_pct)
            rev = _price_to_pips(post_high - anchor, entry, pip_val, is_pct)
            drift = _price_to_pips(anchor - post_close, entry, pip_val, is_pct)

        result["post_extension_pips"] = round(max(0.0, ext), 3)
        result["post_reversal_pips"] = round(max(0.0, rev), 3)
        result["post_close_drift_pips"] = round(drift, 3)
        result["post_bars_consumed"] = len(post_window)
    else:
        result["replay_status"] = "incomplete"

    return result


async def enrich_signals_with_replay(signals: list[dict],
                                       post_bars: int = DEFAULT_POST_BARS,
                                       timeframe: str = DEFAULT_REPLAY_TIMEFRAME,
                                       concurrency: int = 8) -> list[dict]:
    """Batch-replay a list of signal rows. Returns a NEW list of enriched dicts.

    Original keys are preserved; replay output is merged in. On failure for
    a single row, its replay fields default to 0 and replay_status flags the
    reason — the caller decides whether to fall back to stored MFE/MAE.
    """
    sem = asyncio.Semaphore(max(1, concurrency))

    async def _one(row: dict) -> dict:
        async with sem:
            try:
                rep = await replay_signal(row, post_bars=post_bars, timeframe=timeframe)
            except Exception as e:
                logger.debug("[replay] signal %s failed: %s", row.get("id"), e)
                rep = {"replay_status": "exception"}
            return {**row, **rep}

    return await asyncio.gather(*[_one(s) for s in signals])


def summarize_post_drift(enriched: list[dict]) -> dict:
    """Aggregate post-resolution drift across a batch — diagnoses whether the
    current TPs are leaving meat on the table.

    Returns:
      avg_extension_pips     — mean of favorable continuation
      avg_reversal_pips      — mean of adverse reversal
      p50/p75/p90_extension  — extension distribution
      exits_too_early_pct    — % of signals where extension > 50% of MFE during life
                               (price kept going our way well past exit)
      exits_well_timed_pct   — % where reversal exceeded extension (TP was right)
    """
    if not enriched:
        return {}
    rows = [e for e in enriched
            if e.get("replay_status") == "ok" and e.get("post_bars_consumed", 0) > 0]
    if not rows:
        return {"n": 0}

    import numpy as np
    ext = np.array([float(r.get("post_extension_pips") or 0) for r in rows])
    rev = np.array([float(r.get("post_reversal_pips") or 0) for r in rows])
    mfe = np.array([float(r.get("mfe_true_pips") or 0) for r in rows])

    too_early = int(((ext > 0.5 * mfe) & (mfe > 0)).sum())
    well_timed = int((rev >= ext).sum())

    return {
        "n": len(rows),
        "avg_extension_pips": round(float(ext.mean()), 2),
        "avg_reversal_pips": round(float(rev.mean()), 2),
        "p50_extension": round(float(np.percentile(ext, 50)), 2),
        "p75_extension": round(float(np.percentile(ext, 75)), 2),
        "p90_extension": round(float(np.percentile(ext, 90)), 2),
        "exits_too_early_pct": round(100.0 * too_early / len(rows), 1),
        "exits_well_timed_pct": round(100.0 * well_timed / len(rows), 1),
    }
