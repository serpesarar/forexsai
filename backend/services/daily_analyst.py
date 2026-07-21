"""Günlük Veri Analisti — Opus, panelin tüm verisini günde 1 kez inceler.

Akış (DAILY_ANALYST_ENABLED=1, default açık; saat DAILY_ANALYST_UTC):
  1. Panelin tüm istatistikleri toplanır (model WR'ları, bias karnesi +
     dayanıklılık ufukları, decider kırılımı, bot performansı, Bot↔Decider
     diyaloğu, açık backlog).
  2. Claude Code CLI (Opus) bir KIDEMLİ TRADING VERİ ANALİSTİ olarak çalıştırılır
     — abonelikten, API key yok. CLI yoksa mekanik yedek devreye girer
     (Bot↔Decider kural-bazlı dersleri yine de döngüye bağlanır).
  3. Çıktı otomatik dağıtılır:
     - decider_dersleri  → evolution lessons (targets=claude_decider) →
       LESSONS.md panel bloğu + kutuya sync_lessons komutu (ajan uygular;
       diğer bilgisayara DOKUNMADAN)
     - bot_onerileri     → panel dersi (bot kural değişikliği İNSAN ONAYI ister
       — canlı botta otonom kural değiştirme güvenlik ilkesine aykırı)
     - deney_onerileri   → backlog (experiment)
     - Tam rapor         → backend/data/evolution/analyst_reports/YYYY-MM-DD.md
       + değişiklik akışına oturum notu

Önceki günün analist dersleri arşivlenir (LESSONS bloğu şişmesin; her gün
taze, en güncel veriye dayalı görüş).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ENABLED = os.getenv("DAILY_ANALYST_ENABLED", "1") == "1"
RUN_AT_UTC = os.getenv("DAILY_ANALYST_UTC", "22:45")  # notlamalar (22:20) bittikten sonra
CLI_MODEL = os.getenv("DAILY_ANALYST_MODEL", "opus")

_REPO = Path(__file__).resolve().parents[2]
REPORT_DIR = _REPO / "backend" / "data" / "evolution" / "analyst_reports"
STATE_FILE = REPORT_DIR / "_state.json"

ANALYST_SOURCE = "daily_analyst"


# ── Veri toplama ──────────────────────────────────────────────────────────

async def _gather() -> Dict[str, Any]:
    """Panelin tüm istatistiklerini tek sözlükte topla (hepsi fail-open)."""
    out: Dict[str, Any] = {"generated_at": datetime.now(timezone.utc).isoformat()}

    async def _try(name: str, coro_or_fn):
        try:
            if asyncio.iscoroutine(coro_or_fn):
                out[name] = await coro_or_fn
            else:
                out[name] = await asyncio.to_thread(coro_or_fn)
        except Exception as e:
            out[name] = {"error": str(e)[:200]}

    from services import evolution_remote as remote
    from services.bias_test_service import accuracy_report

    await _try("bias_karnesi", accuracy_report)
    await _try("decider_kirilimi", lambda: remote.get_decider_breakdown(30))
    await _try("bot_performansi", lambda: remote.get_bot_performance(30))
    await _try("bot_vs_decider", lambda: remote.get_bot_vs_decider(30))

    try:
        from routers.learning import get_accuracy_by_model
        acc = await get_accuracy_by_model(symbol=None, days=30, check_interval="24h")
        models = (acc or {}).get("models") or []
        out["model_karnesi"] = [
            {k: m.get(k) for k in ("strategy", "with_outcome", "ml_accuracy",
                                   "flip_closed", "expired")}
            for m in models if (m.get("with_outcome") or 0) >= 10
        ][:20]
    except Exception as e:
        out["model_karnesi"] = {"error": str(e)[:200]}

    try:
        from services import evolution_service as evo
        out["acik_backlog"] = [
            {"id": b["id"], "title": b["title"], "priority": b.get("priority")}
            for b in evo.get_backlog(include_done=False)
            if b.get("status") in ("pending", "in_progress")
        ][:25]
    except Exception as e:
        out["acik_backlog"] = {"error": str(e)[:200]}

    return out


# ── Analist prompt'u ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sen ForexSAI trading sisteminin KIDEMLİ VERİ ANALİSTİ ve verimlilik mimarısın. \
Günde bir kez tüm sistem verisini incelersin; işin sistemi yarın bugünden daha isabetli yapmak.

KİMLİK VE İLKELER (pazarlıksız):
1. KANIT DIŞI KONUŞMA. Her iddiaya sayı iliştir (n, WR, dönem). Sayı yoksa iddia yok.
2. KÜÇÜK ÖRNEKLEM DÜRÜSTLÜĞÜ: n<10 ise "erken sinyal" de, karar önerme. n<30 ise kalıcı kural önerme.
3. AŞIRI UYUM BİLİNCİ: Tek haftalık desenlerden kural çıkarma; "bu dönemde" kaydıyla konuş.
4. HAM ORANLARA KANMA: gün-kapanışı (legacy) metrikleri YANILTICIDIR; primary_intraday (birincil ufukta \
yönlü isabet, çekimserler hariç) ana metriktir. Dayanıklılık ufukları (+10dk→+6s) kararın raf ömrünü söyler.
5. FLIP_CLOSED nötrdür (WR'a girmez); expired nötrdür. Bunları kayıp sayan analiz hatalıdır.
6. Trade-off'suz öneri verme: her önerinin bedelini (kaçan fırsat, azalan hacim) söyle.
7. Ders yazarken EYLEME DÖNÜK yaz: "şu koşulda şunu yap/yapma" netliğinde, en fazla 2 cümle.

GÖREV: Aşağıdaki JSON veriyi incele ve SADECE şu şemada tek bir JSON döndür (başka hiçbir şey yazma):
{
  "ozet": "sistemin bugünkü sağlığı, 2-3 cümle, en kritik tek bulgusuyla",
  "bulgular": ["kanıtlı gözlem (sayılarla), en önemli 3-6 madde"],
  "decider_dersleri": ["Claude Decider'ın karar prompt'una girecek ders — eyleme dönük, sayılı, en fazla 3 adet. Sadece decider verisinden GÜÇLÜ kanıtı olanlar; yoksa boş bırak"],
  "bot_onerileri": ["bot kuralları için İNSAN ONAYLI değişiklik önerisi — hangi scope/koşul, beklenen etki; en fazla 2; yoksa boş"],
  "deney_onerileri": [{"baslik": "kısa", "detay": "hangi veriyle nasıl test edilir, başarı ölçütü ne"}],
  "verimlilik_notu": "sistemde israf/kör nokta varsa tek paragraf (ör. hep çekimser kalan sembol, hiç okunmayan metrik); yoksa boş string"
}

Kalite çıtası: bu rapor her gün üretiliyor — dünkü raporun kopyası gibi genel geçer laflar değersizdir. \
Bugünün verisinde DEĞİŞEN ve AYKIRI olanı yakala. Emin olmadığın yerde "veri yetersiz" demek puandır."""


