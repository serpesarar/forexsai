from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter

from services.oil_baltic_live_service import build_oil_baltic_intelligence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/panel", tags=["oil-baltic-intelligence"])


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
