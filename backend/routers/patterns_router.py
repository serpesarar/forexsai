"""Chart pattern endpoint — exposes the shared harmonic/classic pattern
engine (services.harmonic_pattern_service) as structured JSON so the
frontend (Neural panel "Tespit Edilen Formasyonlar") can draw pivot
points, projected D legs and targets on real data.

Read-only; reuses detect_chart_patterns which already fetches candles
through data_fetcher (DataHub) and degrades gracefully on error.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Query

from services.harmonic_pattern_service import detect_chart_patterns

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/patterns", tags=["patterns"])


@router.get("/{symbol}")
async def get_chart_patterns(
    symbol: str,
    timeframe: str = Query("4h", description="Candle timeframe (e.g. 1h, 4h)"),
    limit: int = Query(260, ge=50, le=500, description="Candles to scan"),
) -> Dict[str, Any]:
    """Detected harmonic + classic patterns with pivot points and targets.

    Response mirrors harmonic_pattern_service._summarize: patterns[] items
    carry points {X,A,B,C,D} ({index, price, time}), status
    COMPLETED/FORMING, projected_d {price, time} for forming harmonics,
    target_price, stop_loss, ratios and name/name_tr.
    """
    try:
        result = await detect_chart_patterns(symbol, timeframe=timeframe, limit=limit)
        return {"success": True, **result}
    except Exception as exc:  # fail-open: boş liste dön, paneli düşürme
        logger.warning("patterns endpoint failed for %s %s: %s", symbol, timeframe, exc)
        return {
            "success": False,
            "symbol": symbol,
            "timeframe": timeframe,
            "patterns": [],
            "has_patterns": False,
            "error": str(exc),
        }
