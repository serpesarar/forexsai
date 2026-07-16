"""ForexSAI Evrim Motoru — kendi kendini besleyen sistem çekirdeği.

Bu servis Evrim Paneli'nin (frontend /evolution) arka ucudur:

- **Registry**: Sistemdeki tüm motor/ajan/servislerin kataloğu
  (``data/evolution/system_registry.json``).
- **Analyses**: Tek tıkla çalıştırılabilir hata-analizi / performans / backtest
  scriptlerinin kataloğu (``data/evolution/analyses.json``) + subprocess
  çalıştırıcı ve çıktı yakalama.
- **Backlog**: Unutulan / bekleyen deneyler paneli (``backlog.json``).
- **Changelog**: git geçmişi + oturum notlarından türetilen canlı değişiklik
  akışı (1. Kural — her Claude Code oturumu buraya yazar).
- **Lessons**: Analiz çıktılarından damıtılan dersler (``lessons.json``).
  Tüketiciler (claude_decider, bias debate) ``get_active_lessons()`` ile okur —
  böylece "Çalıştır → Öğret" düğmesi gerçekten davranış değiştirir.

Tüm dosya işlemleri fail-open: dosya yoksa boş liste döner, panel çökmez.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shlex
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Yollar ──────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data" / "evolution"
RUNS_DIR = DATA_DIR / "runs"

REGISTRY_FILE = DATA_DIR / "system_registry.json"
ANALYSES_FILE = DATA_DIR / "analyses.json"
BACKLOG_FILE = DATA_DIR / "backlog.json"
LESSONS_FILE = DATA_DIR / "lessons.json"
SESSION_LOG_FILE = DATA_DIR / "session_log.json"

# Çalışan analiz süreçleri (in-memory; metadata ayrıca diske yazılır)
_ACTIVE_PROCS: Dict[str, asyncio.subprocess.Process] = {}

# Watcher task referansları — referanssız create_task GC ile kaybolabilir
# (CPython dokümante davranışı); kaybolursa run sonsuza dek 'running' kalır.
_BG_TASKS: set = set()


def _track_task(task: "asyncio.Task") -> None:
    _BG_TASKS.add(task)
    task.add_done_callback(_BG_TASKS.discard)

MAX_RUN_SECONDS = 1800  # tek analiz için üst sınır (30 dk)
OUTPUT_TAIL_CHARS = 12000
_SAFE_ARG_RE = re.compile(r"^[-A-Za-z0-9_=./:%,+@ ]*$")

# Lesson cache — tüketiciler (decider/bias) sık okur, disk IO'yu kısıtla
_LESSON_CACHE: Dict[str, Any] = {"ts": 0.0, "data": None}
_LESSON_CACHE_TTL = 60.0


# ── Dosya yardımcıları ───────────────────────────────────────────────────

def _ensure_dirs() -> None:
    """Veri dizinlerini oluştur (idempotent)."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any) -> Any:
    """JSON dosyası oku; yoksa veya bozuksa default dön (fail-open)."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"[evolution] {path.name} okunamadı: {e}")
    return default


def _write_json(path: Path, data: Any) -> None:
    """JSON dosyasına atomik yaz."""
    _ensure_dirs()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _one_line(text: Optional[str], limit: int = 240) -> str:
    """Metni tek satıra düzleştir + kırp.

    GÜVENLİK: ders başlığı/sembolü LESSONS.md ve debate CIO prompt'unda madde
    (`- ...`) olarak render ediliyor. Satır sonu içeren bir başlık kendi maddesinden
    kaçıp prompt'a sahte satır/talimat enjekte edebilir (stored prompt-injection).
    Enjeksiyonu KAYNAĞINDA etkisiz kıl: tüm boşluk dizilerini tek boşluğa indir.
    """
    if not text:
        return ""
    flat = " ".join(str(text).split())
    return flat[:limit]


# ── Registry & Analyses (katalog okuma) ─────────────────────────────────

def get_registry() -> List[dict]:
    """Sistem bileşen kataloğunu dön (motorlar, ajanlar, servisler)."""
    return _read_json(REGISTRY_FILE, [])


def get_analyses() -> List[dict]:
    """Çalıştırılabilir analiz kataloğunu dön."""
    return _read_json(ANALYSES_FILE, [])


def _find_analysis(analysis_id: str) -> Optional[dict]:
    for a in get_analyses():
        if a.get("id") == analysis_id:
            return a
    return None


# ── Backlog (bekleyen / unutulan işler) ──────────────────────────────────

def get_backlog(include_done: bool = True) -> List[dict]:
    """Backlog kayıtlarını dön (öncelik + tarih sıralı)."""
    items = _read_json(BACKLOG_FILE, [])
    if not include_done:
        items = [i for i in items if i.get("status") in ("pending", "in_progress")]
    prio_rank = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda i: (
        0 if i.get("status") in ("pending", "in_progress") else 1,
        prio_rank.get(i.get("priority", "medium"), 1),
        i.get("created_at", ""),
    ))
    return items


def add_backlog_item(
    title: str,
    detail: str = "",
    category: str = "idea",
    priority: str = "medium",
    source: str = "manual",
) -> dict:
    """Backlog'a yeni iş ekle. Aynı başlık aktif kayıtta varsa onu döner (dedup)."""
    items = _read_json(BACKLOG_FILE, [])
    norm = title.strip().lower()
    for i in items:
        if i.get("title", "").strip().lower() == norm and i.get("status") in ("pending", "in_progress"):
            return i
    item = {
        "id": _new_id("bl"),
        "title": title.strip(),
        "detail": detail.strip(),
        "category": category,
        "priority": priority,
        "status": "pending",
        "source": source,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    items.append(item)
    _write_json(BACKLOG_FILE, items)
    return item


def update_backlog_item(item_id: str, **fields: Any) -> Optional[dict]:
    """Backlog kaydını güncelle (status/priority/detail/title)."""
    allowed = {"status", "priority", "detail", "title", "category"}
    items = _read_json(BACKLOG_FILE, [])
    for i in items:
        if i.get("id") == item_id:
            for k, v in fields.items():
                if k in allowed and v is not None:
                    i[k] = v
            i["updated_at"] = _now_iso()
            _write_json(BACKLOG_FILE, items)
            return i
    return None


# ── Changelog (git + oturum notları) ─────────────────────────────────────

async def _run_git(*args: str) -> str:
    """Repo kökünde git komutu çalıştır, stdout dön (hata → boş string)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=str(REPO_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        return out.decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"[evolution] git {' '.join(args)} başarısız: {e}")
        return ""


async def get_changelog(limit: int = 60) -> List[dict]:
    """Git commit'leri + oturum notları + çalışma ağacı özetini birleştir.

    1. Kural'ın görünen yüzü: her oturumun bıraktığı iz burada akıştadır.
    """
    entries: List[dict] = []

    raw = await _run_git(
        "log", f"-n{limit}", "--date=iso-strict",
        "--pretty=format:%h%x1f%ad%x1f%an%x1f%s",
    )
    for line in raw.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 4:
            entries.append({
                "kind": "commit", "id": parts[0], "ts": parts[1],
                "author": parts[2], "summary": parts[3],
            })

    for note in _read_json(SESSION_LOG_FILE, []):
        entries.append({
            "kind": "session",
            "id": note.get("id", ""),
            "ts": note.get("ts", ""),
            "author": "claude-code",
            "summary": note.get("summary", ""),
            "files": note.get("files", []),
            "backlog_added": note.get("backlog_added", []),
        })

    status = await _run_git("status", "--porcelain")
    dirty = [line for line in status.splitlines() if line.strip()]
    if dirty:
        entries.append({
            "kind": "worktree",
            "id": "worktree",
            "ts": _now_iso(),
            "author": "local",
            "summary": f"{len(dirty)} dosyada commit'lenmemiş değişiklik var",
            "files": [d[3:].strip() for d in dirty[:40]],
        })

    def _ts_key(e: dict) -> float:
        """ISO ts → epoch. Git commit'leri yerel ofsetli (+03:00), oturum
        notları UTC gelir — ham string kıyası kronolojiyi bozar."""
        try:
            return datetime.fromisoformat(e.get("ts", "")).timestamp()
        except Exception:
            return 0.0

    entries.sort(key=_ts_key, reverse=True)
    return entries[:limit]


def add_session_note(
    summary: str,
    files: Optional[List[str]] = None,
    backlog_added: Optional[List[str]] = None,
) -> dict:
    """1. Kural girdisi: Claude Code oturumu değişiklik özetini kaydeder."""
    notes = _read_json(SESSION_LOG_FILE, [])
    note = {
        "id": _new_id("ses"),
        "ts": _now_iso(),
        "summary": summary.strip(),
        "files": files or [],
        "backlog_added": backlog_added or [],
    }
    notes.append(note)
    # Dosya sonsuz büyümesin — son 500 kayıt yeter
    _write_json(SESSION_LOG_FILE, notes[-500:])
    return note


# ── Analiz çalıştırıcı ───────────────────────────────────────────────────

def _run_meta_path(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}.json"


def _run_log_path(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}.log"


def _reconcile_run_meta(meta: dict) -> dict:
    """Backend restart'ında yarım kalan run'ları 'interrupted' işaretle.

    Run durumunu yalnız in-memory watcher finalize eder; süreç restart olursa
    diskte 'running' kalır, panel kartı kalıcı kilitlenir ve start_run 409 atar.
    Okuma anında mutabakat: 'running' görünüyor ama takip eden watcher yoksa
    gerçek durum 'interrupted'tir — diske de yaz ki bir daha bakmayalım.
    """
    if meta.get("status") == "running" and meta.get("run_id") not in _ACTIVE_PROCS:
        meta["status"] = "interrupted"
        meta["finished_at"] = meta.get("finished_at") or _now_iso()
        try:
            _write_json(_run_meta_path(meta["run_id"]), meta)
        except Exception:
            pass
    return meta


def list_runs(limit: int = 40) -> List[dict]:
    """Geçmiş analiz çalıştırmalarını (yeniden eskiye) listele."""
    _ensure_dirs()
    metas = []
    for p in RUNS_DIR.glob("run_*.json"):
        meta = _read_json(p, None)
        if meta:
            metas.append(_reconcile_run_meta(meta))
    metas.sort(key=lambda m: m.get("started_at", ""), reverse=True)
    return metas[:limit]


def get_run(run_id: str, tail_chars: int = OUTPUT_TAIL_CHARS) -> Optional[dict]:
    """Tek çalıştırmanın durumu + çıktı kuyruğu."""
    if not re.fullmatch(r"run_[a-f0-9]{10}", run_id):
        return None
    meta = _read_json(_run_meta_path(run_id), None)
    if meta is None:
        return None
    meta = _reconcile_run_meta(meta)
    log_path = _run_log_path(run_id)
    output = ""
    if log_path.exists():
        try:
            # Yalnız kuyruğu oku — uzun backtest logunda her poll'da tüm
            # dosyayı belleğe almak CPU/RAM israfı olur.
            size = log_path.stat().st_size
            max_bytes = tail_chars * 4  # UTF-8 en kötü durum payı
            with open(log_path, "rb") as fh:
                if size > max_bytes:
                    fh.seek(size - max_bytes)
                raw = fh.read().decode("utf-8", errors="replace")
            output = raw[-tail_chars:]
            meta["output_truncated"] = size > len(output.encode("utf-8"))
        except Exception:
            pass
    meta["output"] = output
    return meta


def _build_command(analysis: dict, extra_args: str) -> List[str]:
    """Katalogdaki komutu güvenli argüman listesine çevir.

    Sadece analyses.json'daki komutlar çalışır (paneli açan herkes rastgele
    komut çalıştıramasın); extra_args beyaz-liste regex'inden geçer.
    """
    if extra_args and not _SAFE_ARG_RE.fullmatch(extra_args):
        raise ValueError("extra_args geçersiz karakter içeriyor")
    cmd = shlex.split(analysis["command"])
    # 'python3' → backend'i çalıştıran yorumlayıcı (venv uyumu)
    if cmd and cmd[0] in ("python", "python3"):
        cmd[0] = sys.executable
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    return cmd


def _resolve_cwd(analysis: dict) -> Path:
    """Analizin çalışma dizinini repo köküne göre çöz (path-escape korumalı)."""
    rel = (analysis.get("cwd") or "").strip()
    cwd = (REPO_ROOT / rel).resolve() if rel else REPO_ROOT
    if not str(cwd).startswith(str(REPO_ROOT)):
        raise ValueError("cwd repo dışına çıkamaz")
    return cwd


async def _run_endpoint_analysis(run_id: str, analysis: dict) -> None:
    """Endpoint-tipi analiz: kendi backend'imize HTTP çağrısı, yanıt = çıktı."""
    import httpx

    port = os.getenv("PORT", "8000")
    method = (analysis.get("method") or "POST").upper()
    url = f"http://127.0.0.1:{port}{analysis['path']}"
    status, body = "done", ""
    try:
        async with httpx.AsyncClient(timeout=MAX_RUN_SECONDS) as client:
            resp = await client.request(method, url)
            body = resp.text[:200000]
            if resp.status_code >= 400:
                status = "failed"
        try:
            body = json.dumps(json.loads(body), ensure_ascii=False, indent=2)
        except Exception:
            pass
    except Exception as e:
        status, body = "failed", f"HTTP çağrısı başarısız: {e}"
    _run_log_path(run_id).write_text(f"{method} {url}\n\n{body}", encoding="utf-8")
    meta = _read_json(_run_meta_path(run_id), {})
    meta.update({"status": status, "finished_at": _now_iso()})
    _write_json(_run_meta_path(run_id), meta)
    _ACTIVE_PROCS.pop(run_id, None)
    logger.info(f"[evolution] endpoint run {run_id} bitti: {status}")


