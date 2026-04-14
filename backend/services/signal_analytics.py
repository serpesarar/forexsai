from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, Iterable, List, Optional, Tuple

from services.target_config import calculate_stoploss_price, calculate_target_prices, pips_from_price_change

TIMEFRAME_ORDER = ["5m", "15m", "20m", "30m", "1h", "4h", "1d"]
VALID_TIMEFRAMES = set(TIMEFRAME_ORDER)
MODEL_ORDER = ["ml", "ai_panel", "meta", "pulse1", "pulse2", "pulse3", "emel", "emel_inverse", "smc", "hybrid"]
TP_LEVEL_ORDER = ("TP1", "TP2", "TP3", "TP4")
SMC_CADENCE_MINUTES = {"5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}


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

    if model_type in {"ai_panel", "ai-panel", "ai_panel_hourly"}:
        return "ai_panel"
    if strategy in {"AI_PANEL", "AI_PANEL_HOURLY"}:
        return "ai_panel"

    if model_type in {"meta", "meta_engine", "meta-intelligence-engine", "meta_intelligence_engine"}:
        return "meta"
    if strategy in {"META", "META_ENGINE", "META_INTELLIGENCE_ENGINE"}:
        return "meta"

    if strategy in {"SMART_MONEY_ZONES", "ORDER_BLOCK", "ORDER_BLOCKS", "SMC"}:
        return "smc"

    if model_type in {"smc", "smart_money_zones", "order_block", "order_blocks"}:
        return "smc"

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

    if model_type in {"pulse2", "pulse3", "emel", "emel_inverse", "hybrid", "meta"}:
        return model_type
    return "ml"


def is_market_closed_invalid_signal(sig: dict) -> bool:
    return (sig.get("resolution_reason") or "").lower().strip() == "market_closed_invalid"


def filter_market_closed_invalid_signals(signals: Iterable[dict]) -> List[dict]:
    return [sig for sig in signals if not is_market_closed_invalid_signal(sig)]


def timeframe_cadence_minutes(value: Optional[str]) -> Optional[int]:
    normalized = normalize_timeframe(value)
    if not normalized:
        return None
    return SMC_CADENCE_MINUTES.get(normalized)


def parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def collapse_smc_cadence_signals(signals: Iterable[dict]) -> List[dict]:
    signal_list = list(signals)
    if not signal_list:
        return []

    keep_indexes = set(range(len(signal_list)))
    ranked_rows = []
    for index, sig in enumerate(signal_list):
        if normalize_model_type(sig) != "smc":
            continue
        cadence_minutes = timeframe_cadence_minutes(sig.get("timeframe"))
        created_dt = parse_datetime(sig.get("created_at"))
        symbol = str(sig.get("symbol") or "").upper().strip()
        if cadence_minutes is None or created_dt is None or not symbol:
            continue
        ranked_rows.append((created_dt, index, symbol, normalize_timeframe(sig.get("timeframe")), cadence_minutes))

    ranked_rows.sort(reverse=True)
    seen_buckets = set()
    for created_dt, index, symbol, timeframe, cadence_minutes in ranked_rows:
        bucket = int(created_dt.timestamp()) // (cadence_minutes * 60)
        bucket_key = (symbol, timeframe, bucket)
        if bucket_key in seen_buckets:
            keep_indexes.discard(index)
            continue
        seen_buckets.add(bucket_key)

    return [sig for index, sig in enumerate(signal_list) if index in keep_indexes]


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


def canonical_targets(sig: dict, default_symbol: Optional[str] = None) -> Dict[str, Any]:
    entry_price = coerce_float(sig.get("ml_entry_price"))
    direction = (sig.get("ml_direction") or "").upper().strip()
    symbol = sig.get("symbol") or default_symbol
    timeframe = normalize_timeframe(sig.get("timeframe")) or "15m"

    if entry_price is None or direction not in {"BUY", "SELL"} or not symbol:
        return {}

    try:
        return calculate_target_prices(entry_price, direction, symbol, timeframe)
    except Exception:
        return {}


def canonical_stop_price(sig: dict, default_symbol: Optional[str] = None) -> Optional[float]:
    entry_price = coerce_float(sig.get("ml_entry_price"))
    direction = (sig.get("ml_direction") or "").upper().strip()
    symbol = sig.get("symbol") or default_symbol
    timeframe = normalize_timeframe(sig.get("timeframe")) or "15m"

    if entry_price is None or direction not in {"BUY", "SELL"} or not symbol:
        return coerce_float(sig.get("ml_stop_price"))

    try:
        return calculate_stoploss_price(entry_price, direction, symbol, timeframe)
    except Exception:
        return coerce_float(sig.get("ml_stop_price"))


def canonical_stop_loss_pips(sig: dict, default_symbol: Optional[str] = None) -> Optional[float]:
    entry_price = coerce_float(sig.get("ml_entry_price"))
    symbol = sig.get("symbol") or default_symbol
    stop_price = canonical_stop_price(sig, default_symbol=default_symbol)

    if entry_price is None or stop_price is None or not symbol:
        return abs(coerce_float(sig.get("stop_loss_pips"), 0.0) or 0.0)

    return abs(pips_from_price_change(abs(entry_price - stop_price), symbol))


def resolved_targets(sig: dict, default_symbol: Optional[str] = None) -> Dict[str, Any]:
    targets = canonical_targets(sig, default_symbol=default_symbol)
    if targets:
        return targets
    return parse_targets(sig.get("targets"))


def first_target_profit_floor(sig: dict, default_symbol: Optional[str] = None) -> Optional[float]:
    entry_price = coerce_float(sig.get("ml_entry_price"))
    direction = (sig.get("ml_direction") or "").upper().strip()
    symbol = sig.get("symbol") or default_symbol
    targets = resolved_targets(sig, default_symbol=default_symbol)
    tp1_price = coerce_float(targets.get("TP1"))

    if entry_price is None or direction not in {"BUY", "SELL"} or not symbol or tp1_price is None:
        return None

    price_change = tp1_price - entry_price if direction == "BUY" else entry_price - tp1_price
    return max(pips_from_price_change(price_change, symbol), 0.0)


def normalized_targets_hit(sig: dict, default_symbol: Optional[str] = None) -> Dict[str, bool]:
    normalized = dict(parse_targets_hit(sig.get("targets_hit")))
    highest_confirmed_idx = max(
        (idx for idx, tp_name in enumerate(TP_LEVEL_ORDER) if normalized.get(tp_name)),
        default=-1,
    )
    if highest_confirmed_idx >= 0:
        for idx in range(highest_confirmed_idx + 1):
            normalized[TP_LEVEL_ORDER[idx]] = True
        return normalized

    profit_pips = max(coerce_float(sig.get("highest_profit_pips"), 0.0) or 0.0, 0.0)
    tp1_floor = first_target_profit_floor(sig, default_symbol=default_symbol)
    if tp1_floor is not None and profit_pips >= tp1_floor:
        normalized["TP1"] = True

    return normalized


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
    targets_hit = normalized_targets_hit(sig, default_symbol=default_symbol)
    targets = resolved_targets(sig, default_symbol=default_symbol)

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


def resolved_exit_price(sig: dict, default_symbol: Optional[str] = None) -> Optional[float]:
    raw_exit_price = coerce_float(sig.get("exit_price"))
    targets = resolved_targets(sig, default_symbol=default_symbol)
    targets_hit = normalized_targets_hit(sig, default_symbol=default_symbol)
    normalized_status, _, _ = classify_signal(sig, default_symbol=default_symbol)

    target_exit_price = None
    for target_name in TP_LEVEL_ORDER:
        if not targets_hit.get(target_name):
            continue
        target_exit_price = coerce_float(targets.get(target_name))

    if normalized_status == "completed" and target_exit_price is not None:
        return round(target_exit_price, 4)

    if normalized_status == "stopped":
        stop_price = canonical_stop_price(sig, default_symbol=default_symbol)
        if stop_price is not None:
            return round(stop_price, 4)

    return round(raw_exit_price, 4) if raw_exit_price is not None else None


def classify_signal(
    sig: dict,
    *,
    default_symbol: Optional[str] = None,
) -> Tuple[Optional[str], Optional[bool], Optional[float]]:
    status = (sig.get("status") or "unknown").lower().strip()
    resolution_reason = (sig.get("resolution_reason") or "").lower().strip()
    profit_pips = max(coerce_float(sig.get("highest_profit_pips"), 0.0) or 0.0, 0.0)
    loss_pips = abs(coerce_float(sig.get("lowest_drawdown_pips"), 0.0) or 0.0)
    stop_loss_pips = canonical_stop_loss_pips(sig, default_symbol=default_symbol)
    realized = realized_pips(sig, default_symbol=default_symbol)
    explicit_targets_hit = parse_targets_hit(sig.get("targets_hit"))
    targets_hit = normalized_targets_hit(sig, default_symbol=default_symbol)
    explicit_any_target_hit = any(explicit_targets_hit.values()) if explicit_targets_hit else False
    any_target_hit = any(targets_hit.values()) if targets_hit else False
    target_profit_floor = target_hit_profit_floor(sig, default_symbol=default_symbol)

    def resolved_success_pips() -> float:
        realized_profit = max(realized, 0.0) if realized is not None else None
        target_floor_profit = max(target_profit_floor, 0.0) if target_profit_floor is not None else None

        target_resolution = resolution_reason in {"tp4_hit", "tp1_3_hit_then_sl", "all_targets_hit"}

        if target_floor_profit is not None and (explicit_any_target_hit or target_resolution or (status == "stopped" and any_target_hit)):
            # Sanity check: if highest_profit_pips is far less than the target
            # floor, the target_hit data may be stale/wrong (e.g. from pre-signal
            # candle wicks).  Cap to what was actually observed.
            if profit_pips > 0 and target_floor_profit > profit_pips * 3:
                return max(profit_pips, 0.0)
            return target_floor_profit

        if realized is not None:
            if realized_profit is not None and realized_profit > 0:
                return realized_profit
            if target_floor_profit is not None:
                return target_floor_profit
            return 0.0
        if target_floor_profit is not None:
            return max(target_floor_profit, max(profit_pips, 0.0))
        return max(profit_pips, 0.0)

    if status == "stopped" and resolution_reason == "direction_flip":
        # Direction flip = model predicted wrong direction → this IS a loss, don't exclude
        actual_loss = stop_loss_pips or loss_pips
        return "stopped", False, -actual_loss
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
        if scoped_status == "expired":
            expired += 1
            continue

        scored_signals += 1
        if scoped_status == "completed":
            completed += 1
            total_profit += max(scoped_pips or 0.0, 0.0)
        elif scoped_status == "stopped":
            stopped += 1
            total_loss += abs(scoped_pips or 0.0)

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
        "avg_pips": round(net_pips / resolved, 1) if resolved > 0 else 0,
    }