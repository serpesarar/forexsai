"""
Walk-forward TP/SL designer — distribution-based, overfit-resistant,
order-aware.

Method
------
1. TRAIN slice (signals before train_cutoff): read each signal's MFE/MAE
   (already recorded by the 1m replay) and derive a TP/SL:
     - TP = percentile of the MFE distribution (where price reaches)
     - SL = high percentile of WINNERS' MAE (beyond their drawdown)
2. TEST slice (signals after the cutoff — never seen by the derivation):
   RE-WALK each signal on the real 1m bars with both the current config
   and the derived config. This is order-aware (uses the OHLC bar-path
   heuristic for an in-bar TP+SL) — NOT the aggregate-MFE/MAE shortcut,
   which mis-resolves ambiguity via a stale status field.
3. Compare current vs derived on the test slice. If derived wins on data
   it never saw, it is real; if not, it was overfit.

Public API
----------
    await walk_forward_test(symbol, direction=..., ...) → dict
    await walk_forward_all(...) → list[dict]
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import numpy as np

from services.tp_sl_optimizer import get_current_config, distribution_stats
from services.signal_replay_1m import (
    _load_all_1m_bars_sync, _slice_bars, _parse_iso, _max_hold_minutes,
)

logger = logging.getLogger(__name__)

DEFAULT_TRAIN_CUTOFF = "2026-04-20T00:00:00+00:00"
DEFAULT_TP_PERCENTILE = 50
DEFAULT_SL_PERCENTILE = 85
MIN_TRAIN_SAMPLE = 40
MIN_TEST_SAMPLE = 20
SUPABASE_PAGE = 1000


# ---------------------------------------------------------------------------
# Fetch corrected signals (with created_at + entry for the re-walk)
# ---------------------------------------------------------------------------

async def _fetch_corrected(client, symbol: str, direction: Optional[str],
                            model_type: Optional[str], days: int) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows: list[dict] = []
    offset = 0
    while True:
        q = (client.table("prediction_replay_corrections").select(
            "prediction_id,symbol,model_type,direction,entry_price,timeframe,"
            "signal_created_at,corrected_status,corrected_mfe_pips,"
            "corrected_mae_pips,replay_status")
            .eq("symbol", symbol)
            .gte("signal_created_at", since)
            .order("signal_created_at", desc=False)
            .range(offset, offset + SUPABASE_PAGE - 1))
        if direction in ("BUY", "SELL"):
            q = q.eq("direction", direction)
        if model_type:
            q = q.eq("model_type", model_type)
        res = q.execute() if hasattr(q, "execute") else q
        page = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
        if not page:
            break
        rows.extend(page)
        if len(page) < SUPABASE_PAGE:
            break
        offset += SUPABASE_PAGE
    return [r for r in rows
            if r.get("replay_status") == "ok"
            and r.get("corrected_status") in ("completed", "stopped")]


# ---------------------------------------------------------------------------
# Order-aware single-trade evaluation on real 1m bars
# ---------------------------------------------------------------------------

def evaluate_tpsl(bars: list[dict], entry: float, direction: str,
                   tp_price: float, sl_price: float) -> str:
    """Walk 1m bars; return 'win' | 'loss' | 'timeout' for one (TP, SL).

    In-bar TP+SL ambiguity uses the OHLC bar-path heuristic: a bullish bar
    (close>=open) travels open→low→high→close, a bearish one the reverse."""
    for bar in bars:
        h = float(bar["high"]); l = float(bar["low"])
        o = float(bar.get("open") or 0); c = float(bar.get("close") or 0)
        if direction == "BUY":
            tp_hit = h >= tp_price
            sl_hit = l <= sl_price
        else:
            tp_hit = l <= tp_price
            sl_hit = h >= sl_price
        if tp_hit and sl_hit:
            bullish = c >= o
            tp_first = (not bullish) if direction == "BUY" else bullish
            return "win" if tp_first else "loss"
        if tp_hit:
            return "win"
        if sl_hit:
            return "loss"
    return "timeout"


def _score_config(test_signals: list[dict], symbol_bars: list[dict],
                   ts_keys: list, tp_pips: float, sl_pips: float,
                   symbol: str) -> dict:
    """Re-walk every test signal with one (TP, SL); aggregate net pips."""
    from services.target_config import get_symbol_config
    cfg = get_symbol_config(symbol)
    is_pct = bool(getattr(cfg, "is_percentage", False))

    wins = losses = timeouts = 0
    for s in test_signals:
        created = _parse_iso(s["created_at"])
        entry = float(s.get("entry_price") or 0)
        direction = s.get("direction")
        if not created or entry <= 0 or direction not in ("BUY", "SELL"):
            continue
        # TP/SL prices from pip distances (pct symbols: pips = % of entry).
        if is_pct:
            tp_off = entry * (tp_pips / 100.0)
            sl_off = entry * (sl_pips / 100.0)
        else:
            tp_off = tp_pips
            sl_off = sl_pips
        if direction == "BUY":
            tp_price = entry + tp_off
            sl_price = entry - sl_off
        else:
            tp_price = entry - tp_off
            sl_price = entry + sl_off

        window_end = created + timedelta(minutes=_max_hold_minutes(s.get("timeframe")))
        bars = _slice_bars(symbol_bars, ts_keys, created, window_end)
        if not bars:
            continue
        outcome = evaluate_tpsl(bars, entry, direction, tp_price, sl_price)
        if outcome == "win":
            wins += 1
        elif outcome == "loss":
            losses += 1
        else:
            timeouts += 1

    resolved = wins + losses
    net = wins * tp_pips - losses * sl_pips
    total = wins + losses + timeouts
    return {
        "tp_pips": tp_pips, "sl_pips": sl_pips,
        "wins": wins, "losses": losses, "timeouts": timeouts,
        "win_rate": round(100 * wins / resolved, 2) if resolved else None,
        "net_pnl_pips": round(net, 2),
        "avg_pnl_per_trade": round(net / total, 4) if total else 0,
        "trigger_rate_pct": round(100 * resolved / total, 1) if total else 0,
        "rr_ratio": round(tp_pips / sl_pips, 2) if sl_pips else None,
    }


# ---------------------------------------------------------------------------
# Distribution-based derivation (TRAIN only)
# ---------------------------------------------------------------------------

def derive_tp_sl(train_rows: list[dict], tp_pct: float, sl_pct: float) -> dict:
    """TP = percentile of MFE; SL = high percentile of winners' MAE."""
    mfe = np.array([abs(float(r.get("corrected_mfe_pips") or 0)) for r in train_rows])
    mae = np.array([abs(float(r.get("corrected_mae_pips") or 0)) for r in train_rows])
    if mfe.size == 0:
        return {"tp": None, "sl": None}
    tp = float(np.percentile(mfe, tp_pct))
    if tp <= 0 and (mfe > 0).any():
        tp = float(np.percentile(mfe[mfe > 0], tp_pct))
    winner_mae = mae[mfe >= tp]
    sl = float(np.percentile(winner_mae if winner_mae.size >= 10 else mae, sl_pct))
    return {
        "tp": round(tp, 4), "sl": round(sl, 4),
        "tp_percentile": tp_pct, "sl_percentile": sl_pct,
        "winners_in_train": int((mfe >= tp).sum()),
        "mfe_distribution": distribution_stats(list(mfe)),
        "mae_winners_distribution": distribution_stats(list(winner_mae)) if winner_mae.size else {},
    }