def _kill_run_process(proc: asyncio.subprocess.Process) -> None:
    """Süreci VE torunlarını öldür (start_new_session=True ile grup kurulur)."""
    import signal

    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except ProcessLookupError:
            pass


async def _watch_process(run_id: str, proc: asyncio.subprocess.Process, log_file: Path) -> None:
    """Süreç bitişini bekle, metadata'yı güncelle."""
    status, rc = "done", None
    try:
        rc = await asyncio.wait_for(proc.wait(), timeout=MAX_RUN_SECONDS)
        if rc != 0:
            status = "failed"
    except asyncio.TimeoutError:
        status = "timeout"
        _kill_run_process(proc)
        try:
            # Zombie bırakma — kill sonrası süreci topla (kısa sınırla)
            await asyncio.wait_for(proc.wait(), timeout=10)
        except asyncio.TimeoutError:
            pass
    except asyncio.CancelledError:
        # Backend kapanıyor: yarım işi 'done' diye kaydetme, süreci de öldür
        status = "interrupted"
        _kill_run_process(proc)
        raise
    finally:
        _ACTIVE_PROCS.pop(run_id, None)
        meta = _read_json(_run_meta_path(run_id), {})
        meta.update({
            "status": status,
            "return_code": rc,
            "finished_at": _now_iso(),
        })
        _write_json(_run_meta_path(run_id), meta)
        logger.info(f"[evolution] run {run_id} bitti: {status} (rc={rc})")


