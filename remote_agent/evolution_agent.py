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

CANLILIK DENETİMİ (2026-10-29, WATCHDOG_ENABLED=True default): ayrı iş
parçacığı 2 dk'da bir bot (forexsai_demo_bot.py + demo_bot.log tazeliği) ve
decider (run_decider.py + memory/decider_heartbeat.json) süreçlerine bakar;
süreç yoksa ya da dosya eşikten uzun sessizse ERTELEMEDEN yeniden başlatır
(geri çekilmeli: 15→30→60→120 dk). Sonuç kalp atışında bot_alive /
bot_log_age_s / bot_last_restart olarak panele gider. remote_agent/WATCHDOG_OFF
dosyası varken yalnız raporlar.

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
PUSH_SECONDS = 300         # journal/haftalık işler/heartbeat
# 2026-08-28: İŞLEMLER ayrı ve DAHA SIK — panel "MT5'teki işlemler anlık
# güncellensin" istiyor; 5dk'lık PUSH_SECONDS'la bir kapanan işlem panelde
# görünmesi ortalama 2,5dk (en kötü 5dk) sürüyordu. push_trades tek başına
# ucuz (bir history_deals_get + gerekirse birkaç position lookup) — journal/
# haftalık işlerden ayırıp kısaltmak güvenli.
TRADE_PUSH_SECONDS = int(getattr(cfg, "TRADE_PUSH_SECONDS", 20))
CMD_TIMEOUT_DEFAULT = 1800  # run_analysis varsayılan zaman aşımı (sn)
OUTPUT_LIMIT = 60_000      # komut çıktısının Supabase'e yazılan kuyruğu

# backend/services/evolution_service.py::_PANEL_START/_PANEL_END ile birebir aynı
LESSONS_BEGIN = "<!-- PANEL-LESSONS START -->"
LESSONS_END = "<!-- PANEL-LESSONS END -->"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_dt(ts: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _iso_age_s(ts: str | None) -> float | None:
    """ISO zaman damgasının şimdiden yaşı (sn); boş/bozuksa None."""
    dt = _iso_dt(ts)
    return (datetime.now(timezone.utc) - dt).total_seconds() if dt else None


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict, own_pending: bool = False) -> None:
    """Durumu yaz. Restart borcu (PENDING_RESTART_KEY) YALNIZ borç fonksiyonlarına aittir.

    2026-10-20 bulgusu: ana döngü açılışta yüklediği `state`'i her turda yazıyordu; borç
    fonksiyonları dosyaya yazdığı `pending_restarts`'ı bir sonraki turda bu eski kopya
    siliyordu → ertelenen restart'lar hiç ödenmedi (bot 10-15'ten beri eski kodla). Artık
    own_pending=False iken borç anahtarı diskteki hâliyle korunur (bellekteki değer yok sayılır).
    """
    out = dict(state)
    if not own_pending:
        try:
            disk = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            disk = {}
        if PENDING_RESTART_KEY in disk:
            out[PENDING_RESTART_KEY] = disk[PENDING_RESTART_KEY]
        else:
            out.pop(PENDING_RESTART_KEY, None)
    STATE_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")


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


# Broker sembolü → ForexSAI kanonik adı. bot_trades.symbol broker adını korur,
# normalized_symbol ise sistemin geri kalanıyla (prediction_logs, candle_cache,
# decider_journal) JOIN edilebilir kanonik adı taşır. 2026-07-31 denetimi:
# bu kolon yokken her çapraz analiz elle eşleme gerektiriyordu.
BROKER_SYMBOL_MAP = dict(getattr(cfg, "BROKER_SYMBOL_MAP", {}) or {
    "NAS100": "NDX.INDX",
    "GER40": "GDAXI.INDX",
    "SpotCrude": "USOIL.FOREX",
    "XAUUSD": "XAUUSD",
})


#: Trade senkronunun son durumu — heartbeat'e ve panele taşınır.
#: 2026-08-26 vakası: mt5_connect() YALNIZ açılışta çağrılıyordu; bağlantı
#: sonradan düşünce history_deals_get sessizce None döndü, push_trades
#: `if not deals: return 0` ile hiçbir iz bırakmadan çıktı ve bot_trades
#: 8 gün boyunca donmuş kaldı — ajan "çevrimiçi" görünürken. Artık okuma
#: hatası ile "yeni deal yok" AYRIŞTIRILIR, yeniden bağlanma denenir ve
#: durum kalp atışıyla panele gider.
TRADE_SYNC = {"ok": True, "last_push_at": None, "last_error": None, "fail_streak": 0}


def _lookup_entry(position_id: int) -> tuple:
    """Bir pozisyonun giriş fiyatı/zamanı + PLANLANAN SL/TP'si.

    Kapanan (OUT) deal'de yalnız ÇIKIŞ bilgisi var. Giriş, aynı position_id'yi
    taşıyan AYRI bir deal'dedir (entry=0 = DEAL_ENTRY_IN) — MT5
    ``history_deals_get(position=...)`` bunu doğrudan verir. Planlanan SL/TP
    ise deal'de değil, pozisyonu açan ORDER'da durur (trailing sonradan
    değiştirse bile bu İLK plandır — decider'ın ``trade.sl/tp`` alanına
    karşılık gelir). İkisi de best-effort: bulunamazsa None döner, satır
    yine de yazılır (eksik zenginlik veri kaybı değil).
    """
    open_price = open_time = sl = tp = None
    try:
        deals = mt5.history_deals_get(position=position_id)
        entries = [d for d in (deals or []) if getattr(d, "entry", None) == 0]
        if entries:
            first = min(entries, key=lambda d: d.time)
            open_price, open_time = first.price, first.time
    except Exception:
        pass
    try:
        orders = mt5.history_orders_get(position=position_id)
        for o in orders or []:
            if getattr(o, "sl", 0) or getattr(o, "tp", 0):
                sl, tp = (o.sl or None), (o.tp or None)
                break
    except Exception:
        pass
    return open_price, open_time, sl, tp


