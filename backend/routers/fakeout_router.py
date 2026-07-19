"""Fakeout Radar API — sahte kırılım tespit + kural servisi.

  GET  /api/fakeout/assess/{symbol}   Canlı değerlendirme: taze kırılım var mı,
                                      sahte olasılığı, eşleşen kurallar.
  GET  /api/fakeout/rules             Yüklü kural seti + üretim meta verisi.
  GET  /api/fakeout/report            İnsan-okur madencilik raporu (markdown).
  POST /api/fakeout/mine              Madenciyi yeniden çalıştır (research dir
                                      varsa; production'da 'unavailable' döner).

Kaynak: backend/research/fakeout_miner.py → backend/data/fakeout_rules.json.
Runtime değerlendirme: services/fakeout_service.py (60s TTL cache).
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from services import fakeout_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fakeout", tags=["Fakeout Radar"])

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_RESEARCH_DIR = Path(__file__).resolve().parent.parent / "research"

#: Madenci uzun sürer; aynı anda tek çalıştırma yeterli.
_mine_lock = asyncio.Lock()


@router.get("/assess/{symbol}")
async def assess(symbol: str):
    """Sembol için canlı sahte-kırılım değerlendirmesi (5m, 60s cache)."""
    try:
        result = await fakeout_service.assess_symbol(symbol)
        return {"symbol": symbol, **result}
    except Exception as exc:
        logger.exception("[fakeout] assess hatası: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)[:200])


@router.get("/rules")
async def rules(symbol: str = Query(default="NDX.INDX")):
    """Yüklü kural seti (kalite filtreli runtime kuralları işaretli)."""
    payload = fakeout_service.load_rules(symbol)
    if not payload:
        return {"status": "no_rules",
                "note": "backend/data/fakeout_rules.json yok — önce POST /api/fakeout/mine"}
    quality = fakeout_service._quality_rules(payload)
    return {"status": "ok",
            "generated_at": payload.get("generated_at"),
            "symbol": payload.get("symbol"),
            "events_total": payload.get("events_total"),
            "base_fake_rate_train": payload.get("base_fake_rate_train"),
            "base_fake_rate_test": payload.get("base_fake_rate_test"),
            "segments": payload.get("segments"),
            "runtime_rule_count": len(quality),
            "rules": payload.get("rules")}


@router.get("/report")
async def report():
    """Madencilik raporu (markdown metni)."""
    path = _DATA_DIR / "fakeout_report.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Rapor yok — önce mining çalıştırın")
    return {"markdown": path.read_text()}


@router.post("/mine")
async def mine(symbol: str = Query(default="NDX.INDX")):
    """Madenciyi yeniden çalıştır (dakikalar sürebilir; research dir gerekir)."""
    if not (_RESEARCH_DIR / "fakeout_miner.py").exists():
        return {"status": "miner_unavailable",
                "note": "research dizini deploy'da yok — miner'ı lokalde çalıştırıp "
                        "fakeout_rules.json'ı commit'leyin"}
    if _mine_lock.locked():
        return {"status": "already_running"}
    async with _mine_lock:
        try:
            import sys
            if str(_RESEARCH_DIR) not in sys.path:
                sys.path.insert(0, str(_RESEARCH_DIR))
            import fakeout_miner  # type: ignore
            loop = asyncio.get_running_loop()
            summary = await loop.run_in_executor(
                None, lambda: fakeout_miner.run_mining(symbol=symbol, write_files=True))
            summary.pop("rules", None)   # yanıtı şişirme; kurallar /rules'tan okunur
            return {"status": "ok", **{k: v for k, v in summary.items()
                                       if k not in ("segments",)}}
        except Exception as exc:
            logger.exception("[fakeout] mining hatası: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc)[:300])
