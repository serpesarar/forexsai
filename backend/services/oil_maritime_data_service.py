from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from dateutil import parser as dateutil_parser

from database.supabase_client import get_auth_error, get_supabase_client, is_auth_failed

try:
    from config import settings as _settings
except Exception:  # pragma: no cover - config always present in app runtime
    _settings = None

logger = logging.getLogger(__name__)

# In-memory mirror of the last tanker_state row we wrote per MMSI. Replaces a
# per-AIS-message SELECT against tanker_state (was ~16M calls) — the upsert we
# perform right after already produces the authoritative row, so we cache that.
_STATE_CACHE: Dict[int, Dict[str, Any]] = {}
_STATE_CACHE_MAX = 20000


def _cfg(name: str, default: Any) -> Any:
    return getattr(_settings, name, default) if _settings is not None else default

REGIONS: Dict[str, Dict[str, Any]] = {
    "strait_of_hormuz": {
        "label": "Strait of Hormuz",
        "bounds": [[24.5, 55.0], [27.0, 57.5]],
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


def get_tanker_state(mmsi: int, use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """Latest tanker_state row for an MMSI.

    On the hot AIS ingest path we serve this from ``_STATE_CACHE`` (populated by
    the upsert in :func:`persist_tanker_observation`) so we only ever hit the DB
    once per vessel per process lifetime. Pass ``use_cache=False`` for read
    endpoints that need a guaranteed-fresh row.
    """
    if use_cache:
        cached = _STATE_CACHE.get(int(mmsi))
        if cached is not None:
            return cached
    client = get_supabase_client()
    if client is None:
        return None
    if is_auth_failed():
        return None
    result = client.table("tanker_state").select("*").eq("mmsi", mmsi).limit(1).execute()
    row = _safe_row(result)
    if row is not None and use_cache:
        _cache_state(int(mmsi), row)
    return row


def _cache_state(mmsi: int, row: Dict[str, Any]) -> None:
    if len(_STATE_CACHE) >= _STATE_CACHE_MAX and mmsi not in _STATE_CACHE:
        # Cheap eviction — drop an arbitrary older entry. tanker_state has
        # ~34k total rows; this cap is only a memory guardrail.
        try:
            _STATE_CACHE.pop(next(iter(_STATE_CACHE)))
        except StopIteration:
            pass
    _STATE_CACHE[mmsi] = row


def get_recent_tankers(limit: int = 80, freshness_hours: int = 48) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return []
    if is_auth_failed():
        return []

    cutoff = (_now() - timedelta(hours=max(1, int(freshness_hours or 48)))).isoformat()
    result = (
        client.table("tanker_state")
        .select("mmsi,vessel_name,lat,lon,speed_knots,heading,region,status,idle_days,last_seen_at,estimated_barrels,ship_category")
        .gte("last_seen_at", cutoff)
        .order("last_seen_at", desc=True)
        .limit(max(1, min(int(limit or 80), 200)))
        .execute()
    )

    items: List[Dict[str, Any]] = []
    for row in _safe_rows(result):
        try:
            lat = float(row.get("lat"))
            lon = float(row.get("lon"))
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        items.append({
            "mmsi": int(row.get("mmsi") or 0),
            "vessel_name": row.get("vessel_name"),
            "lat": lat,
            "lon": lon,
            "speed_knots": row.get("speed_knots"),
            "heading": row.get("heading"),
            "region": row.get("region") or detect_region(lat, lon),
            "status": row.get("status") or "transit",
            "idle_days": row.get("idle_days"),
            "last_seen_at": row.get("last_seen_at"),
            "estimated_barrels": row.get("estimated_barrels"),
            "ship_category": row.get("ship_category"),
        })
    return items


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
        previous_state = get_tanker_state(mmsi, use_cache=True)
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
        }
        # raw_payload (full AIS websocket frame) is never read back — writing it
        # on every row is what ballooned tanker_positions to 38 GB. Off by
        # default; AIS_STORE_RAW_PAYLOAD=1 restores it for debugging.
        if _cfg("ais_store_raw_payload", False):
            position_row["raw_payload"] = observation.get("raw_payload") or {}
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

        position_result = client.table("tanker_positions").insert_ignore(
            position_row, on_conflict="mmsi,observed_at"
        )
        state_result = client.table("tanker_state").upsert(state_row, on_conflict="mmsi")
        write_error = position_result.get("error") or state_result.get("error")
        if write_error:
            return {"ok": False, "error": write_error}
        # Feed the cache so the next observation for this vessel skips the DB read.
        _cache_state(mmsi, state_row)
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


def _aggregate_from_positions(client: Any, region: str, hours: int) -> Dict[str, Any]:
    """Aggregate chokepoint metrics from tanker_positions using trailing window.

    For transit chokepoints like Hormuz, this captures vessels that passed through
    recently even if they've already exited the region (unlike tanker_state which
    only shows current position).
    """
    cutoff = (_now() - timedelta(hours=hours)).isoformat()
    bounds = REGIONS.get(region, {}).get("bounds", [[0, 0], [0, 0]])
    (min_lat, min_lon), (max_lat, max_lon) = bounds

    # Query tanker_positions for this region within the time window
    result = (
        client.table("tanker_positions")
        .select("mmsi,status,speed_knots,estimated_barrels,heading,observed_at")
        .eq("region", region)
        .gte("observed_at", cutoff)
        .execute()
    )
    rows = _safe_rows(result)

    if not rows:
        return {
            "vessel_count": 0,
            "floating_storage_vessels": 0,
            "anchored_vessels": 0,
            "inbound_vessels": 0,
            "outbound_vessels": 0,
            "avg_speed": 0.0,
            "storage_estimate_mm_bbl": 0.0,
            "active_rows": 0,
        }

    # Get distinct vessels (latest record per mmsi)
    seen_mmsi: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        mmsi = int(row.get("mmsi") or 0)
        if mmsi not in seen_mmsi:
            seen_mmsi[mmsi] = row
        else:
            # Keep the more recent observation
            try:
                current_ts = _parse_dt(row.get("observed_at")).timestamp()
                existing_ts = _parse_dt(seen_mmsi[mmsi].get("observed_at")).timestamp()
                if current_ts > existing_ts:
                    seen_mmsi[mmsi] = row
            except Exception:
                pass

    relevant = list(seen_mmsi.values())
    vessel_count = len(relevant)
    floating_storage_vessels = sum(1 for r in relevant if r.get("status") == "floating_storage")
    anchored_vessels = sum(1 for r in relevant if r.get("status") in {"anchored", "idle", "floating_storage"})

    # Calculate inbound/outbound from heading using same logic as _heading_bucket
    inbound_vessels = 0
    outbound_vessels = 0
    for r in relevant:
        heading = r.get("heading")
        if heading is not None:
            bucket = _heading_bucket(region, float(heading))
            if bucket == "inbound":
                inbound_vessels += 1
            elif bucket == "outbound":
                outbound_vessels += 1

    speeds = [float(r.get("speed_knots") or 0.0) for r in relevant]
    avg_speed = round(sum(speeds) / len(speeds), 2) if speeds else 0.0
    storage_estimate_mm_bbl = round(
        sum(float(r.get("estimated_barrels") or 0.0) for r in relevant if r.get("status") == "floating_storage") / 1_000_000.0, 2
    )

    return {
        "vessel_count": vessel_count,
        "floating_storage_vessels": floating_storage_vessels,
        "anchored_vessels": anchored_vessels,
        "inbound_vessels": inbound_vessels,
        "outbound_vessels": outbound_vessels,
        "avg_speed": avg_speed,
        "storage_estimate_mm_bbl": storage_estimate_mm_bbl,
        "active_rows": len(rows),  # Total position records (not distinct vessels)
    }


def refresh_chokepoint_metrics() -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return []
    if is_auth_failed():
        return []

    # Determine trailing window per region type:
    # - Transit chokepoints (Hormuz, US Gulf): 12h window (fast passage)
    # - Storage hubs (Rotterdam, Singapore): 48h window (vessels stay longer)
    TRANSIT_REGIONS = {"strait_of_hormuz", "us_gulf"}

    aggregated: List[Dict[str, Any]] = []

    for region in REGIONS:
        is_transit = region in TRANSIT_REGIONS
        trailing_hours = 12 if is_transit else 48

        # Use tanker_positions with trailing window for all regions
        # This captures recent passage even for vessels that have exited
        metrics = _aggregate_from_positions(client, region, trailing_hours)

        vessel_count = metrics["vessel_count"]
        floating_storage_vessels = metrics["floating_storage_vessels"]
        anchored_vessels = metrics["anchored_vessels"]
        inbound_vessels = metrics["inbound_vessels"]
        outbound_vessels = metrics["outbound_vessels"]
        avg_speed = metrics["avg_speed"]
        storage_estimate_mm_bbl = metrics["storage_estimate_mm_bbl"]

        # Congestion score calculation
        congestion_score = min(
            100.0,
            round(vessel_count * 2.2 + floating_storage_vessels * 5.5 + anchored_vessels * 1.7 + max(0.0, 10 - avg_speed), 2),
        )

        # Signal logic
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
                "active_rows": metrics["active_rows"],
                "anchored_vessels": anchored_vessels,
                "trailing_hours": trailing_hours,
                "aggregation_method": "positions_trailing_window",
            },
        }
        upsert_result = client.table("chokepoint_metrics").upsert(row, on_conflict="region")
        if upsert_result.get("error"):
            logger.error("Failed to upsert chokepoint_metrics for %s: %s", region, upsert_result.get("error"))
            continue
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