#: Geriye dönük dolum şeması sürümü — artırılırsa ajan bir kez daha tarar.
#: 2026-08-27 v1→v2: v1 sırasında 479 satırın 0'ı doldu (ayrı thread'de MT5
#: API'sine eşzamanlı erişim + eski pozisyonlar için terminal geçmiş önbelleği
#: ısınmamış olabilir — MetaTrader5 paketi resmî olarak thread-safe DEĞİL).
#: v2 ANA thread'de senkron çalışır ve önce geniş bir tarih aralığı çekerek
#: terminalin deal geçmişini o dönem için önceden ısıtır.
ENTRY_BACKFILL_VERSION = 2


def backfill_trade_entries(client, state: dict) -> int:
    """Var olan bot_trades satırlarının open_price/sl/tp'sini bir KEZ doldurur.

    2026-08-27'ye kadar push_trades yalnız ÇIKIŞ bilgisini yazıyordu —
    open_price/open_time/sl/tp kolonları şemada vardı ama hiç kullanılmamıştı.
    Bu, panelin bot işlemleri için decider'daki gibi giriş→çıkış / R / TP-SL
    döküm göstermesini engelliyordu. Bir kerelik tarama state bayrağıyla
    korunur — her turda tekrar 400+ satır taramaz.

    ⚠️ ANA THREAD'DE, senkron çağrılmalı (main() içinde, heartbeat thread'i
    başlamadan ÖNCE) — MetaTrader5 paketi resmî olarak thread-safe değildir;
    ayrı thread'de çalıştırılan ilk denemede (v1) 479 satırın 0'ı dolmuştu.
    """
    if not HAS_MT5 or state.get("entry_backfill_version") == ENTRY_BACKFILL_VERSION:
        return 0
    try:
        res = (client.table("bot_trades").select("ticket,close_time,raw")
               .eq("host", HOST).is_("open_price", "null")
               .order("close_time").limit(2000).execute())
        rows = res.data or []
    except Exception as e:
        log.warning("backfill_trade_entries okunamadı: %s", e)
        return 0

    if not rows:
        state["entry_backfill_version"] = ENTRY_BACKFILL_VERSION
        return 0

    # Terminal deal geçmişini bu aralık için ısıt — bazı MT5 kurulumlarında
    # history_deals_get(position=...) yalnız daha önce bir tarih-aralığı
    # sorgusuyla "görülmüş" dönemler için sonuç döndürür.
    try:
        first_ts = _parse_ts(rows[0].get("close_time"))
        span_from = (first_ts - timedelta(days=1)) if first_ts else datetime.now(timezone.utc) - timedelta(days=90)
        mt5.history_deals_get(span_from, datetime.now(timezone.utc))
    except Exception as e:
        log.warning("backfill ısıtma sorgusu başarısız (devam ediliyor): %s", e)

    filled = 0
    no_position_id = 0
    lookup_miss = 0
    update_failed = 0
    for r in rows:
        pos_id = (r.get("raw") or {}).get("position_id")
        if not pos_id:
            no_position_id += 1
            continue
        open_price, open_time, sl, tp = _lookup_entry(pos_id)
        if open_price is None:
            lookup_miss += 1
            continue
        try:
            client.table("bot_trades").update({
                "open_price": open_price,
                "open_time": (datetime.fromtimestamp(open_time, tz=timezone.utc).isoformat()
                              if open_time else None),
                "sl": sl, "tp": tp,
            }).eq("ticket", r["ticket"]).eq("host", HOST).execute()
            filled += 1
        except Exception as e:
            update_failed += 1
            log.warning("backfill güncelleme hatası (ticket=%s): %s", r.get("ticket"), e)

    state["entry_backfill_version"] = ENTRY_BACKFILL_VERSION
    log.info("bot_trades geriye dönük giriş/SL/TP dolumu: %d/%d satır "
             "(position_id yok=%d, MT5'te bulunamadı=%d, güncelleme hatası=%d)",
             filled, len(rows), no_position_id, lookup_miss, update_failed)
    return filled


