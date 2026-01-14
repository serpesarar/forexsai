from fastapi import APIRouter, Query
from typing import Optional

from backend.models.rtyhiim import RtyhiimResponse
from backend.services.rtyhiim_service import run_rtyhiim_detector_async, detect_consolidation

router = APIRouter(prefix="/api/rtyhiim", tags=["rtyhiim"])


@router.post("/detect", response_model=RtyhiimResponse)
async def detect_rtyhiim(
    symbol: str = Query(default="NDX.INDX", description="Symbol to analyze (NDX.INDX or XAUUSD)")
) -> RtyhiimResponse:
    result = await run_rtyhiim_detector_async(symbol=symbol, timeframe="1m")
    return RtyhiimResponse(**result)


@router.get("/consolidation")
async def get_consolidation(
    symbol: str = Query(default="NDX.INDX", description="Symbol to analyze"),
    lookback: int = Query(default=20, ge=5, le=100, description="Number of candles to analyze"),
    interval: str = Query(default="1m", description="Timeframe: 1m, 5m, or 1h")
):
    """
    Yatay hareket (consolidation/range) tespiti.
    
    Son N mumu analiz ederek piyasanın yatay hareket içinde olup olmadığını tespit eder.
    
    Returns:
        - is_consolidating: Yatay hareket var mı?
        - range_high/low: Range sınırları
        - consolidation_score: 0-100 arası skor (60+ = consolidation)
        - breakout_direction: Potansiyel kırılım yönü (UP/DOWN/NEUTRAL)
    """
    result = await detect_consolidation(symbol, lookback, interval)
    return result.to_dict()
