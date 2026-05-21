"""
Walk-forward TP/SL designer — distribution-based, overfit-resistant.

Why this exists
---------------
The grid-search optimizer (tp_sl_optimizer.py) maximises in-sample net
P&L. On a near-zero-edge system that just curve-fits the noise of one
history — it spat out absurd configs (TP=370pt, "+190k pip"). This
module instead does what the user actually asked for:

  1. Each historical signal is followed on the 1m chart; the replay
     already recorded its max favourable excursion (MFE — how far price
     ran) and max adverse excursion (MAE — how deep it dipped).
  2. TP is set where price ACTUALLY tends to reach — a percentile of the
     MFE distribution (default median).
  3. SL is set just beyond the typical drawdown of WINNING signals — a
     high percentile of the MAE-of-winners distribution — so a trade
     that would have won is not stopped out early.
  4. CRITICAL: this is derived on a TRAIN slice (older signals) and then
     scored on an untouched TEST slice (recent signals). If the derived
     config still beats the current one on data it never saw, it is
     real; if not, it was overfit. That train/test split is the honest
     "try both systems" the user wants.

Public API
----------
    await walk_forward_test(symbol, direction=None, model_type=None,
                             train_cutoff=..., tp_pct=50, sl_pct=85) → dict
    await walk_forward_all(train_cutoff=..., ...) → list[dict]
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import numpy as np

from services.tp_sl_optimizer import (
    get_current_config, simulate_tp_sl, distribution_stats,
)

logger = logging.getLogger(__name__)

DEFAULT_TRAIN_CUTOFF = "2026-04-20T00:00:00+00:00"  # ~1 month of test data
DEFAULT_TP_PERCENTILE = 50      # TP at the median MFE — price reaches it ~half the time
DEFAULT_SL_PERCENTILE = 85      # SL beyond p85 of winners' drawdown
MIN_TRAIN_SAMPLE = 40
MIN_TEST_SAMPLE = 20
SUPABASE_PAGE = 1000


# ---------------------------------------------------------------------------
# Fetch corrected signals WITH created_at (needed to split train/test)
# ---------------------------------------------------------------------------

async def _fetch_corrected_with_dates(
    client, symbol: str, direction: Optional[str],
    model_type: Optional[str], days: int,
) -> list[dict]:
    """Pull replay-corrected signals — keeps signal_created_at so the
    walk-forward split can be made."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows: list[dict] = []
    offset = 0
    while True:
        q = (client.table("prediction_replay_corrections").select(
            "prediction_id,symbol,model_type,direction,entry_price,"
            "signal_created_at,corrected_status,corrected_exit_price,"
            "corrected_mfe_pips,corrected_mae_pips,replay_status")
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

    # Only trustworthy, resolved rows.
    rows = [r for r in rows
            if r.get("replay_status") == "ok"
            and r.get("corrected_status") in ("completed", "stopped")]

    # Percentage-unit detection (USOIL stores TP/SL as % of entry).
    try:
        from services.target_config import get_symbol_config
        cfg = get_symbol_config(symbol)
        is_pct = bool(getattr(cfg, "is_percentage", False))
        pip_val = float(getattr(cfg, "pip_value", 1.0)) or 1.0
    except Exception:
        is_pct, pip_val = False, 1.0

    out: list[dict] = []
    for r in rows:
        mfe = abs(float(r.get("corrected_mfe_pips") or 0))
        mae = abs(float(r.get("corrected_mae_pips") or 0))
        entry = float(r.get("entry_price") or 0)
        exit_p = float(r.get("corrected_exit_price") or 0)
        status = r.get("corrected_status")
        direction_ = r.get("direction")
        if entry > 0 and exit_p > 0 and direction_ in ("BUY", "SELL"):
            raw = (exit_p - entry) if direction_ == "BUY" else (entry - exit_p)
            realized = (raw / entry) * 100.0 if is_pct else raw / pip_val
        else:
            realized = mfe if status == "completed" else -mae
        out.append({
            "id": r.get("prediction_id"),
            "created_at": r.get("signal_created_at"),
            "direction": direction_,
            "status": status,
            "mfe_pips": mfe,
            "mae_pips": mae,
            "realized_pnl_pips": realized,
        })
    return out


# ---------------------------------------------------------------------------
# Distribution-based TP/SL derivation
# ---------------------------------------------------------------------------

def derive_tp_sl(train_signals: list[dict],
                  tp_pct: float = DEFAULT_TP_PERCENTILE,
                  sl_pct: float = DEFAULT_SL_PERCENTILE) -> dict:
    """Derive TP/SL purely from the MFE/MAE distribution of the train set.

    TP = percentile(MFE, tp_pct)  — where price actually tends to reach.
    SL = percentile(MAE of winners, sl_pct) — beyond the typical drawdown
         of signals that would still have reached the derived TP, so we
         don't stop a would-be winner early.

    'Winners' are re-evaluated against the DERIVED TP (not the old one):
    a signal is a winner-candidate if its MFE >= TP_derived.
    """
    if not train_signals:
        return {"tp": None, "sl": None, "reason": "no train signals"}

    mfe = np.array([s["mfe_pips"] for s in train_signals], dtype=float)
    mae = np.array([s["mae_pips"] for s in train_signals], dtype=float)

    tp = float(np.percentile(mfe, tp_pct))
    if tp <= 0:
        tp = float(np.percentile(mfe[mfe > 0], tp_pct)) if (mfe > 0).any() else 0.0

    # Winners under the derived TP — their drawdown drives the SL.
    winner_mae = mae[mfe >= tp]
    if winner_mae.size >= 10:
        sl = float(np.percentile(winner_mae, sl_pct))
    else:
        # Too few winners to characterise — fall back to the overall MAE.
        sl = float(np.percentile(mae, sl_pct))

    return {
        "tp": round(tp, 4),
        "sl": round(sl, 4),
        "tp_percentile": tp_pct,
        "sl_percentile": sl_pct,
        "winners_in_train": int((mfe >= tp).sum()),
        "mfe_distribution": distribution_stats(list(mfe)),
        "mae_winners_distribution": distribution_stats(list(winner_mae)) if winner_mae.size else {},
    }


# ---------------------------------------------------------------------------
# Walk-forward: derive on train, score on test
# ---------------------------------------------------------------------------

async def walk_forward_test(
    symbol: str,
    direction: Optional[str] = None,
    model_type: Optional[str] = None,
    train_cutoff: str = DEFAULT_TRAIN_CUTOFF,
    days: int = 120,
    tp_pct: float = DEFAULT_TP_PERCENTILE,
    sl_pct: float = DEFAULT_SL_PERCENTILE,
) -> dict:
    """Derive TP/SL on signals before `train_cutoff`, then score current vs
    derived config on signals after it (data the derivation never saw)."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "error", "error": "db_unavailable"}
    client = get_supabase_client()

    try:
        cutoff = datetime.fromisoformat(train_cutoff.replace("Z", "+00:00"))
    except ValueError:
        return {"status": "error", "error": f"bad train_cutoff: {train_cutoff}"}

    signals = await _fetch_corrected_with_dates(client, symbol, direction, model_type, days)
    out: dict = {
        "status": "ok", "symbol": symbol, "direction": direction,
        "model_type": model_type, "train_cutoff": train_cutoff,
        "total_signals": len(signals),
    }
    if not signals:
        out["status"] = "no_data"
        return out

    def _parse(v):
        try:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except Exception:
            return None

    train = [s for s in signals if (_parse(s["created_at"]) or cutoff) < cutoff]
    test = [s for s in signals if (_parse(s["created_at"]) or cutoff) >= cutoff]
    out["train_size"] = len(train)
    out["test_size"] = len(test)

    if len(train) < MIN_TRAIN_SAMPLE or len(test) < MIN_TEST_SAMPLE:
        out["status"] = "insufficient_data"
        out["reason"] = (f"train={len(train)} (need ≥{MIN_TRAIN_SAMPLE}), "
                          f"test={len(test)} (need ≥{MIN_TEST_SAMPLE})")
        return out

    # ── Derive TP/SL from the TRAIN distribution ────────────────────────────
    derived = derive_tp_sl(train, tp_pct=tp_pct, sl_pct=sl_pct)
    out["derived"] = derived
    if not derived.get("tp") or not derived.get("sl"):
        out["status"] = "derivation_failed"
        return out

    # ── Current config ──────────────────────────────────────────────────────
    current_cfg = get_current_config(symbol)
    cur_tp = current_cfg.get("tp_pips") or 0
    cur_sl = current_cfg.get("sl_pips") or 0
    out["current_config"] = {"tp": cur_tp, "sl": cur_sl}

    # ── Score BOTH on the untouched TEST slice ──────────────────────────────
    sim_current = simulate_tp_sl(test, cur_tp, cur_sl) if (cur_tp and cur_sl) else None
    sim_derived = simulate_tp_sl(test, derived["tp"], derived["sl"])

    out["test_current"] = sim_current
    out["test_derived"] = sim_derived

    # ── Verdict ─────────────────────────────────────────────────────────────
    if sim_current:
        delta = sim_derived["net_pnl"] - sim_current["net_pnl"]
        out["oos_net_pnl_delta"] = round(delta, 2)
        out["derived_beats_current_oos"] = bool(delta > 0)
        # Per-trade is the honest figure — total scales with sample size.
        cur_avg = sim_current.get("avg_pnl_per_trade") or 0
        der_avg = sim_derived.get("avg_pnl_per_trade") or 0
        out["oos_avg_pnl_per_trade"] = {"current": cur_avg, "derived": der_avg}
        out["verdict"] = (
            "derived config holds up out-of-sample" if delta > 0
            else "derived config does NOT beat current out-of-sample — likely overfit"
        )
    else:
        out["verdict"] = "no current config to compare"

    return out


async def walk_forward_all(
    train_cutoff: str = DEFAULT_TRAIN_CUTOFF,
    days: int = 120,
    tp_pct: float = DEFAULT_TP_PERCENTILE,
    sl_pct: float = DEFAULT_SL_PERCENTILE,
    symbols: Optional[list[str]] = None,
) -> list[dict]:
    """Run the walk-forward test for every symbol × direction."""
    symbols = symbols or ["XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"]
    results: list[dict] = []
    for sym in symbols:
        for direction in ("BUY", "SELL"):
            try:
                r = await walk_forward_test(
                    sym, direction=direction, train_cutoff=train_cutoff,
                    days=days, tp_pct=tp_pct, sl_pct=sl_pct)
                results.append(r)
            except Exception as e:
                logger.exception("[walkforward] %s %s failed: %s", sym, direction, e)
                results.append({"status": "error", "symbol": sym,
                                 "direction": direction, "error": str(e)[:160]})
    return results