def push_trades(client, state: dict) -> int:
    """MT5 kapanan deal'leri watermark'tan itibaren bot_trades'e yaz."""
    if not HAS_MT5:
        return 0
    last_ts = state.get("last_deal_ts", time.time() - 30 * 86400)
    deals = mt5.history_deals_get(datetime.fromtimestamp(last_ts - 3600, tz=timezone.utc),
                                  datetime.now(timezone.utc))
    if deals is None:
        # OKUMA HATASI — "yeni deal yok" ile aynı şey DEĞİL. Bağlantı düşmüş
        # olabilir; sessizce geçme, logla ve yeniden bağlanmayı dene.
        err = mt5.last_error()
        TRADE_SYNC.update(ok=False, last_error=str(err),
                          fail_streak=TRADE_SYNC["fail_streak"] + 1)
        log.warning("history_deals_get None döndü (%s) — MT5 yeniden bağlanılıyor "
                    "[üst üste %d]", err, TRADE_SYNC["fail_streak"])
        try:
            mt5.shutdown()
        except Exception:
            pass
        if mt5_connect():
            log.info("MT5 yeniden bağlandı — trade senkronu sonraki turda denenecek")
        return 0

    # Buradan sonrası sağlıklı okuma: boş tuple = gerçekten yeni deal yok.
    TRADE_SYNC.update(ok=True, last_push_at=now_iso(), last_error=None, fail_streak=0)
    if not deals:
        return 0
    # Sadece pozisyon KAPATAN deal'ler (entry=1 → DEAL_ENTRY_OUT) gerçek sonuçtur
    rows = []
    max_ts = last_ts
    for d in deals:
        if getattr(d, "entry", None) != 1:
            continue
        max_ts = max(max_ts, d.time)
        # Giriş + planlanan SL/TP: canlı işlem olduğu için ucuz (tek deal grubu).
        open_price, open_time, sl, tp = _lookup_entry(d.position_id)
        rows.append({
            "ticket": d.ticket,
            "host": HOST,
            "symbol": d.symbol,
            "normalized_symbol": BROKER_SYMBOL_MAP.get(d.symbol),
            "direction": "SELL" if d.type == 0 else "BUY",  # kapatan deal ters yönlüdür
            "volume": d.volume,
            "open_time": (datetime.fromtimestamp(open_time, tz=timezone.utc).isoformat()
                         if open_time else None),
            "open_price": open_price,
            "close_time": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
            "close_price": d.price,
            "sl": sl, "tp": tp,
            "profit": d.profit,
            "commission": d.commission,
            "swap": d.swap,
            "comment": d.comment,
            "magic": d.magic,
            # reason: 4=SL, 5=TP, diğerleri manuel/expert/stop-out (MT5 sabitleri).
            "raw": {"position_id": d.position_id, "order": d.order, "reason": d.reason},
        })
    if rows:
        for i in range(0, len(rows), 200):
            client.table("bot_trades").upsert(rows[i:i + 200]).execute()
        state["last_deal_ts"] = max_ts
        log.info("bot_trades += %d", len(rows))
    return len(rows)


#: entry_fingerprints.jsonl yolu — bot bunu SR/momentum girişlerinde yazar
#: (record_fingerprint, forexsai_demo_bot.py). CHREV/VIXREG/DAYCOMBO/USOIL_
#: BREAKOUT/reflex/reentry için satır YOK — yalnız base MAGIC_NUMBER kapsar.
FINGERPRINT_FILE = Path(getattr(
    cfg, "FINGERPRINT_JOURNAL",
    str(Path(getattr(cfg, "REPO_ROOT", ".")) / "yeni deneme" / "entry_fingerprints.jsonl")))


def push_fingerprints(client, state: dict) -> int:
    """entry_fingerprints.jsonl → bot_entry_fingerprints (yalnız YENİ satırlar).

    "Bu işlem HANGİ KURALA göre açıldı" sorusunun ham verisi. Dosya sadece
    EKLENİR (rewrite yok) — journal'ın aksine tam byte-offset tail'i güvenli.
    ticket = bot_trades.raw->>'position_id' ile eşleşir (panel tarafı JOIN'i
    services/evolution_remote.py::get_bot_symbol_history yapar).
    """
    if not FINGERPRINT_FILE.exists():
        return 0
    size = FINGERPRINT_FILE.stat().st_size
    offset = state.get("fingerprint_offset", 0)
    if size < offset:            # dosya döndürülmüş/yeniden yazılmış
        offset = 0
    if size == offset:
        return 0

    try:
        with FINGERPRINT_FILE.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(offset)
            new_text = f.read()
    except Exception as e:
        log.warning("entry_fingerprints okunamadı: %s", e)
        return 0

    rows = []
    for line in new_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        ticket = rec.get("ticket")
        if not ticket:
            continue
        rows.append({
            "ticket": int(ticket),
            "host": HOST,
            "ts": rec.get("ts"),
            "scope": rec.get("scope"),
            "symbol": rec.get("symbol"),
            "mt5_symbol": rec.get("mt5_symbol"),
            "direction": rec.get("direction"),
            "entry": rec.get("entry"),
            "tp": rec.get("tp"),
            "sl": rec.get("sl"),
            "lot": rec.get("lot"),
            "rr": rec.get("rr"),
            "entry_type": rec.get("entry_type"),
            "tp_source": rec.get("tp_source"),
            "voters": rec.get("voters") or [],
            "raw": rec,
        })

    if rows:
        for i in range(0, len(rows), 200):
            client.table("bot_entry_fingerprints").upsert(rows[i:i + 200]).execute()
        log.info("bot_entry_fingerprints += %d", len(rows))
    state["fingerprint_offset"] = size
    return len(rows)


# journal senkronu: kaç günlük pencere her turda YENİDEN gönderilsin
JOURNAL_RESYNC_DAYS = float(getattr(cfg, "JOURNAL_RESYNC_DAYS", 5))

# Kimlik şeması sürümü. _journal_id'nin ürettiği anahtar DEĞİŞİRSE bunu artır:
# ajan bir kez TAM senkron yapıp eski şemadaki satırları tazeler.
# 2026-07-31: v1(satır-SHA1) → v2(ts|symbol|mode) geçişi 5 günlük pencerenin
# dışındaki 3.617 satırı geride bırakmıştı; 387 karar iki kimlikle birden
# duruyordu ve panelde çözülme oranı %80 görünüyordu (gerçek %99,9).
JOURNAL_ID_VERSION = 2
# Pencere dışında geç çözülen kararlar da bir gün içinde panele ulaşsın diye
# günde bir kez tam senkron (2-3 bin satır, ~15 batch — ihmal edilebilir).
JOURNAL_FULL_RESYNC_SEC = float(getattr(cfg, "JOURNAL_FULL_RESYNC_SEC", 86400))


