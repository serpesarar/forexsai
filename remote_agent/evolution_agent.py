"""
evolution_agent.py — Evrim Ajanı (MT5 kutusunda çalışır, tek süreç)
====================================================================
Panel ile MT5 kutusu arasındaki çift yönlü köprü. Kurulduktan sonra
kutuya bir daha dokunmak gerekmez — her şey panelden yönetilir.

YUKARI AKIŞ (kutu → Supabase, 5 dk'da bir):
  • bot_trades        MT5 kapanan deal'ler (gerçek performansın tek kaynağı)
  • decider_journal   claude_decider/memory/journal.jsonl yeni satırları
  • agent_heartbeat   kalp atışı + açık pozisyon sayısı (panelde 🟢/🔴)

AŞAĞI AKIŞ (Supabase → kutu, 30 sn'de bir komut kuyruğu):
  • run_analysis      paneldeki 'MT5 kutusu' etiketli analizleri koşturur,
                      çıktıyı canlı olarak geri yazar (panel çekmecesi izler)
  • sync_lessons      panel derslerini claude_decider/memory/LESSONS.md
                      panel bloğuna yazar (git gerekmez)
  • git_pull          repoyu günceller (yeni kural/kod, commit'li olanlar)
  • restart_bot       botu GÜVENLİ pencerede yeniden başlatır
                      (açık pozisyon varsa bekler; payload {"force": true} beklemez)
  • restart_process   payload {"target": "decider|bot|backend|agent"} — ilgili
                      süreci öldürüp .bat'ıyla yeniden açar (bot güvenli-bekler)
  • claude_task       payload {"prompt", model?, cwd?, timeout?} — kutuda
                      Claude Code'u headless koşturur, çıktı canlı geri akar.
                      Panelden: `python3 scripts/remote.py ask "<görev>"`.
                      Kutu Claude'u sonunda === SONUÇ === bloğu yazar; panel
                      onu ayrıştırıp iki taraf arasında iş devri kurar.
                      agent_config.CLAUDE_TASK_ENABLED=False ile kapatılır.

OTO-GÜNCELLEME (AUTO_UPDATE_ENABLED=True default): 10 dk'da bir git fetch;
origin gerideyse pull + değişen klasöre göre İLGİLİ süreci kendiliğinden
yeniden başlatır (claude_decider/ → decider, yeni deneme/ → bot [pozisyonsuz
anda], backend/ → panel backend, remote_agent/ → ajan kendini yeniler —
start_agent.bat döngüsü yeni kodla kaldırır). Ana bilgisayardan push etmek
YETERLİ; kutuya dokunmak gerekmez.

HAFTALIK İŞLER: agent_config.WEEKLY_JOBS — her hafta belirlenen gün/saatte
kendi kendine koşar, sonuçlar komut kaydı olarak panele düşer.

GÜVENLİK İLKESİ: Ajan yalnız TANIMLI komut türlerini işler. Komutlar sadece
projenin kendi Supabase'inden (service-role) gelir. run_analysis paneldeki
imzalı katalogdan; claude_task repo kökü altına kilitli, prompt/timeout
tavanlı ve tek bayrakla kapatılabilir. Görev protokolü kutudaki Claude'a
"canlı trade süreçlerine izinsiz dokunma, MT5'te elle emir açma" der.

Kurulum (Windows):  README.md'ye bak.  Çalıştırma:  python evolution_agent.py
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import agent_config as cfg

try:
    from supabase import create_client
except ImportError:
    print("HATA: pip install supabase")
    sys.exit(1)

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    HAS_MT5 = False  # Mac/test kutusunda trade push atlanır, komut döngüsü çalışır

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler("evolution_agent.log", encoding="utf-8")],
)
log = logging.getLogger("evo-agent")

HOST = getattr(cfg, "AGENT_HOST", "mt5_box")
STATE_FILE = Path(__file__).parent / "agent_state.json"
POLL_SECONDS = 30          # komut kuyruğu
PUSH_SECONDS = 300         # trade/journal/heartbeat
CMD_TIMEOUT_DEFAULT = 1800  # run_analysis varsayılan zaman aşımı (sn)
OUTPUT_LIMIT = 60_000      # komut çıktısının Supabase'e yazılan kuyruğu

# backend/services/evolution_service.py::_PANEL_START/_PANEL_END ile birebir aynı
LESSONS_BEGIN = "<!-- PANEL-LESSONS START -->"
LESSONS_END = "<!-- PANEL-LESSONS END -->"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def supa():
    return create_client(cfg.SUPABASE_URL, cfg.SUPABASE_SERVICE_KEY)


# ── MT5 yardımcıları ──────────────────────────────────────────────────────

def mt5_connect() -> bool:
    if not HAS_MT5:
        return False
    kw = {}
    if getattr(cfg, "MT5_ACCOUNT", None):
        kw = dict(login=cfg.MT5_ACCOUNT, password=cfg.MT5_PASSWORD, server=cfg.MT5_SERVER)
    path = getattr(cfg, "MT5_TERMINAL_PATH", None)
    ok = mt5.initialize(path, **kw) if path else mt5.initialize(**kw)
    if not ok:
        log.warning("mt5.initialize başarısız: %s", mt5.last_error())
    return bool(ok)


def open_position_count() -> int:
    if not HAS_MT5:
        return 0
    try:
        positions = mt5.positions_get()
        return len(positions) if positions else 0
    except Exception:
        return -1  # bilinmiyor


def push_trades(client, state: dict) -> int:
    """MT5 kapanan deal'leri watermark'tan itibaren bot_trades'e yaz."""
    if not HAS_MT5:
        return 0
    last_ts = state.get("last_deal_ts", time.time() - 30 * 86400)
    deals = mt5.history_deals_get(datetime.fromtimestamp(last_ts - 3600, tz=timezone.utc),
                                  datetime.now(timezone.utc))
    if not deals:
        return 0
    # Sadece pozisyon KAPATAN deal'ler (entry=1 → DEAL_ENTRY_OUT) gerçek sonuçtur
    rows = []
    max_ts = last_ts
    for d in deals:
        if getattr(d, "entry", None) != 1:
            continue
        max_ts = max(max_ts, d.time)
        rows.append({
            "ticket": d.ticket,
            "host": HOST,
            "symbol": d.symbol,
            "direction": "SELL" if d.type == 0 else "BUY",  # kapatan deal ters yönlüdür
            "volume": d.volume,
            "close_time": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
            "close_price": d.price,
            "profit": d.profit,
            "commission": d.commission,
            "swap": d.swap,
            "comment": d.comment,
            "magic": d.magic,
            "raw": {"position_id": d.position_id, "order": d.order, "reason": d.reason},
        })
    if rows:
        for i in range(0, len(rows), 200):
            client.table("bot_trades").upsert(rows[i:i + 200]).execute()
        state["last_deal_ts"] = max_ts
        log.info("bot_trades += %d", len(rows))
    return len(rows)


