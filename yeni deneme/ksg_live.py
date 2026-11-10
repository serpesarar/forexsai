"""ksg_live.py — NAS100 "kapanış saati gecesi" (KSG) CANLI icra (demo hesap).

KART: backend/data/evolution/go_live_cards/ndx_ksg_gece.json — 6/6, n=1039, net +7,0 bp/gece, karşı kol −6,1 bp.
Kanıt: research/ndx_kapi_20261110/ (PROTOCOL.md EK-5/EK-6, RAPOR.md). Sınıf C+: etki 2020'den beri (7/7 yıl), 2018-19 eksi.
KULLANICI KARARI 2026-11-10: "bunu canlıya bağla, gölgeye bağlama". Lot: kural_katalogu (0.5).
Kapatma: config.KSG_LIVE = False. Durdurma ölçütü (önceden yazılı): n=60 gecede ort. net < 0 → kapat.

KURAL (donduruldu; değiştirmek kanıtı geçersiz kılar):
  O15 = bugünkü 15:00 ET M30 barının açılışı, O16 = 16:00 ET barının açılışı.  O16/O15 − 1 < 0  →  16:00'da AL.
  Çıkış: sonraki işlem gününün 09:30 ET'si (Cuma girişi Pazartesi 09:30'da kapanır). Stop/TP yok.
  Seans kısa günse (09:30–16:00 arası < 12 M30 barı) işlem yok — araştırma da bu günleri dışlıyor.
  TEK FARK (C3b ile aynı): broker tarafında ACİL DURUM SL'i (varsayılan %6, `KSG_LIVE_EMERGENCY_SL`). Araştırmadaki en kötü
  gece −%4,0 (bar-low bazlı −%6,1) olduğundan örneklemde net sonucu neredeyse değiştirmez; bot ölürse sınırsız zarara karşı sigorta.
  Giriş gecikmesi: 16:00 barı açılışından en çok 10 dk sonra (araştırma: 16:01 +5,1, 16:05 +5,2, 16:14 +4,5 bp — kenar sürer).
"""
from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import c3b_shadow as sh          # TZ="US", MARKET="NDX.INDX" (yalnız sabitler)
import caprev_shadow as cs
import kural_katalogu as kk

RULE = "KSG"
HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "ksg_live_state.json"
POLL_EVERY_S = 20
MIN_SIGNAL_BAR = 15 * 60          # 15:00 ET
MIN_ENTRY_BAR = 16 * 60           # 16:00 ET
MIN_OPEN = 9 * 60 + 30            # 09:30 ET — çıkış anı ve seans başı
MIN_SESSION_BARS = 12             # 09:30–16:00 arası M30 bar sayısı (tam seans 13; kısa gün elenir)
MAX_LATE_S = 600
EMERGENCY_SL = 0.06
FETCH_M30 = 120

_last_poll = 0.0
_last_exit_poll = 0.0


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def find_signal(bars: list[dict], today: date) -> dict | None:
    """bars: [{t (UTC epoch, bar açılışı), open, high, low, close}]. Bugünün 16:00 barı görünmüşse ve
    O16/O15 − 1 < 0 ise {o15, o16, ret_bp, t16} döner; aksi halde None. Kısa seans günü → None."""
    o15 = o16 = t16 = None
    n_session = 0
    for b in bars:
        d, m, wd = cs.to_local(b["t"], sh.TZ)
        if d != today or wd >= 5:
            continue
        if MIN_OPEN <= m < MIN_ENTRY_BAR:
            n_session += 1
        if m == MIN_SIGNAL_BAR:
            o15 = b["open"]
        elif m == MIN_ENTRY_BAR:
            o16, t16 = b["open"], b["t"]
    if o15 is None or o16 is None or o15 <= 0 or n_session < MIN_SESSION_BARS:
        return None
    ret_bp = (o16 / o15 - 1.0) * 1e4
    if ret_bp >= 0.0:
        return None
    return {"o15": o15, "o16": o16, "ret_bp": round(ret_bp, 2), "t16": t16}


def exit_due(entry_day: date, now_day: date, now_min: int, now_wd: int) -> bool:
    """Giriş gününden SONRAKİ bir işlem günü (hafta içi) ve yerel saat ≥ 09:30 ise çıkış zamanı."""
    return now_day > entry_day and now_wd < 5 and now_min >= MIN_OPEN


