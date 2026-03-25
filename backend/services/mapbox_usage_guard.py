from __future__ import annotations

import calendar
import logging
import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from database.supabase_client import get_auth_error, get_supabase_client, is_auth_failed

logger = logging.getLogger(__name__)

MAPBOX_WEB_METRIC = "map_loads_web"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_rows(result: Dict[str, Any]) -> list[Dict[str, Any]]:
    rows = result.get("data") if isinstance(result, dict) else None
    return rows if isinstance(rows, list) else []


def _safe_row(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rows = _safe_rows(result)
    return rows[0] if rows else None


def _int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default)).strip()))
    except Exception:
        return default


def _float_env(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)).strip())
    except Exception:
        return default
    return max(0.0, min(0.9, value))


def _month_key(now: datetime) -> str:
    return now.strftime("%Y-%m")


def _day_key(now: datetime) -> str:
    return now.strftime("%Y-%m-%d")


def _budget_config(now: Optional[datetime] = None) -> Dict[str, Any]:
    ts = now or _now()
    reserve_ratio = _float_env("MAPBOX_WEB_MONTHLY_RESERVE_RATIO", 0.10)
    vendor_free_limit = _int_env("MAPBOX_VENDOR_FREE_WEB_LIMIT", 50_000)
    automatic_month_limit = max(1, math.floor(vendor_free_limit * (1.0 - reserve_ratio)))
    requested_month_limit = _int_env("MAPBOX_WEB_MONTHLY_HARD_LIMIT", automatic_month_limit)
    days_in_month = calendar.monthrange(ts.year, ts.month)[1]
    monthly_limit = min(requested_month_limit, automatic_month_limit)
    derived_daily_limit = max(1, math.floor(monthly_limit / max(days_in_month, 1)))
    daily_limit = min(_int_env("MAPBOX_WEB_DAILY_HARD_LIMIT", derived_daily_limit), monthly_limit)
    return {
        "metric_name": MAPBOX_WEB_METRIC,
        "month_key": _month_key(ts),
        "day_key": _day_key(ts),
        "month_limit": monthly_limit,
        "day_limit": daily_limit,
        "reserve_ratio": reserve_ratio,
        "vendor_free_limit": vendor_free_limit,
        "days_in_month": days_in_month,
    }


def _status_payload(
    *,
    allowed: bool,
    claimed: bool,
    reason: str,
    month_used: int,
    day_used: int,
    month_limit: int,
    day_limit: int,
    reserve_ratio: float,
    vendor_free_limit: int,
) -> Dict[str, Any]:
    remaining_month = max(0, month_limit - month_used)
    remaining_day = max(0, day_limit - day_used)
    return {
        "allow_live_map": bool(allowed),
        "claimed": bool(claimed),
        "mode": "live" if allowed else "fallback",
        "reason": reason,
        "month_used": int(month_used),
        "month_limit": int(month_limit),
        "remaining_month": int(remaining_month),
        "day_used": int(day_used),
        "day_limit": int(day_limit),
        "remaining_day": int(remaining_day),
        "reserve_ratio": float(reserve_ratio),
        "vendor_free_limit": int(vendor_free_limit),
        "metric": MAPBOX_WEB_METRIC,
    }


def get_mapbox_web_load_status() -> Dict[str, Any]:
    config = _budget_config()
    client = get_supabase_client()
    if client is None or is_auth_failed():
        return _status_payload(
            allowed=False,
            claimed=False,
            reason=get_auth_error() or "quota_guard_unavailable",
            month_used=0,
            day_used=0,
            month_limit=config["month_limit"],
            day_limit=config["day_limit"],
            reserve_ratio=config["reserve_ratio"],
            vendor_free_limit=config["vendor_free_limit"],
        )

    try:
        month_row = _safe_row(
            client.table("mapbox_usage_counters")
            .select("usage_count")
            .eq("metric_name", MAPBOX_WEB_METRIC)
            .eq("period_type", "month")
            .eq("period_key", config["month_key"])
            .limit(1)
            .execute()
        )
        day_row = _safe_row(
            client.table("mapbox_usage_counters")
            .select("usage_count")
            .eq("metric_name", MAPBOX_WEB_METRIC)
            .eq("period_type", "day")
            .eq("period_key", config["day_key"])
            .limit(1)
            .execute()
        )
        month_used = int((month_row or {}).get("usage_count") or 0)
        day_used = int((day_row or {}).get("usage_count") or 0)
        allowed = month_used < config["month_limit"] and day_used < config["day_limit"]
        if month_used >= config["month_limit"]:
            reason = "monthly_cap_reached"
        elif day_used >= config["day_limit"]:
            reason = "daily_budget_exhausted"
        else:
            reason = "within_budget"
        return _status_payload(
            allowed=allowed,
            claimed=False,
            reason=reason,
            month_used=month_used,
            day_used=day_used,
            month_limit=config["month_limit"],
            day_limit=config["day_limit"],
            reserve_ratio=config["reserve_ratio"],
            vendor_free_limit=config["vendor_free_limit"],
        )
    except Exception as exc:
        logger.error("get_mapbox_web_load_status error: %s", exc, exc_info=True)
        return _status_payload(
            allowed=False,
            claimed=False,
            reason="quota_guard_error",
            month_used=0,
            day_used=0,
            month_limit=config["month_limit"],
            day_limit=config["day_limit"],
            reserve_ratio=config["reserve_ratio"],
            vendor_free_limit=config["vendor_free_limit"],
        )


def claim_mapbox_web_load(session_key: Optional[str] = None) -> Dict[str, Any]:
    config = _budget_config()
    client = get_supabase_client()
    if client is None or is_auth_failed():
        return _status_payload(
            allowed=False,
            claimed=False,
            reason=get_auth_error() or "quota_guard_unavailable",
            month_used=0,
            day_used=0,
            month_limit=config["month_limit"],
            day_limit=config["day_limit"],
            reserve_ratio=config["reserve_ratio"],
            vendor_free_limit=config["vendor_free_limit"],
        )

    try:
        rpc_result = client.rpc(
            "claim_mapbox_web_load",
            {
                "p_metric_name": MAPBOX_WEB_METRIC,
                "p_month_key": config["month_key"],
                "p_day_key": config["day_key"],
                "p_month_limit": config["month_limit"],
                "p_day_limit": config["day_limit"],
                "p_session_key": session_key or "",
            },
        )
        data = rpc_result.get("data") if isinstance(rpc_result, dict) else None
        if not isinstance(data, dict):
            raise RuntimeError(rpc_result.get("error") if isinstance(rpc_result, dict) else "quota_guard_rpc_failed")
        return _status_payload(
            allowed=bool(data.get("allowed")),
            claimed=bool(data.get("claimed")),
            reason=str(data.get("reason") or "quota_guard_unknown"),
            month_used=int(data.get("month_used") or 0),
            day_used=int(data.get("day_used") or 0),
            month_limit=config["month_limit"],
            day_limit=config["day_limit"],
            reserve_ratio=config["reserve_ratio"],
            vendor_free_limit=config["vendor_free_limit"],
        )
    except Exception as exc:
        logger.error("claim_mapbox_web_load error: %s", exc, exc_info=True)
        return _status_payload(
            allowed=False,
            claimed=False,
            reason="quota_guard_error",
            month_used=0,
            day_used=0,
            month_limit=config["month_limit"],
            day_limit=config["day_limit"],
            reserve_ratio=config["reserve_ratio"],
            vendor_free_limit=config["vendor_free_limit"],
        )
