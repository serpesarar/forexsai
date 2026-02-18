from fastapi import APIRouter

from models.responses import SignalResponse
from services.ml_service import run_usoil_signal_async

router = APIRouter(prefix="/api/run", tags=["usoil"])


@router.post("/usoil", response_model=SignalResponse)
async def run_usoil(timeframe: str = "1h") -> SignalResponse:
    """
    Run US OIL (CL.COMM) trend analysis using real-time data and trend_analyzer.
    Returns signal, confidence, reasoning, and metrics.
    timeframe: 5m, 15m, 30m, 1h, 4h, 1d
    """
    result = await run_usoil_signal_async(timeframe=timeframe)
    return SignalResponse(
        signal=result.signal,
        confidence=result.confidence,
        reasoning=result.reasoning,
        metrics=result.metrics,
        timestamp=result.timestamp,
        model_status=result.model_status,
    )
