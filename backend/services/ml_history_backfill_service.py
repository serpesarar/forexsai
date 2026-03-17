from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from database.supabase_client import get_supabase_client, is_db_available
from services.signal_analytics import normalize_model_type, normalize_timeframe
from services.target_config import calculate_stoploss_price, calculate_target_prices, pips_from_price_change
from utils.json_helpers import parse_json_field

DESIRED_TIMEFRAME = "30m"
TP_LEVELS = ("TP1", "TP2", "TP3", "TP4")
DEFAULT_ML_BACKFILL_SYMBOLS = ("NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: Optional[datetime] = None) -> str:
    return (dt or _utc_now()).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _rows_from_result(result: Any) -> List[Dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, dict):
        rows = result.get("data")
        return rows if isinstance(rows, list) else []
    rows = getattr(result, "data", None)
    return rows if isinstance(rows, list) else []


def _coerce_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _normalize_targets_hit(value: Any) -> Dict[str, bool]:
    parsed = parse_json_field(value, {})
    if not isinstance(parsed, dict):
        parsed = {}
    return {tp: bool(parsed.get(tp)) for tp in TP_LEVELS}


def _normalize_targets(value: Any) -> Dict[str, Any]:
    parsed = parse_json_field(value, {})
    return parsed if isinstance(parsed, dict) else {}


def _target_pips(entry_price: float, direction: str, symbol: str, target_price: Optional[float]) -> Optional[float]:
    if target_price is None:
        return None
    price_change = target_price - entry_price if direction == "BUY" else entry_price - target_price
    return max(pips_from_price_change(price_change, symbol), 0.0)


def _infer_targets_hit(
    *,
    existing_targets_hit: Dict[str, bool],
    highest_profit_pips: float,
    desired_targets: Dict[str, float],
    entry_price: float,
    direction: str,
    symbol: str,
) -> Dict[str, bool]:
    inferred = {tp: bool(existing_targets_hit.get(tp)) for tp in TP_LEVELS}
    peak_profit = max(highest_profit_pips, 0.0)

    for tp_name in TP_LEVELS:
        if inferred.get(tp_name):
            continue
        target_price = _coerce_float(desired_targets.get(tp_name))
        target_pips = _target_pips(entry_price, direction, symbol, target_price)
        if target_pips is None:
            continue
        if peak_profit + 1e-9 >= target_pips:
            inferred[tp_name] = True

    highest_true_index = max((idx for idx, tp_name in enumerate(TP_LEVELS) if inferred.get(tp_name)), default=-1)
    if highest_true_index >= 0:
        for idx in range(highest_true_index + 1):
            inferred[TP_LEVELS[idx]] = True

    return inferred


def _desired_payload(entry_price: float, direction: str, symbol: str, timeframe: str = DESIRED_TIMEFRAME) -> Dict[str, Any]:
    targets = calculate_target_prices(entry_price, direction, symbol, timeframe)
    sl_price = calculate_stoploss_price(entry_price, direction, symbol, timeframe)
    full_targets = {tp_name: round(float(tp_price), 4) for tp_name, tp_price in targets.items()}
    full_targets["SL"] = round(float(sl_price), 4)
    stop_loss_pips = round(abs(pips_from_price_change(abs(entry_price - sl_price), symbol)), 2)
    return {
        "targets": full_targets,
        "stop_loss_pips": stop_loss_pips,
    }


def normalize_requested_symbols(symbols: Optional[Iterable[str]] = None) -> List[str]:
    normalized: List[str] = []
    source = symbols or DEFAULT_ML_BACKFILL_SYMBOLS
    for symbol in source:
        symbol_text = str(symbol or "").upper().strip()
        if not symbol_text or symbol_text in normalized:
            continue
        normalized.append(symbol_text)
    return normalized


def plan_ml_backfill_update(row: Dict[str, Any], *, desired_timeframe: str = DESIRED_TIMEFRAME) -> Optional[Dict[str, Any]]:
    symbol = (row.get("symbol") or "").upper().strip()
    if not symbol:
        return None
    if normalize_model_type(row) != "ml":
        return None

    direction = (row.get("ml_direction") or "").upper().strip()
    entry_price = _coerce_float(row.get("ml_entry_price"))
    if direction not in {"BUY", "SELL"} or entry_price is None or entry_price <= 0:
        return None

    desired = _desired_payload(entry_price, direction, symbol, desired_timeframe)
    existing_targets = _normalize_targets(row.get("targets"))
    existing_targets_hit = _normalize_targets_hit(row.get("targets_hit"))
    highest_profit_pips = max(_coerce_float(row.get("highest_profit_pips")) or 0.0, 0.0)
    desired_targets_hit = _infer_targets_hit(
        existing_targets_hit=existing_targets_hit,
        highest_profit_pips=highest_profit_pips,
        desired_targets=desired["targets"],
        entry_price=entry_price,
        direction=direction,
        symbol=symbol,
    )

    updates: Dict[str, Any] = {}
    changes: Dict[str, Dict[str, Any]] = {}

    if normalize_timeframe(row.get("timeframe")) != desired_timeframe:
        updates["timeframe"] = desired_timeframe
        changes["timeframe"] = {"from": row.get("timeframe"), "to": desired_timeframe}

    comparable_existing_targets = {key: existing_targets.get(key) for key in (*TP_LEVELS, "SL")}
    comparable_desired_targets = {key: desired["targets"].get(key) for key in (*TP_LEVELS, "SL")}
    if comparable_existing_targets != comparable_desired_targets:
        updates["targets"] = desired["targets"]
        changes["targets"] = {"from": comparable_existing_targets, "to": comparable_desired_targets}

    existing_stop_loss_pips = _coerce_float(row.get("stop_loss_pips"))
    if existing_stop_loss_pips != desired["stop_loss_pips"]:
        updates["stop_loss_pips"] = desired["stop_loss_pips"]
        changes["stop_loss_pips"] = {"from": existing_stop_loss_pips, "to": desired["stop_loss_pips"]}

    if existing_targets_hit != desired_targets_hit:
        updates["targets_hit"] = desired_targets_hit
        changes["targets_hit"] = {"from": existing_targets_hit, "to": desired_targets_hit}

    if not updates:
        return None

    return {
        "id": row.get("id"),
        "symbol": symbol,
        "strategy": row.get("strategy"),
        "model_type": row.get("model_type"),
        "created_at": row.get("created_at"),
        "status": row.get("status"),
        "updates": updates,
        "changes": changes,
    }


def _fetch_oldest_created_at(client, symbols: List[str]) -> Optional[datetime]:
    result = client.table("prediction_logs").select("created_at, symbol").in_("symbol", symbols).order("created_at", desc=False).limit(1).execute()
    rows = _rows_from_result(result)
    if not rows:
        return None
    return _parse_iso(rows[0].get("created_at"))


def _fetch_window_rows(client, symbols: List[str], start: datetime, end: datetime) -> List[Dict[str, Any]]:
    result = client.table("prediction_logs").select(
        "id, symbol, strategy, model_type, timeframe, ml_direction, ml_entry_price, "
        "targets, targets_hit, highest_profit_pips, stop_loss_pips, status, created_at"
    ).in_("symbol", symbols).gte("created_at", _utc_iso(start)).lt("created_at", _utc_iso(end)).order("created_at", desc=False).limit(1000).execute()
    return _rows_from_result(result)


def run_ml_history_backfill(
    *,
    dry_run: bool = True,
    client=None,
    symbols: Optional[Iterable[str]] = None,
    max_records: int = 20000,
    window_days: int = 1,
    sample_size: int = 10,
) -> Dict[str, Any]:
    target_symbols = normalize_requested_symbols(symbols)
    if not target_symbols:
        return {"error": "No symbols provided"}

    if client is None:
        if not is_db_available():
            return {"error": "Database not available"}
        client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}

    oldest = _fetch_oldest_created_at(client, target_symbols)
    if oldest is None:
        return {
            "success": True,
            "dry_run": dry_run,
            "desired_timeframe": DESIRED_TIMEFRAME,
            "symbols": target_symbols,
            "rows_scanned": 0,
            "ml_rows_considered": 0,
            "rows_needing_update": 0,
            "rows_updated": 0,
            "field_change_counts": {},
            "symbol_update_counts": {},
            "sample": [],
        }

    scanned = 0
    ml_considered = 0
    rows_needing_update = 0
    rows_updated = 0
    field_change_counts: Dict[str, int] = {}
    symbol_update_counts: Dict[str, int] = {}
    sample: List[Dict[str, Any]] = []
    errors: List[str] = []

    start = oldest.replace(hour=0, minute=0, second=0, microsecond=0)
    end = _utc_now()
    cursor = start

    while cursor < end and scanned < max_records:
        window_end = min(cursor + timedelta(days=window_days), end)
        batch_rows = _fetch_window_rows(client, target_symbols, cursor, window_end)
        if not batch_rows:
            cursor = window_end
            continue

        for row in batch_rows:
            scanned += 1
            if scanned > max_records:
                break
            if normalize_model_type(row) != "ml":
                continue
            ml_considered += 1
            plan = plan_ml_backfill_update(row)
            if not plan:
                continue

            rows_needing_update += 1
            plan_symbol = plan["symbol"]
            symbol_update_counts[plan_symbol] = symbol_update_counts.get(plan_symbol, 0) + 1
            for field_name in plan["updates"].keys():
                field_change_counts[field_name] = field_change_counts.get(field_name, 0) + 1

            if len(sample) < sample_size:
                sample.append(
                    {
                        "id": plan["id"],
                        "symbol": plan_symbol,
                        "created_at": plan.get("created_at"),
                        "strategy": plan.get("strategy"),
                        "model_type": plan.get("model_type"),
                        "status": plan.get("status"),
                        "update_keys": sorted(plan["updates"].keys()),
                        "changes": plan["changes"],
                    }
                )

            if dry_run:
                continue

            try:
                result = client.table("prediction_logs").eq("id", plan["id"]).update(plan["updates"])
                if (result or {}).get("error"):
                    errors.append(f"{plan['id']}: {(result or {}).get('error')}")
                    continue
                rows_updated += 1
            except Exception as exc:
                errors.append(f"{plan['id']}: {exc}")

        cursor = window_end

    payload: Dict[str, Any] = {
        "success": True,
        "dry_run": dry_run,
        "desired_timeframe": DESIRED_TIMEFRAME,
        "symbols": target_symbols,
        "rows_scanned": scanned,
        "ml_rows_considered": ml_considered,
        "rows_needing_update": rows_needing_update,
        "rows_updated": rows_updated,
        "field_change_counts": field_change_counts,
        "symbol_update_counts": symbol_update_counts,
        "sample": sample,
    }
    if errors:
        payload["errors"] = errors[:20]
    return payload
