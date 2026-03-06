from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Tuple

from services.target_config import pips_from_price_change

TIMEFRAME_ORDER = ["5m", "15m", "30m", "1h", "4h", "1d"]
VALID_TIMEFRAMES = set(TIMEFRAME_ORDER)
MODEL_ORDER = ["ml", "pulse1", "pulse2", "pulse3", "emel", "emel_inverse", "hybrid"]
TP_LEVEL_ORDER = ("TP1", "TP2", "TP3", "TP4")


def sort_timeframes(values: Iterable[str]) -> List[str]:
    unique_values = {value for value in values if value}
    return sorted(
        unique_values,
        key=lambda value: (TIMEFRAME_ORDER.index(value) if value in TIMEFRAME_ORDER else 99, value),
    )


def sort_models(values: Iterable[str]) -> List[str]:
    unique_values = {value for value in values if value}
    return sorted(
        unique_values,
        key=lambda value: (MODEL_ORDER.index(value) if value in MODEL_ORDER else 99, value),
    )


def normalize_timeframe(value: Optional[str]) -> Optional[str]:
    normalized = (value or "").lower().strip()
    return normalized if normalized in VALID_TIMEFRAMES else None


def normalize_model_type(sig: dict) -> str:
    model_type = (sig.get("model_type") or sig.get("strategy") or "ml").lower().strip()
    strategy = (sig.get("strategy") or "").upper().strip()

    if model_type in {"pulse", "pulse1", ""}:
        if strategy == "PULSE_V3":
            return "pulse3"
        if strategy == "PULSE_ML":
            return "pulse2"
        if "EMEL" in strategy and "INVERSE" in strategy:
            return "emel_inverse"
        if "EMEL" in strategy:
            return "emel"
        if "PULSE" in strategy or model_type == "pulse1":
            return "pulse1"
        return "ml"

    if model_type in {"pulse2", "pulse3", "emel", "emel_inverse", "hybrid"}:
        return model_type
    return "ml"


def coerce_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed:
        return default
    return parsed


def parse_json_object(raw_value: Any) -> Dict[str, Any]:
    parsed = raw_value
    for _ in range(3):
        if isinstance(parsed, dict):
            return parsed
        if not isinstance(parsed, str):
            return {}
        text = parsed.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except Exception:
            return {}
    return parsed if isinstance(parsed, dict) else {}


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    if isinstance(value, (int, float)):
        return value != 0
    return False


def parse_targets_hit(raw_value: Any) -> Dict[str, bool]:
    parsed = parse_json_object(raw_value)
    return {str(key): _coerce_bool(value) for key, value in parsed.items()}


def parse_targets(raw_value: Any) -> Dict[str, Any]:
    return parse_json_object(raw_value)


def realized_pips(sig: dict, default_symbol: Optional[str] = None) -> Optional[float]:
    entry_price = coerce_float(sig.get("ml_entry_price"))
    exit_price = coerce_float(sig.get("exit_price"))
    direction = (sig.get("ml_direction") or "").upper().strip()
    symbol = sig.get("symbol") or default_symbol

    if entry_price is None or exit_price is None or direction not in {"BUY", "SELL"} or not symbol:
        return None

    price_change = exit_price - entry_price if direction == "BUY" else entry_price - exit_price
    return pips_from_price_change(price_change, symbol)


def target_hit_profit_floor(sig: dict, default_symbol: Optional[str] = None) -> Optional[float]:
    entry_price = coerce_float(sig.get("ml_entry_price"))
    direction = (sig.get("ml_direction") or "").upper().strip()
    symbol = sig.get("symbol") or default_symbol
    targets_hit = parse_targets_hit(sig.get("targets_hit"))
    targets = parse_targets(sig.get("targets"))

    if entry_price is None or direction not in {"BUY", "SELL"} or not symbol or not targets_hit or not targets:
        return None

    derived_pips: List[float] = []
    for target_name in TP_LEVEL_ORDER:
        if not targets_hit.get(target_name):
            continue
        target_price = coerce_float(targets.get(target_name))
        if target_price is None:
            continue
        price_change = target_price - entry_price if direction == "BUY" else entry_price - target_price
        derived_pips.append(max(pips_from_price_change(price_change, symbol), 0.0))

    return max(derived_pips) if derived_pips else None


def classify_signal(
    sig: dict,
    *,
    default_symbol: Optional[str] = None,
) -> Tuple[Optional[str], Optional[bool], Optional[float]]:
    status = (sig.get("status") or "unknown").lower().strip()
    profit_pips = max(coerce_float(sig.get("highest_profit_pips"), 0.0) or 0.0, 0.0)
    loss_pips = abs(coerce_float(sig.get("lowest_drawdown_pips"), 0.0) or 0.0)
    stop_loss_pips = abs(coerce_float(sig.get("stop_loss_pips"), 0.0) or 0.0)
    realized = realized_pips(sig, default_symbol=default_symbol)
    targets_hit = parse_targets_hit(sig.get("targets_hit"))
    any_target_hit = any(targets_hit.values()) if targets_hit else False
    target_profit_floor = target_hit_profit_floor(sig, default_symbol=default_symbol)

    def resolved_success_pips() -> float:
        if realized is not None and realized > 0:
            return max(realized, 0.0)
        return max(target_profit_floor or 0.0, profit_pips, 0.0)

    if status == "completed" or (status == "stopped" and any_target_hit):
        actual_profit = resolved_success_pips()
        return "completed", True, actual_profit
    if status == "stopped":
        actual_loss = stop_loss_pips or loss_pips
        return "stopped", False, -actual_loss
    if status == "expired":
        return "expired", False, 0.0
    if status == "active":
        return "active", None, None
    if any_target_hit:
        fallback_profit = resolved_success_pips()
        return "completed", True, fallback_profit
    return None, None, None


def summarize_scope(scope_signals: List[dict], *, default_symbol: Optional[str] = None) -> dict:
    completed = 0
    stopped = 0
    expired = 0
    active = 0
    total_profit = 0.0
    total_loss = 0.0
    scored_signals = 0

    for signal in scope_signals:
        scoped_status, _, scoped_pips = classify_signal(signal, default_symbol=default_symbol)
        if scoped_status == "active":
            active += 1
            continue
        if scoped_status is None:
            continue

        scored_signals += 1
        if scoped_status == "completed":
            completed += 1
            total_profit += max(scoped_pips or 0.0, 0.0)
        elif scoped_status == "stopped":
            stopped += 1
            total_loss += abs(scoped_pips or 0.0)
        elif scoped_status == "expired":
            expired += 1

    resolved = completed + stopped
    net_pips = total_profit - total_loss
    return {
        "total_signals": len(scope_signals),
        "scored_signals": scored_signals,
        "completed": completed,
        "stopped": stopped,
        "expired": expired,
        "active": active,
        "win_rate": round((completed / resolved * 100) if resolved > 0 else 0, 1),
        "net_pips": round(net_pips, 1),
        "avg_pips": round(net_pips / scored_signals, 1) if scored_signals > 0 else 0,
    }