def _build_user_prompt(data: Dict[str, Any]) -> str:
    return (
        "Bugünün sistem verisi (JSON):\n\n"
        + json.dumps(data, ensure_ascii=False, default=str)[:60000]
        + "\n\nAnalizini yap ve SADECE istenen şemadaki JSON'u döndür."
    )


# ── Çıktı dağıtımı ────────────────────────────────────────────────────────

def _extract_json(text: str) -> Optional[dict]:
    import re
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _archive_previous_analyst_lessons() -> int:
    """Dünkü analist derslerini arşivle — LESSONS bloğu hep taze kalsın."""
    from services import evolution_service as evo
    n = 0
    for l in evo.get_lessons(include_archived=False):
        src = l.get("source") or {}
        if isinstance(src, dict) and src.get("kind") == ANALYST_SOURCE:
            evo.update_lesson_status(l["id"], "archived")
            n += 1
    return n


def _distribute(report: dict, raw_text: str, mechanical: bool) -> Dict[str, int]:
    """Analist çıktısını derslere/backlog'a/rapora dağıt + kutuya senkron komutu."""
    from services import evolution_service as evo
    from services import evolution_remote as remote

    counts = {"archived": _archive_previous_analyst_lessons(),
              "decider": 0, "panel": 0, "backlog": 0}
    today = datetime.now(timezone.utc).date().isoformat()
    src = {"kind": ANALYST_SOURCE, "date": today, "mechanical": mechanical}

    for text in (report.get("decider_dersleri") or [])[:3]:
        if isinstance(text, str) and len(text.strip()) > 10:
            evo.add_lesson(title=f"Günlük Analist ({today})", summary=text.strip(),
                           targets=["claude_decider"], source=src)
            counts["decider"] += 1

    panel_bits: List[str] = []
    for text in (report.get("bot_onerileri") or [])[:2]:
        if isinstance(text, str) and text.strip():
            panel_bits.append(f"BOT ÖNERİSİ (insan onayı gerekir): {text.strip()}")
    if (report.get("verimlilik_notu") or "").strip():
        panel_bits.append(f"VERİMLİLİK: {report['verimlilik_notu'].strip()}")
    if report.get("ozet"):
        panel_bits.insert(0, str(report["ozet"]).strip())
    if panel_bits:
        evo.add_lesson(title=f"Günlük Analist raporu ({today})",
                       summary="\n".join(panel_bits), targets=["panel"], source=src)
        counts["panel"] += 1

    for exp in (report.get("deney_onerileri") or [])[:3]:
        if isinstance(exp, dict) and exp.get("baslik"):
            try:
                evo.add_backlog_item(title=f"[Analist] {str(exp['baslik'])[:150]}",
                                     detail=str(exp.get("detay") or "")[:800],
                                     category="experiment", priority="medium",
                                     source=ANALYST_SOURCE)
                counts["backlog"] += 1
            except Exception as e:
                logger.warning("[analyst] backlog eklenemedi: %s", e)

    # Kutudaki decider'a OTOMATİK senkron — panel bloğunu komut kuyruğuna koy;
    # ajan 30 sn içinde LESSONS.md'ye işler. Diğer bilgisayara dokunmak yok.
    if counts["decider"] > 0:
        try:
            remote.enqueue_command(
                kind="sync_lessons",
                payload={"content": evo.build_decider_lessons_block()},
                requested_by=ANALYST_SOURCE)
        except Exception as e:
            logger.warning("[analyst] sync_lessons kuyruğa yazılamadı: %s", e)

    # Tam raporu diske yaz
    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        body = [f"# Günlük Analist Raporu — {today}",
                f"_mod: {'mekanik yedek' if mechanical else 'Opus (' + CLI_MODEL + ')'}_", ""]
        if report.get("ozet"):
            body += ["## Özet", str(report["ozet"]), ""]
        if report.get("bulgular"):
            body += ["## Bulgular"] + [f"- {b}" for b in report["bulgular"]] + [""]
        if report.get("decider_dersleri"):
            body += ["## Decider dersleri (otomatik enjekte edildi)"] + \
                    [f"- {d}" for d in report["decider_dersleri"]] + [""]
        if report.get("bot_onerileri"):
            body += ["## Bot önerileri (insan onayı bekliyor)"] + \
                    [f"- {b}" for b in report["bot_onerileri"]] + [""]
        if report.get("verimlilik_notu"):
            body += ["## Verimlilik", str(report["verimlilik_notu"]), ""]
        (REPORT_DIR / f"{today}.md").write_text("\n".join(body), encoding="utf-8")
    except Exception as e:
        logger.warning("[analyst] rapor dosyası yazılamadı: %s", e)

    try:
        from services.evolution_service import add_session_note
        add_session_note(
            summary=(f"Günlük Analist ({'mekanik' if mechanical else 'Opus'}): "
                     f"{counts['decider']} decider dersi enjekte, {counts['panel']} panel notu, "
                     f"{counts['backlog']} deney backlog'a. Özet: "
                     + str(report.get('ozet') or '')[:200]),
            files=[f"backend/data/evolution/analyst_reports/{today}.md"])
    except Exception:
        pass
    return counts


