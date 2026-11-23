"""soma_e2x3_live.py — Soma klon modeli AL (SC-13 E2X3) CANLI icra (demo): XAUUSD + NAS100.

KULLANICI KARARI 2026-11-23: "canlıya al direk … nasdaq'ta özellikle". Kaynak: research/soma_cozum_20261122 (SC-08 model,
SC-13 E2X3, SC-19 kart). Model = Soma PureGold'un giriş dakikalarını rastgele dakikalardan ayıran HistGradientBoosting
(çok zaman dilimli ~200 özellik; KEŞİF bölümüyle eğitildi, eşik = KEŞİF skorlarının q0,998'i). NASDAQ'a DONDURULMUŞ taşındı.

KANIT (SC-19, son 4 yıl 2022-11 → 2026-11, gerçek icra = sonraki 1m açılışı + spread; kart 6/6):
  XAUUSD: n 945, ort +0,269 R, P(EV>0) 0,99, tek pozisyon +0,276 R; 2023 +0,37 / 2024 +0,12 / 2025 +0,33 / 2026 +0,26 R
          (2025 model eğitim dönemiyle kısmen çakışır — örneklem içi).
  NAS100: n 589, ort +0,272 R, P 0,976, tek pozisyon +0,191 R, rastgele alışa fark +7,8 bp (P 0,977);
          2018-2026 dokuz yılın dokuzu artı. DAX/Nikkei gölge seviyesi, CAC/Stoxx/FTSE eksi → yalnız XAU + NAS100.
Kartlar: backend/data/evolution/go_live_cards/soma_e2x3_xau.json, soma_e2x3_ndx.json.
Durdurma ölçütü (önceden yazılı): sembol başına canlı n=60 işlemde ort. R < 0 → config.SOMA_E2_<XAU|NDX>_LIVE = False.

KURAL (sc10_klon_kar.skorla + sc14_bakis.alis_ates + sc13 X3, birebir):
  Her kapanmış 1m bar k: y = +1 eğer c_k > EMA1440(1m). Skor = model(özellik(k, p=c_k, y, t=k+60 sn)).
  Ateşleme = skor ≥ eşik VE bir önceki dakikanın skoru < eşik (kenar; soğuma 0). Yalnız y = +1 (AL).
  Giriş: market BUY (araştırma = sonraki 1m açılışı + spread). SL = 1,0 × ATR14(H1, son tamamlanmış H1). TP yok. 480 dk zaman çıkışı.
  Kural başına tek pozisyon (kart 6. ölçütü bu kısıtla da artı).
VERİ: MT5 terminali en çok 100.000 M1 bar veriyor (≈ 69 gün). D1 EMA200 / H4 göstergelerinin ısınması için daha eski
  dönem H1 barlarından birer "sentetik dakika" ile doldurulur (H4/D1 OHLC'si birebir korunur; M1–H1 göstergeleri yalnız gerçek
  M1 bölgesinde ölçülür — hepsi < 10 günde ısınır). Hacim = broker tick hacmi (araştırma: Dukascopy hacmi; özellikler oran).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import broker_time as bt
import caprev_shadow as cs
import kural_katalogu as kk

HERE = Path(__file__).resolve().parent
MODEL_FILE = HERE / "models" / "soma_e2_model.joblib"
STATE_FILE = HERE / "soma_e2x3_live_state.json"
MARKETS = {"SOMA_E2_XAU": "XAUUSD", "SOMA_E2_NDX": "NDX.INDX"}   # resolve_symbol anahtarı (NDX.INDX → NAS100)
POLL_EVERY_S = 10
MAX_LATE_S = 90
MAX_TICK_AGE_S = 120
HOLD_S = 480 * 60
SL_K = 1.0
FETCH_M1 = 99_000
FETCH_H1 = 6_500                        # ≈ 270 işlem günü → D1 EMA200 ısınır
EMA_Y = 1440
FRIDAY_CLOSE_NY_MIN = 16 * 60 + 50
FRIDAY_LAST_ENTRY_NY_MIN = 8 * 60 + 50

_last_poll: dict[str, float] = {}
_model_cache: dict = {}


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def load_model(path: Path = MODEL_FILE) -> dict:
    if "m" not in _model_cache:
        import joblib
        _model_cache["m"] = joblib.load(path)                          # {"model", "oz", "esik", ...}
    return _model_cache["m"]


def srv_to_utc(t_srv: np.ndarray) -> np.ndarray:
    """Broker sunucu epoch → UTC (sunucu = New York + 7; dönem kuralı saat başına)."""
    t_srv = np.asarray(t_srv, np.int64)
    saat = t_srv // 3600
    u, inv = np.unique(saat, return_inverse=True)
    off = np.array([bt.rule_offset_sec(int(x) * 3600) for x in u], np.int64)
    return t_srv - off[inv]


def build_series(m1: dict, h1: dict) -> dict:
    """m1/h1: UTC zamanlı kapanmış barlar (t,o,h,l,c,v). M1'den eski H1 barları birer sentetik dakika olarak öne eklenir."""
    t0 = m1["t"][0]
    eski = h1["t"] + 3600 <= t0
    return {x: np.r_[h1[x][eski], m1[x]] for x in ("t", "o", "h", "l", "c", "v")} | {"n_sentetik": int(eski.sum())}