def stop_price(ask: float, digits: int, frac: float = EMERGENCY_SL) -> float:
    return round(ask * (1.0 - frac), digits)


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"last_d": None}


def _save_state(st: dict) -> None:
    kk.save_json(STATE_FILE, st)


# ═════════════════════════ çıkış (ana döngüde frenden ÖNCE) ═════════════════════════

def manage_exits(mt5, config, log, send_order, offset_fn, resolve_symbol, now: float | None = None) -> None:
    """Açık KSG pozisyonlarını ertesi işlem günü 09:30 ET'de kapatır. Broker SL'i acil durum içindir."""
    global _last_exit_poll
    now = time.time() if now is None else now
    if now - _last_exit_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_exit_poll = now
    sym = resolve_symbol(sh.MARKET)
    if not sym:
        return
    now_day, now_min, now_wd = cs.to_local(now, sh.TZ)
    for pos in kk.open_positions(mt5, config, RULE, sym):
        entry_day = cs.to_local(pos.time - offset_fn(sym), sh.TZ)[0]
        if exit_due(entry_day, now_day, now_min, now_wd):
            kk.close(mt5, config, log, send_order, RULE, pos, "ertesi seans 09:30 ET çıkışı")


# ═════════════════════════ giriş ═════════════════════════

def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    """Bot ana döngüsünden her tarama çağrılır. Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_poll = now
    today, mloc, wd = cs.to_local(now, sh.TZ)
    if wd >= 5 or not (MIN_ENTRY_BAR <= mloc <= MIN_ENTRY_BAR + MAX_LATE_S // 60):
        return
    st = _load_state()
    if st.get("last_d") == str(today):
        return
    sym = resolve_symbol(sh.MARKET)
    if not sym:
        return
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M30, 0, FETCH_M30)     # 0 → 16:00 barı açılışı görünür
    if rates is None or len(rates) < 40:
        return
    bars = cs._m15_utc(rates, offset_fn(sym))
    if not any(cs.to_local(b["t"], sh.TZ)[:2] == (today, MIN_ENTRY_BAR) for b in bars):
        return                                                                 # 16:00 barı henüz yok
    st["last_d"] = str(today)                                                  # günde ≤ 1 karar (reddedilse de)
    _save_state(st)
    sig = find_signal(bars, today)
    if sig is None:
        return
    late = now - sig["t16"]
    rec = {"day": str(today), "o15": sig["o15"], "o16": sig["o16"], "ret_bp": sig["ret_bp"], "latency_s": round(late, 1)}
    if late > MAX_LATE_S:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "geç tespit", **rec})
        return
    if kk.open_positions(mt5, config, RULE, sym):
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "açık KSG pozisyonu var (tek pozisyon)", **rec})
        return
    _enter(mt5, config, log, sym, rec, send_order, mk_comment, autotrading_ok, log_trade)


def _enter(mt5, config, log, sym, rec, send_order, mk_comment, autotrading_ok, log_trade) -> None:
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return
    ask = round(tick.ask, info.digits)
    lot = kk.lot_of(config, RULE)
    sl = stop_price(ask, info.digits, float(getattr(config, "KSG_LIVE_EMERGENCY_SL", EMERGENCY_SL)))
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": f"yoğunlaşma tavanı {open_lot}+{lot}>{cap}", **rec})
        log.warning("KSG atlandı: %s üzerinde açık kural lotu %.2f + %.2f > tavan %.2f", sym, open_lot, lot, cap)
        return
    if not autotrading_ok():
        log.error("KSG AutoTrading KAPALI — emir gönderilmedi")
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "autotrading kapalı", **rec})
        return
    ok, ticket, rc = kk.buy(mt5, config, log, send_order, mk_comment, RULE, sym, lot, ask, sl, 0.0, "KSG NDX gece")
    kk.append_event({"kind": "entry", "rule": RULE, "ok": ok, "retcode": rc, "ticket": ticket, "ask": ask, "sl": sl,
                     "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ KSG emir reddedildi retcode=%s", rc)
        return
    kk.announce_open(log, RULE, f"{sym} BUY {lot} lot @ {ask} · acil SL {sl} · son saat {rec['ret_bp']} bp · ticket {ticket}",
                     {"gecikme_s": rec["latency_s"]})
    log_trade("LIVE", "NDX.INDX:BUY:KSG", sym, "BUY", ask, 0.0, sl, ["ksg"], f"ticket={ticket}")
