from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import websockets

from config import settings
from services.oil_maritime_data_service import TANKER_TYPES, persist_tanker_observation, refresh_chokepoint_metrics

logger = logging.getLogger(__name__)

DEFAULT_BOUNDING_BOXES = [
    [[25.0, 56.0], [26.5, 57.5]],
    [[1.0, 103.5], [1.5, 104.5]],
    [[28.0, -95.0], [30.5, -89.5]],
    [[51.7, 3.8], [52.2, 4.6]],
]


class AISOilCollector:
    def __init__(self) -> None:
        self.ws_url = settings.aisstream_ws_url or "wss://stream.aisstream.io/v0/stream"
        self.api_key = settings.aisstream_api_key
        self.running = False
        self._static_cache: Dict[int, Dict[str, Any]] = {}

    def _subscription(self) -> Dict[str, Any]:
        return {
            "APIKey": self.api_key,
            "BoundingBoxes": DEFAULT_BOUNDING_BOXES,
            "FilterMessageTypes": ["PositionReport", "ShipStaticData"],
            "FilterShipTypes": sorted(TANKER_TYPES),
        }

    def _parse_timestamp(self, value: Any) -> str:
        if isinstance(value, str) and value:
            return value
        if isinstance(value, (int, float)):
            timestamp = float(value)
            if timestamp > 10_000_000_000:
                timestamp /= 1000.0
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        return datetime.now(timezone.utc).isoformat()

    def _normalize_static(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        meta = payload.get("MetaData") or {}
        message = payload.get("Message") or {}
        ship_static = message.get("ShipStaticData") or message
        mmsi = meta.get("MMSI") or ship_static.get("UserID") or ship_static.get("MMSI")
        if not mmsi:
            return {}
        row = {
            "mmsi": int(mmsi),
            "imo": ship_static.get("ImoNumber") or meta.get("IMO") or ship_static.get("IMO"),
            "vessel_name": ship_static.get("Name") or meta.get("ShipName") or meta.get("Name"),
            "ship_type_code": ship_static.get("Type") or meta.get("ShipType"),
            "destination": ship_static.get("Destination"),
            "draught_meters": ship_static.get("MaximumStaticDraught") or ship_static.get("Draft"),
            "meta": {
                "call_sign": ship_static.get("CallSign"),
                "dimension": ship_static.get("Dimension"),
            },
        }
        self._static_cache[int(mmsi)] = row
        return row

    def _normalize_position(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        meta = payload.get("MetaData") or {}
        message = payload.get("Message") or {}
        position = message.get("PositionReport") or message.get("StandardClassBPositionReport") or message.get("BaseStationReport") or {}
        mmsi = meta.get("MMSI") or position.get("UserID") or position.get("MMSI")
        if not mmsi:
            return {}
        static = self._static_cache.get(int(mmsi), {})
        return {
            "mmsi": int(mmsi),
            "imo": static.get("imo") or meta.get("IMO"),
            "vessel_name": static.get("vessel_name") or meta.get("ShipName") or meta.get("Name"),
            "ship_type_code": static.get("ship_type_code") or meta.get("ShipType"),
            "destination": static.get("destination"),
            "draught_meters": static.get("draught_meters"),
            "lat": position.get("Latitude") or meta.get("latitude") or meta.get("lat"),
            "lon": position.get("Longitude") or meta.get("longitude") or meta.get("lon"),
            "speed_knots": position.get("Sog") or position.get("SpeedOverGround"),
            "heading": position.get("Cog") or position.get("TrueHeading"),
            "nav_status": position.get("NavigationalStatus"),
            "observed_at": self._parse_timestamp(meta.get("time_utc") or payload.get("time_utc") or position.get("Timestamp")),
            "data_source": "aisstream",
            "raw_payload": payload,
            "meta": static.get("meta") or {},
        }

    async def _handle_message(self, raw_message: str) -> None:
        try:
            payload = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.debug("AIS message is not valid JSON")
            return

        message_type = str(payload.get("MessageType") or payload.get("message_type") or "")
        if message_type == "ShipStaticData":
            self._normalize_static(payload)
            return

        normalized = self._normalize_position(payload)
        if not normalized:
            return
        if normalized.get("lat") is None or normalized.get("lon") is None:
            return

        result = persist_tanker_observation(normalized)
        if result.get("ok"):
            refresh_chokepoint_metrics()
            return

        error_text = str(result.get("error") or "")
        if "authentication failed" in error_text.lower() or "supabase_auth_failed" in error_text.lower():
            logger.error("AIS collector stopping because Supabase authentication failed")
            self.running = False

    async def run_forever(self) -> None:
        if not self.api_key:
            raise RuntimeError("AISSTREAM_API_KEY is not configured")
        self.running = True
        while self.running:
            try:
                async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=20, close_timeout=10, max_size=2_000_000) as socket:
                    await socket.send(json.dumps(self._subscription()))
                    logger.info("AIS oil collector connected")
                    async for raw_message in socket:
                        await self._handle_message(raw_message)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("AIS collector loop error: %s", exc, exc_info=True)
                await asyncio.sleep(8)

    def stop(self) -> None:
        self.running = False


_COLLECTOR_TASK: Optional[asyncio.Task] = None
_COLLECTOR: Optional[AISOilCollector] = None


def _log_collector_task_result(task: asyncio.Task) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        logger.info("AIS oil collector task cancelled")
    except Exception as exc:
        logger.error("AIS oil collector task crashed: %s", exc, exc_info=True)


def start_ais_oil_collector() -> None:
    global _COLLECTOR, _COLLECTOR_TASK
    if _COLLECTOR_TASK and not _COLLECTOR_TASK.done():
        return
    _COLLECTOR = AISOilCollector()
    if not _COLLECTOR.api_key:
        logger.warning("AIS oil collector not started because AISSTREAM_API_KEY is not configured")
        return
    _COLLECTOR_TASK = asyncio.create_task(_COLLECTOR.run_forever())
    _COLLECTOR_TASK.add_done_callback(_log_collector_task_result)
    logger.info("AIS oil collector background task created")


def stop_ais_oil_collector() -> None:
    global _COLLECTOR, _COLLECTOR_TASK
    if _COLLECTOR:
        _COLLECTOR.stop()
    if _COLLECTOR_TASK and not _COLLECTOR_TASK.done():
        _COLLECTOR_TASK.cancel()
