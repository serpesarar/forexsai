from fastapi import APIRouter

from models.responses import SignalResponse
from services.ml_service import run_nasdaq_signal_async

router = APIRouter(prefix="/api/run", tags=["nasdaq"])


@router.post("/nasdaq", response_model=SignalResponse)
async def run_nasdaq() -> SignalResponse:
    """
    Run NASDAQ trend analysis using real-time data and trend_analyzer.
    Returns signal, confidence, reasoning, and metrics.
    """
    result = await run_nasdaq_signal_async()
    return SignalResponse(
        signal=result.signal,
        confidence=result.confidence,
        reasoning=result.reasoning,
        metrics=result.metrics,
        timestamp=result.timestamp,
        model_status=result.model_status,
    )
