from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from database.supabase_client import get_supabase_client, is_db_available
from services.signal_analytics import (
    canonical_stop_loss_pips,
    canonical_targets,
    classify_signal,
    coerce_float,
    normalize_model_type,
    normalized_targets_hit,
    parse_targets,
    parse_targets_hit,
    resolved_exit_price,
)

TP_LEVELS = ("TP1", "TP2", "TP3", "TP4")
DEFAULT_SIGNAL_REPAIR_SYMBOLS = ("NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX")
_TARGET_RESOLUTION_REASONS = {"tp4_hit", "tp1_3_hit_then_sl", "all_targets_hit"}


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


def _same_number(left: Optional[float], right: Optional[float], tolerance: float = 1e-4) -> bool:
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    return abs(left - right) <= tolerance


def _rounded_targets(targets: Dict[str, Any]) -> Dict[str, float]:
    rounded: Dict[str, float] = {}
    for target_name in TP_LEVELS:
        target_price = coerce_float(targets.get(target_name))
        if target_price is None:
            continue
        rounded[target_name] = round(target_price, 4)
    return rounded


def _normalized_targets_hit_payload(row: Dict[str, Any], *, default_symbol: Optional[str] = None) -> Dict[str, bool]:
    normalized = normalized_targets_hit(row, default_symbol=default_symbol)
    return {tp_name: bool(normalized.get(tp_name)) for tp_name in TP_LEVELS}


def _highest_hit_target_name(targets_hit: Dict[str, bool]) -> Optional[str]:
    for target_name in reversed(TP_LEVELS):
        if targets_hit.get(target_name):
            return target_name
    return None


def _resolved_stop_loss_pips(row: Dict[str, Any], *, default_symbol: Optional[str] = None) -> Optional[float]:
    resolved = canonical_stop_loss_pips(row, default_symbol=default_symbol)
    return round(resolved, 2) if resolved is not None else None


def _infer_resolution_reason(
    row: Dict[str, Any],
    *,
    normalized_status: Optional[str],
    normalized_targets: Dict[str, bool],
) -> Optional[str]:
    raw_reason = (row.get("resolution_reason") or "").lower().strip()
    raw_status = (row.get("status") or "").lower().strip()

    if normalized_status != "completed":
        return raw_reason or None

    highest_hit = _highest_hit_target_name(normalized_targets)
    if highest_hit == "TP4":
        return "tp4_hit"

    if any(normalized_targets.values()):
        if raw_status == "stopped" or raw_reason in {"sl_hit", "window_resolve_negative"}:
            return "tp1_3_hit_then_sl"
        if raw_reason:
            return raw_reason
        if all(normalized_targets.get(tp_name) for tp_name in TP_LEVELS):
            return "all_targets_hit"
        return None

    return raw_reason or None


def normalize_requested_symbols(symbols: Optional[Iterable[str]] = None) -> List[str]:
    normalized: List[str] = []
    source = symbols or DEFAULT_SIGNAL_REPAIR_SYMBOLS
    for symbol in source:
        symbol_text = str(symbol or "").upper().strip()
        if not symbol_text or symbol_text in normalized:
            continue
        normalized.append(symbol_text)
    return normalized


