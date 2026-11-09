"""orb_vix_live.py — NDX açılış aralığı kırılımı × VIX (ORB×VIX) CANLI icra (demo hesap).

KART: backend/data/evolution/go_live_cards/ndx_orb_vix.json — 6/6, n=152, isabet %48,7, ort +0,295R (2026 zayıf +0,10R).
KULLANICI KARARI 2026-11-08: kendi lotuyla canlıya bağla (kural_katalogu: 0.75). Kapatma: config.ORB_VIX_LIVE = False.

KURAL (orb_vix_shadow ile BİREBİR; tetik fonksiyonu oradan alınır — yalnız "hi" kolu, yani önceki işlem gününün son VIX'i ≥ 18,4):
  09:30–09:45 ET ilk 15 dk aralığı (3 M5 bar); ilk M5 kapanışı aralık tepesinin üstünde (bar bitişi ≤ 15:30 ET)
  → hemen market BUY. SL = aralık ortası, TP = giriş + 2×risk, 15:55 ET zaman çıkışı. Günde ≤ 1, kısa yok.
  Risk < giriş × %0,05 → işlem yok (kart). VIX geçmişi yoksa ('unknown' kol) işlem açılmaz.
  EK GÜVENLİK (kartta yok; örneklemde tetiklenmez): risk > giriş × %2 ise işlem yok (`ORB_VIX_LIVE_MAX_RISK_FRAC`).
"""
from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import caprev_shadow as cs
import kural_katalogu as kk
import orb_vix_shadow as sh

RULE = "ORBVIX"
HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "orb_vix_live_state.json"
POLL_EVERY_S = 30
MAX_LATE_S = 300
MAX_RISK_FRAC = 0.02

_last_poll = 0.0


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"fired": {}}


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def plan(trig: dict, ask: float, vix_prev: float | None, max_risk_frac: float = MAX_RISK_FRAC) -> tuple[dict | None, str | None]:
    """(emir planı, ret nedeni). Saf fonksiyon: kart kuralları + ek risk tavanı."""
    if vix_prev is None:
        return None, "VIX geçmişi yok (kol belirsiz)"
    if vix_prev < sh.VIX_MIN:
        return None, f"VIX(dün) {vix_prev:.1f} < {sh.VIX_MIN} (alt kol)"
    stop = trig["stop"]
    risk = ask - stop
    if risk <= sh.MIN_RISK_FRAC * ask:
        return None, "risk çok dar (kart: olay yok)"
    if risk > max_risk_frac * ask:
        return None, f"risk {risk:.1f} > fiyatın %{100 * max_risk_frac:.0f}'si (ek güvenlik)"
    return {"sl": stop, "tp": ask + sh.TARGET_R * risk, "risk": risk}, None


def manage_exits(mt5, config, log, send_order, offset_fn, resolve_symbol, now: float | None = None) -> None:
    """15:55 ET zaman çıkışı (ana döngüde frenden ÖNCE çağrılır); SL/TP broker tarafında."""
    now = time.time() if now is None else now
    sym = resolve_symbol(sh.MARKET)
    if not sym or not kk.is_enabled(config, RULE):
        return
    for pos in kk.open_positions(mt5, config, RULE, sym):
        day = cs.to_local(pos.time - offset_fn(sym), sh.TZ)[0]
        if now >= sh.session_end_utc(day):
            kk.close(mt5, config, log, send_order, RULE, pos, "15:55 ET zaman çıkışı")


def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_poll = now
    today, mloc, wd = cs.to_local(now, sh.TZ)
    key = f"{sh.MARKET}|{today}"
    st = _load_state()
    if wd >= 5 or not (sh.OPEN_MIN + sh.OR_MIN <= mloc < sh.SESSION_END_MIN) or key in st["fired"]:
        return
    sym = resolve_symbol(sh.MARKET)
    if not sym:
        return
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M5, 1, sh.FETCH_M5)       # 1 → koşan bar hariç
    if rates is None or len(rates) == 0:
        return
    trig = sh.find_trigger(sh.session_bars(cs._m15_utc(rates, offset_fn(sym)), today))
    if trig is None:
        return
    st["fired"][key] = True                                                       # günde ≤ 1 (reddedilse de)
    st["fired"] = {k: v for k, v in st["fired"].items() if k.split("|")[1] >= str(date.fromordinal(today.toordinal() - 5))}
    _save_state(st)
    vix_prev = cs.vix_features(sh._load_state().get("vix_hist", {}), today, None)["vix_prev"]
    late = now - (trig["trig_t"] + sh.BAR_MIN * 60)
    rec = {"day": str(today), "oh": trig["oh"], "ol": trig["ol"], "trig_close": trig["trig_close"], "vix_prev": vix_prev,
           "latency_s": round(late, 1)}
    if late > MAX_LATE_S:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "geç tespit", **rec})
        return
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return
    ask = round(tick.ask, info.digits)
    pl, why = plan(trig, ask, vix_prev, float(getattr(config, "ORB_VIX_LIVE_MAX_RISK_FRAC", MAX_RISK_FRAC)))
    if pl is None:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": why, **rec})
        log.info("ORB×VIX tetik ama işlem yok: %s", why)
        return
    _enter(mt5, config, log, sym, ask, pl, rec, send_order, mk_comment, autotrading_ok, log_trade, info.digits)


def _enter(mt5, config, log, sym, ask, pl, rec, send_order, mk_comment, autotrading_ok, log_trade, digits) -> None:
    lot = kk.lot_of(config, RULE)
    sl, tp = round(pl["sl"], digits), round(pl["tp"], digits)
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": f"yoğunlaşma tavanı {open_lot}+{lot}>{cap}", **rec})
        log.warning("ORB×VIX atlandı: açık kural lotu %.2f + %.2f > tavan %.2f", open_lot, lot, cap)
        return
    if not autotrading_ok():
        log.error("ORB×VIX AutoTrading KAPALI — emir gönderilmedi")
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "autotrading kapalı", **rec})
        return
    ok, ticket, rc = kk.buy(mt5, config, log, send_order, mk_comment, RULE, sym, lot, ask, sl, tp, "ORBVIX NDX")
    kk.append_event({"kind": "entry", "rule": RULE, "ok": ok, "retcode": rc, "ticket": ticket, "ask": ask, "sl": sl,
                     "tp": tp, "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ ORB×VIX emir reddedildi retcode=%s", rc)
        return
    kk.announce_open(log, RULE, f"{sym} BUY {lot} lot @ {ask} · SL {sl} · TP {tp} (2R) · VIX(dün) {rec['vix_prev']:.1f} · ticket {ticket}",
                     {"gecikme_s": rec["latency_s"]})
    log_trade("LIVE", "NDX.INDX:BUY:ORBVIX", sym, "BUY", ask, tp, sl, ["orbvix"], f"ticket={ticket}")
