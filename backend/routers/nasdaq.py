from fastapi import APIRouter

from models.responses import SignalResponse
from services.data_fetcher import fetch_latest_price
from services.ml_service import run_nasdaq_signal

router = APIRouter(prefix="/api/run", tags=["nasdaq"])


@router.post("/nasdaq", response_model=SignalResponse)
async def run_nasdaq() -> SignalResponse:
    # EODHD real-time supports NDX.INDX reliably; NAS100.INDX often returns "NA".
    current_price = await fetch_latest_price("NDX.INDX")
    result = run_nasdaq_signal(current_price=current_price)
    return SignalResponse(
        signal=result.signal,
        confidence=result.confidence,
        reasoning=result.reasoning,
        metrics=result.metrics,
        timestamp=result.timestamp,
        model_status=result.model_status,
    )