def push_journal(client, state: dict) -> int:
    """journal.jsonl'in yeni satırlarını decider_journal'a yaz (byte offset takibi)."""
    path = Path(getattr(cfg, "DECIDER_JOURNAL", ""))
    if not path.exists():
        return 0
    offset = state.get("journal_offset", 0)
    size = path.stat().st_size
    if size < offset:      # dosya döndürülmüş/sıfırlanmış
        offset = 0
    if size == offset:
        return 0
    with open(path, "rb") as fh:
        fh.seek(offset)
        chunk = fh.read()
    rows = []
    for line in chunk.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        rid = hashlib.sha1(line.encode()).hexdigest()[:16]
        rows.append({
            "id": rid,
            "host": HOST,
            "ts": rec.get("ts") or rec.get("timestamp"),
            "symbol": rec.get("symbol"),
            "decision": rec.get("decision") or rec.get("action"),
            "confidence": rec.get("confidence"),
            "outcome": rec.get("outcome"),
            "raw": rec,
        })
    if rows:
        for i in range(0, len(rows), 200):
            client.table("decider_journal").upsert(rows[i:i + 200]).execute()
        log.info("decider_journal += %d", len(rows))
    state["journal_offset"] = size
    return len(rows)


def push_heartbeat(client, extra: dict | None = None) -> None:
    meta = {
        "mt5": HAS_MT5,
        "open_positions": open_position_count(),
        "agent_version": "1.0",
        **(extra or {}),
    }
    client.table("agent_heartbeat").upsert(
        {"host": HOST, "last_seen": now_iso(), "meta": meta}
    ).execute()


# ── Komut işleyiciler ─────────────────────────────────────────────────────

