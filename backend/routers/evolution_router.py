"""Evrim Paneli API'si — /api/evolution/*

Kendi kendini besleyen sistemin kontrol yüzeyi. Frontend /evolution sayfası
bu endpoint'leri tüketir. Tüm iş mantığı services/evolution_service.py'de.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services import evolution_service as evo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evolution", tags=["evolution"])


# ── Request modelleri ────────────────────────────────────────────────────

class BacklogCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    detail: str = ""
    category: str = "idea"
    priority: str = "medium"
    source: str = "manual"


class BacklogUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    title: Optional[str] = None
    detail: Optional[str] = None
    category: Optional[str] = None


class RunRequest(BaseModel):
    extra_args: str = ""


class LearnRequest(BaseModel):
    targets: List[str] = Field(default_factory=lambda: ["panel"])
    symbol: Optional[str] = None
    instruction: str = ""


class LessonCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    summary: str = Field(..., min_length=3)
    targets: List[str] = Field(default_factory=lambda: ["panel"])
    symbol: Optional[str] = None


class LessonStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|archived)$")


class SessionNote(BaseModel):
    summary: str = Field(..., min_length=3)
    files: List[str] = Field(default_factory=list)
    backlog_added: List[str] = Field(default_factory=list)


# ── Genel bakış + katalog ────────────────────────────────────────────────

@router.get("/overview")
async def get_overview(days: int = Query(30, ge=1, le=365)):
    """Panelin üst kartları: model başarıları + bias karnesi + sayaçlar."""
    return await evo.get_overview(days=days)


@router.get("/registry")
async def get_registry():
    """Sistem haritası: tüm motor/ajan/servis kataloğu."""
    return {"components": evo.get_registry()}


@router.get("/analyses")
async def get_analyses():
    """Tek tıkla çalıştırılabilir analiz kataloğu."""
    return {"analyses": evo.get_analyses()}


@router.get("/changelog")
async def get_changelog(limit: int = Query(60, ge=1, le=200)):
    """Canlı değişiklik akışı: git commit'leri + oturum notları + worktree."""
    return {"entries": await evo.get_changelog(limit=limit)}


# ── Backlog ──────────────────────────────────────────────────────────────

@router.get("/backlog")
async def get_backlog(include_done: bool = Query(True)):
    """Bekleyen / unutulan işler."""
    return {"items": evo.get_backlog(include_done=include_done)}


@router.post("/backlog")
async def create_backlog_item(body: BacklogCreate):
    """Yeni bekleyen iş ekle (başlık bazlı dedup)."""
    return evo.add_backlog_item(
        title=body.title, detail=body.detail, category=body.category,
        priority=body.priority, source=body.source,
    )


@router.patch("/backlog/{item_id}")
async def patch_backlog_item(item_id: str, body: BacklogUpdate):
    """Backlog kaydını güncelle (durum/öncelik/metin)."""
    item = evo.update_backlog_item(item_id, **body.model_dump(exclude_none=True))
    if item is None:
        raise HTTPException(status_code=404, detail=f"backlog kaydı yok: {item_id}")
    return item


# ── Analiz çalıştırma ────────────────────────────────────────────────────

@router.post("/analyses/{analysis_id}/run")
async def run_analysis(analysis_id: str, body: RunRequest | None = None):
    """Katalogdaki analizi arka planda başlat."""
    try:
        return await evo.start_run(analysis_id, extra_args=(body.extra_args if body else ""))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RuntimeError, ValueError) as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/runs")
async def get_runs(limit: int = Query(40, ge=1, le=200)):
    """Geçmiş çalıştırmalar (yeniden eskiye)."""
    return {"runs": evo.list_runs(limit=limit)}


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Tek çalıştırmanın durumu + çıktı kuyruğu (polling için)."""
    run = evo.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run yok: {run_id}")
    return run


# ── Öğrenme köprüsü ─────────────────────────────────────────────────────

@router.post("/runs/{run_id}/learn")
async def learn_from_run(run_id: str, body: LearnRequest):
    """Çalıştır → Öğret: analiz çıktısını LLM ile derse damıt ve hedeflere enjekte et."""
    try:
        return await evo.distill_run_to_lesson(
            run_id, targets=body.targets, symbol=body.symbol,
            instruction=body.instruction,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/lessons")
async def get_lessons(include_archived: bool = Query(False)):
    """Damıtılmış dersler."""
    return {"lessons": evo.get_lessons(include_archived=include_archived)}


@router.post("/lessons")
async def create_lesson(body: LessonCreate):
    """Elle ders ekle (analiz çıktısı olmadan)."""
    return evo.add_lesson(
        title=body.title, summary=body.summary,
        targets=body.targets, symbol=body.symbol,
    )


@router.patch("/lessons/{lesson_id}")
async def patch_lesson(lesson_id: str, body: LessonStatusUpdate):
    """Dersi arşivle / yeniden etkinleştir."""
    lesson = evo.update_lesson_status(lesson_id, body.status)
    if lesson is None:
        raise HTTPException(status_code=404, detail=f"ders yok: {lesson_id}")
    return lesson


# ── 1. Kural: oturum notu ────────────────────────────────────────────────

@router.post("/session-note")
async def add_session_note(body: SessionNote):
    """Claude Code oturumu değişiklik özetini kaydeder (1. Kural)."""
    return evo.add_session_note(
        summary=body.summary, files=body.files, backlog_added=body.backlog_added,
    )