# ---------------------------------------------------------------------------
# Walk-forward
# ---------------------------------------------------------------------------

async def walk_forward_test(
    symbol: str,
    direction: Optional[str] = None,
    model_type: Optional[str] = None,
    train_cutoff: str = DEFAULT_TRAIN_CUTOFF,
    days: int = 120,
    tp_pct: float = DEFAULT_TP_PERCENTILE,
    sl_pct: float = DEFAULT_SL_PERCENTILE,
    _symbol_bars: Optional[list] = None,
    _ts_keys: Optional[list] = None,
) -> dict:
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "error", "error": "db_unavailable"}
    client = get_supabase_client()

    try:
        cutoff = datetime.fromisoformat(train_cutoff.replace("Z", "+00:00"))
    except ValueError:
        return {"status": "error", "error": f"bad train_cutoff: {train_cutoff}"}

    rows = await _fetch_corrected(client, symbol, direction, model_type, days)
    out: dict = {
        "status": "ok", "symbol": symbol, "direction": direction,
        "model_type": model_type, "train_cutoff": train_cutoff,
        "total_signals": len(rows),
    }
    if not rows:
        out["status"] = "no_data"
        return out

    train = [r for r in rows if (_parse_iso(r["signal_created_at"]) or cutoff) < cutoff]
    test = [r for r in rows if (_parse_iso(r["signal_created_at"]) or cutoff) >= cutoff]
    out["train_size"] = len(train)
    out["test_size"] = len(test)
    if len(train) < MIN_TRAIN_SAMPLE or len(test) < MIN_TEST_SAMPLE:
        out["status"] = "insufficient_data"
        out["reason"] = (f"train={len(train)} (need ≥{MIN_TRAIN_SAMPLE}), "
                          f"test={len(test)} (need ≥{MIN_TEST_SAMPLE})")
        return out

    derived = derive_tp_sl(train, tp_pct, sl_pct)
    out["derived"] = derived
    if not derived.get("tp") or not derived.get("sl"):
        out["status"] = "derivation_failed"
        return out

    current_cfg = get_current_config(symbol)
    cur_tp = current_cfg.get("tp_pips") or 0
    cur_sl = current_cfg.get("sl_pips") or 0
    out["current_config"] = {"tp": cur_tp, "sl": cur_sl}

    # 1m bars for the order-aware re-walk (load once; reusable across a batch).
    symbol_bars = _symbol_bars
    ts_keys = _ts_keys
    if symbol_bars is None:
        symbol_bars = await asyncio.to_thread(_load_all_1m_bars_sync, symbol)
        ts_keys = [b["ts"] for b in symbol_bars]
    if not symbol_bars:
        out["status"] = "no_candles"
        return out

    # Normalise test rows for _score_config.
    test_norm = [{
        "created_at": r["signal_created_at"],
        "entry_price": r.get("entry_price"),
        "direction": r.get("direction"),
        "timeframe": r.get("timeframe"),
    } for r in test]

    sim_current = (_score_config(test_norm, symbol_bars, ts_keys, cur_tp, cur_sl, symbol)
                   if (cur_tp and cur_sl) else None)
    sim_derived = _score_config(test_norm, symbol_bars, ts_keys,
                                 derived["tp"], derived["sl"], symbol)
    out["test_current"] = sim_current
    out["test_derived"] = sim_derived

    if sim_current:
        d_avg = sim_derived["avg_pnl_per_trade"]
        c_avg = sim_current["avg_pnl_per_trade"]
        out["oos_avg_delta"] = round(d_avg - c_avg, 4)
        out["derived_beats_current_oos"] = bool(d_avg > c_avg)
        out["verdict"] = (
            "derived config holds up out-of-sample"
            if d_avg > c_avg else
            "derived config does NOT beat current out-of-sample — likely overfit"
        )
    else:
        out["verdict"] = "no current config to compare"
    return out


