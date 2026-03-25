from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from services.mapbox_usage_guard import claim_mapbox_web_load
from services.oil_baltic_live_service import build_oil_baltic_intelligence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/panel", tags=["oil-baltic-intelligence"])


class MapboxClaimRequest(BaseModel):
    session_key: str = ""


@router.get("/oil-baltic-intelligence")
async def get_oil_baltic_intelligence() -> Dict[str, Any]:
    try:
        return await build_oil_baltic_intelligence()
    except Exception as exc:
        logger.error("Oil Baltic intelligence error: %s", exc, exc_info=True)
        return {
            "available": False,
            "error": str(exc),
            "source_health": [
                {
                    "name": "Oil Baltic intelligence",
                    "status": "error",
                    "mode": "internal",
                    "note": "Panel engine failed during computation.",
                }
            ],
        }


@router.post("/oil-baltic-intelligence/mapbox-claim")
async def claim_oil_baltic_mapbox_load(payload: MapboxClaimRequest) -> Dict[str, Any]:
    try:
        return claim_mapbox_web_load(session_key=payload.session_key)
    except Exception as exc:
        logger.error("Oil Baltic mapbox claim error: %s", exc, exc_info=True)
        return {
            "allow_live_map": False,
            "claimed": False,
            "mode": "fallback",
            "reason": str(exc),
            "month_used": 0,
            "month_limit": 0,
            "remaining_month": 0,
            "day_used": 0,
            "day_limit": 0,
            "remaining_day": 0,
            "reserve_ratio": 0.0,
            "vendor_free_limit": 0,
            "metric": "map_loads_web",
        }
