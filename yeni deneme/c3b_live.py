"""c3b_live.py — NDX RSI2 geri dönüşü (C3b) CANLI icra (demo hesap).

KART: backend/data/evolution/go_live_cards/ndx_c3b_rsi2_upexit.json — 6/6, n=155, isabet %78,1, ort +65 bp, 11/11 yıl artı.
KULLANICI KARARI 2026-11-08: "pozitif olanların hepsini kendilerine özel lotla canlıya bağla". Lot: kural_katalogu (2.0).
Kapatma: config.C3B_LIVE = False.

KURAL (c3b_shadow ile BİREBİR; sinyal ve seri fonksiyonları oradan alınır):
  S = 15:30 ET M30 barından önceki barın kapanışı, E = 15:30 barının açılışı. RSI2(S serisi) < 10 → E'de uzun.
  Çıkış: ilk S_t > S_{t−1} günü 15:30 açılışında; en geç 5 işlem günü sonra. Tek pozisyon; çıkış günü yeni sinyal
  varsa aynı açılışta yeniden girilir. TP yok.
  TEK FARK: kartta stop yok; broker tarafında ACİL DURUM SL'i (varsayılan %10, `C3B_LIVE_EMERGENCY_SL`) konur — geçmişteki en
  kötü işlem −%6,8 olduğundan örneklemde hiçbir işlemi değiştirmez; yalnız bot ölürse sınırsız zarara karşı sigortadır.
"""
from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import c3b_shadow as sh
import caprev_shadow as cs
import kural_katalogu as kk

RULE = "C3B"
HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "c3b_live_state.json"
POLL_EVERY_S = 30
EMERGENCY_SL = 0.10

_last_poll = 0.0


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"last_d": None, "pos": {}}


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def should_exit(series: list[dict], entry_idx: int, i: int) -> str | None:
    """Pozisyon çıkış nedeni: 'yukselis' (girişten sonra herhangi bir gün S_t > S_{t−1}), 'sure' (≥ MAX_HOLD) ya da None.
    Bot kapalıyken kaçan yükseliş günü de sayılır (geç çıkış, kayıtta gecikme görünür)."""
    for k in range(entry_idx + 1, i + 1):
        if series[k]["S"] > series[k - 1]["S"]:
            return "yukselis"
    return "sure" if i - entry_idx >= sh.MAX_HOLD else None


def _entry_index(series: list[dict], d_iso: str) -> int | None:
    for k, s in enumerate(series):
        if str(s["d"]) == d_iso:
            return k
    return None


def manage_and_enter(mt5, config, log, series: list[dict], today: date, st: dict, now: float, sym: str, off: int,
                     send_order, mk_comment, autotrading_ok, log_trade) -> None:
    """Bugünün 15:30 barı göründüğünde: önce çıkış, sonra giriş (tek pozisyon)."""
    i = len(series) - 1
    day = series[i]
    rsi = sh.rsi2([s["S"] for s in series])
    for pos in kk.open_positions(mt5, config, RULE, sym):
        meta = st["pos"].get(str(pos.ticket))
        if meta is None:       # bot yeniden başladı: giriş gününü pozisyon zamanından türet
            meta = {"d": str(cs.to_local(pos.time - off, sh.TZ)[0])}
        k0 = _entry_index(series, meta["d"])
        why = "giriş günü seride yok" if k0 is None else should_exit(series, k0, i)
        if why and kk.close(mt5, config, log, send_order, RULE, pos, why):
            st["pos"].pop(str(pos.ticket), None)
    if rsi[i] >= sh.RSI_TH:
        return
    late = now - day["t"]
    rec = {"day": str(day["d"]), "rsi2": round(rsi[i], 2), "S": day["S"], "E": day["E"], "latency_s": round(late, 1)}
    if kk.open_positions(mt5, config, RULE, sym):
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "açık C3b pozisyonu var (tek pozisyon)", **rec})
        return
    if late > sh.MAX_LATE_S:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "geç tespit", **rec})
        return
    _enter(mt5, config, log, sym, rec, st, now, send_order, mk_comment, autotrading_ok, log_trade)


def _enter(mt5, config, log, sym, rec, st, now, send_order, mk_comment, autotrading_ok, log_trade) -> None:
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return
    ask = round(tick.ask, info.digits)
    lot = kk.lot_of(config, RULE)
    sl = round(ask * (1 - float(getattr(config, "C3B_LIVE_EMERGENCY_SL", EMERGENCY_SL))), info.digits)
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": f"yoğunlaşma tavanı {open_lot}+{lot}>{cap}", **rec})
        log.warning("C3b atlandı: %s üzerinde açık kural lotu %.2f + %.2f > tavan %.2f", sym, open_lot, lot, cap)
        return
    if not autotrading_ok():
        log.error("C3b AutoTrading KAPALI — emir gönderilmedi")
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "autotrading kapalı", **rec})
        return
    ok, ticket, rc = kk.buy(mt5, config, log, send_order, mk_comment, RULE, sym, lot, ask, sl, 0.0, "C3b NDX RSI2")
    kk.append_event({"kind": "entry", "rule": RULE, "ok": ok, "retcode": rc, "ticket": ticket, "ask": ask, "sl": sl,
                     "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ C3b emir reddedildi retcode=%s", rc)
        return
    st["pos"][str(ticket)] = {"d": rec["day"], "entry_t": now}
    kk.announce_open(log, RULE, f"{sym} BUY {lot} lot @ {ask} · acil SL {sl} · RSI2={rec['rsi2']} · ticket {ticket}",
                     {"gecikme_s": rec["latency_s"]})
    log_trade("LIVE", "NDX.INDX:BUY:C3B", sym, "BUY", ask, 0.0, sl, ["c3b"], f"ticket={ticket}")


def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    """Bot ana döngüsünden her tarama çağrılır (shadow'dan SONRA: VIX geçmişini o günceller). Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_poll = now
    today, mloc, wd = cs.to_local(now, sh.TZ)
    if wd >= 5 or mloc < sh.ENTRY_MIN:
        return
    st = _load_state()
    if st.get("last_d") == str(today):
        return
    sym = resolve_symbol(sh.MARKET)
    if not sym:
        return
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M30, 0, sh.FETCH_M30)    # 0 → 15:30 barı açılışı görünür
    if rates is None or len(rates) < 100:
        return
    off = offset_fn(sym)
    series = sh.daily_series(cs._m15_utc(rates, off))
    if not series or series[-1]["d"] != today:
        return                                                                  # bugünün 15:30 barı henüz yok
    manage_and_enter(mt5, config, log, series, today, st, now, sym, off, send_order, mk_comment, autotrading_ok, log_trade)
    st["last_d"] = str(today)
    _save_state(st)