async def start_run(analysis_id: str, extra_args: str = "") -> dict:
    """Katalogdaki bir analizi arka planda başlat, run metadata'sını dön."""
    analysis = _find_analysis(analysis_id)
    if analysis is None:
        raise KeyError(f"analiz bulunamadı: {analysis_id}")
    if analysis.get("runnable_here") is False:
        raise RuntimeError(
            f"{analysis_id} bu makinede çalıştırılamaz: {analysis.get('run_note', 'MT5/Windows kutusu gerekli')}")

    # Aynı analiz zaten koşuyorsa ikinci kez başlatma
    for rid, p in list(_ACTIVE_PROCS.items()):
        meta = _read_json(_run_meta_path(rid), {})
        if meta.get("analysis_id") == analysis_id and meta.get("status") == "running":
            raise RuntimeError(f"{analysis_id} zaten çalışıyor (run: {rid})")

    _ensure_dirs()
    run_id = _new_id("run")

    # Endpoint-tipi analiz: subprocess yerine kendi API'mize çağrı
    if analysis.get("kind") == "endpoint":
        meta = {
            "run_id": run_id,
            "analysis_id": analysis_id,
            "analysis_name": analysis.get("name", analysis_id),
            "command": f"{analysis.get('method', 'POST')} {analysis['path']}",
            "status": "running",
            "started_at": _now_iso(),
            "finished_at": None,
            "return_code": None,
        }
        _write_json(_run_meta_path(run_id), meta)
        _ACTIVE_PROCS[run_id] = None  # slot işgali (dedup için)
        _track_task(asyncio.create_task(_run_endpoint_analysis(run_id, analysis)))
        return meta

    cmd = _build_command(analysis, extra_args)
    log_file = _run_log_path(run_id)
    fh = open(log_file, "wb")
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(_resolve_cwd(analysis)),
            stdout=fh,
            stderr=asyncio.subprocess.STDOUT,
            # Kendi süreç grubu: timeout'ta torunlarıyla birlikte öldürülebilsin
            start_new_session=True,
        )
    except Exception:
        fh.close()
        raise
    _ACTIVE_PROCS[run_id] = proc

    meta = {
        "run_id": run_id,
        "analysis_id": analysis_id,
        "analysis_name": analysis.get("name", analysis_id),
        "command": " ".join(cmd),
        "status": "running",
        "started_at": _now_iso(),
        "finished_at": None,
        "return_code": None,
        "pid": proc.pid,
    }
    _write_json(_run_meta_path(run_id), meta)

    async def _close_when_done():
        try:
            await _watch_process(run_id, proc, log_file)
        finally:
            try:
                fh.close()
            except Exception:
                pass

    _track_task(asyncio.create_task(_close_when_done()))
    logger.info(f"[evolution] run {run_id} başladı: {' '.join(cmd)}")
    return meta