def _journal_id(rec: dict) -> str:
    """DETERMİNİSTİK kayıt kimliği — outcome değişse bile AYNI kalır.

    2026-07-29 hata düzeltmesi: eskiden id = satırın SHA1'iydi. outcomes.resolve
    kayda `outcome` eklediğinde satır değişiyor → hash değişiyor → upsert
    GÜNCELLEMİYOR, İKİNCİ SATIR açıyordu. Sonuç: panelde aynı karar iki kez
    (biri NULL, biri WIN/LOSS) ve "çözülmemiş" görünen yüzlerce kayıt.
    Kimlik artık kararın kendisinden türer (ts+sembol+mod).
    """
    key = f"{rec.get('ts')}|{rec.get('symbol')}|{rec.get('mode', '')}"
    return "v2" + hashlib.sha1(key.encode()).hexdigest()[:14]


def push_journal(client, state: dict) -> int:
    """journal.jsonl → decider_journal.

    İKİ AŞAMA (2026-07-29):
      1. YENİ satırlar: byte offset'ten sonrası (hızlı yol).
      2. GÜNCELLENEN satırlar: son JOURNAL_RESYNC_DAYS günlük pencere her turda
         yeniden upsert edilir. Bu şart, çünkü `outcomes.resolve` dosyayı TAM
         yeniden yazarak eski satırlara outcome ekliyor; offset'in gerisinde
         kalan bu güncellemeler aksi halde panele HİÇ ulaşmıyordu (470 karar
         "çözülmemiş" görünüyordu, oysa kutuda çözülmüştü).
    """
    path = Path(getattr(cfg, "DECIDER_JOURNAL", ""))
    if not path.exists():
        return 0
    size = path.stat().st_size
    offset = state.get("journal_offset", 0)
    if size < offset:            # dosya küçüldü (döndürüldü/yeniden yazıldı)
        offset = 0

    try:
        all_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        log.warning("journal okunamadı: %s", e)
        return 0

    # TAM senkron gerekiyor mu? (a) kimlik şeması değişti, (b) günlük tazeleme.
    # Aksi halde yalnız son JOURNAL_RESYNC_DAYS günlük pencere gönderilir.
    now_s = time.time()
    full = (state.get("journal_id_version") != JOURNAL_ID_VERSION
            or now_s - float(state.get("last_full_resync", 0)) > JOURNAL_FULL_RESYNC_SEC)
    cutoff = 0.0 if full else now_s - JOURNAL_RESYNC_DAYS * 86400
    rows, seen = [], set()
    for line in all_lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        ts_raw = rec.get("ts") or rec.get("timestamp")
        try:
            ts_epoch = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).timestamp()
        except Exception:
            ts_epoch = cutoff        # ayrıştırılamazsa pencereye dahil et
        if ts_epoch < cutoff:
            continue                 # pencere dışı — zaten senkron
        rid = _journal_id(rec)
        if rid in seen:              # aynı anahtar iki kez varsa SONRAKİ kazanır
            rows = [r for r in rows if r["id"] != rid]
        seen.add(rid)
        rows.append({
            "id": rid,
            "host": HOST,
            "ts": ts_raw,
            "symbol": rec.get("symbol"),
            "decision": rec.get("decision") or rec.get("action"),
            "confidence": rec.get("confidence"),
            "outcome": rec.get("outcome"),
            "raw": rec,
        })
    if rows:
        for i in range(0, len(rows), 200):
            client.table("decider_journal").upsert(rows[i:i + 200]).execute()
        n_res = sum(1 for r in rows if r.get("outcome") is not None)
        log.info("decider_journal senkron: %d satır (%d sonuçlu, %s)",
                 len(rows), n_res,
                 "TAM senkron" if full else f"pencere {JOURNAL_RESYNC_DAYS:.0f}g")
    # Tam senkron ancak GERÇEKTEN yazdıysak işaretlenir; boş dosyada işaretleyip
    # bir sonraki gerçek tam senkronu bir gün ertelemeyelim.
    if full and rows:
        state["journal_id_version"] = JOURNAL_ID_VERSION
        state["last_full_resync"] = now_s
    state["journal_offset"] = size
    return len(rows)


