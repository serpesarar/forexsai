from fastapi import APIRouter

from models.responses import SignalResponse
from services.data_fetcher import fetch_latest_price
from services.ml_service import run_xauusd_signal

router = APIRouter(prefix="/api/run", tags=["xauusd"])


@router.post("/xauusd", response_model=SignalResponse)
async def run_xauusd() -> SignalResponse:
    current_price = await fetch_latest_price("XAUUSD")
    result = run_xauusd_signal(current_price=current_price)
    return SignalResponse(
        signal=result.signal,
        confidence=result.confidence,
        reasoning=result.reasoning,
        metrics=result.metrics,
        timestamp=result.timestamp,
        model_status=result.model_status,
    )
