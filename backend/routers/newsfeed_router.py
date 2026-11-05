"""Canlı haber akışı API'si. Emir açmaz, sinyal üretmez, prediction_logs'a yazmaz.

  GET /api/newsfeed/latest?symbol=&min_relevance=&limit=  → en yeni hikâyeler
  GET /api/newsfeed/sources                               → kaynak hız karnesi (hangisi önce getiriyor)
  GET /api/newsfeed/status                                → motor sağlığı
  GET /api/newsfeed/stream                                → canlı olay akışı (SSE)
  GET /api/newsfeed/repo-scorecard                        → 40 GitHub deposunun karnesi (statik dosya)
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from services.newsfeed.classifier import RELEVANCE_MIN
from services.newsfeed.engine import get_engine

router = APIRouter(prefix="/api/newsfeed", tags=["newsfeed"])
logger = logging.getLogger(__name__)
SSE_HEARTBEAT_S = 20.0
SCORECARD_FILE = Path(__file__).resolve().parents[1] / "data" / "evolution" / "repo_karnesi.json"


@router.get("/latest")
async def latest(symbol: str | None = None, min_relevance: int = Query(RELEVANCE_MIN, ge=0, le=100),
                 limit: int = Query(100, ge=1, le=500), include_opinion: bool = False) -> dict[str, Any]:
    """En yeni hikâyeler; yeni başlıklar yapay zekâ beklemeden burada görünür."""
    engine = get_engine()
    return {"running": engine.status()["running"], "items": engine.latest(symbol, min_relevance, limit, include_opinion)}


@router.get("/sources")
async def sources() -> dict[str, Any]:
    """Kaynak karnesi: yarış sayısı, önde olma oranı, gecikme, hata, sorgu aralığı."""
    engine = get_engine()
    return {"sources": engine.board.table(), "inactive": engine.status()["inactive_sources"]}


@router.get("/status")
async def status() -> dict[str, Any]:
    """Motor durumu."""
    return get_engine().status()


@router.get("/repo-scorecard")
async def repo_scorecard() -> dict[str, Any]:
    """Depo karnesi; üretici `research/github_haber_sekil_20261104/degerlendirme/karne_olustur.py`."""
    if not SCORECARD_FILE.exists():
        return {"repolar": [], "uretim": None}
    return json.loads(SCORECARD_FILE.read_text(encoding="utf-8"))


async def _sse(engine: Any) -> AsyncIterator[str]:
    stream = engine.subscribe()
    pending = asyncio.ensure_future(stream.__anext__())
    try:
        while True:
            done, _ = await asyncio.wait({pending}, timeout=SSE_HEARTBEAT_S)
            if not done:
                yield ": hb\n\n"
                continue
            yield f"data: {json.dumps(pending.result(), ensure_ascii=False)}\n\n"
            pending = asyncio.ensure_future(stream.__anext__())
    finally:
        pending.cancel()
        await stream.aclose()


@router.get("/stream")
async def stream() -> StreamingResponse:
    """Yeni hikâyeleri anında iletir (EventSource)."""
    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(_sse(get_engine()), media_type="text/event-stream", headers=headers)
