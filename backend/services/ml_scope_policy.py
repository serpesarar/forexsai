from __future__ import annotations

from typing import Any, Dict, Optional

ML_SCOPE_ALIASES: Dict[str, str] = {
    "main": "main",
    "ml": "main",
    "ml:main": "main",
    "raw_ml": "main",
    "base_ml": "main",
    "ultra_safe": "ultra_safe",
    "ultrasafe": "ultra_safe",
    "ml:ultra_safe": "ultra_safe",
    "balanced": "balanced",
    "ml:balanced": "balanced",
    "full_power": "full_power",
    "fullpower": "full_power",
    "ml:full_power": "full_power",
    "aggressive": "aggressive",
    "ml:aggressive": "aggressive",
    "nasdaq_precision": "nasdaq_precision",
    "nasdaqprecision": "nasdaq_precision",
    "ml:nasdaq_precision": "nasdaq_precision",
}

ML_SCOPE_MIN_CONFIDENCE: Dict[str, float] = {
    "ultra_safe": 58.0,
    "balanced": 55.0,
    "full_power": 52.0,
    "aggressive": 50.0,
    "nasdaq_precision": 60.0,
}


def normalize_ml_scope(value: Optional[str]) -> Optional[str]:
    normalized = (value or "").lower().strip()
    if not normalized:
        return None
    if normalized.startswith("ml:"):
        normalized = normalized.split(":", 1)[1].strip()
    return ML_SCOPE_ALIASES.get(normalized)


def minimum_confidence_for_ml_scope(scope: Optional[str]) -> Optional[float]:
    normalized_scope = normalize_ml_scope(scope)
    if not normalized_scope:
        return None
    return ML_SCOPE_MIN_CONFIDENCE.get(normalized_scope)


def is_ml_scope_confidence_eligible(scope: Optional[str], confidence: Any) -> bool:
    minimum = minimum_confidence_for_ml_scope(scope)
    if minimum is None:
        return True
    try:
        parsed = float(confidence)
    except (TypeError, ValueError):
        return False
    if parsed != parsed:
        return False
    return parsed + 1e-9 >= minimum
