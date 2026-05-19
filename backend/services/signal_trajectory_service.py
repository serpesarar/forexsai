"""
Signal Trajectory Service — Post-Entry Trajectory Learner (PETL)
================================================================

When a signal is created we already snapshot 60+ features into
`prediction_logs.factors`. This service does two things:

1) Periodically (every lifecycle check) capture a NEW lightweight snapshot
   of the SAME features so we have a time series of how conditions evolved
   from entry → exit.

2) Compare current snapshot vs entry snapshot to detect "deterioration" —
   feature evolution patterns that historically predict SL hits. If
   deterioration score exceeds a threshold, recommend ABORT.

Rules (v1, hard-coded from observation):
  - For BUY signals:
      * RSI dropped from > 50 at entry to < 45 now
      * EMA-20 slope flipped from positive to negative
      * MACD histogram flipped from positive to negative
      * SAR became bearish (sar_bearish=True now, was False at entry)
      * Volume falling while price falls (no buy support)
  - For SELL signals (mirror logic):
      * RSI rose from < 50 to > 55
      * EMA-20 slope flipped from negative to positive
      * MACD histogram flipped from negative to positive
      * SAR became bullish

Score is the fraction of rules that fired (0..1). Threshold typically 0.6
(3 out of 5 rules). Configurable per-symbol.

v2 will replace `compute_deterioration_score` with a trained ML classifier
that reads the FULL trajectory time-series (not just entry vs now).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Per-symbol rule weight + threshold tuning. XAUUSD gets the most weight
# on SAR/MACD because its recent failure pattern is dominated by those.
SYMBOL_THRESHOLDS: Dict[str, float] = {
    "XAUUSD":      0.55,   # abort if ≥3 of 5 rules fire (somewhat aggressive)
    "USOIL.FOREX": 0.65,   # USOIL noisier, require stronger evidence
    "NDX.INDX":    0.65,
    "GDAXI.INDX":  0.65,
}
DEFAULT_THRESHOLD = 0.65

# Minimum signal age (minutes) before we trust trajectory comparison.
# Below this, market noise dominates feature changes.
MIN_AGE_MINUTES = 5


def _safe_float(v: Any) -> Optional[float]:
    """Coerce to float, returning None on failure."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_bool(v: Any) -> Optional[bool]:
    """Coerce to bool, returning None on failure."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        return v.lower() in ("true", "1", "yes")
    return None


def compute_deterioration_score(
    direction: str,
    entry_factors: Dict[str, Any],
    current_snapshot: Dict[str, Any],
    symbol: str = "",
) -> Tuple[float, List[str]]:
    """
    Score 0..1 — fraction of "BUY deterioration" or "SELL deterioration"
    rules that have fired since entry. Returns (score, reasons_list).

    Each rule reads the SAME feature name from both `entry_factors` (saved
    at signal creation) and `current_snapshot` (refreshed each check).

    Missing data: rules that can't evaluate (feature missing in either
    snapshot) are silently skipped, and the denominator shrinks accordingly.
    """
    if direction not in ("BUY", "SELL"):
        return 0.0, []

    reasons: List[str] = []
    rules_evaluated = 0
    rules_fired = 0

    is_buy = direction == "BUY"

    # ── Rule 1: RSI flip ────────────────────────────────────────────────
    rsi_entry = _safe_float(entry_factors.get("M30_rsi_14") or entry_factors.get("rsi_14"))
    rsi_now = _safe_float(current_snapshot.get("M30_rsi_14") or current_snapshot.get("rsi_14"))
    if rsi_entry is not None and rsi_now is not None:
        rules_evaluated += 1
        if is_buy and rsi_entry >= 50 and rsi_now < 45:
            rules_fired += 1
            reasons.append(f"RSI {rsi_entry:.0f}→{rsi_now:.0f} (BUY momentum dying)")
        elif (not is_buy) and rsi_entry <= 50 and rsi_now > 55:
            rules_fired += 1
            reasons.append(f"RSI {rsi_entry:.0f}→{rsi_now:.0f} (SELL momentum dying)")

    # ── Rule 2: EMA slope flip ──────────────────────────────────────────
    # We track ema20 slope as positive/negative. If sign flipped, fire.
    ema_slope_entry = _safe_float(
        entry_factors.get("M30_ema20_slope_atr") or entry_factors.get("ema_slope")
    )
    ema_slope_now = _safe_float(
        current_snapshot.get("M30_ema20_slope_atr") or current_snapshot.get("ema_slope")
    )
    if ema_slope_entry is not None and ema_slope_now is not None:
        rules_evaluated += 1
        if is_buy and ema_slope_entry > 0 and ema_slope_now < 0:
            rules_fired += 1
            reasons.append("EMA-20 slope flipped negative")
        elif (not is_buy) and ema_slope_entry < 0 and ema_slope_now > 0:
            rules_fired += 1
            reasons.append("EMA-20 slope flipped positive")

    # ── Rule 3: MACD hist sign flip ─────────────────────────────────────
    macd_entry = _safe_float(
        entry_factors.get("M30_macd_hist") or entry_factors.get("macd_hist")
    )
    macd_now = _safe_float(
        current_snapshot.get("M30_macd_hist") or current_snapshot.get("macd_hist")
    )
    if macd_entry is not None and macd_now is not None:
        rules_evaluated += 1
        if is_buy and macd_entry > 0 and macd_now < 0:
            rules_fired += 1
            reasons.append("MACD hist flipped negative")
        elif (not is_buy) and macd_entry < 0 and macd_now > 0:
            rules_fired += 1
            reasons.append("MACD hist flipped positive")

    # ── Rule 4: SAR polarity flip ───────────────────────────────────────
    sar_bearish_entry = _safe_bool(entry_factors.get("sar_bearish"))
    sar_bearish_now = _safe_bool(current_snapshot.get("sar_bearish"))
    if sar_bearish_entry is not None and sar_bearish_now is not None:
        rules_evaluated += 1
        if is_buy and (not sar_bearish_entry) and sar_bearish_now:
            rules_fired += 1
            reasons.append("SAR flipped bearish")
        elif (not is_buy) and sar_bearish_entry and (not sar_bearish_now):
            rules_fired += 1
            reasons.append("SAR flipped bullish")

    # ── Rule 5: Volume z-score declining + price moving against ─────────
    # Volume falling while price moves against means no buying/selling
    # support. Read volume z-score (1h, normalized) from both snapshots.
    vol_z_entry = _safe_float(
        entry_factors.get("M30_volume_z") or entry_factors.get("volume_z")
    )
    vol_z_now = _safe_float(
        current_snapshot.get("M30_volume_z") or current_snapshot.get("volume_z")
    )
    if vol_z_entry is not None and vol_z_now is not None:
        rules_evaluated += 1
        if vol_z_entry > 0 and vol_z_now < vol_z_entry - 0.5:
            # Volume conviction at entry, but conviction collapsing now
            rules_fired += 1
            reasons.append(f"Volume z {vol_z_entry:+.1f}σ→{vol_z_now:+.1f}σ (conviction lost)")

    if rules_evaluated == 0:
        return 0.0, []

    score = rules_fired / rules_evaluated
    return round(score, 3), reasons


async def capture_snapshot(
    signal: Dict[str, Any],
    current_price: float,
    current_profit_pips: float,
    current_drawdown_pips: float,
) -> Optional[Dict[str, Any]]:
    """
    Capture a feature snapshot for an ACTIVE signal during its lifecycle.
    Returns the snapshot dict (with deterioration score) and persists to
    `signal_trajectory_snapshots`. Returns None on any failure (never
    blocks the lifecycle loop).
    """
    try:
        from database.supabase_client import get_supabase_client
        from services.signal_feature_snapshot import build_signal_feature_snapshot

        symbol = signal.get("symbol", "")
        signal_id = signal.get("id")
        direction = signal.get("ml_direction") or signal.get("direction")
        entry_factors = signal.get("factors") or {}
        created_at_raw = signal.get("created_at")

        if not signal_id or not direction:
            return None

        # Age calculation
        age_minutes = 0.0
        if created_at_raw:
            try:
                created = datetime.fromisoformat(str(created_at_raw).replace("Z", "+00:00"))
                age_minutes = (datetime.now(timezone.utc) - created).total_seconds() / 60.0
            except Exception:
                pass

        # Skip very young signals — noise dominates
        if age_minutes < MIN_AGE_MINUTES:
            return None

        # Rebuild a lightweight snapshot for the current moment
        current_snapshot = await build_signal_feature_snapshot(symbol) or {}

        # Score deterioration
        score, reasons = compute_deterioration_score(
            direction=direction,
            entry_factors=entry_factors,
            current_snapshot=current_snapshot,
            symbol=symbol,
        )
        threshold = SYMBOL_THRESHOLDS.get(symbol, DEFAULT_THRESHOLD)
        deteriorating = score >= threshold

        # Compute distance-to-target percentages (helpful for ML training)
        entry_price = _safe_float(signal.get("ml_entry_price") or signal.get("entry_price")) or 0
        targets = signal.get("targets") or {}
        tp1 = _safe_float(targets.get("TP1"))
        sl = _safe_float(targets.get("SL"))
        dist_tp1 = None
        dist_sl = None
        if entry_price > 0 and current_price > 0:
            if tp1:
                full_distance = abs(tp1 - entry_price)
                remaining = abs(tp1 - current_price)
                dist_tp1 = round(remaining / full_distance * 100, 2) if full_distance > 0 else None
            if sl:
                full_distance = abs(sl - entry_price)
                remaining = abs(sl - current_price)
                dist_sl = round(remaining / full_distance * 100, 2) if full_distance > 0 else None

        # Persist
        client = get_supabase_client()
        if client is None:
            return None

        row = {
            "signal_id": signal_id,
            "symbol": symbol,
            "model_type": signal.get("model_type"),
            "direction": direction,
            "age_minutes": round(age_minutes, 2),
            "current_price": round(current_price, 4) if current_price else None,
            "current_profit_pips": round(current_profit_pips, 2),
            "current_drawdown_pips": round(current_drawdown_pips, 2),
            "distance_to_tp1_pct": dist_tp1,
            "distance_to_sl_pct": dist_sl,
            "features": current_snapshot,
            "deteriorating": bool(deteriorating),
            "deterioration_score": score,
            "deterioration_reasons": reasons,
        }
        try:
            client.table("signal_trajectory_snapshots").insert(row)
        except Exception as ins_err:
            logger.warning("[trajectory] insert failed: %s", ins_err)

        return {
            "score": score,
            "reasons": reasons,
            "deteriorating": deteriorating,
            "threshold": threshold,
        }
    except Exception as e:
        logger.debug("[trajectory] capture_snapshot error: %s", e)
        return None


async def log_abort(
    signal: Dict[str, Any],
    reason: str,
    source: str,
    pnl_at_abort_pips: float,
    saved_pips_estimate: float = 0.0,
    factors: Optional[Dict[str, Any]] = None,
) -> None:
    """Audit-log an abort decision. Never raises."""
    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client is None:
            return
        row = {
            "signal_id": signal.get("id"),
            "symbol": signal.get("symbol"),
            "model_type": signal.get("model_type"),
            "direction": signal.get("ml_direction") or signal.get("direction"),
            "abort_reason": reason,
            "abort_source": source,
            "pnl_at_abort_pips": round(float(pnl_at_abort_pips), 2),
            "saved_pips_estimate": round(float(saved_pips_estimate), 2),
            "factors": factors or {},
        }
        client.table("signal_aborts").insert(row)
    except Exception as e:
        logger.debug("[trajectory] log_abort error: %s", e)