def push_heartbeat(client, extra: dict | None = None) -> None:
    meta = {
        "mt5": HAS_MT5,
        "open_positions": open_position_count(),
        "agent_version": "1.2",
        # Panel "ajan çevrimiçi ama işlem verisi bayat" durumunun SEBEBİNİ
        # görebilsin diye trade senkron sağlığı da taşınır.
        "trade_sync_ok": TRADE_SYNC["ok"],
        "trade_sync_last_push": TRADE_SYNC["last_push_at"],
        "trade_sync_error": TRADE_SYNC["last_error"],
        "trade_sync_fail_streak": TRADE_SYNC["fail_streak"],
        # 1.2 (2026-10-29): ajan çevrimiçi ≠ bot çalışıyor — süreç canlılığı ayrı.
        **_watchdog_meta(),
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
    # 2026-08-21: kutudaki ajan da Sonnet 5 + yüksek düşünme eforuyla çalışır
    # (Opus kotası hızlı tükeniyordu). payload.effort ile çağrı bazında ezilebilir.
    effort = p.get("effort") or getattr(cfg, "CLAUDE_TASK_EFFORT", "high")
    full_prompt = prompt if p.get("raw") else f"{CLAUDE_TASK_PROTOCOL}\n\nGÖREV:\n{prompt}"

    claude_bin = _resolve_claude_bin()
    argv = [claude_bin, "-p", "--dangerously-skip-permissions", "--model", model]
    if effort:
        argv += ["--effort", effort]
    log.info("claude_task: model=%s efor=%s cwd=%s timeout=%ss prompt=%d karakter",
             model, effort or "-", cwd, timeout, len(full_prompt))
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


def _ps_cmdline_filter(match: str) -> str:
    """Komut satırında `match` geçen süreçler — bu sorguyu koşturan kabuğun kendisi hariç."""
    return f"$_.CommandLine -like '*{match}*' -and $_.CommandLine -notlike '*Win32_Process*'"


def _kill_by_cmdline(match: str) -> str:
    """Komut satırında `match` geçen python süreçlerini öldür (Windows/Mac)."""
    if sys.platform == "win32":
        ps = ("Get-CimInstance Win32_Process | "
              f"Where-Object {{ {_ps_cmdline_filter(match)} }} | "
              "ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $_.ProcessId }")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=60)
        return (r.stdout or r.stderr or "").strip()
    r = subprocess.run(["pkill", "-f", match], capture_output=True, text=True)
    return f"pkill rc={r.returncode}"


def _pids_by_cmdline(match: str) -> list[int] | None:
    """Komut satırında `match` geçen PYTHON süreçlerinin PID'leri; sorgu başarısızsa None.

    _kill_by_cmdline ile aynı eşleme, ama yalnız python* adlı süreçler sayılır —
    `remote.py sh "... forexsai_demo_bot.py ..."` gibi bir kabuk komutu ölü botu
    'canlı' göstermesin. None = BİLİNMİYOR (boş liste = süreç gerçekten yok).
    """
    try:
        if sys.platform == "win32":
            ps = ("Get-CimInstance Win32_Process | "
                  f"Where-Object {{ $_.Name -like 'python*' -and {_ps_cmdline_filter(match)} }} | "
                  "ForEach-Object { $_.ProcessId }")
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                               capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                return None
        else:
            r = subprocess.run(["pgrep", "-f", match], capture_output=True, text=True, timeout=30)
            if r.returncode not in (0, 1):      # pgrep: 1 = eşleşme yok
                return None
        return [int(x) for x in r.stdout.split() if x.isdigit()]
    except Exception as e:
        log.warning("süreç sorgusu başarısız (%s): %s", match, e)
        return None


def _start_bat(rel_bat: str) -> str:
    path = Path(cfg.REPO_ROOT) / rel_bat
    if not path.exists():
        return f"HATA: {path} yok"
    if sys.platform == "win32":
        subprocess.Popen(["cmd", "/c", "start", "", str(path)], cwd=str(cfg.REPO_ROOT))
        return f"başlatıldı: {rel_bat}"
    return f"(windows-dışı: {rel_bat} elle başlatılmalı)"


#: Öldür+başlat ve canlılık denetiminin gözle+karar ver adımı bu kilidin altında koşar —
#: denetim iş parçacığı, oto-güncellemenin kill→start arasındaki 3 sn'lik boşlukta
#: "süreç yok" görüp ikinci bir restart atmasın. RLock: denetim kilidi tutarken
#: restart_target'ı çağırır.
RESTART_LOCK = threading.RLock()
#: Son restart'lar + denetim serisi; agent_state.json'dan AYRI dosya (ana döngü o
#: dosyayı kendi kopyasıyla yazar, iki iş parçacığı aynı dosyayı yazmasın).
WATCHDOG_STATE_FILE = Path(__file__).parent / "watchdog_state.json"


def _load_wd() -> dict:
    with RESTART_LOCK:          # yazan da kilitli → yarım yazılmış dosya okunmaz
        try:
            return json.loads(WATCHDOG_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}


def _update_wd(fn) -> dict:
    """watchdog_state.json'ı kilit altında oku → fn(d) → yaz."""
    with RESTART_LOCK:
        d = _load_wd()
        fn(d)
        try:
            WATCHDOG_STATE_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")
        except Exception as e:
            log.warning("watchdog_state yazılamadı: %s", e)
        return d


def _record_restart(name: str, why: str) -> None:
    def _set(d: dict) -> None:
        d.setdefault("restarts", {})[name] = {"at": now_iso(), "why": why}
    _update_wd(_set)


def restart_target(name: str, force: bool = False, why: str = "") -> tuple[str, int]:
    """Bir süreci yeniden başlat. 'agent' → kendini kapatır (start_agent.bat
    döngüsü yeni kodla kaldırır). Bot güvenli-bekler (pozisyon açıkken ertelenir).

    rc: 0 tamam · 3 ertelendi (açık pozisyon) · 4 eski süreç öldürülemedi →
    İKİNCİ kopya başlatılmadı (iki bot = çift emir; canlılık denetimi sonra yeniden dener).
    """
    t = _process_targets().get(name)
    if not t:
        return f"[ajan] bilinmeyen hedef: {name}", 2
    if t.get("self"):
        log.info("ajan kendini yeniliyor (start_agent.bat yeniden kaldıracak)")
        threading.Timer(2.0, lambda: os._exit(0)).start()
        return "[ajan] kendini kapatıyor — 30 sn içinde yeni kodla geri gelir", 0
    if t.get("safe_wait") and not force and open_position_count() > 0:
        return f"[ajan] {name}: açık pozisyon var — yeniden başlatma ERTELENDİ", 3
    with RESTART_LOCK:
        killed = _kill_by_cmdline(t["match"])
        time.sleep(3)
        left = _pids_by_cmdline(t["match"])
        if left:
            log.error("[ajan] %s öldürülemedi (PID %s) — ikinci kopya BAŞLATILMADI", name, left)
            return f"[ajan] {name}: kill[{killed}] sonrası hâlâ PID {left} — ikinci kopya başlatılmadı", 4
        started = _start_bat(t["bat"])
        _record_restart(name, why or "elle/oto-güncelleme")
    return f"[ajan] {name}: kill[{killed or 'süreç yoktu'}] → {started}", 0