def _update_cmd(client, cmd_id: str, **fields) -> None:
    client.table("evolution_commands").update(fields).eq("id", cmd_id).execute()


def _stream_process(client, cmd_id: str, proc: subprocess.Popen, timeout: int) -> tuple[str, int]:
    """Süreç çıktısını topla; her ~5 sn'de kuyruğu Supabase'e yaz (panel canlı izler)."""
    buf: list[str] = []
    lock = threading.Lock()

    def reader():
        for line in proc.stdout:  # type: ignore[union-attr]
            with lock:
                buf.append(line)

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    start = time.time()
    last_flush = 0.0
    while proc.poll() is None:
        if time.time() - start > timeout:
            proc.kill()
            with lock:
                buf.append(f"\n[ajan] zaman aşımı ({timeout}s) — süreç öldürüldü\n")
            break
        if time.time() - last_flush > 5:
            with lock:
                tail = "".join(buf)[-OUTPUT_LIMIT:]
            _update_cmd(client, cmd_id, output=tail)
            last_flush = time.time()
        time.sleep(1)
    t.join(timeout=10)
    with lock:
        out = "".join(buf)[-OUTPUT_LIMIT:]
    rc = proc.returncode if proc.returncode is not None else -9
    # Windows 0xFFFFFFFF gibi işaretsiz kodlar Postgres integer'a sığmaz —
    # işaretli 32-bit'e indir (4294967295 → -1). 2026-07-21 canlı hatası.
    if rc > 2**31 - 1 or rc < -(2**31):
        rc = rc - 2**32 if rc > 0 else -1
    return out, rc


def handle_run_analysis(client, cmd: dict) -> tuple[str, int]:
    p = cmd.get("payload") or {}
    command = p.get("command", "")
    cwd = Path(cfg.REPO_ROOT) / p.get("cwd", "") if p.get("cwd") else Path(cfg.REPO_ROOT)
    timeout = int(p.get("timeout", CMD_TIMEOUT_DEFAULT))
    if not command:
        return "[ajan] payload.command boş", 2
    log.info("run_analysis: %s (cwd=%s)", command, cwd)
    proc = subprocess.Popen(
        command, shell=True, cwd=str(cwd),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1,
    )
    return _stream_process(client, cmd["id"], proc, timeout)


CLAUDE_TASK_MAX_PROMPT = 100_000
CLAUDE_TASK_MAX_TIMEOUT = 3600
CLAUDE_TASK_DEFAULT_TIMEOUT = 900

CLAUDE_TASK_PROTOCOL = """
────────────────────────────────────────────────────────────
Bu görevi ForexSAI MT5 kutusunda çalışan Claude Code olarak yapıyorsun.
Görevi veren: panel tarafındaki (Mac) Claude — sonucu O okuyacak.

KURALLAR
1. Yalnız bu görevin kapsamındaki işi yap; kapsam dışı değişiklik yapma.
2. Canlı trade süreçlerini (bot / decider / ajan) İZİNSİZ durdurma-yeniden
   başlatma; gerekiyorsa SONUÇ'ta öner, kararı panel versin.
3. MT5'te elle emir açma/kapatma YOK. Emir gönderen kod yazma.
4. Gözlem ve teşhis önce gelir: log/dosya/süreç durumuna bak, sonra yorumla.
5. Bulguyu olduğu gibi yaz — sayılar uydurma, göremediğine "göremedim" de.

Bitirince ÇIKTININ SONUNA tam olarak şu bloğu ekle (panel bunu ayrıştırır):

=== SONUÇ ===
durum: ok | kismi | hata
ozet: <en fazla 3 cümle>
bulgular:
- <madde>
- <madde>
onerilen_adim: <panelin yapması gereken tek şey; yoksa "yok">
=== BITTI ===
────────────────────────────────────────────────────────────
""".strip()