# ── Dersler (öğrenme köprüsü) ────────────────────────────────────────────

def get_lessons(include_archived: bool = False) -> List[dict]:
    """Tüm dersleri dön (yeniden eskiye)."""
    lessons = _read_json(LESSONS_FILE, [])
    if not include_archived:
        lessons = [l for l in lessons if l.get("status", "active") == "active"]
    lessons.sort(key=lambda l: l.get("created_at", ""), reverse=True)
    return lessons


def get_active_lessons(target: str, symbol: Optional[str] = None, limit: int = 8) -> List[dict]:
    """Tüketici API'si: bir hedef (claude_decider / bias_debate) için aktif dersler.

    claude_decider ve bias_debate_engine prompt kurarken bunu çağırır —
    paneldeki "Öğret" düğmesinin davranışa dönüştüğü yer burası.
    Sembol verilirse: o sembole özel + genel (symbol=null) dersler döner.
    60s cache'li (disk IO sıcak yolda tekrarlanmasın).
    """
    now = time.time()
    if _LESSON_CACHE["data"] is None or now - _LESSON_CACHE["ts"] > _LESSON_CACHE_TTL:
        _LESSON_CACHE["data"] = _read_json(LESSONS_FILE, [])
        _LESSON_CACHE["ts"] = now
    out = []
    for l in _LESSON_CACHE["data"]:
        if l.get("status", "active") != "active":
            continue
        if target not in (l.get("targets") or []):
            continue
        lsym = l.get("symbol")
        if symbol and lsym and lsym != symbol:
            continue
        out.append(l)
    out.sort(key=lambda l: l.get("created_at", ""), reverse=True)
    return out[:limit]


