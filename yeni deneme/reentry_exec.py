"""reentry_exec.py — kapanış sonrası yeniden giriş (re-entry).

KURAL: bot bir pozisyonu kapattığında (TP veya SL), AYNI YÖNDE bir kez daha
girilir — TP sonrası +5 dk, SL sonrası +1 dk. Zincirleme YOK (bir ana işlemden
en fazla bir re-entry doğar; re-entry'den re-entry doğmaz).

KANIT (bar-bar 1m replay, üç kapılı sınav — `1MDATA/mt5_islem_analizi/
08_reentry_testi.py` + `backend/research/box_reentry_oos.py`):

              bağımsızlık   eşit-risk alfa   plasebo
  iç-örneklem    %55 ✅        +12.462$ ✅     p=0.000 ✅
  DIŞ-örneklem   %53 ✅         +3.850$ ✅     p=0.187 ❌

Piramit önerisinden farkı: re-entry ana işlem KAPANDIKTAN sonra açılır, yani
aynı bahsin kopyası değildir (piramitte sonuç örtüşmesi %94'tü, burada %53) ve
eşit tepe riske ölçeklenmiş taban akışı İKİ dönemde de geçiyor. Ama plasebo
kapısı dış-örneklemde geçilemedi → **varsayılan GÖLGE**.

⚠️ VARSAYILAN `REENTRY_MODE="shadow"`: hiçbir emir gönderilmez, yalnız "ne
açardım + sonucu ne olurdu" kaydı tutulur. 2-4 hafta gölge verisi biriktikten
sonra `scripts/bot_flags.py reentry live` ile açılır.

ÇAKIŞMA ÇÖZÜMLERİ (canlı modda):
  * AYRI MAGIC (+6) → `MAX_OPEN_PER_SCOPE=1` slot kilidini tetiklemez.
  * `MAX_TOTAL_POSITIONS` global tavanına SAYILIR (risk tavanı korunur).
  * Faz-1 zaman pencerelerine TABİ (ASIA/Cuma yasağı re-entry'yi de kapatır).
  * MOD-E probasyonundan MUAF (re-entry'nin kendi zamanlaması var).
  * `trade_manager` BE/trail kapsamı DIŞINDA — kanıt düz TP/SL ile ölçüldü.
  * Günlük zarar limiti ve AutoTrading kontrolü normal akışta uygulanır.
"""
from __future__ import annotations

import time
from typing import Callable, Optional

import config
import phase_rules as pr

# ana işlem kapanışından sonra beklenecek dakika
GEC_TP, GEC_SL = 5, 1

_pending: list[dict] = []          # bekleyen re-entry niyetleri
_gorulen: set[int] = set()         # işlenmiş ana pozisyon ticket'ları
_uretilen: set[int] = set()        # re-entry doğurmuş ana ticket'lar (zincir engeli)


def mode() -> str:
    """'off' | 'shadow' | 'live'."""
    return str(pr.flag(config, "REENTRY_MODE")).lower()


def is_enabled(forexsai_sym: str) -> bool:
    if mode() == "off":
        return False
    return forexsai_sym in pr.flag(config, "REENTRY_SYMBOLS")


def magic() -> int:
    return int(getattr(config, "MAGIC_NUMBER", 52890969)) + 6


# ── saf karar çekirdeği (test edilebilir) ──────────────────────────────────

def gecikme_dk(ana_kazandi: bool, config_=None) -> int:
    """TP sonrası +5 dk, SL sonrası +1 dk (kanıt bu ikilide ölçüldü)."""
    if ana_kazandi:
        return int(pr.flag(config_, "REENTRY_DELAY_TP_MIN"))
    return int(pr.flag(config_, "REENTRY_DELAY_SL_MIN"))


def hazir_mi(elapsed_sec: float, ana_kazandi: bool, config_=None) -> tuple[str, str]:
    """('wait' | 'go' | 'cancel', sebep). Bayat niyet iptal edilir."""
    gec = gecikme_dk(ana_kazandi, config_)
    max_bekle = float(pr.flag(config_, "REENTRY_MAX_WAIT_MIN"))
    if elapsed_sec > max_bekle * 60:
        return "cancel", f"bayat ({elapsed_sec/60:.0f}dk > {max_bekle:.0f}dk)"
    if elapsed_sec < gec * 60:
        return "wait", f"{elapsed_sec/60:.1f}/{gec} dk"
    return "go", f"{gec} dk doldu ({'TP' if ana_kazandi else 'SL'} sonrası)"


def zincir_engeli(ana_magic: int, config_=None) -> bool:
    """Re-entry'den re-entry doğmaz — ana işlem zaten bir re-entry ise dur."""
    return ana_magic == int(getattr(config, "MAGIC_NUMBER", 52890969)) + 6


