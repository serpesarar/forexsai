"""
Market Events API — mum bazlı "Ne oldu?" endpoint'leri.

Frontend news-correlation grafiği bu router'ı kullanır:
  GET /api/market-events/candle-context   → tıklanan mumun tam bağlamı
  GET /api/market-events/markers/{symbol} → grafik olay işaretçileri

Haber akışı bağlı olmasa da çalışır (makro + takvim + seans + teknik anomali).
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from services.market_event_service import get_candle_context, get_event_markers

router = APIRouter(prefix="/api/market-events", tags=["market-events"])
logger = logging.getLogger(__name__)


@router.get("/candle-context")
async def candle_context(
    symbol: str = Query(..., description="Sembol (NDX, DAX, XAUUSD, USOIL veya kanonik ad)"),
    timestamp: int = Query(..., description="Mum açılışı UNIX saniye"),
    timeframe: str = Query("1h", description="Mum periyodu: 5m/15m/30m/1h/4h/1d"),
    lang: str = Query("tr", description="Tercih dili (payload iki dilde döner)"),
):
    """Tıklanan mumun 'Ne oldu?' bağlamı: teknik + makro + seans + olaylar."""
    try:
        result = await get_candle_context(symbol, timestamp, timeframe, lang)
        return result
    except Exception as e:
        logger.exception("candle-context failed for %s @ %s", symbol, timestamp)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/markers/{symbol}")
async def event_markers(
    symbol: str,
    hours: int = Query(168, ge=1, le=2160, description="Geriye dönük pencere (saat)"),
    timeframe: str = Query("1h", description="Anomali taraması için mum periyodu"),
    max_markers: int = Query(80, ge=1, le=200),
):
    """Grafik olay işaretçileri: takvim + haber + makro spike + anomali."""
    try:
        return await get_event_markers(symbol, hours=hours, timeframe=timeframe, max_markers=max_markers)
    except Exception as e:
        logger.exception("event markers failed for %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))