def _invalidate_lesson_cache() -> None:
    _LESSON_CACHE["data"] = None
    _LESSON_CACHE["ts"] = 0.0


# claude_decider/memory/LESSONS.md içindeki panel bloğu işaretleri.
# distill_journal.py'nin AUTO bloğuna DOKUNMAYIZ — kendi bloğumuzu yönetiriz.
DECIDER_LESSONS_FILE = REPO_ROOT / "claude_decider" / "memory" / "LESSONS.md"
_PANEL_START = "<!-- PANEL-LESSONS START -->"
_PANEL_END = "<!-- PANEL-LESSONS END -->"


def build_decider_lessons_block() -> str:
    """Aktif 'claude_decider' derslerinin panel bloğu — İÇERİK (marker'sız).

    İki tüketici: (1) _sync_decider_lessons bu makinedeki LESSONS.md'ye yazar,
    (2) evolution_remote sync_lessons komutuyla MT5 kutusundaki ajana yollar —
    iki makinede birebir aynı blok oluşur.
    """
    lessons = [
        l for l in _read_json(LESSONS_FILE, [])
        if l.get("status", "active") == "active"
        and "claude_decider" in (l.get("targets") or [])
    ]
    lessons.sort(key=lambda l: l.get("created_at", ""), reverse=True)
    lines = ["## 📟 Panel dersleri (Evrim Paneli'nden — analiz çıktısı, İHTİYATLA uygula)"]
    for l in lessons[:12]:
        # Tümü tek-satıra düzleştirilir: satır sonu içeren başlık/sembol
        # kendi maddesinden kaçıp prompt'a sahte satır enjekte edemesin.
        sym = f" [{_one_line(l['symbol'], 24)}]" if l.get("symbol") else ""
        title = _one_line(l.get("title"), 160) or "Ders"
        summary = _one_line(l.get("summary"), 400)
        lines.append(f"- **{title}**{sym} ({l.get('created_at', '')[:10]}): {summary}")
    if not lessons:
        lines.append("*(aktif panel dersi yok)*")
    return "\n".join(lines)