def handle_restart_process(client, cmd: dict) -> tuple[str, int]:
    """ELLE istenen restart. 2026-07-28 bulgusu: borç yalnız OTO-güncelleme yolunda
    yazılıyordu (auto_update rc==3); panelden/köprüden elle istenen restart ertelenince
    (rc=3) borç YAZILMIYOR ve bir daha denenmiyordu → süreç eski kod/config ile çalışmaya
    devam ediyordu. Bu, 07-23'teki '3 gün eski kodla çalıştı' vakasının elle-tetikleme
    versiyonu. Artık iki yol da aynı borç mekanizmasına yazar."""
    p = cmd.get("payload") or {}
    target = str(p.get("target", ""))
    out, rc = restart_target(target, force=bool(p.get("force")))
    if rc == 3:
        _queue_pending_restart(target, "elle istendi")
        out += " → BORÇ yazıldı (pozisyon kapanınca ödenecek, 72s sonra zorla)"
    return out, rc


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
        save_state(st, own_pending=True)
        log.warning("[oto] %s restart'ı ERTELENDİ → borç yazıldı, "
                    "pozisyon kapanınca uygulanacak", target)


def flush_pending_restarts(client) -> None:
    """Bekleyen restart borçlarını uygun anda öde (her ana döngü turunda)."""
    st = load_state()
    pend = st.get(PENDING_RESTART_KEY) or {}
    if not pend:
        return
    # Borçtan SONRA süreç zaten yeniden başladıysa (ör. canlılık denetimi ölü botu
    # kaldırdı) yeni kodla çalışıyordur → borç ödenmiş sayılır; sağlıklı süreç bir
    # daha öldürülmez.
    restarts = _load_wd().get("restarts") or {}
    for target, info in list(pend.items()):
        borc_at = _iso_dt(info.get("since"))
        restart_at = _iso_dt((restarts.get(target) or {}).get("at"))
        if borc_at and restart_at and restart_at > borc_at:
            pend.pop(target)
            log.info("[oto] %s borcu kapandı — süreç borçtan sonra zaten yeniden başlamış", target)
    if not pend:
        st[PENDING_RESTART_KEY] = pend
        save_state(st, own_pending=True)
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
    save_state(st, own_pending=True)
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


# ── Canlılık denetimi (watchdog) ─────────────────────────────────────────
# 2026-10-29 bulgusu (defter §1 E83): bot 10-21 04:25 UTC'de hata/kapanış satırı
# yazmadan durdu, 10-29 14:57'ye kadar kalkmadı. Ajan süreçleri yalnız main
# değişince yeniden başlatıyordu; kalp atışı (mt5/trade_sync) botu hiç ölçmüyordu
# → 8 gün kimse görmedi. Bu sırada decider 112 XAU işlemi açtı; bot içindeki
# decider_early_cut hiç uygulanmadı. Artık ayrı bir iş parçacığı birkaç dakikada
# bir süreç + tazelik dosyasına bakar ve ölü/asılı süreci ERTELEMEDEN yeniden
# başlatır: ölü bot pozisyon yönetemez, "pozisyon kapanınca" beklemek tam o
# boşluğu yeniden açar (decider pozisyonları hesabı nadiren düzleştirir).

WATCHDOG_ENABLED = getattr(cfg, "WATCHDOG_ENABLED", True)
WATCHDOG_SECONDS = int(getattr(cfg, "WATCHDOG_SECONDS", 120))
#: Bu dosya varsa denetim yalnız RAPORLAR, restart atmaz (botu bilerek durdururken):
#:   remote.py sh "type nul > remote_agent\WATCHDOG_OFF"   ·   kaldır: del remote_agent\WATCHDOG_OFF
WATCHDOG_OFF_FILE = Path(__file__).parent / "WATCHDOG_OFF"
#: İki denetim restart'ı arası taban bekleme; üst üste her restart'ta ikiye katlanır
#: (çökme döngüsünde 2 dk'da bir pencere yığılmasın): 15 → 30 → 60 → 120 dk.
WATCHDOG_COOLDOWN_SEC = int(getattr(cfg, "WATCHDOG_COOLDOWN_SEC", 900))
WATCHDOG_COOLDOWN_MAX_SEC = int(getattr(cfg, "WATCHDOG_COOLDOWN_MAX_SEC", 7200))

_REPO = Path(getattr(cfg, "REPO_ROOT", "."))
#: hedef → tazelik dosyası + sessizlik eşiği (süreç eşlemesi DEFAULT_PROCESS_TARGETS'tan).
WATCHDOG_SPECS = {
    # bot her döngüde (~60 sn, hafta sonu dahil) '─── tarama @' yazar → 10 dk sessizlik = ölü/asılı
    "bot": {"file": Path(getattr(cfg, "BOT_LOG_FILE", _REPO / "yeni deneme" / "demo_bot.log")),
            "stale_after_s": int(getattr(cfg, "BOT_LOG_STALE_SEC", 600))},
    # decider her döngü başında kalp atışı yazar (20 dk kadans + Opus çağrıları ≤5 dk×deneme).
    # journal yaşı canlılık DEĞİL — olay-tetikli, hafta sonu günlerce yazmaz → yalnız raporlanır.
    "decider": {"file": Path(getattr(cfg, "DECIDER_HEARTBEAT_FILE",
                                     _REPO / "claude_decider" / "memory" / "decider_heartbeat.json")),
                "stale_after_s": int(getattr(cfg, "DECIDER_STALE_SEC", 10800))},
}
WATCHDOG_WATCH = tuple(getattr(cfg, "WATCHDOG_WATCH", ("bot", "decider")))

