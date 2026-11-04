"""Zaman Makinesi API'si (yöntem: day-trader-skill / trader-timemachine, MIT — services/time_machine_service.py).

  GET /api/time-machine/{symbol}?side=buy&stop_atr=1&target_r=1&bars=48&replays=5000&seed=19
      → planın olasılıkları (hedef önce / stop önce / hiçbiri), ufuk-sonu fiyat aralığı, geçmiş tekrar, hüküm
  GET /api/time-machine/calibration → aracın kendi geçmiş kalibrasyon karnesi (TM-01)
Bilgi amaçlıdır; emir açmaz, prediction_logs'a yazmaz.
"""
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from services.time_machine_service import TMError, get_time_machine

router = APIRouter(prefix="/api/time-machine", tags=["time-machine"])
logger = logging.getLogger(__name__)
CALIBRATION_FILE = Path(__file__).resolve().parents[1] / "data" / "time_machine_calibration.json"


@router.get("/calibration")
async def calibration():
    try:
        return json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


@router.get("/{symbol}")
async def time_machine(
    symbol: str,
    side: str = Query("buy", pattern="^(buy|sell)$"),
    stop_atr: float = Query(1.0, gt=0, le=10),
    target_r: float = Query(1.0, gt=0, le=10),
    bars: int = Query(48, ge=1, le=287),
    replays: int = Query(5000, ge=500, le=20000),
    seed: int = Query(19, ge=0),
):
    try:
        return await get_time_machine(symbol, side, stop_atr, target_r, bars, replays, seed)
    except TMError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("time-machine failed %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))