async def rolling_walk_forward(
    symbol: str,
    direction: Optional[str] = None,
    model_type: Optional[str] = None,
    days: int = 120,
    test_window_days: int = 12,
    min_train_days: int = 40,
    tp_pct: float = DEFAULT_TP_PERCENTILE,
    sl_pct: float = DEFAULT_SL_PERCENTILE,
    _symbol_bars: Optional[list] = None,
    _ts_keys: Optional[list] = None,
) -> dict:
    """Proper walk-forward analysis: roll multiple non-overlapping test
    windows forward in time. Each fold derives TP/SL on all data BEFORE
    the test window (expanding/anchored train) and scores it on that
    untouched window. The derived config may differ per fold — that is
    the point: it validates the DERIVATION METHOD, not one lucky config.
    A method that beats current across most folds is genuinely robust."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "error", "error": "db_unavailable"}
    client = get_supabase_client()

    rows = await _fetch_corrected(client, symbol, direction, model_type, days)
    out: dict = {"status": "ok", "symbol": symbol, "direction": direction,
                 "model_type": model_type, "total_signals": len(rows)}
    if len(rows) < MIN_TRAIN_SAMPLE + MIN_TEST_SAMPLE:
        out["status"] = "insufficient_data"
        return out

    rows.sort(key=lambda r: r.get("signal_created_at") or "")
    first = _parse_iso(rows[0]["signal_created_at"])
    last = _parse_iso(rows[-1]["signal_created_at"])
    if not first or not last:
        out["status"] = "error"; out["error"] = "unparseable dates"; return out

    current_cfg = get_current_config(symbol)
    cur_tp = current_cfg.get("tp_pips") or 0
    cur_sl = current_cfg.get("sl_pips") or 0
    out["current_config"] = {"tp": cur_tp, "sl": cur_sl}

    symbol_bars = _symbol_bars
    ts_keys = _ts_keys
    if symbol_bars is None:
        symbol_bars = await asyncio.to_thread(_load_all_1m_bars_sync, symbol)
        ts_keys = [b["ts"] for b in symbol_bars]
    if not symbol_bars:
        out["status"] = "no_candles"; return out

    folds: list[dict] = []
    test_start = first + timedelta(days=min_train_days)
    while test_start < last:
        test_end = test_start + timedelta(days=test_window_days)
        train = [r for r in rows if (_parse_iso(r["signal_created_at"]) or last) < test_start]
        test = [r for r in rows
                if test_start <= (_parse_iso(r["signal_created_at"]) or first) < test_end]
        if len(train) >= MIN_TRAIN_SAMPLE and len(test) >= MIN_TEST_SAMPLE:
            derived = derive_tp_sl(train, tp_pct, sl_pct)
            if derived.get("tp") and derived.get("sl"):
                test_norm = [{
                    "created_at": r["signal_created_at"],
                    "entry_price": r.get("entry_price"),
                    "direction": r.get("direction"),
                    "timeframe": r.get("timeframe"),
                } for r in test]
                sim_cur = (_score_config(test_norm, symbol_bars, ts_keys,
                                          cur_tp, cur_sl, symbol)
                           if (cur_tp and cur_sl) else None)
                sim_der = _score_config(test_norm, symbol_bars, ts_keys,
                                         derived["tp"], derived["sl"], symbol)
                folds.append({
                    "test_window": [test_start.date().isoformat(),
                                     test_end.date().isoformat()],
                    "train_size": len(train), "test_size": len(test),
                    "derived_tp": derived["tp"], "derived_sl": derived["sl"],
                    "current_avg": sim_cur["avg_pnl_per_trade"] if sim_cur else None,
                    "derived_avg": sim_der["avg_pnl_per_trade"],
                    "current_wr": sim_cur["win_rate"] if sim_cur else None,
                    "derived_wr": sim_der["win_rate"],
                    "derived_wins_fold": bool(
                        sim_cur and sim_der["avg_pnl_per_trade"] > sim_cur["avg_pnl_per_trade"]),
                })
        test_start = test_end

    out["folds"] = folds
    out["n_folds"] = len(folds)
    if not folds:
        out["status"] = "insufficient_data"
        out["reason"] = "no fold had enough train+test signals"
        return out

    wins = sum(1 for f in folds if f["derived_wins_fold"])
    # Sample-weighted mean avg/trade across all OOS test signals.
    tot = sum(f["test_size"] for f in folds)
    cur_w = sum((f["current_avg"] or 0) * f["test_size"] for f in folds) / tot if tot else 0
    der_w = sum(f["derived_avg"] * f["test_size"] for f in folds) / tot if tot else 0
    out["folds_derived_won"] = f"{wins}/{len(folds)}"
    out["oos_avg_per_trade"] = {"current": round(cur_w, 4), "derived": round(der_w, 4)}
    out["robust"] = bool(wins >= max(1, round(len(folds) * 0.7)))
    out["verdict"] = (
        f"derivation method ROBUST — beats current in {wins}/{len(folds)} "
        f"rolling windows" if out["robust"] else
        f"derivation method NOT robust — only {wins}/{len(folds)} windows"
    )

    # Final config to actually use: derive on ALL available data.
    final = derive_tp_sl(rows, tp_pct, sl_pct)
    out["final_recommended"] = {"tp": final.get("tp"), "sl": final.get("sl")}
    return out


async def rolling_walk_forward_all(days: int = 120,
                                    test_window_days: int = 12,
                                    min_train_days: int = 40,
                                    tp_pct: float = DEFAULT_TP_PERCENTILE,
                                    sl_pct: float = DEFAULT_SL_PERCENTILE,
                                    symbols: Optional[list[str]] = None) -> list[dict]:
    symbols = symbols or ["XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"]
    results: list[dict] = []
    for sym in symbols:
        bars = await asyncio.to_thread(_load_all_1m_bars_sync, sym)
        tsk = [b["ts"] for b in bars]
        for direction in ("BUY", "SELL"):
            try:
                results.append(await rolling_walk_forward(
                    sym, direction=direction, days=days,
                    test_window_days=test_window_days, min_train_days=min_train_days,
                    tp_pct=tp_pct, sl_pct=sl_pct, _symbol_bars=bars, _ts_keys=tsk))
            except Exception as e:
                logger.exception("[rolling-wf] %s %s failed: %s", sym, direction, e)
                results.append({"status": "error", "symbol": sym,
                                 "direction": direction, "error": str(e)[:160]})
    return results


async def walk_forward_all(train_cutoff: str = DEFAULT_TRAIN_CUTOFF,
                            days: int = 120,
                            tp_pct: float = DEFAULT_TP_PERCENTILE,
                            sl_pct: float = DEFAULT_SL_PERCENTILE,
                            symbols: Optional[list[str]] = None) -> list[dict]:
    symbols = symbols or ["XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"]
    results: list[dict] = []
    for sym in symbols:
        # Load each symbol's 1m bars ONCE, share across both directions.
        bars = await asyncio.to_thread(_load_all_1m_bars_sync, sym)
        tsk = [b["ts"] for b in bars]
        for direction in ("BUY", "SELL"):
            try:
                results.append(await walk_forward_test(
                    sym, direction=direction, train_cutoff=train_cutoff,
                    days=days, tp_pct=tp_pct, sl_pct=sl_pct,
                    _symbol_bars=bars, _ts_keys=tsk))
            except Exception as e:
                logger.exception("[walkforward] %s %s failed: %s", sym, direction, e)
                results.append({"status": "error", "symbol": sym,
                                 "direction": direction, "error": str(e)[:160]})
    return results