def handle_claude_task(client, cmd: dict) -> tuple[str, int]:
    """Kutuda Claude Code'u headless çalıştır (panel→kutu ajan orkestrasyonu).

    payload: {prompt (zorunlu), model?, cwd?, timeout?, raw?}
      raw=True → protokol başlığı eklenmez (ham prompt).
    Güvenlik: agent_config.CLAUDE_TASK_ENABLED ile kapatılabilir; cwd repo
    kökünün ALTINDA olmalı; prompt ve timeout tavanlı.
    """
    if not getattr(cfg, "CLAUDE_TASK_ENABLED", True):
        return "[ajan] claude_task devre dışı (agent_config.CLAUDE_TASK_ENABLED=False)", 2
    p = cmd.get("payload") or {}
    prompt = (p.get("prompt") or "").strip()
    if not prompt:
        return "[ajan] payload.prompt boş", 2
    if len(prompt) > CLAUDE_TASK_MAX_PROMPT:
        return f"[ajan] prompt çok uzun ({len(prompt)} > {CLAUDE_TASK_MAX_PROMPT})", 2

    repo = Path(cfg.REPO_ROOT).resolve()
    cwd = (repo / p["cwd"]).resolve() if p.get("cwd") else repo
    if repo not in cwd.parents and cwd != repo:
        return f"[ajan] cwd repo dışında reddedildi: {cwd}", 2
    if not cwd.is_dir():
        return f"[ajan] cwd yok: {cwd}", 2

    timeout = min(int(p.get("timeout", CLAUDE_TASK_DEFAULT_TIMEOUT)), CLAUDE_TASK_MAX_TIMEOUT)
    model = p.get("model") or getattr(cfg, "CLAUDE_TASK_MODEL", "sonnet")
    full_prompt = prompt if p.get("raw") else f"{CLAUDE_TASK_PROTOCOL}\n\nGÖREV:\n{prompt}"

    claude_bin = _resolve_claude_bin()
    argv = [claude_bin, "-p", "--dangerously-skip-permissions", "--model", model]
    log.info("claude_task: model=%s cwd=%s timeout=%ss prompt=%d karakter",
             model, cwd, timeout, len(full_prompt))
    try:
        proc = subprocess.Popen(
            argv, cwd=str(cwd), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
    except FileNotFoundError:
        return (f"[ajan] Claude CLI bulunamadı ({claude_bin}). CLAUDE_BIN env'i "
                f"veya agent_config.CLAUDE_BIN ayarla.", 2)
    try:
        proc.stdin.write(full_prompt)
        proc.stdin.close()
    except Exception as exc:
        proc.kill()
        return f"[ajan] prompt yazılamadı: {exc}", 1
    return _stream_process(client, cmd["id"], proc, timeout)


def _resolve_claude_bin() -> str:
    """CLAUDE_BIN (config/env) → PATH → bilinen kurulum yolları.

    claude_decider/decide.py._claude_bin ile aynı mantık; ajan o modülü
    import etmesin diye burada bağımsız duruyor (kutu kurulumu tek dosya).
    """
    import shutil
    cand_env = getattr(cfg, "CLAUDE_BIN", None) or os.getenv("CLAUDE_BIN")
    if cand_env and Path(cand_env).exists():
        return cand_env
    found = shutil.which("claude")
    if found:
        return found
    home = Path.home()
    for c in (home / "node_modules/.bin/claude.cmd",
              home / "node_modules/.bin/claude",
              home / "AppData/Roaming/npm/claude.cmd",
              home / ".local/bin/claude",
              Path("/usr/local/bin/claude"),
              Path("/opt/homebrew/bin/claude")):
        if c.exists():
            return str(c)
    for root in (home / "node_modules/@anthropic-ai",
                 home / "AppData/Roaming/npm/node_modules/@anthropic-ai"):
        if root.is_dir():
            for pkg in sorted(root.glob("claude-code-*")):
                for exe in ("claude.exe", "claude"):
                    if (pkg / exe).exists():
                        return str(pkg / exe)
    return "claude"


def handle_sync_lessons(client, cmd: dict) -> tuple[str, int]:
    """Panel derslerini LESSONS.md panel bloğuna yaz (git'e gerek yok)."""
    p = cmd.get("payload") or {}
    block = p.get("content", "")
    path = Path(cfg.REPO_ROOT) / "claude_decider" / "memory" / "LESSONS.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else "# LESSONS\n"
    new_block = f"{LESSONS_BEGIN}\n{block}\n{LESSONS_END}"
    if LESSONS_BEGIN in text and LESSONS_END in text:
        pre = text.split(LESSONS_BEGIN)[0]
        post = text.split(LESSONS_END, 1)[1]
        text = pre + new_block + post
    else:
        text = text.rstrip() + "\n\n" + new_block + "\n"
    path.write_text(text, encoding="utf-8")
    n = len([l for l in block.splitlines() if l.strip().startswith("-")])
    return f"[ajan] LESSONS.md panel bloğu güncellendi ({n} ders) → {path}", 0


def handle_git_pull(client, cmd: dict) -> tuple[str, int]:
    proc = subprocess.Popen(
        "git pull --ff-only", shell=True, cwd=str(cfg.REPO_ROOT),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    return _stream_process(client, cmd["id"], proc, 300)


def handle_restart_bot(client, cmd: dict) -> tuple[str, int]:
    """Botu güvenli pencerede yeniden başlat: açık pozisyon varsa bekle."""
    p = cmd.get("payload") or {}
    force = bool(p.get("force"))
    wait_max = int(p.get("wait_max_minutes", 120))
    lines = []
    if not force:
        deadline = time.time() + wait_max * 60
        while open_position_count() > 0:
            if time.time() > deadline:
                return "\n".join(lines) + f"\n[ajan] {wait_max} dk doldu, hâlâ açık pozisyon var — İPTAL (force ile zorlanabilir)", 3
            lines.append(f"[ajan] açık pozisyon var, bekleniyor… ({now_iso()})")
            _update_cmd(client, cmd["id"], output="\n".join(lines)[-OUTPUT_LIMIT:])
            time.sleep(60)
    script = getattr(cfg, "BOT_RESTART_SCRIPT", None)
    if not script:
        return "[ajan] BOT_RESTART_SCRIPT tanımlı değil (agent_config.py)", 2
    lines.append(f"[ajan] yeniden başlatma scripti çalışıyor: {script}")
    proc = subprocess.Popen(
        script, shell=True, cwd=str(cfg.REPO_ROOT),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    out, rc = _stream_process(client, cmd["id"], proc, 600)
    return "\n".join(lines) + "\n" + out, rc


# ── Süreç yönetimi: öldür + .bat ile yeniden aç ───────────────────────────
# Hedef süreçler komut satırı imzasıyla bulunur (pencere başlığına güvenmez);
# .bat yolları repo köküne göre. agent_config.PROCESS_TARGETS ile ezilebilir.

DEFAULT_PROCESS_TARGETS = {
    "decider": {"match": "run_decider.py", "bat": r"calistir\3_claude_decider.bat"},
    "bot":     {"match": "forexsai_demo_bot.py", "bat": r"calistir\2_oto_trade_bot.bat",
                "safe_wait": True},
    "backend": {"match": "uvicorn", "bat": r"calistir\18_panel_backend.bat"},
    "agent":   {"self": True},
}


def _process_targets() -> dict:
    targets = dict(DEFAULT_PROCESS_TARGETS)
    targets.update(getattr(cfg, "PROCESS_TARGETS", {}) or {})
    return targets


def _kill_by_cmdline(match: str) -> str:
    """Komut satırında `match` geçen python süreçlerini öldür (Windows/Mac)."""
    if sys.platform == "win32":
        ps = ("Get-CimInstance Win32_Process | "
              f"Where-Object {{ $_.CommandLine -like '*{match}*' -and $_.CommandLine -notlike '*Win32_Process*' }} | "
              "ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $_.ProcessId }")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=60)
        return (r.stdout or r.stderr or "").strip()
    r = subprocess.run(["pkill", "-f", match], capture_output=True, text=True)
    return f"pkill rc={r.returncode}"


def _start_bat(rel_bat: str) -> str:
    path = Path(cfg.REPO_ROOT) / rel_bat
    if not path.exists():
        return f"HATA: {path} yok"
    if sys.platform == "win32":
        subprocess.Popen(["cmd", "/c", "start", "", str(path)], cwd=str(cfg.REPO_ROOT))
        return f"başlatıldı: {rel_bat}"
    return f"(windows-dışı: {rel_bat} elle başlatılmalı)"


def restart_target(name: str, force: bool = False) -> tuple[str, int]:
    """Bir süreci yeniden başlat. 'agent' → kendini kapatır (start_agent.bat
    döngüsü yeni kodla kaldırır). Bot güvenli-bekler (pozisyon açıkken ertelenir)."""
    t = _process_targets().get(name)
    if not t:
        return f"[ajan] bilinmeyen hedef: {name}", 2
    if t.get("self"):
        log.info("ajan kendini yeniliyor (start_agent.bat yeniden kaldıracak)")
        threading.Timer(2.0, lambda: os._exit(0)).start()
        return "[ajan] kendini kapatıyor — 30 sn içinde yeni kodla geri gelir", 0
    if t.get("safe_wait") and not force and open_position_count() > 0:
        return f"[ajan] {name}: açık pozisyon var — yeniden başlatma ERTELENDİ", 3
    killed = _kill_by_cmdline(t["match"])
    time.sleep(3)
    started = _start_bat(t["bat"])
    return f"[ajan] {name}: kill[{killed or 'süreç yoktu'}] → {started}", 0


def handle_restart_process(client, cmd: dict) -> tuple[str, int]:
    p = cmd.get("payload") or {}
    return restart_target(str(p.get("target", "")), force=bool(p.get("force")))


# ── Ertelenen yeniden başlatma borcu ─────────────────────────────────────
# 2026-07-26 canlı bulgu: 07-23'te oto-güncelleme kodu çekti ama bot açık
# pozisyon yüzünden ERTELENDİ (rc=3) ve BİR DAHA DENENMEDİ → bot 3 gün eski
# kodla çalıştı (07-23/24 düzeltmeleri hiç devreye girmedi, sessizce).
# Artık erteleme "borç" olarak yazılır ve pozisyonlar kapanınca ödenir.

PENDING_RESTART_KEY = "pending_restarts"
PENDING_RESTART_MAX_AGE_H = 72


def _queue_pending_restart(target: str, behind: str = "") -> None:
    st = load_state()
    pend = st.get(PENDING_RESTART_KEY) or {}
    if target not in pend:
        pend[target] = {"since": now_iso(), "commits": behind}
        st[PENDING_RESTART_KEY] = pend
        save_state(st)
        log.warning("[oto] %s restart'ı ERTELENDİ → borç yazıldı, "
                    "pozisyon kapanınca uygulanacak", target)


def flush_pending_restarts(client) -> None:
    """Bekleyen restart borçlarını uygun anda öde (her ana döngü turunda)."""
    st = load_state()
    pend = st.get(PENDING_RESTART_KEY) or {}
    if not pend:
        return
    if open_position_count() > 0:
        return                                  # hâlâ uygun değil
    done = []
    for target, info in list(pend.items()):
        out, rc = restart_target(target)
        log.info("[oto] ertelenmiş restart ödendi: %s → rc=%s", target, rc)
        if rc == 0:
            done.append((target, info, out))
    for target, _info, _out in done:
        pend.pop(target, None)
    # 72 saati aşan borçlar: zorla uygula (pozisyon hiç kapanmıyorsa bile
    # eski kodla çalışmak daha riskli — bu bulgu 3 günlük sessiz sapmadan geldi)
    for target, info in list(pend.items()):
        try:
            age_h = (datetime.now(timezone.utc)
                     - datetime.fromisoformat(info["since"])).total_seconds() / 3600
        except Exception:
            age_h = 0
        if age_h > PENDING_RESTART_MAX_AGE_H:
            out, rc = restart_target(target, force=True)
            log.warning("[oto] %s borcu %.0f saattir bekliyordu → ZORLA "
                        "yeniden başlatıldı (rc=%s)", target, age_h, rc)
            if rc == 0:
                done.append((target, info, out))
                pend.pop(target, None)
    st[PENDING_RESTART_KEY] = pend
    save_state(st)
    if done and client is not None:
        try:
            client.table("evolution_commands").insert({
                "host": HOST, "kind": "run_analysis", "requested_by": "auto_update",
                "analysis_id": "pending_restart", "status": "done",
                "analysis_name": "Ertelenmiş yeniden başlatma ödendi",
                "payload": {"targets": [d[0] for d in done]},
                "started_at": now_iso(), "finished_at": now_iso(), "return_code": 0,
                "output": "\n".join(f"{t}: {o}" for t, _i, o in done),
            }).execute()
        except Exception:
            pass


# ── Oto-güncelleme: push et → kutu kendini günceller ─────────────────────

AUTO_UPDATE_ENABLED = getattr(cfg, "AUTO_UPDATE_ENABLED", True)
AUTO_UPDATE_INTERVAL = int(getattr(cfg, "AUTO_UPDATE_INTERVAL_SECONDS", 600))

# Değişen klasör → yeniden başlatılacak süreç ('agent' EN SON — kendimizi
# kapatınca kalan restart'ları yeni ajan değil bu tur yapmış olmalıyız).
AUTO_RESTART_MAP = [
    ("claude_decider/", "decider"),
    ("yeni deneme/", "bot"),
    ("backend/", "backend"),
    ("remote_agent/", "agent"),
]


def auto_update_tick(client) -> None:
    """git fetch → gerideysek pull → değişen klasörlere göre süreçleri tazele."""
    repo = str(cfg.REPO_ROOT)

    def _git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=repo, capture_output=True,
                              text=True, timeout=180)

    if _git("fetch", "--quiet").returncode != 0:
        return
    behind = _git("rev-list", "--count", "HEAD..@{u}").stdout.strip()
    if not behind or behind == "0":
        return
    old_head = _git("rev-parse", "HEAD").stdout.strip()
    pull = _git("pull", "--ff-only")
    if pull.returncode != 0:
        log.warning("oto-güncelleme pull başarısız: %s", (pull.stderr or "")[:200])
        return
    changed = _git("diff", "--name-only", f"{old_head}..HEAD").stdout.splitlines()
    log.info("oto-güncelleme: %s commit çekildi, %d dosya değişti", behind, len(changed))

    results = []
    for prefix, target in AUTO_RESTART_MAP:
        if any(f.startswith(prefix) for f in changed):
            out, rc = restart_target(target)
            results.append(f"{target}: rc={rc} {out[:80]}")
            log.info("oto-restart %s → rc=%s", target, rc)
            if rc == 3:            # ertelendi (açık pozisyon) → borç yaz
                _queue_pending_restart(target, behind)
    # Panelde iz bırak: değişiklik akışında görünsün
    try:
        client.table("evolution_commands").insert({
            "host": HOST, "kind": "run_analysis", "requested_by": "auto_update",
            "analysis_id": "auto_update", "analysis_name": "Oto-güncelleme (git pull + restart)",
            "payload": {"command": "(otomatik)"}, "status": "done",
            "started_at": now_iso(), "finished_at": now_iso(), "return_code": 0,
            "output": f"{behind} commit çekildi.\nDeğişen: " + "\n".join(changed[:30])
                      + ("\nYeniden başlatılan:\n" + "\n".join(results) if results else "\nSüreç restart'ı gerekmedi."),
        }).execute()
    except Exception:
        pass


HANDLERS = {
    "run_analysis": handle_run_analysis,
    "claude_task": handle_claude_task,
    "sync_lessons": handle_sync_lessons,
    "git_pull": handle_git_pull,
    "restart_bot": handle_restart_bot,
    "restart_process": handle_restart_process,
}


def process_commands(client) -> None:
    res = (client.table("evolution_commands")
           .select("*").eq("host", HOST).eq("status", "pending")
           .order("created_at").limit(5).execute())
    for cmd in (res.data or []):
        # İyimser kilit: pending → running (başka ajan kopyası kapmasın)
        claim = (client.table("evolution_commands")
                 .update({"status": "running", "started_at": now_iso()})
                 .eq("id", cmd["id"]).eq("status", "pending").execute())
        if not claim.data:
            continue
        handler = HANDLERS.get(cmd["kind"])
        if handler is None:
            _update_cmd(client, cmd["id"], status="failed", finished_at=now_iso(),
                        output=f"[ajan] bilinmeyen komut türü: {cmd['kind']}", return_code=2)
            continue
        try:
            out, rc = handler(client, cmd)
            status = "done" if rc == 0 else ("timeout" if rc == -9 else "failed")
            _update_cmd(client, cmd["id"], status=status, finished_at=now_iso(),
                        output=out[-OUTPUT_LIMIT:], return_code=rc)
            log.info("komut %s → %s (rc=%s)", cmd["kind"], status, rc)
        except Exception as e:
            log.exception("komut hata: %s", cmd["kind"])
            _update_cmd(client, cmd["id"], status="failed", finished_at=now_iso(),
                        output=f"[ajan] istisna: {e}", return_code=1)


# ── Haftalık zamanlayıcı ─────────────────────────────────────────────────

def run_weekly_jobs(client, state: dict) -> None:
    """cfg.WEEKLY_JOBS: [{'id','command','cwd','day','hour_utc'}] — haftada 1 koşar."""
    jobs = getattr(cfg, "WEEKLY_JOBS", [])
    if not jobs:
        return
    now = datetime.now(timezone.utc)
    week_key = now.strftime("%G-W%V")  # ISO hafta
    done = state.setdefault("weekly_done", {})
    day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    for job in jobs:
        jid = job["id"]
        if done.get(jid) == week_key:
            continue
        if day_names[now.weekday()] != job.get("day", "sun"):
            continue
        if now.hour < int(job.get("hour_utc", 6)):
            continue
        log.info("haftalık iş başlıyor: %s", jid)
        row = (client.table("evolution_commands").insert({
            "host": HOST, "kind": "run_analysis", "requested_by": "scheduler",
            "analysis_id": jid, "analysis_name": job.get("name", jid),
            "payload": {"command": job["command"], "cwd": job.get("cwd", ""),
                        "timeout": job.get("timeout", CMD_TIMEOUT_DEFAULT)},
            "status": "pending",
        }).execute())
        done[jid] = week_key   # kuyruğa girdi — komut döngüsü işleyecek
        save_state(state)
        log.info("haftalık iş kuyruğa alındı: %s → %s", jid, row.data[0]["id"] if row.data else "?")


# ── Ana döngü ─────────────────────────────────────────────────────────────

def _heartbeat_thread() -> None:
    """Kalp atışını AYRI iş parçacığında at (60 sn'de bir).

    2026-07-20 düzeltmesi: eskiden kalp atışı ana döngüdeydi — uzun süren bir
    komut (ör. restart_bot'un açık-pozisyon bekleyişi) döngüyü bloklayınca
    kalp atışı kesiliyor, MT5 kutusu gayet canlıyken panel 'çevrimdışı'
    gösteriyordu. Artık komutlar ne yaparsa yapsın nabız atmaya devam eder.
    """
    hb_client = supa()
    while True:
        try:
            push_heartbeat(hb_client)
        except Exception as e:
            log.warning("kalp atışı hatası (devam): %s", e)
            try:
                hb_client = supa()
            except Exception:
                pass
        time.sleep(60)


def reconcile_stale_commands(client) -> None:
    """Başlangıçta yarım kalmış 'running' komutları 'failed' işaretle.

    Ajan çökerse/yeniden başlarsa üstlendiği komutun süreci ölmüştür ama satır
    'running' kalır — panelde sonsuza dek 'çalışıyor' görünür (canlıda 15 saat
    asılı kalan bot restart bu yüzdendi). Taze başlangıçta bize ait koşan
    komut OLAMAZ → hepsi kesinti sayılır.
    """
    try:
        res = (client.table("evolution_commands").select("id,kind,started_at")
               .eq("host", HOST).eq("status", "running").execute())
        for cmd in (res.data or []):
            _update_cmd(client, cmd["id"], status="failed", finished_at=now_iso(),
                        output=(f"[ajan] yarıda kesildi — ajan yeniden başladı "
                                f"({cmd.get('kind')}, başlangıç {cmd.get('started_at')}). "
                                f"Gerekirse panelden tekrar gönder."),
                        return_code=-1)
            log.info("yarım kalmış komut kapatıldı: %s (%s)", cmd["id"], cmd.get("kind"))
    except Exception as e:
        log.warning("stale komut mutabakatı başarısız: %s", e)


def main() -> None:
    log.info("Evrim Ajanı başlıyor | host=%s mt5=%s", HOST, HAS_MT5)
    client = supa()
    state = load_state()
    if HAS_MT5 and not mt5_connect():
        log.warning("MT5 bağlanamadı — trade push devre dışı, komut döngüsü sürüyor")
    reconcile_stale_commands(client)
    threading.Thread(target=_heartbeat_thread, daemon=True, name="heartbeat").start()
    last_push = 0.0
    last_update = time.time()  # açılışta pull zaten taze (start_agent döngüsü)
    while True:
        try:
            if time.time() - last_push > PUSH_SECONDS:
                push_trades(client, state)
                push_journal(client, state)
                run_weekly_jobs(client, state)
                save_state(state)
                last_push = time.time()
            if AUTO_UPDATE_ENABLED and time.time() - last_update > AUTO_UPDATE_INTERVAL:
                last_update = time.time()
                auto_update_tick(client)
                flush_pending_restarts(client)   # ertelenmiş restart borcu
            process_commands(client)
        except KeyboardInterrupt:
            log.info("kapanıyor")
            return
        except Exception as e:
            log.warning("döngü hatası (devam): %s", e)
            try:
                client = supa()  # bağlantı tazele
            except Exception:
                pass
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