def _sync_decider_lessons() -> None:
    """Aktif 'claude_decider' hedefli dersleri LESSONS.md panel bloğuna yaz.

    Blok idempotent olarak yeniden üretilir (append-çöplüğü olmaz). Dersler
    Evrim Paneli'nden geldiği için 'ihtiyatla uygula' çerçevesiyle sunulur —
    kanıt-kapısını geçmiş ✅ derslerle karışmaz.
    """
    try:
        block = f"{_PANEL_START}\n{build_decider_lessons_block()}\n{_PANEL_END}"

        if DECIDER_LESSONS_FILE.exists():
            text = DECIDER_LESSONS_FILE.read_text(encoding="utf-8")
            if _PANEL_START in text and _PANEL_END in text:
                pre = text.split(_PANEL_START)[0]
                post = text.split(_PANEL_END, 1)[1]
                new_text = pre + block + post
            else:
                new_text = text.rstrip() + "\n\n" + block + "\n"
            DECIDER_LESSONS_FILE.write_text(new_text, encoding="utf-8")
            logger.info("[evolution] decider LESSONS.md panel bloğu güncellendi")
    except Exception as e:
        logger.error(f"[evolution] decider lesson senkronu başarısız: {e}")


def add_lesson(
    title: str,
    summary: str,
    targets: List[str],
    symbol: Optional[str] = None,
    source: Optional[dict] = None,
) -> dict:
    """Yeni ders kaydet (Öğret düğmesi / distilasyon çıktısı).

    title/symbol tek-satıra düzleştirilir (LESSONS.md + CIO prompt madde-bloğu
    enjeksiyonuna karşı kaynak-temizliği). summary korunur — panelde React ile
    güvenle escape edilir, prompt render'larında ayrıca düzleştirilir.
    """
    lessons = _read_json(LESSONS_FILE, [])
    lesson = {
        "id": _new_id("les"),
        "created_at": _now_iso(),
        "title": _one_line(title, 200),
        "summary": summary.strip(),
        "symbol": _one_line(symbol, 24) or None,
        "targets": targets or ["panel"],
        "source": source or {"manual": True},
        "status": "active",
    }
    lessons.append(lesson)
    _write_json(LESSONS_FILE, lessons)
    _invalidate_lesson_cache()
    if "claude_decider" in (targets or []):
        _sync_decider_lessons()
    return lesson


