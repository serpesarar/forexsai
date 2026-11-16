"""orb_vix_live.py — NDX açılış aralığı kırılımı × VIX (ORB×VIX) CANLI icra (demo hesap).

KART: backend/data/evolution/go_live_cards/ndx_orb_vix.json — 6/6, n=152, isabet %48,7, ort +0,295R (2026 zayıf +0,10R).
KULLANICI KARARI 2026-11-08: kendi lotuyla canlıya bağla (kural_katalogu: 0.75). Kapatma: config.ORB_VIX_LIVE = False.

KURAL (orb_vix_shadow ile BİREBİR; tetik fonksiyonu oradan alınır — yalnız "hi" kolu, yani önceki işlem gününün son VIX'i ≥ 18,4):
  09:30–09:45 ET ilk 15 dk aralığı (3 M5 bar); ilk M5 kapanışı aralık tepesinin üstünde (bar bitişi ≤ 15:30 ET)
  → hemen market BUY. SL = aralık ortası, TP = giriş + 3×risk (2026-11-16'ya kadar 2R), 15:55 ET zaman çıkışı. Günde ≤ 1, kısa yok.
  TP 3R GEREKÇESİ (research/ndx_10y_1m_20261116, Dukascopy 1m 2018-01→2026-11): 2R çıkış eğrisinin en kötü noktası; 3R/4R/5R/TP'siz
  hepsi iki dönemde de üstün. TP 3R kartı 6/6: n 741, ort +0,199R (2R: +0,101), P 1,00, yarılar +0,19/+0,21, spr×1,5 +0,18, 9/9 yıl artı.
  Eski davranış: config.ORB_VIX_LIVE_TP_R = 2.0.
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
TP_R_LIVE = 3.0                  # 2026-11-16: 2R → 3R (ndx_10y_1m_20261116 EK1-a, kart 6/6); ezme config.ORB_VIX_LIVE_TP_R

_last_poll = 0.0


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"fired": {}}


def _save_state(st: dict) -> None:
    kk.save_json(STATE_FILE, st)


def plan(trig: dict, ask: float, vix_prev: float | None, max_risk_frac: float = MAX_RISK_FRAC,
         tp_r: float = TP_R_LIVE) -> tuple[dict | None, str | None]:
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
    return {"sl": stop, "tp": ask + tp_r * risk, "risk": risk, "tp_r": tp_r}, None


def anatomy_1m(bars: list[dict], today: date, now_utc: float) -> dict:
    """GÖLGE ETİKETİ (research/mum_anatomi_1m_20261117, sınıf C): 09:30 ET → şimdiye kadar KAPANMIŞ 1m barların anatomisi.
    f_run = sona biten ardışık yeşil bar sayısı, f_uw5 = son 5 barda üst fitil / aralık, f_clv = ort. kapanış konumu,
    f_flip = renk değişim oranı. Karar vermez; yalnız olay kaydına yazılır (ileri karne)."""
    sel = [b for b in bars if cs.to_local(b["t"], sh.TZ)[0] == today and cs.to_local(b["t"], sh.TZ)[1] >= sh.OPEN_MIN
           and b["t"] + 60 <= now_utc]
    if len(sel) < 5:
        return {}
    up = [b["close"] > b["open"] for b in sel]
    run = 0
    for x in reversed(up):
        if not x:
            break
        run += 1
    last = sel[-5:]
    rng5 = sum(b["high"] - b["low"] for b in last)
    uw5 = sum(b["high"] - max(b["open"], b["close"]) for b in last) / rng5 if rng5 > 0 else None
    clv = [(b["close"] - b["low"]) / (b["high"] - b["low"]) for b in sel if b["high"] > b["low"]]
    flips = sum(1 for a, b in zip(up, up[1:]) if a != b) / (len(up) - 1)
    return {"f_run": run, "f_uw5": None if uw5 is None else round(uw5, 4),
            "f_clv": round(sum(clv) / len(clv), 4) if clv else None, "f_flip": round(flips, 4), "n_1m": len(sel)}


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
    try:                                                                          # gölge etiketi; hata emri etkilemez
        m1 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, 450)
        if m1 is not None and len(m1):
            rec["anatomi_1m"] = anatomy_1m(cs._m15_utc(m1, offset_fn(sym)), today, now)
    except Exception:
        pass
    if late > MAX_LATE_S:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "geç tespit", **rec})
        return
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return
    ask = round(tick.ask, info.digits)
    pl, why = plan(trig, ask, vix_prev, float(getattr(config, "ORB_VIX_LIVE_MAX_RISK_FRAC", MAX_RISK_FRAC)),
                   float(getattr(config, "ORB_VIX_LIVE_TP_R", TP_R_LIVE)))
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
                     "tp": tp, "tp_r": pl["tp_r"], "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ ORB×VIX emir reddedildi retcode=%s", rc)
        return
    kk.announce_open(log, RULE, f"{sym} BUY {lot} lot @ {ask} · SL {sl} · TP {tp} ({pl['tp_r']:g}R) · VIX(dün) {rec['vix_prev']:.1f} · ticket {ticket}",
                     {"gecikme_s": rec["latency_s"]})
    log_trade("LIVE", "NDX.INDX:BUY:ORBVIX", sym, "BUY", ask, tp, sl, ["orbvix"], f"ticket={ticket}")