def scores(seri: dict, mdl: dict) -> dict:
    """Son iki kapanmış dakika için (skor, y) + son dakikanın ATR_H1'i. soma_motor araştırma Motor'unun birebir kopyası."""
    import pandas as pd

    import soma_motor as F
    n = len(seri["t"])
    bar = F.Bar(seri["t"].astype(np.int64), seri["o"], seri["h"], seri["l"], seri["c"], np.zeros(n))
    M = F.Motor(bar, seri["v"].astype(float))
    e1440 = pd.Series(bar.c).ewm(span=EMA_Y, adjust=False).mean().to_numpy()
    j = np.array([n - 2, n - 1])
    y = np.where(bar.c[j] > e1440[j], 1, -1)
    X = M.ozellik(j, bar.c[j], y, bar.t[j] + 60)
    sk = mdl["model"].predict_proba(X[mdl["oz"]].to_numpy(np.float32))[:, 1]
    H1 = M.tf["H1"]
    bc = np.clip(np.searchsorted(H1.kova, H1.kova_1m[j[-1]]) - 1, 0, len(H1.C) - 1)
    return {"skor_onceki": float(sk[0]), "skor": float(sk[1]), "y_onceki": int(y[0]), "y": int(y[1]),
            "atr_h1": float(H1.g["atr"][bc]), "close": float(bar.c[-1]), "bar_t": float(bar.t[-1])}


def fires(s: dict, esik: float) -> bool:
    """Kenar ateşleme (sc08_kural.ateslemeler, soğuma 0) + yalnız AL."""
    return s["y"] > 0 and s["skor"] >= esik and not s["skor_onceki"] >= esik


def friday_close_due(now: float) -> bool:
    _, m, wd = cs.to_local(now, "US")
    return wd == 4 and m >= FRIDAY_CLOSE_NY_MIN


def friday_no_entry(now: float) -> bool:
    _, m, wd = cs.to_local(now, "US")
    return wd == 4 and m >= FRIDAY_LAST_ENTRY_NY_MIN


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"last_bar": {}, "pos": {}}


def _save_state(st: dict) -> None:
    kk.save_json(STATE_FILE, st)


def _arr(rates) -> dict:
    return {"t": srv_to_utc(rates["time"]).astype(float), "o": np.asarray(rates["open"], float),
            "h": np.asarray(rates["high"], float), "l": np.asarray(rates["low"], float),
            "c": np.asarray(rates["close"], float), "v": np.asarray(rates["tick_volume"], float)}


# ═════════════════════════ MT5 ═════════════════════════

def manage_exits(mt5, config, log, send_order, offset_fn, resolve_symbol, now: float | None = None) -> None:
    now = time.time() if now is None else now
    st = None
    for rule in MARKETS:
        if not kk.is_enabled(config, rule):
            continue
        for pos in kk.open_positions(mt5, config, rule):
            st = st or _load_state()
            meta = st.get("pos", {}).get(str(pos.ticket))
            t_in = float(meta["entry_t"]) if meta else float(pos.time) - bt.rule_offset_sec(int(pos.time))
            why = "480 dk zaman çıkışı" if now - t_in >= HOLD_S else ("Cuma kapanışı" if friday_close_due(now) else None)
            if why and kk.close(mt5, config, log, send_order, rule, pos, why):
                st.get("pos", {}).pop(str(pos.ticket), None)
                _save_state(st)


