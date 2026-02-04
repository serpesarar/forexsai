from fastapi import APIRouter

from models.responses import SignalResponse
from services.ml_service import run_nasdaq_signal_async, run_xauusd_signal_async

router = APIRouter(prefix="/api/run", tags=["nasdaq"])


@router.post("/nasdaq", response_model=SignalResponse)
async def run_nasdaq(timeframe: str = "1h") -> SignalResponse:
    """
    Run NASDAQ trend analysis using real-time data and trend_analyzer.
    Returns signal, confidence, reasoning, and metrics.
    timeframe: 5m, 15m, 30m, 1h, 4h, 1d
    """
    result = await run_nasdaq_signal_async(timeframe=timeframe)
    return SignalResponse(
        signal=result.signal,
        confidence=result.confidence,
        reasoning=result.reasoning,
        metrics=result.metrics,
        timestamp=result.timestamp,
        model_status=result.model_status,
    )