# ── kapanan pozisyonları yakala ────────────────────────────────────────────

def tara(mt5, log, resolve_symbol) -> None:
    """Bot magic'lerine ait YENİ kapanmış pozisyonları bul, kuyruğa al."""
    if mode() == "off":
        return
    try:
        import trade_manager
        magics = trade_manager._all_bot_magics()
    except Exception:
        magics = {getattr(config, "MAGIC_NUMBER", 52890969)}
    for fxs in pr.flag(config, "REENTRY_SYMBOLS"):
        sym = resolve_symbol(fxs)
        if not sym:
            continue
        acik = {p.ticket for p in (mt5.positions_get(symbol=sym) or [])}
        try:
            frm = __import__("datetime").datetime.now() - __import__("datetime").timedelta(hours=6)
            deals = mt5.history_deals_get(frm, __import__("datetime").datetime.now()) or []
        except Exception:
            continue
        for d in deals:
            if d.symbol != sym or d.entry not in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY):
                continue
            pid = int(d.position_id)
            if pid in _gorulen or pid in acik:
                continue
            _gorulen.add(pid)
            if int(d.magic) not in magics or zincir_engeli(int(d.magic)):
                continue
            if pid in _uretilen:
                continue
            kazandi = float(d.profit) > 0
            yon = "SELL" if d.type == mt5.DEAL_TYPE_BUY else "BUY"   # çıkış tersidir
            _pending.append({
                "ana_ticket": pid, "fx": fxs, "sym": sym, "dir": yon,
                "kapanis_px": float(d.price), "kazandi": kazandi,
                "t0": time.time(),
            })
            _uretilen.add(pid)
            log.info("[RE-ENTRY] ana #%s %s ile kapandı (%s) → %d dk sonra %s "
                     "değerlendirilecek [%s]", pid, "TP" if kazandi else "SL",
                     yon, gecikme_dk(kazandi, config), yon, mode().upper())


# ── kuyruğu işle ───────────────────────────────────────────────────────────

def isle(mt5, log, opener: Callable, log_gate_skip: Optional[Callable] = None,
         shadow_record: Optional[Callable] = None,
         guard: Optional[Callable] = None) -> None:
    """Her taramada çağrılır.

    opener(fx, sym, direction, magic) → canlı modda emri gönderir.
    guard(item) → (ok, sebep); tavan/pencere kontrolü.
    """
    if not _pending:
        return
    now = time.time()
    biten = []
    for p in list(_pending):
        try:
            verdict, why = hazir_mi(now - p["t0"], p["kazandi"], config)
            if verdict == "wait":
                continue
            biten.append(p)
            if verdict == "cancel":
                log.info("[RE-ENTRY] #%s iptal — %s", p["ana_ticket"], why)
                continue

            # ── Faz-1 zaman penceresi + tavan kontrolleri ──
            if guard is not None:
                ok, sebep = guard(p)
                if not ok:
                    log.info("[RE-ENTRY] #%s açılmadı — %s", p["ana_ticket"], sebep)
                    if log_gate_skip:
                        log_gate_skip(f"{p['fx']}:{p['dir']}:REENTRY", p["sym"],
                                      p["fx"], p["dir"], p["kapanis_px"],
                                      "reentry_guard", extra={"why": sebep})
                    continue

            tick = mt5.symbol_info_tick(p["sym"])
            px = (tick.ask if p["dir"] == "BUY" else tick.bid) if tick else p["kapanis_px"]

            if mode() == "shadow":
                log.info("[RE-ENTRY][GÖLGE] #%s → %s %s @%.2f açardım (%s)",
                         p["ana_ticket"], p["fx"], p["dir"], px, why)
                if shadow_record:
                    shadow_record(f"{p['fx']}:{p['dir']}:REENTRY", p["fx"], p["sym"],
                                  p["dir"], "reentry", "would_open", px,
                                  extra={"ana_ticket": p["ana_ticket"],
                                         "ana_sonuc": "TP" if p["kazandi"] else "SL",
                                         "gecikme_dk": gecikme_dk(p["kazandi"], config)})
                continue

            log.info("[RE-ENTRY][CANLI] #%s → %s %s @%.2f (%s)",
                     p["ana_ticket"], p["fx"], p["dir"], px, why)
            opener(p["fx"], p["sym"], p["dir"], magic())
        except Exception as exc:
            log.warning("[RE-ENTRY] #%s değerlendirilemedi (%s) → iptal",
                        p.get("ana_ticket"), exc)
            if p not in biten:
                biten.append(p)
    for p in biten:
        if p in _pending:
            _pending.remove(p)
    if len(_gorulen) > 5000:
        _gorulen.clear(); _uretilen.clear()
