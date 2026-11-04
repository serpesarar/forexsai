"""Issue #17 predicate, shared by the live gate and offline evaluation.

The six reported failures are a hypothesis, not evidence of winner retention.
Missing data must never become a zero distance or an implicit unknown regime.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

SWING_HIGH_THRESHOLD_ATR = 2.0
SWING_HIGH_GATE = "pulse1_swing_high_gate"
DISTANCE_FIELD = "M30_dist_swing_high_30_atr"


def is_candidate(symbol: str, direction: str, model_type: str) -> bool:
    """Restrict the rule to gold PULSE1 BUYs, excluding inverse experiments."""
    return (
        (symbol or "").strip().upper() in {"XAUUSD", "XAUUSD.FOREX", "GOLD"}
        and direction == "BUY"
        and (model_type or "").strip().lower().split(":")[0] == "pulse1"
    )


def filter_inputs(factors: Any) -> tuple[str | None, float | None]:
    """Read an explicit regime and finite distance; invalid inputs stay missing."""
    if not isinstance(factors, Mapping):
        return None, None
    regime = factors.get("regime_label")
    regime = regime.strip().lower() if isinstance(regime, str) else None
    value = factors.get(DISTANCE_FIELD)
    if value is None or isinstance(value, bool):
        return regime or None, None
    try:
        distance = float(value)
    except (TypeError, ValueError, OverflowError):
        return regime or None, None
    return regime or None, distance if math.isfinite(distance) else None


def would_block(symbol: str, direction: str, model_type: str, factors: Any) -> bool:
    """Match transition/unknown BUYs strictly below 2 ATR (2.0 passes)."""
    if not is_candidate(symbol, direction, model_type):
        return False
    regime, distance = filter_inputs(factors)
    return (
        regime in {"transition", "unknown"}
        and distance is not None
        and distance < SWING_HIGH_THRESHOLD_ATR
    )
