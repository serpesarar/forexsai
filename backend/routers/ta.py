from __future__ import annotations

from fastapi import APIRouter, Query

from services.ta_service import compute_ta_snapshot


router = APIRouter(prefix="/api/ta", tags=["ta"])


@router.get("/snapshot")
async def snapshot(symbol: str = Query(default="NDX.INDX")) -> dict:
    return await compute_ta_snapshot(symbol=symbol)