def plan_signal_history_repair(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    symbol = (row.get("symbol") or "").upper().strip()
    direction = (row.get("ml_direction") or "").upper().strip()
    entry_price = coerce_float(row.get("ml_entry_price"))
    raw_status = (row.get("status") or "").lower().strip()
    raw_exit_price = coerce_float(row.get("exit_price"))
    raw_targets = parse_targets(row.get("targets"))
    raw_targets_hit = parse_targets_hit(row.get("targets_hit"))
    raw_resolution_reason = (row.get("resolution_reason") or "").lower().strip()

    if not symbol or direction not in {"BUY", "SELL"} or entry_price is None or entry_price <= 0:
        return None

    normalized_status, _, calculated_pnl = classify_signal(row, default_symbol=symbol)
    if normalized_status in {None, "direction_flip"}:
        return None

    explicit_targets_available = any(coerce_float(raw_targets.get(tp_name)) is not None for tp_name in TP_LEVELS)
    explicit_any_target_hit = any(bool(raw_targets_hit.get(tp_name)) for tp_name in TP_LEVELS)
    target_resolution = raw_resolution_reason in _TARGET_RESOLUTION_REASONS
    explicit_target_semantics = explicit_any_target_hit or target_resolution

    corrected_targets_hit = _normalized_targets_hit_payload(row, default_symbol=symbol)
    corrected_exit_price = resolved_exit_price(row, default_symbol=symbol)
    corrected_targets = _rounded_targets(canonical_targets(row, default_symbol=symbol))
    corrected_stop_loss_pips = _resolved_stop_loss_pips(row, default_symbol=symbol)
    inferred_resolution_reason = _infer_resolution_reason(
        row,
        normalized_status=normalized_status,
        normalized_targets=corrected_targets_hit,
    )

    updates: Dict[str, Any] = {}
    changes: Dict[str, Dict[str, Any]] = {}

    safe_to_reclassify_completed = explicit_target_semantics
    safe_to_repair_completed_exit = normalized_status == "completed" and explicit_target_semantics

    if normalized_status != raw_status:
        if normalized_status != "completed" or safe_to_reclassify_completed:
            updates["status"] = normalized_status
            changes["status"] = {"from": raw_status, "to": normalized_status}

    if corrected_stop_loss_pips is not None:
        raw_stop_loss_pips = coerce_float(row.get("stop_loss_pips"))
        if not _same_number(raw_stop_loss_pips, corrected_stop_loss_pips, tolerance=1e-2):
            updates["stop_loss_pips"] = corrected_stop_loss_pips
            changes["stop_loss_pips"] = {"from": raw_stop_loss_pips, "to": corrected_stop_loss_pips}

    if corrected_targets:
        comparable_existing_targets = {tp_name: coerce_float(raw_targets.get(tp_name)) for tp_name in TP_LEVELS}
        comparable_corrected_targets = {tp_name: corrected_targets.get(tp_name) for tp_name in TP_LEVELS}
        if comparable_existing_targets != comparable_corrected_targets:
            updates["targets"] = corrected_targets
            changes["targets"] = {"from": comparable_existing_targets, "to": comparable_corrected_targets}

    if explicit_targets_available or explicit_target_semantics or normalized_status == "active":
        comparable_existing_targets_hit = {tp_name: bool(raw_targets_hit.get(tp_name)) for tp_name in TP_LEVELS}
        if comparable_existing_targets_hit != corrected_targets_hit:
            updates["targets_hit"] = corrected_targets_hit
            changes["targets_hit"] = {"from": comparable_existing_targets_hit, "to": corrected_targets_hit}

    if normalized_status == "stopped" or safe_to_repair_completed_exit:
        if not _same_number(raw_exit_price, corrected_exit_price):
            updates["exit_price"] = round(corrected_exit_price, 4) if corrected_exit_price is not None else None
            changes["exit_price"] = {"from": raw_exit_price, "to": corrected_exit_price}

    if inferred_resolution_reason and inferred_resolution_reason != raw_resolution_reason:
        if normalized_status != "completed" or safe_to_reclassify_completed:
            updates["resolution_reason"] = inferred_resolution_reason
            changes["resolution_reason"] = {"from": raw_resolution_reason or None, "to": inferred_resolution_reason}

    if not updates:
        return None

    return {
        "id": row.get("id"),
        "symbol": symbol,
        "strategy": row.get("strategy"),
        "model_type": row.get("model_type"),
        "raw_status": raw_status,
        "normalized_status": normalized_status,
        "calculated_pnl_pips": round(calculated_pnl, 2) if calculated_pnl is not None else None,
        "created_at": row.get("created_at"),
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
        "ml_stop_price, targets, targets_hit, highest_profit_pips, lowest_drawdown_pips, "
        "stop_loss_pips, status, created_at, exit_price, exit_time, resolution_reason"
    ).in_("symbol", symbols).gte("created_at", _utc_iso(start)).lt("created_at", _utc_iso(end)).order("created_at", desc=False).limit(1000).execute()
    return _rows_from_result(result)


def run_signal_history_repair(
    *,
    dry_run: bool = True,
    client=None,
    symbols: Optional[Iterable[str]] = None,
    max_records: int = 50000,
    window_days: int = 1,
    sample_size: int = 20,
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
            "symbols": target_symbols,
            "rows_scanned": 0,
            "eligible_rows_considered": 0,
            "rows_needing_update": 0,
            "rows_updated": 0,
            "field_change_counts": {},
            "symbol_update_counts": {},
            "sample": [],
        }

    scanned = 0
    eligible_rows_considered = 0
    rows_needing_update = 0
    rows_updated = 0
    field_change_counts: Dict[str, int] = {}
    symbol_update_counts: Dict[str, int] = {}
    sample: List[Dict[str, Any]] = []
    errors: List[str] = []

    start = oldest.replace(hour=0, minute=0, second=0, microsecond=0)
    end = _utc_now() + timedelta(seconds=1)
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

            eligible_rows_considered += 1
            plan = plan_signal_history_repair(row)
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
                        "model_type": normalize_model_type(plan),
                        "raw_status": plan.get("raw_status"),
                        "normalized_status": plan.get("normalized_status"),
                        "calculated_pnl_pips": plan.get("calculated_pnl_pips"),
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
        "symbols": target_symbols,
        "rows_scanned": scanned,
        "eligible_rows_considered": eligible_rows_considered,
        "rows_needing_update": rows_needing_update,
        "rows_updated": rows_updated,
        "field_change_counts": field_change_counts,
        "symbol_update_counts": symbol_update_counts,
        "sample": sample,
    }
    if errors:
        payload["errors"] = errors[:20]
    return payload