def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    now = time.time() if now is None else now
    for rule, market in MARKETS.items():
        if now - _last_poll.get(rule, 0.0) < POLL_EVERY_S or not kk.is_enabled(config, rule):
            continue
        _last_poll[rule] = now
        try:
            _poll_one(mt5, config, log, resolve_symbol, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
                      rule, market, now)
        except Exception as e:  # noqa: BLE001 — bir sembolün hatası diğerini durdurmasın
            log.warning("SOMA E2X3 %s hatası: %s", market, e)


def _poll_one(mt5, config, log, resolve_symbol, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
              rule, market, now) -> None:
    sym = resolve_symbol(market)
    if not sym:
        return
    st = _load_state()
    r1 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 1, FETCH_M1)    # 1 → koşan bar hariç
    if r1 is None or len(r1) < 20_000:
        return
    m1 = _arr(r1)
    late = now - (m1["t"][-1] + 60)
    key = str(int(m1["t"][-1]))
    if late < 0 or late > MAX_LATE_S or st.get("last_bar", {}).get(rule) == key:
        return
    st.setdefault("last_bar", {})[rule] = key
    _save_state(st)
    rh = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 1, FETCH_H1)
    if rh is None or len(rh) < 500:
        return
    mdl = load_model()
    s = scores(build_series(m1, _arr(rh)), mdl)
    if not fires(s, mdl["esik"]):
        return
    rec = {"market": market, "bar_t": s["bar_t"], "latency_s": round(late, 1), "skor": round(s["skor"], 4),
           "skor_onceki": round(s["skor_onceki"], 4), "esik": round(mdl["esik"], 4), "atr_h1": round(s["atr_h1"], 3),
           "close": s["close"]}
    _try_enter(mt5, config, log, sym, rule, market, s, rec, st, now, bt.rule_offset_sec(int(now) + 3 * 3600), send_order, mk_comment, autotrading_ok,
               log_trade)


def _try_enter(mt5, config, log, sym, rule, market, s, rec, st, now, off, send_order, mk_comment, autotrading_ok,
               log_trade) -> None:
    skip = lambda r: kk.append_event({"kind": "skip", "rule": rule, "reason": r, **rec})
    if kk.open_positions(mt5, config, rule, sym):
        return skip("açık pozisyon var (kural başına tek pozisyon)")
    if friday_no_entry(now):
        return skip("Cuma 08:50 NY sonrası (480 dk hafta sonuna taşar)")
    if not (np.isfinite(s["atr_h1"]) and s["atr_h1"] > 0):
        return skip("ATR_H1 yok")
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return skip("tick/sembol bilgisi yok")
    if abs(now - (float(tick.time) - off)) > MAX_TICK_AGE_S:
        return skip("bayat tick (piyasa kapalı?)")
    ask = round(float(tick.ask), info.digits)
    lot = kk.lot_of(config, rule)
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        return skip(f"yoğunlaşma tavanı {open_lot}+{lot}>{cap}")
    if not autotrading_ok():
        log.error("SOMA E2X3 AutoTrading KAPALI — emir gönderilmedi")
        return skip("autotrading kapalı")
    sl = round(ask - SL_K * s["atr_h1"], info.digits)
    ok, ticket, rc = kk.buy(mt5, config, log, send_order, mk_comment, rule, sym, lot, ask, sl, 0.0, "SOMA E2")
    kk.append_event({"kind": "entry", "rule": rule, "ok": ok, "retcode": rc, "ticket": ticket, "ask": ask, "sl": sl,
                     "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ SOMA E2X3 %s emir reddedildi retcode=%s", market, rc)
        return
    st.setdefault("pos", {})[str(ticket)] = {"entry_t": now, "ask": ask, "sl": sl, "rule": rule}
    _save_state(st)
    kk.announce_open(log, rule, f"{sym} BUY {lot} lot @ {ask} · SL {sl} (1×ATR_H1) · TP yok · 480 dk · ticket {ticket}",
                     {"gecikme_s": rec["latency_s"], "skor": rec["skor"], "eşik": rec["esik"]})
    log_trade("LIVE", f"{market}:BUY:{rule}", sym, "BUY", ask, 0.0, sl, ["soma_e2x3"], f"ticket={ticket}")