def _mechanical_report() -> dict:
    """CLI yoksa: Bot↔Decider kural-bazlı dersleri yine de döngüye bağla."""
    from services import evolution_remote as remote
    try:
        bvd = remote.get_bot_vs_decider(30)
    except Exception as e:
        return {"ozet": f"Analist çalışamadı (CLI yok) ve veri alınamadı: {e}",
                "decider_dersleri": [], "bulgular": []}
    lessons = [l["text"] for l in bvd.get("lessons", []) if "henüz yeterli" not in l["text"]]
    return {
        "ozet": "Opus CLI erişilemedi — Bot↔Decider kural-bazlı sayım dersleri otomatik bağlandı.",
        "bulgular": [f"stats: {json.dumps(bvd.get('stats'), ensure_ascii=False)}"],
        "decider_dersleri": [t for l in lessons if ("decider" in l.lower() or "zıt" in l.lower())
                             for t in [l]][:2],
        "bot_onerileri": [l for l in lessons if l.lower().startswith("decider'ın wait")][:1],
        "deney_onerileri": [],
        "verimlilik_notu": "",
    }


# ── Çalıştırıcı ───────────────────────────────────────────────────────────

async def run_daily_analysis(force: bool = False) -> Dict[str, Any]:
    """Analizi ŞİMDİ çalıştır (loop günde 1 çağırır; panel/endpoint force edebilir)."""
    data = await _gather()

    from services.claude_cli import call_claude_cli, claude_cli_available
    report: Optional[dict] = None
    mechanical = True
    raw = ""
    if claude_cli_available():
        raw = await call_claude_cli(SYSTEM_PROMPT, _build_user_prompt(data),
                                    model=CLI_MODEL, timeout=420) or ""
        report = _extract_json(raw)
        if report:
            mechanical = False
        else:
            logger.warning("[analyst] Opus çıktısı parse edilemedi — mekanik yedek")
    if report is None:
        report = _mechanical_report()

    counts = _distribute(report, raw, mechanical)
    logger.info("[analyst] günlük analiz bitti: %s (mod=%s)",
                counts, "mekanik" if mechanical else "opus")
    return {"mode": "mechanical" if mechanical else "opus",
            "counts": counts, "ozet": report.get("ozet")}


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(s: dict) -> None:
    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(s), encoding="utf-8")
    except Exception:
        pass


async def analyst_loop() -> None:
    """60 sn'lik tick: her gün DAILY_ANALYST_UTC'de bir kez çalıştır."""
    logger.info("[analyst] günlük analist döngüsü açık (saat %s UTC, model %s)",
                RUN_AT_UTC, CLI_MODEL)
    while True:
        try:
            now = datetime.now(timezone.utc)
            state = _load_state()
            today = now.date().isoformat()
            if state.get("last_run") != today and now.strftime("%H:%M") >= RUN_AT_UTC:
                state["last_run"] = today
                _save_state(state)  # önce yaz — hata olursa da günde 1 dene
                await run_daily_analysis()
        except Exception as e:
            logger.error("[analyst] döngü hatası: %s", e)
        await asyncio.sleep(60)
