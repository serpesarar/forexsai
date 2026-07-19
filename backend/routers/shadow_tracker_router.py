"""Shadow Trade Tracker endpoint'leri — formasyon + fakeout tespitlerinin
sızıntısız paper-trade doğrulama raporu.

Read-only rapor + status; run-once yalnız tetikleyicidir (canlı sinyal
akışına, prediction_logs'a veya MT5 bot'a hiçbir etkisi yoktur).
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from services.shadow_trade_tracker import build_report, get_status, run_cycle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/shadow-tracker", tags=["shadow-tracker"])


@router.get("/report")
async def shadow_report(
    days: int = Query(30, ge=1, le=120, description="Rapor penceresi (gün)"),
    symbol: Optional[str] = Query(None, description="Tek sembole filtrele"),
) -> Dict[str, Any]:
    """Kaynak / sembol / formasyon / güven-kovası kırılımlı isabet raporu."""
    try:
        return await build_report(days=days, symbol=symbol)
    except Exception as exc:  # fail-open
        logger.warning("shadow report hata: %s", exc)
        return {"success": False, "error": str(exc)[:200]}


@router.get("/status")
async def shadow_status() -> Dict[str, Any]:
    """Döngü durumu + konfigürasyon."""
    return {"success": True, **get_status()}


@router.post("/run-once")
async def shadow_run_once() -> Dict[str, Any]:
    """Bir tarama + çözümleme turunu ŞİMDİ çalıştır (test/tetik amaçlı)."""
    try:
        cycle = await run_cycle()
        return {"success": True, "cycle": cycle}
    except Exception as exc:
        logger.warning("shadow run-once hata: %s", exc)
        return {"success": False, "error": str(exc)[:200]}