#: Son denetimin gözlemi — kalp atışı iş parçacığı buradan okur (her turda yeni dict atanır).
WATCHDOG: dict = {}


def liveness_verdict(proc_alive: bool | None, age_s: float | None, stale_after_s: float,
                     since_restart_s: float | None, cooldown_s: float) -> tuple[str, str]:
    """SAF karar → (eylem, sebep); eylem ∈ ok | restart | cooldown | unknown.

    proc_alive None = süreç sorgusu başarısız; age_s None = tazelik dosyası yok.
    Süreç yoksa ya da dosya eşikten uzun süredir yazılmıyorsa süreç ölü/asılıdır.
    Süreç var ama dosya yoksa (kalp atışı yazmayan eski sürüm) karar verilemez → ok.
    Son restart'tan beri cooldown_s dolmadıysa yeni restart atılmaz (açılış payı + geri çekilme).
    """
    if proc_alive is False:
        reason = "süreç yok"
    elif age_s is not None and age_s > stale_after_s:
        reason = f"{age_s / 60:.0f} dk sessiz" + (" (süreç var → asılı)" if proc_alive else "")
    elif proc_alive is None and age_s is None:
        return "unknown", "süreç sorgusu ve tazelik dosyası okunamadı"
    else:
        return "ok", ""
    if since_restart_s is not None and since_restart_s < cooldown_s:
        return "cooldown", f"{reason} — son restart {since_restart_s / 60:.0f} dk önce, bekleniyor"
    return "restart", reason


def watchdog_cooldown_s(streak: int, base: float = WATCHDOG_COOLDOWN_SEC,
                        cap: float = WATCHDOG_COOLDOWN_MAX_SEC) -> float:
    """Üst üste `streak` denetim restart'ından sonra beklenecek süre (sn)."""
    return min(cap, base * 2 ** max(streak - 1, 0))


def _file_age_s(path: Path) -> float | None:
    """Dosyanın son yazılmasından bu yana sn; yoksa None. Kutuda doğrulandı (10-29):
    bot log'u sürekli açık tutsa da mtime her satırda tazeleniyor."""
    try:
        return max(0.0, time.time() - path.stat().st_mtime)
    except OSError:
        return None


def _watchdog_restart(client, name: str, reason: str, streak: int) -> None:
    log.warning("[watchdog] %s ÖLÜ/ASILI (%s) → ertelemeden yeniden başlatılıyor", name, reason)
    out, rc = restart_target(name, force=True, why=f"watchdog: {reason}")

    def _bump(d: dict) -> None:
        d.setdefault("streak", {})[name] = streak + 1
        d.setdefault("attempts", {})[name] = now_iso()   # rc≠0'da da geri çekilme işlesin
    _update_wd(_bump)
    log.warning("[watchdog] %s restart → rc=%s %s", name, rc, out[:200])
    if client is None:
        return
    try:
        client.table("evolution_commands").insert({
            "host": HOST, "kind": "run_analysis", "requested_by": "watchdog",
            "analysis_id": "watchdog_restart",
            "analysis_name": f"Canlılık denetimi: {name} yeniden başlatıldı ({reason})",
            "payload": {"target": name, "reason": reason, "streak": streak + 1},
            "status": "done" if rc == 0 else "failed",
            "started_at": now_iso(), "finished_at": now_iso(), "return_code": rc,
            "output": out,
        }).execute()
    except Exception as e:
        log.warning("[watchdog] panel izi yazılamadı: %s", e)


def watchdog_tick(client=None) -> dict:
    """Her hedefi gözle → liveness_verdict → gerekiyorsa ertelemeden yeniden başlat.

    Gözlem + eylem RESTART_LOCK altında: oto-güncellemenin kill→start boşluğunu
    "süreç yok" diye okuyup ikinci restart atmaz. WATCHDOG_OFF varken yalnız raporlar.
    """
    global WATCHDOG
    off = (not WATCHDOG_ENABLED) or WATCHDOG_OFF_FILE.exists()
    snap: dict = {"checked_at": now_iso(), "off": off}
    targets = _process_targets()
    with RESTART_LOCK:
        wd = _load_wd()
        for name in WATCHDOG_WATCH:
            spec, t = WATCHDOG_SPECS.get(name), targets.get(name) or {}
            if not spec or "match" not in t:
                continue
            pids = _pids_by_cmdline(t["match"])
            alive = None if pids is None else bool(pids)
            age = _file_age_s(spec["file"])
            last = (wd.get("restarts") or {}).get(name) or {}
            since = [s for s in (_iso_age_s(last.get("at")),
                                 _iso_age_s((wd.get("attempts") or {}).get(name))) if s is not None]
            streak = int((wd.get("streak") or {}).get(name, 0))
            action, reason = liveness_verdict(alive, age, spec["stale_after_s"],
                                              min(since) if since else None,
                                              watchdog_cooldown_s(streak))
            snap[name] = {"alive": {"ok": True, "unknown": None}.get(action, False),
                          "proc": alive, "age_s": age, "action": action, "reason": reason,
                          "last_restart": last.get("at"), "last_restart_why": last.get("why")}
            changed = (WATCHDOG.get(name) or {}).get("action") != action
            if action == "ok":
                if streak:
                    _update_wd(lambda d, n=name: d.setdefault("streak", {}).update({n: 0}))
                    log.info("[watchdog] %s yeniden sağlıklı", name)
            elif action == "restart" and not off:
                _watchdog_restart(client, name, reason, streak)
            elif changed:       # cooldown / unknown / OFF iken restart: her turda değil, değişince yaz
                log.warning("[watchdog] %s: %s%s", name, reason or action,
                            " — WATCHDOG_OFF: yeniden başlatılmıyor" if action == "restart" else "")
    WATCHDOG = snap
    return snap


