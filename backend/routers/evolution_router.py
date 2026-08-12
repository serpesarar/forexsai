"""Evrim Paneli API'si — /api/evolution/*

Kendi kendini besleyen sistemin kontrol yüzeyi. Frontend /evolution sayfası
bu endpoint'leri tüketir. Tüm iş mantığı services/evolution_service.py'de.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services import evolution_service as evo
from services import evolution_remote as remote

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
    """Katalogdaki analizi başlat — yerelde, ya da 'MT5 kutusu' etiketliyse uzakta."""
    extra_args = body.extra_args if body else ""
    analysis = evo._find_analysis(analysis_id)
    if analysis is not None and analysis.get("runnable_here") is False:
        try:
            return await asyncio.to_thread(remote.start_remote_analysis, analysis, extra_args)
        except (RuntimeError, ValueError) as e:
            raise HTTPException(status_code=409, detail=str(e))
    try:
        return await evo.start_run(analysis_id, extra_args=extra_args)
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
    """Tek çalıştırmanın durumu + çıktı kuyruğu (polling için).

    'cmd_' önekli id'ler MT5 kutusundaki uzak komutlardır — Supabase'ten okunur;
    frontend'in çıktı çekmecesi ikisini de aynı şekilde gösterir.
    """
    cmd_id = remote.parse_cmd_run_id(run_id)
    if cmd_id is not None:
        cmd = await asyncio.to_thread(remote.get_command, cmd_id)
        if cmd is None:
            raise HTTPException(status_code=404, detail=f"uzak komut yok: {run_id}")
        return remote.command_to_run_meta(cmd)
    run = evo.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run yok: {run_id}")
    return run


# ── Evrim Ajanı köprüsü (MT5 kutusu) ─────────────────────────────────────

class RemoteCommandRequest(BaseModel):
    kind: str = Field(..., pattern="^(sync_lessons|git_pull|restart_bot)$")
    payload: dict = Field(default_factory=dict)


@router.get("/remote/status")
async def remote_status():
    """MT5 kutusu kalp atışı + komut kuyruğu durumu."""
    try:
        return await asyncio.to_thread(remote.get_remote_status)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/remote/bot-performance")
async def remote_bot_performance(days: int = Query(30, ge=1, le=365)):
    """Gerçek MT5 işlem sonuçları (bot_trades) — sembol kırılımlı."""
    try:
        return await asyncio.to_thread(remote.get_bot_performance, days)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/remote/bot-trades")
async def remote_bot_trades(symbol: str = Query(..., min_length=2, max_length=20),
                            days: int = Query(30, ge=1, le=365)):
    """Tek sembolün son MT5 işlemleri (Canlı Bot panelinde sembole tıkla)."""
    try:
        return await asyncio.to_thread(remote.get_bot_trades, symbol, days)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/analyst/run")
async def run_analyst_now():
    """Günlük Veri Analisti'ni ŞİMDİ çalıştır (panelden manuel tetik)."""
    from services.daily_analyst import run_daily_analysis
    try:
        return await run_daily_analysis(force=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyst/latest")
async def analyst_latest():
    """Son analist raporu (markdown) + tarih."""
    from services.daily_analyst import REPORT_DIR
    try:
        reports = sorted(REPORT_DIR.glob("2*.md"), reverse=True)
        if not reports:
            return {"date": None, "report": None}
        return {"date": reports[0].stem, "report": reports[0].read_text(encoding="utf-8")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/remote/decider-breakdown")
async def remote_decider_breakdown(days: int = Query(30, ge=1, le=365)):
    """Decider sembol × yön kırılımı + son kararlar (yüzdeye tıkla → detay)."""
    try:
        return await asyncio.to_thread(remote.get_decider_breakdown, days)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/remote/decider-symbol-history")
async def remote_decider_symbol_history(
    symbol: str = Query(..., min_length=2, max_length=32),
    days: int = Query(30, ge=1, le=365),
):
    """Tek sembolün decider geçmişi — gün bazlı + yön bazlı kırılım (karta tıkla)."""
    try:
        return await asyncio.to_thread(remote.get_decider_symbol_history, symbol, days)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/remote/bot-vs-decider")
async def remote_bot_vs_decider(days: int = Query(30, ge=1, le=365)):
    """Bot ↔ Decider yakın-zaman karşılaştırması + karşılıklı dersler."""
    try:
        return await asyncio.to_thread(remote.get_bot_vs_decider, days)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/remote/decider-stats")
async def remote_decider_stats(days: int = Query(30, ge=1, le=365)):
    """Claude Decider karar karnesi (decider_journal)."""
    try:
        return await asyncio.to_thread(remote.get_decider_stats, days)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/remote/command")
async def remote_command(body: RemoteCommandRequest):
    """Kutuya komut gönder: ders senkronu / git pull / güvenli bot restart.

    sync_lessons payload'ı sunucuda üretilir (aktif panel dersleri bloğu) —
    istemciden içerik kabul edilmez.
    """
    payload = dict(body.payload)
    if body.kind == "sync_lessons":
        payload = {"content": evo.build_decider_lessons_block()}
    try:
        cmd = await asyncio.to_thread(
            remote.enqueue_command, body.kind, payload,
            remote.DEFAULT_HOST, "panel",
        )
        return remote.command_to_run_meta(cmd)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(status_code=409, detail=str(e))


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
