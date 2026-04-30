"""
Failure Tagger — Layer 1 of the AI-ops loop.

Pure rule-based: takes a resolved failed signal (with its enriched factors
snapshot from signal_feature_snapshot.py) and assigns root-cause tags.

These tags become the GROUP-BY keys for failure_clusters, which are then sent
to DeepSeek for strategic analysis (Layer 2).

No LLM dependency. Free. Runs over thousands of signals in seconds.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def parse_factors(raw: Any) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


def _f(v: Any) -> Optional[float]:
    if v in (None, "", []):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f


def tag_failure(prediction: dict, outcome: Optional[dict] = None) -> Optional[dict]:
    """Return a dict of {failure_reason, signature, ...} or None if not a failure."""
    direction = prediction.get("ml_direction") or "HOLD"
    if direction not in ("BUY", "SELL"):
        return None

    status = prediction.get("status")
    resolution = (prediction.get("resolution_reason") or "").lower()
    factors = parse_factors(prediction.get("factors"))

    # Definition of "failure" — broader than just sl_hit
    is_failure = (
        status == "stopped"
        or resolution in ("sl_hit", "tp1_3_hit_then_sl",
                          "window_resolve_negative", "direction_flip")
    )
    if not is_failure:
        return None

    tags: list[str] = []
    sig_parts: list[str] = []

    # Use snapshot warning flags first (these are pre-computed, reliable)
    if factors.get("near_resistance") is True and direction == "BUY":
        tags.append("BUY_INTO_RESISTANCE")
        sig_parts.append("near_resistance")
    if factors.get("near_support") is True and direction == "SELL":
        tags.append("SELL_INTO_SUPPORT")
        sig_parts.append("near_support")

    if factors.get("overbought") is True and direction == "BUY":
        tags.append("RSI_OVERBOUGHT_BUY")
        sig_parts.append("rsi_overbought_buy")
    if factors.get("oversold") is True and direction == "SELL":
        tags.append("RSI_OVERSOLD_SELL")
        sig_parts.append("rsi_oversold_sell")

    if factors.get("exhaustion_up") is True and direction == "BUY":
        tags.append("EXHAUSTION_UP_BUY")
        sig_parts.append("exhaustion_up")
    if factors.get("exhaustion_down") is True and direction == "SELL":
        tags.append("EXHAUSTION_DOWN_SELL")
        sig_parts.append("exhaustion_down")

    if factors.get("bb_extreme_upper") is True and direction == "BUY":
        tags.append("BB_UPPER_BUY")
        sig_parts.append("bb_upper_buy")
    if factors.get("bb_extreme_lower") is True and direction == "SELL":
        tags.append("BB_LOWER_SELL")
        sig_parts.append("bb_lower_sell")

    # SAR position contradicts direction
    sar_above = factors.get("sar_bearish")  # True if SAR is above price = bearish
    if sar_above is True and direction == "BUY":
        tags.append("SAR_AGAINST_BUY")
        sig_parts.append("sar_against")
    if sar_above is False and direction == "SELL":
        tags.append("SAR_AGAINST_SELL")
        sig_parts.append("sar_against")

    # MTF trend mismatch — using regime label
    mtf = factors.get("mtf_trend")
    if mtf == "all_down" and direction == "BUY":
        tags.append("AGAINST_MTF_TREND_BUY")
        sig_parts.append("against_mtf")
    elif mtf == "all_up" and direction == "SELL":
        tags.append("AGAINST_MTF_TREND_SELL")
        sig_parts.append("against_mtf")

    # Regime context
    regime = factors.get("regime_label") or "unknown"
    sig_parts.append(f"regime={regime}")

    # Volatility regime
    vol_regime = factors.get("volatility_regime")
    if vol_regime == "high":
        tags.append("HIGH_VOLATILITY")
    elif vol_regime == "low":
        tags.append("LOW_VOLATILITY_RANGING")

    # Fallback indicator-level checks (covers signals logged before snapshot deploy)
    base_tf = "M30" if "M30_rsi_14" in factors else "M15"
    rsi = _f(factors.get(f"{base_tf}_rsi_14") or factors.get("rsi_14"))
    if rsi is not None:
        if direction == "BUY" and rsi > 70 and "RSI_OVERBOUGHT_BUY" not in tags:
            tags.append("RSI_OVERBOUGHT_BUY")
            sig_parts.append("rsi_overbought_buy")
        if direction == "SELL" and rsi < 30 and "RSI_OVERSOLD_SELL" not in tags:
            tags.append("RSI_OVERSOLD_SELL")
            sig_parts.append("rsi_oversold_sell")

    adx = _f(factors.get(f"{base_tf}_adx_14") or factors.get("adx"))
    if adx is not None and adx < 18:
        tags.append("LOW_ADX_RANGING")
        sig_parts.append("low_adx")

    # Resolution-derived tags
    if resolution == "tp1_3_hit_then_sl":
        tags.append("TP_GREED_REVERSAL")
        sig_parts.append("tp_greed")
    if resolution == "direction_flip":
        tags.append("REGIME_FLIP")
        sig_parts.append("regime_flip")

    # Outcome MFE/MAE pattern (fake-move detection)
    if outcome:
        mfe = _f(outcome.get("highest_profit_pips")) or 0
        mae = _f(outcome.get("lowest_drawdown_pips")) or 0
        if mfe > 5 and mae > mfe * 1.5:
            tags.append("FAKE_MOVE_REVERSAL")
            sig_parts.append("fake_move")
        if mfe < 5 and mae > 15:
            tags.append("STOP_HUNT")
            sig_parts.append("stop_hunt")

    if not tags:
        tags = ["UNKNOWN_REASON"]
        sig_parts.append("unknown")

    # Build a stable signature for clustering — sort + deduplicate
    sig = "|".join(sorted(set(sig_parts)))

    # Recommendation hints (used by orchestrator if it wants to skip LLM call)
    recommendation = ""
    if "BUY_INTO_RESISTANCE" in tags:
        recommendation = "Reject BUY when near_resistance=true AND direction=BUY"
    elif "SELL_INTO_SUPPORT" in tags:
        recommendation = "Reject SELL when near_support=true"
    elif "RSI_OVERBOUGHT_BUY" in tags or "RSI_OVERSOLD_SELL" in tags:
        recommendation = "Reduce confidence by 30 when RSI extreme contradicts direction"
    elif "TP_GREED_REVERSAL" in tags:
        recommendation = "Trail SL to BE after TP1 hit"
    elif "AGAINST_MTF_TREND_BUY" in tags or "AGAINST_MTF_TREND_SELL" in tags:
        recommendation = "Block signals against MTF trend in trending regimes"

    return {
        "prediction_id": prediction["id"],
        "symbol": prediction.get("symbol"),
        "direction": direction,
        "entry_price": _f(prediction.get("ml_entry_price")),
        "failure_price": _f((outcome or {}).get("exit_price")) or _f(prediction.get("ml_stop_price")),
        "failure_reason": "|".join(tags),
        "rsi_at_failure": rsi,
        "volume_change": _f(factors.get(f"{base_tf}_vol_z")),
        "nearest_resistance": _f(factors.get(f"{base_tf}_swing_high_30")),
        "nearest_support": _f(factors.get(f"{base_tf}_swing_low_30")),
        "fib_level_hit": None,
        "macd_divergence": (factors.get(f"{base_tf}_macd_hist_sign") == -1 and direction == "BUY")
                           or (factors.get(f"{base_tf}_macd_hist_sign") == 1 and direction == "SELL"),
        "recommendation": recommendation,
        # Cluster signature returned separately so orchestrator can group
        "_signature": sig,
        "_tags": tags,
    }
