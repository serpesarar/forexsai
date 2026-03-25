from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dateutil import parser as dateutil_parser

from database.supabase_client import get_auth_error, get_supabase_client, is_auth_failed

logger = logging.getLogger(__name__)

REGIONS: Dict[str, Dict[str, Any]] = {
    "strait_of_hormuz": {
        "label": "Strait of Hormuz",
        "bounds": [[25.0, 56.0], [26.5, 57.5]],
        "storage_hub": False,
    },
    "singapore_anchorage": {
        "label": "Singapore Anchorage",
        "bounds": [[1.0, 103.5], [1.5, 104.5]],
        "storage_hub": True,
    },
    "us_gulf": {
        "label": "US Gulf",
        "bounds": [[28.0, -95.0], [30.5, -89.5]],
        "storage_hub": False,
    },
    "rotterdam": {
        "label": "Rotterdam",
        "bounds": [[51.7, 3.8], [52.2, 4.6]],
        "storage_hub": True,
    },
}

STORAGE_REGIONS = {name for name, config in REGIONS.items() if config.get("storage_hub")}
TANKER_TYPES = {80, 81, 82, 83, 84, 85}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if not value:
        return _now()

    text = str(value).strip().replace("Z", "+00:00")
    text = re.sub(r"^(\d{4}-\d{2}-\d{2})T(?=\d{2}:\d{2}:\d{2})", r"\1 ", text)
    text = re.sub(r"\s+UTC$", "", text)

    explicit_match = re.match(
        r"^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})(?:\.(\d+))?(?:\s*([+-]\d{2}):?(\d{2}))?$",
        text,
    )
    if explicit_match:
        date_part, time_part, fraction_part, tz_hours, tz_minutes = explicit_match.groups()
        normalized = f"{date_part}T{time_part}"
        if fraction_part:
            normalized += f".{fraction_part[:6].ljust(6, '0')}"
        if tz_hours and tz_minutes:
            normalized += f"{tz_hours}:{tz_minutes}"
        else:
            normalized += "+00:00"
        try:
            return datetime.fromisoformat(normalized).astimezone(timezone.utc)
        except ValueError:
            pass

    text = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", text)
    text = re.sub(r"\.(\d{6})\d+(?=(?:\s?[+-]\d{2}:\d{2})?$)", r".\1", text)
    text = re.sub(r"\s+([+-]\d{2}:\d{2})$", r"\1", text)

    candidates = [text]
    if " " in text:
        candidates.append(text.replace(" ", "T", 1))

    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    try:
        parsed = dateutil_parser.parse(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        pass

    logger.warning("AIS timestamp parse failed for value=%r", value)
    return _now()


def _safe_rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = result.get("data") if isinstance(result, dict) else None
    return rows if isinstance(rows, list) else []


def _safe_row(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rows = _safe_rows(result)
    return rows[0] if rows else None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def detect_region(lat: float, lon: float) -> str:
    for region, config in REGIONS.items():
        (min_lat, min_lon), (max_lat, max_lon) = config["bounds"]
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return region
    return "transit"


def estimate_ship_category(ship_type_code: Optional[int], deadweight_tons: Optional[float] = None) -> str:
    code = int(ship_type_code) if ship_type_code is not None else None
    if code == 80:
        return "vlcc"
    if code == 81:
        return "aframax"
    if code == 82:
        return "suezmax"
    if code in {83, 84, 85}:
        return "product"
    dwt = float(deadweight_tons or 0)
    if dwt >= 200000:
        return "vlcc"
    if dwt >= 120000:
        return "suezmax"
    if dwt >= 80000:
        return "aframax"
    return "product"


def estimate_barrels(ship_category: str) -> int:
    mapping = {
        "vlcc": 2_000_000,
        "suezmax": 1_000_000,
        "aframax": 700_000,
        "product": 300_000,
    }
    return mapping.get(ship_category, 300_000)


def _heading_bucket(region: str, heading: Optional[float]) -> str:
    if heading is None:
        return "neutral"
    hdg = float(heading) % 360
    if region == "strait_of_hormuz":
        if 90 <= hdg <= 180:
            return "outbound"
        if 270 <= hdg or hdg <= 45:
            return "inbound"
    if region == "us_gulf":
        if 45 <= hdg <= 135:
            return "inbound"
        if 225 <= hdg <= 315:
            return "outbound"
    if region == "singapore_anchorage":
        if 300 <= hdg or hdg <= 60:
            return "inbound"
        if 120 <= hdg <= 240:
            return "outbound"
    if region == "rotterdam":
        if 0 <= hdg <= 120:
            return "inbound"
        if 180 <= hdg <= 330:
            return "outbound"
    return "neutral"


def _compute_status(
    region: str,
    lat: float,
    lon: float,
    speed_knots: Optional[float],
    observed_at: datetime,
    previous_state: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    speed = float(speed_knots or 0.0)
    stationary = speed < 0.5
    first_stationary_at = None
    idle_days = 0.0
    last_movement_at = observed_at

    if previous_state:
        if previous_state.get("last_movement_at"):
            last_movement_at = _parse_dt(previous_state.get("last_movement_at"))
        previous_stationary = previous_state.get("first_stationary_at")
        previous_lat = float(previous_state.get("lat") or lat)
        previous_lon = float(previous_state.get("lon") or lon)
        same_anchor = haversine_km(previous_lat, previous_lon, lat, lon) <= 2.0
        if stationary and previous_stationary and same_anchor:
            first_stationary_at = _parse_dt(previous_stationary)
        elif stationary:
            first_stationary_at = observed_at
        else:
            last_movement_at = observed_at
    elif stationary:
        first_stationary_at = observed_at

    if stationary and first_stationary_at:
        idle_days = max(0.0, (observed_at - first_stationary_at).total_seconds() / 86400.0)

    if stationary:
        if idle_days >= 7 and region in STORAGE_REGIONS:
            status = "floating_storage"
        elif idle_days >= 1:
            status = "idle"
        else:
            status = "anchored"
    else:
        status = "transit"

    return {
        "status": status,
        "idle_days": round(idle_days, 2),
        "first_stationary_at": first_stationary_at.isoformat() if first_stationary_at else None,
        "last_movement_at": last_movement_at.isoformat() if last_movement_at else None,
    }


def get_tanker_state(mmsi: int) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return None
    if is_auth_failed():
        return None
    result = client.table("tanker_state").select("*").eq("mmsi", mmsi).limit(1).execute()
    return _safe_row(result)


def persist_tanker_observation(observation: Dict[str, Any]) -> Dict[str, Any]:
    client = get_supabase_client()
    if client is None:
        return {"ok": False, "error": "supabase_unavailable"}
    if is_auth_failed():
        return {"ok": False, "error": get_auth_error() or "supabase_auth_failed"}

    try:
        mmsi = int(observation["mmsi"])
        lat = float(observation["lat"])
        lon = float(observation["lon"])
        observed_at = _parse_dt(observation.get("observed_at"))
        ship_type_code = observation.get("ship_type_code")
        ship_category = observation.get("ship_category") or estimate_ship_category(ship_type_code, observation.get("deadweight_tons"))
        region = observation.get("region") or detect_region(lat, lon)
        previous_state = get_tanker_state(mmsi)
        status_info = _compute_status(region, lat, lon, observation.get("speed_knots"), observed_at, previous_state)
        estimated_barrels = int(observation.get("estimated_barrels") or estimate_barrels(ship_category))
        heading_bucket = _heading_bucket(region, observation.get("heading"))

        position_row = {
            "mmsi": mmsi,
            "imo": observation.get("imo"),
            "vessel_name": observation.get("vessel_name"),
            "ship_type_code": ship_type_code,
            "ship_category": ship_category,
            "lat": lat,
            "lon": lon,
            "speed_knots": observation.get("speed_knots"),
            "heading": observation.get("heading"),
            "draught_meters": observation.get("draught_meters"),
            "destination": observation.get("destination"),
            "nav_status": observation.get("nav_status"),
            "region": region,
            "status": status_info["status"],
            "idle_days": status_info["idle_days"],
            "is_dark": bool(observation.get("is_dark") or False),
            "estimated_barrels": estimated_barrels,
            "observed_at": observed_at.isoformat(),
            "data_source": observation.get("data_source") or "aisstream",
            "raw_payload": observation.get("raw_payload") or {},
        }
        state_row = {
            "mmsi": mmsi,
            "imo": observation.get("imo"),
            "vessel_name": observation.get("vessel_name"),
            "ship_type_code": ship_type_code,
            "ship_category": ship_category,
            "region": region,
            "status": status_info["status"],
            "lat": lat,
            "lon": lon,
            "speed_knots": observation.get("speed_knots"),
            "heading": observation.get("heading"),
            "draught_meters": observation.get("draught_meters"),
            "destination": observation.get("destination"),
            "nav_status": observation.get("nav_status"),
            "estimated_barrels": estimated_barrels,
            "first_seen_at": previous_state.get("first_seen_at") if previous_state else observed_at.isoformat(),
            "first_stationary_at": status_info["first_stationary_at"],
            "last_movement_at": status_info["last_movement_at"],
            "last_seen_at": observed_at.isoformat(),
            "idle_days": status_info["idle_days"],
            "is_dark": bool(observation.get("is_dark") or False),
            "movement_bias": heading_bucket,
            "meta": observation.get("meta") or {},
            "updated_at": _now().isoformat(),
        }

        position_result = client.table("tanker_positions").insert_ignore(position_row)
        state_result = client.table("tanker_state").upsert(state_row, on_conflict="mmsi")
        write_error = position_result.get("error") or state_result.get("error")
        if write_error:
            return {"ok": False, "error": write_error}
        return {
            "ok": True,
            "region": region,
            "status": status_info["status"],
            "idle_days": status_info["idle_days"],
            "movement_bias": heading_bucket,
            "estimated_barrels": estimated_barrels,
        }
    except Exception as exc:
        logger.error("persist_tanker_observation error: %s", exc, exc_info=True)
        return {"ok": False, "error": str(exc)}


def refresh_chokepoint_metrics() -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return []
    if is_auth_failed():
        return []

    result = client.table("tanker_state").select("region,status,speed_knots,estimated_barrels,movement_bias,last_seen_at").execute()
    rows = _safe_rows(result)
    cutoff = _now().timestamp() - 48 * 3600
    aggregated: List[Dict[str, Any]] = []

    for region in REGIONS:
        relevant = []
        for row in rows:
            if row.get("region") != region:
                continue
            try:
                last_seen = _parse_dt(row.get("last_seen_at")).timestamp()
            except Exception:
                last_seen = 0.0
            if last_seen >= cutoff:
                relevant.append(row)

        vessel_count = len(relevant)
        floating_storage_vessels = sum(1 for row in relevant if row.get("status") == "floating_storage")
        anchored_vessels = sum(1 for row in relevant if row.get("status") in {"anchored", "idle", "floating_storage"})
        inbound_vessels = sum(1 for row in relevant if row.get("movement_bias") == "inbound")
        outbound_vessels = sum(1 for row in relevant if row.get("movement_bias") == "outbound")
        speeds = [float(row.get("speed_knots") or 0.0) for row in relevant]
        avg_speed = round(sum(speeds) / len(speeds), 2) if speeds else 0.0
        storage_estimate_mm_bbl = round(sum(float(row.get("estimated_barrels") or 0.0) for row in relevant if row.get("status") == "floating_storage") / 1_000_000.0, 2)
        congestion_score = min(100.0, round(vessel_count * 2.2 + floating_storage_vessels * 5.5 + anchored_vessels * 1.7 + max(0.0, 10 - avg_speed), 2))

        if floating_storage_vessels >= 4 or storage_estimate_mm_bbl >= 6:
            pressure_bias = "bearish"
            signal = "storage_buildup"
        elif outbound_vessels >= max(3, inbound_vessels + 2) and avg_speed >= 10:
            pressure_bias = "bullish"
            signal = "rush_delivery"
        elif vessel_count <= 1:
            pressure_bias = "neutral"
            signal = "thin_flow"
        else:
            pressure_bias = "neutral"
            signal = "watch"

        row = {
            "region": region,
            "vessel_count": vessel_count,
            "floating_storage_vessels": floating_storage_vessels,
            "anchored_vessels": anchored_vessels,
            "inbound_vessels": inbound_vessels,
            "outbound_vessels": outbound_vessels,
            "avg_speed": avg_speed,
            "congestion_score": congestion_score,
            "storage_estimate_mm_bbl": storage_estimate_mm_bbl,
            "pressure_bias": pressure_bias,
            "signal": signal,
            "source": "aisstream",
            "last_updated": _now().isoformat(),
            "meta": {
                "active_rows": vessel_count,
                "anchored_vessels": anchored_vessels,
            },
        }
        upsert_result = client.table("chokepoint_metrics").upsert(row, on_conflict="region")
        if upsert_result.get("error"):
            return aggregated
        aggregated.append(row)

    return aggregated


def get_chokepoint_metrics() -> Dict[str, Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return {}
    if is_auth_failed():
        return {}
    result = client.table("chokepoint_metrics").select("*").execute()
    rows = _safe_rows(result)
    return {str(row.get("region")): row for row in rows if row.get("region")}
