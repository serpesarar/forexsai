from fastapi import APIRouter, Query

from models.chart import ChartDataResponse
from services.chart_data_service import build_support_resistance, fetch_ohlcv_data

router = APIRouter(prefix="/api/data", tags=["chart_data"])


@router.get("/ohlcv", response_model=ChartDataResponse)
async def get_ohlcv_data(
    symbol: str = "NDX.INDX",
    timeframe: str = Query(default="5m", pattern="^(5m|15m|1h|4h|1d)$"),
    limit: int = Query(default=500, ge=50, le=500),
) -> ChartDataResponse:
    candles = await fetch_ohlcv_data(symbol, timeframe, limit)
    support_resistance = build_support_resistance(candles)
    return ChartDataResponse(
        symbol=symbol,
        timeframe=timeframe,
        data=candles,
        support_resistance=support_resistance,
    )