def update_lesson_status(lesson_id: str, status: str) -> Optional[dict]:
    """Dersi arşivle / yeniden etkinleştir."""
    lessons = _read_json(LESSONS_FILE, [])
    for l in lessons:
        if l.get("id") == lesson_id:
            l["status"] = status
            _write_json(LESSONS_FILE, lessons)
            _invalidate_lesson_cache()
            if "claude_decider" in (l.get("targets") or []):
                _sync_decider_lessons()
            return l
    return None


async def distill_run_to_lesson(
    run_id: str,
    targets: List[str],
    symbol: Optional[str] = None,
    instruction: str = "",
) -> dict:
    """Analiz çıktısını LLM ile derse damıt (Çalıştır → Öğret akışı).

    llm_router üzerinden DeepSeek/Kimi kullanır; anahtar yoksa çıktının ham
    kuyruğunu ders olarak kaydeder (fail-open — düğme asla ölü kalmaz).
    """
    if run_id.startswith("cmd_"):
        # Uzak (MT5 kutusu) çalıştırma — Supabase'ten oku; Öğret akışı aynı.
        from services import evolution_remote as _remote
        cmd_id = _remote.parse_cmd_run_id(run_id)
        cmd = await asyncio.to_thread(_remote.get_command, cmd_id) if cmd_id else None
        run = _remote.command_to_run_meta(cmd) if cmd else None
    else:
        run = get_run(run_id)
    if run is None:
        raise KeyError(f"run bulunamadı: {run_id}")
    output = (run.get("output") or "").strip()
    if not output:
        raise ValueError("çalıştırma çıktısı boş — damıtılacak bir şey yok")

    name = run.get("analysis_name", run.get("analysis_id", ""))
    title = f"{name} bulgusu"
    summary = output[-3000:]

    try:
        from services.llm_router import chat  # type: ignore
        system = (
            "Trading sistemi analiz çıktısını, sinyal karar motorlarının "
            "prompt'una enjekte edilecek KISA ve EYLEME DÖNÜK bir derse çevir "
            "(Türkçe, en fazla 5 cümle; sayısal kanıtları koru; 'şu koşulda "
            "şunu yapma / şuna ağırlık ver' netliğinde yaz)."
        )
        user = (
            f"{('Ek yönerge: ' + instruction) if instruction else ''}\n\n"
            f"--- ANALİZ: {name} ---\n{output[-8000:]}"
        )
        text, _provider = await chat(system=system, user=user, importance="important")
        if text and text.strip():
            summary = text.strip()
            title = f"{name} dersi"
    except Exception as e:
        logger.warning(f"[evolution] LLM damıtma başarısız, ham çıktı kaydedildi: {e}")

    return add_lesson(
        title=title,
        summary=summary,
        targets=targets,
        symbol=symbol,
        source={"run_id": run_id, "analysis_id": run.get("analysis_id")},
    )


# ── Genel bakış (panelin tek fetch'i) ────────────────────────────────────