def _watchdog_meta() -> dict:
    """Kalp atışına süreç canlılığı: denetimin son kararı + TAZE dosya yaşları."""
    def _age(p) -> int | None:
        a = _file_age_s(Path(p)) if p else None
        return round(a) if a is not None else None

    bot, dec = WATCHDOG.get("bot") or {}, WATCHDOG.get("decider") or {}
    return {
        "bot_alive": bot.get("alive"),
        "bot_log_age_s": _age(WATCHDOG_SPECS["bot"]["file"]),
        "bot_last_restart": bot.get("last_restart"),
        "bot_last_restart_why": bot.get("last_restart_why"),
        "decider_alive": dec.get("alive"),
        "decider_hb_age_s": _age(WATCHDOG_SPECS["decider"]["file"]),
        "decider_journal_age_s": _age(getattr(cfg, "DECIDER_JOURNAL", None)),
        "decider_last_restart": dec.get("last_restart"),
        "decider_last_restart_why": dec.get("last_restart_why"),
        "watchdog_off": WATCHDOG.get("off"),
        "watchdog_checked_at": WATCHDOG.get("checked_at"),
    }


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

# Koda gömülü haftalık işler — agent_config.py gitignore'da olduğu için config'e yazılan iş
# push'la taşınamaz. Aynı id config'de varsa config kazanır.
# 2026-10-08: decider öğrenme döngüsü 2026-07-23'ten beri hiç çalışmamıştı (yalnız elle
# tetiklenebiliyordu) → LESSONS_AUTO.md haftalık güncellenir, decider her kararda okur.
BUILTIN_WEEKLY_JOBS = [
    {"id": "decider_distill", "name": "Decider öğrenme (distill_journal, haftalık)",
     "command": "python distill_journal.py", "cwd": "claude_decider", "day": "sun", "hour_utc": 9},
]


def _weekly_jobs() -> list:
    jobs = list(getattr(cfg, "WEEKLY_JOBS", []) or [])
    ids = {j.get("id") for j in jobs}
    return jobs + [j for j in BUILTIN_WEEKLY_JOBS if j["id"] not in ids]


def run_weekly_jobs(client, state: dict) -> None:
    """WEEKLY_JOBS (config) + BUILTIN_WEEKLY_JOBS: [{'id','command','cwd','day','hour_utc'}] — haftada 1 koşar."""
    jobs = _weekly_jobs()
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


def _watchdog_thread() -> None:
    """Canlılık denetimini AYRI iş parçacığında koştur (WATCHDOG_SECONDS'da bir).

    Ana döngü uzun komutlarda bloklanır (claude_task ≤1 sa; restart_bot açık
    pozisyon beklerken ≤2 sa) — kalp atışı 07-20'de aynı sebeple ayrılmıştı.
    Supabase yalnız panel izi için; bağlanamasa da denetim çalışır.
    """
    client = None
    while True:
        try:
            if client is None:
                client = supa()
        except Exception as e:
            log.warning("[watchdog] Supabase bağlantısı yok (denetim yine de koşar): %s", e)
        try:
            watchdog_tick(client)
        except Exception as e:
            log.warning("canlılık denetimi hatası (devam): %s", e)
            client = None
        time.sleep(WATCHDOG_SECONDS)


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
    # Geriye dönük giriş/SL/TP dolumu (bir kerelik) — HEARTBEAT THREAD'İNDEN
    # ÖNCE, ana thread'de SENKRON çalışır. MetaTrader5 paketi thread-safe
    # değildir; ayrı thread'de denendiğinde (v1) MT5 çağrıları sessizce None
    # dönmüştü. ~480 satır × ≤2 MT5 çağrısı — birkaç saniye sürer, kabul
    # edilebilir tek seferlik başlangıç gecikmesi.
    if HAS_MT5:
        backfill_trade_entries(client, state)
        save_state(state)
    threading.Thread(target=_heartbeat_thread, daemon=True, name="heartbeat").start()
    threading.Thread(target=_watchdog_thread, daemon=True, name="watchdog").start()
    last_push = 0.0
    last_trade_push = 0.0
    last_update = time.time()  # açılışta pull zaten taze (start_agent döngüsü)
    while True:
        try:
            # İşlemler AYRI ve DAHA SIK — "MT5'teki işlemler anlık güncellensin"
            # (panel isteği, 2026-08-28). Journal/haftalık işler ucuz değil,
            # onlar eski 5dk'lık ritimde kalır.
            if time.time() - last_trade_push > TRADE_PUSH_SECONDS:
                push_trades(client, state)
                push_fingerprints(client, state)
                save_state(state)
                last_trade_push = time.time()
            if time.time() - last_push > PUSH_SECONDS:
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
