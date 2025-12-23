from fastapi import APIRouter

from backend.models.rtyhiim import RtyhiimResponse
from backend.services.rtyhiim_service import run_rtyhiim_detector

router = APIRouter(prefix="/api/rtyhiim", tags=["rtyhiim"])


@router.post("/detect", response_model=RtyhiimResponse)
async def detect_rtyhiim() -> RtyhiimResponse:
    result = run_rtyhiim_detector(symbol="NDX.INDX", timeframe="1m")
    return RtyhiimResponse(**result)