# Soğuk başlangıçta prediction_logs sorgusu ~100s sürebilir; panel BEKLEMEZ.
# Zaman aşımında kaynak arka planda çalışmaya devam eder (shield) — kendi
# cache'ini ısıtır, panelin 60s'lik otomatik yenilemesi sıcak veriyi alır.
# 20→8: iki kaynak artık paralel beklendiği için endpoint tavanı ~8s.
OVERVIEW_SOURCE_TIMEOUT = 8


async def _bounded(task: "asyncio.Task", timeout: float) -> Any:
    """Task'i süre sınırıyla bekle; aşarsa İPTAL ETME (cache ısınsın), None dön."""
    try:
        return await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
    except asyncio.TimeoutError:
        return None


# Soğuk kaynak başına TEK uçuşta ısınma görevi — her overview isteği yeni bir
# 75k-satırlık Supabase taraması başlatmasın (panel 60s'de bir yeniliyor).
_WARM_TASKS: Dict[str, "asyncio.Task"] = {}


def _shared_task(key: str, factory) -> "asyncio.Task":
    """Aynı key için çalışan task varsa onu döndür; yoksa factory ile başlat."""
    task = _WARM_TASKS.get(key)
    if task is not None and not task.done():
        return task
    task = asyncio.create_task(factory())
    _track_task(task)
    _WARM_TASKS[key] = task
    task.add_done_callback(lambda t, k=key: _WARM_TASKS.pop(k, None) if _WARM_TASKS.get(k) is t else None)
    return task


async def get_overview(days: int = 30) -> dict:
    """Panelin üst kartları: model başarıları + bias + sistem sayaçları.

    Her alt kaynak fail-open + süre sınırlı — biri yavaşsa/çökerse panel
    beklemez, diğer veriler gelmeye devam eder.
    """
    overview: Dict[str, Any] = {
        "generated_at": _now_iso(),
        "days": days,
        "models": None,
        "bias": None,
        "counts": {},
        "active_runs": [],
    }

    # İki yavaş kaynak PARALEL beklenir — endpoint tavanı tek timeout olur
    # (eskiden sıralıydı: 20s models + 20s bias = 40s'ye kadar sürüyordu).
    task = None
    btask = None
    try:
        from routers.learning import get_accuracy_by_model
        task = _shared_task(
            f"models:{days}",
            lambda: get_accuracy_by_model(symbol=None, days=days, check_interval="24h"))
    except Exception as e:
        logger.warning(f"[evolution] model accuracy task kurulamadı: {e}")
    try:
        from services.bias_test_service import accuracy_report  # type: ignore
        btask = _shared_task("bias", lambda: asyncio.to_thread(accuracy_report))
    except Exception as e:
        logger.warning(f"[evolution] bias task kurulamadı: {e}")

    acc, bias = await asyncio.gather(
        _bounded(task, OVERVIEW_SOURCE_TIMEOUT) if task else asyncio.sleep(0, result=None),
        _bounded(btask, OVERVIEW_SOURCE_TIMEOUT) if btask else asyncio.sleep(0, result=None),
    )

    if isinstance(acc, dict) and "models" in acc:
        overview["models"] = acc
    elif task is not None and acc is None and not task.done():
        overview["models_warming"] = True
        logger.info("[evolution] model accuracy yavaş — arka planda ısınıyor")

    if bias is not None:
        overview["bias"] = bias
    elif btask is not None and not btask.done():
        overview["bias_warming"] = True

    backlog = get_backlog()
    overview["counts"] = {
        "registry": len(get_registry()),
        "analyses": len(get_analyses()),
        "backlog_pending": sum(1 for b in backlog if b.get("status") == "pending"),
        "backlog_total": len(backlog),
        "lessons_active": len(get_lessons()),
    }
    overview["active_runs"] = [
        m for m in list_runs(10) if m.get("status") == "running"
    ]
    return overview
