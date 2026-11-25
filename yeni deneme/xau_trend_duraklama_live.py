"""xau_trend_duraklama_live.py — XAUUSD "trend içinde duraklamayı al" (MG-4 G0) CANLI icra (demo).

KULLANICI KARARI 2026-11-25: "Doğrudan canlıya al" (2010–17 KASA doğrulaması YAPILMADAN). Kaynak: MQL5 Market EA "My AI Gold" canlı
sinyalinin (2389616) davranışından çözüldü, geliştirildi (research/myaigold_20261125, MG-1…5). Kod/ex5 kullanılmadı.
KANIT (Dukascopy XAU 1m, saat başı 1m açılışında giriş + yıl×saat spread + 0,08 $/ons):
  KEŞİF 2018–21 n 231 +0,081 R, plaseboya +0,089 R (P 0,987). TEST 2022-01 → 2026-05-18 (tek atış) n 308 (ayda ~6) +0,096 R, isabet %76,
  P 0,999, 2022 +0,04 / 2023 +0,09 / 2024 +0,05 / 2025 +0,20 / 2026 +0,08 R, spread ×1,5 +0,081, en iyi 10 gün hariç +0,067. Kart 6/6:
  backend/data/evolution/go_live_cards/xau_trend_duraklama_al.json.
UYARILAR: yalnız AL — plaseboya fark P 0,951 (sınırda, altın boğası); kör dönem 2026-05→11 (altın −%20) n 26 −0,06 R; canlı R0B ve SOMA
E4X3/E2 ile aynı yön/varlık (ortak lot tavanı). Durdurma ölçütü (önceden yazılı): canlı n=60 işlemde ort. R < 0 → config.XAU_TDA_LIVE = False.

KURAL (research/myaigold_20261125/src/mg4.py + mg5.py G0 ile birebir; H1 kovaları UTC saat başı — sunucu ofseti tam saat olduğundan
broker H1 mumları aynı kovalar): karar anı u = UTC saat başı; kullanılan = u'dan önce KAPANMIŞ son H1 mumu (j):
  ATR = Wilder ATR14(H1), EMA50(H1 kapanış), r12 = (c_j − c_{j−12}) / ATR, r4 = (c_j − c_{j−4}) / ATR,
  konum24 = (c_j − min L_{j−23..j}) / (max H − min L).
  AL ⇔ r12 ≥ 1,0 ∧ |r4| ≤ 0,5 ∧ (c_j − EMA50) / ATR ≥ 1,0 ∧ 0,55 ≤ konum24 ≤ 0,95 ∧ UTC saat(u) ∈ {07,08,12,15,20,22} ∧ Pzt–Cum.
  Giriş: u'dan sonra ilk fırsatta market BUY (ask; ≤ 90 sn gecikme). TP = giriş × (1 + 59,2 bp), SL = giriş × (1 − 94,7 bp) — broker tarafında.
  Kilit: bid ≥ giriş × (1 + 38,2 bp) olunca SL → giriş × (1 + 37,9 bp) (bir kez). 4.000 dk emniyet çıkışı. Tek pozisyon. Cuma kısıtı YOK
  (araştırma hafta sonu taşımasını içeriyor).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import broker_time as bt
import kural_katalogu as kk

RULE = "XAU_TDA"
MARKET = "XAUUSD"
HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "xau_tda_live_state.json"
POLL_EVERY_S = 5
MAX_LATE_S = 90
MAX_TICK_AGE_S = 120
FETCH_H = 700                          # ATR14/EMA50 ısınması
SAATLER = (7, 8, 12, 15, 20, 22)
R12_MIN, R4_MAX, UZ_MIN, KZ_MIN, KZ_MAX = 1.0, 0.5, 1.0, 0.55, 0.95
TP_BP, SL_BP, KILIT_TETIK_BP, KILIT_STOP_BP = 59.2, 94.7, 38.2, 37.9
HOLD_S = 4000 * 60

_last_poll = 0.0


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def ozellik(h1: dict) -> dict | None:
    """h1: UTC zamanlı (kova başı) KAPANMIŞ H1 mumları t,o,h,l,c (son eleman = j). Araştırma anatomi.h1 ile aynı formüller."""
    import pandas as pd
    h, l, c = (pd.Series(np.asarray(h1[x], float)) for x in ("h", "l", "c"))
    if len(c) < 300:
        return None
    pc = c.shift(1)
    tr = np.maximum(h - l, np.maximum((h - pc).abs(), (l - pc).abs()))
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean().iloc[-1]
    ema50 = c.ewm(span=50, adjust=False).mean().iloc[-1]
    if not (np.isfinite(atr) and atr > 0):
        return None
    cj = c.iloc[-1]
    hh, ll = h.iloc[-24:].max(), l.iloc[-24:].min()
    return {"bar_t": float(h1["t"][-1]), "c": float(cj), "atr": float(atr), "ema50": float(ema50),
            "r12": float((cj - c.iloc[-13]) / atr), "r4": float((cj - c.iloc[-5]) / atr), "uz": float((cj - ema50) / atr),
            "konum24": float((cj - ll) / (hh - ll)) if hh > ll else float("nan")}


def karar(f: dict | None, u_utc: float) -> bool:
    """u_utc: karar saat başı (UTC epoch, j mumunun kapanışı)."""
    if f is None:
        return False
    import datetime as dt
    z = dt.datetime.fromtimestamp(u_utc, dt.timezone.utc)
    if z.weekday() >= 5 or z.hour not in SAATLER:
        return False
    return (f["r12"] >= R12_MIN and abs(f["r4"]) <= R4_MAX and f["uz"] >= UZ_MIN and np.isfinite(f["konum24"])
            and KZ_MIN <= f["konum24"] <= KZ_MAX)


def seviyeler(giris: float, digits: int) -> dict:
    return {"tp": round(giris * (1 + TP_BP / 1e4), digits), "sl": round(giris * (1 - SL_BP / 1e4), digits),
            "kilit_tetik": giris * (1 + KILIT_TETIK_BP / 1e4), "kilit_sl": round(giris * (1 + KILIT_STOP_BP / 1e4), digits)}


def srv_to_utc(t_srv: np.ndarray) -> np.ndarray:
    t_srv = np.asarray(t_srv, np.int64)
    saat = t_srv // 3600
    u, inv = np.unique(saat, return_inverse=True)
    off = np.array([bt.rule_offset_sec(int(x) * 3600) for x in u], np.int64)
    return t_srv - off[inv]


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"last_u": 0, "pos": {}}


def _save_state(st: dict) -> None:
    kk.save_json(STATE_FILE, st)


# ═════════════════════════ MT5 ═════════════════════════

def manage_exits(mt5, config, log, send_order, offset_fn, resolve_symbol, now: float | None = None) -> None:
    """Kilit (SL'yi +37,9 bp'ye bir kez taşı) + 4.000 dk emniyet çıkışı. TP/SL broker tarafında."""
    if not kk.is_enabled(config, RULE):
        return
    now = time.time() if now is None else now
    positions = kk.open_positions(mt5, config, RULE)
    if not positions:
        return
    st = _load_state()
    for pos in positions:
        meta = st.setdefault("pos", {}).setdefault(str(pos.ticket), {"entry_t": float(pos.time) - bt.rule_offset_sec(int(pos.time))})
        if now - float(meta["entry_t"]) >= HOLD_S:
            if kk.close(mt5, config, log, send_order, RULE, pos, "4.000 dk emniyet çıkışı"):
                st["pos"].pop(str(pos.ticket), None)
                _save_state(st)
            continue
        if meta.get("kilit"):
            continue
        tick, info = mt5.symbol_info_tick(pos.symbol), mt5.symbol_info(pos.symbol)
        if tick is None or info is None:
            continue
        lv = seviyeler(float(pos.price_open), info.digits)
        if float(tick.bid) >= lv["kilit_tetik"] and float(getattr(pos, "sl", 0.0) or 0.0) < lv["kilit_sl"]:
            try:
                res = mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "symbol": pos.symbol, "position": pos.ticket, "sl": lv["kilit_sl"],
                                      "tp": float(getattr(pos, "tp", 0.0) or 0.0)})
                ok = res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
            except Exception:  # noqa: BLE001
                ok, res = False, None
            kk.append_event({"kind": "kilit", "rule": RULE, "ticket": pos.ticket, "bid": float(tick.bid), "sl": lv["kilit_sl"], "ok": ok,
                             "retcode": getattr(res, "retcode", None)})
            if ok:
                meta["kilit"] = True
                _save_state(st)
                log.info("[CANLI] XAU TDA kilit: SL → %.2f (+37,9 bp) ticket %s", lv["kilit_sl"], pos.ticket)
            else:
                log.error("XAU TDA kilit SL taşıma BAŞARISIZ ticket=%s retcode=%s — sonraki turda yeniden", pos.ticket,
                          getattr(res, "retcode", None))


def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_poll = now
    u = (int(now) // 3600) * 3600
    if now - u > MAX_LATE_S:
        return
    st = _load_state()
    if st.get("last_u") == u:
        return
    sym = resolve_symbol(MARKET)
    if not sym:
        return
    rh = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, FETCH_H + 2)
    if rh is None or len(rh) < 300:
        return
    t = srv_to_utc(rh["time"]).astype(float)
    kapanmis = t + 3600 <= u                                             # u'dan önce kapanmış mumlar
    h1 = {"t": t[kapanmis], "o": np.asarray(rh["open"], float)[kapanmis], "h": np.asarray(rh["high"], float)[kapanmis],
          "l": np.asarray(rh["low"], float)[kapanmis], "c": np.asarray(rh["close"], float)[kapanmis]}
    if not len(h1["t"]) or h1["t"][-1] != u - 3600:
        return                                                          # son mum henüz yok (piyasa kapalı/boşluk) — bu saati atla
    st["last_u"] = u
    _save_state(st)
    f = ozellik(h1)
    if not karar(f, u):
        return
    rec = {"market": MARKET, "u": u, "gecikme_s": round(now - u, 1), **{k: round(v, 4) for k, v in f.items() if k != "bar_t"}}
    _try_enter(mt5, config, log, sym, rec, st, now, send_order, mk_comment, autotrading_ok, log_trade)


def _try_enter(mt5, config, log, sym, rec, st, now, send_order, mk_comment, autotrading_ok, log_trade) -> None:
    skip = lambda r: kk.append_event({"kind": "skip", "rule": RULE, "reason": r, **rec})
    if kk.open_positions(mt5, config, RULE, sym):
        return skip("açık XAU TDA pozisyonu var (tek pozisyon)")
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return skip("tick/sembol bilgisi yok")
    if abs(now - (float(tick.time) - bt.rule_offset_sec(int(tick.time)))) > MAX_TICK_AGE_S:
        return skip("bayat tick (piyasa kapalı?)")
    ask = round(float(tick.ask), info.digits)
    lot = kk.lot_of(config, RULE)
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        return skip(f"yoğunlaşma tavanı {open_lot}+{lot}>{cap}")
    if not autotrading_ok():
        log.error("XAU TDA AutoTrading KAPALI — emir gönderilmedi")
        return skip("autotrading kapalı")
    lv = seviyeler(ask, info.digits)
    ok, ticket, rc = kk.buy(mt5, config, log, send_order, mk_comment, RULE, sym, lot, ask, lv["sl"], lv["tp"], "XAU TDA")
    kk.append_event({"kind": "entry", "rule": RULE, "ok": ok, "retcode": rc, "ticket": ticket, "ask": ask, "sl": lv["sl"], "tp": lv["tp"],
                     "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ XAU TDA emir reddedildi retcode=%s", rc)
        return
    st.setdefault("pos", {})[str(ticket)] = {"entry_t": now, "ask": ask}
    _save_state(st)
    kk.announce_open(log, RULE, f"{sym} BUY {lot} lot @ {ask} · TP {lv['tp']} (+59 bp) · SL {lv['sl']} (−95 bp) · kilit +38→+38 bp · "
                                f"ticket {ticket}", {"r12": rec["r12"], "r4": rec["r4"], "konum24": rec["konum24"]})
    log_trade("LIVE", f"{MARKET}:BUY:{RULE}", sym, "BUY", ask, lv["tp"], lv["sl"], ["xau_tda"], f"ticket={ticket}")
