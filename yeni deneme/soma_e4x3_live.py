"""soma_e4x3_live.py — XAUUSD "trend içi yeni gün tepesi + H4 kanal tavanı + güçlü 1m gövde" AL (SC-13 E4X3) CANLI icra (demo).

KULLANICI KARARI 2026-11-23: "canlıya al direk". Kaynak: Soma PureGold çözümlemesi (research/soma_cozum_20261122, SC-13 → SC-19).
Modelsiz kural; Soma hesabının giriş anının ortak imzasından türetildi (SC-11: giriş saniyesi = yeni gün ucu + 30 sn momentum).

KANIT (Dukascopy XAU 1m, gerçek icra = sonraki 1m açılışı + yıl×saat spread + 0,08 $/ons komisyon):
  SC-18: 2023 +6,97 / 2024 +4,41 & +7,40 / 2025 +5,79 / 2026 +7,69 bp — son 4 yılın her yılı artı; eşleşmiş rastgele alışa
  fark +5,26 bp (P 0,974) ve +8,81 bp (P 0,975). Kart: backend/data/evolution/go_live_cards/soma_e4x3_xau.json (SC-19).
UYARILAR: 2018-21 GELISTIRME döneminde bu hücre ön kayıtlı eşiği geçmedi (son yıllar ölçütüyle — kullanıcı kararı 2026-11-23 —
aday oldu). İşlem başı kenar küçük (~+0,2 R); spread genişlerse ilk bozulacak kalem budur. Durdurma ölçütü (önceden yazılı):
canlı n=60 işlemde ort. R < 0 → config.SOMA_E4X3_LIVE = False.

KURAL (research/soma_cozum_20261122/src/sc13_strateji.py::soma_tetik ile birebir; tüm kovalar BROKER SUNUCU SAATİNDE —
Pepperstone sunucusu = New York + 7, araştırmanın sunucu ofseti ile aynı):
  Son KAPANMIŞ 1m bar k için hepsi:
    c > EMA1440(1m kapanış) ve c > EMA240(1m kapanış)                         (trend, yalnız AL)
    k bu sunucu gününün ilk barı değil ve high_k > günün k'dan önceki en yükseği  (yeni gün tepesi)
    c ≥ HH20(H4) − 0,25 × ATR14(H4)  — son TAMAMLANMIŞ H4 barına göre           (kanal tavanı)
    (c − o) / (h − l) ≥ 0,5                                                   (güçlü yükseliş gövdesi)
  Sunucu günü başına yalnız İLK olay. Giriş: bar kapanır kapanmaz market BUY (≤ 90 sn gecikme).
  SL = giriş − 1,0 × ATR14(H1, k'nın saatinden önceki H1 mumu — araştırmayla aynı), broker tarafında. TP YOK. Çıkış: girişten 480 dk sonra.
  Cuma 16:50 NY'de açık pozisyon kapatılır, Cuma 08:50 NY sonrası yeni giriş yok (480 dk hafta sonuna taşmasın).
  Tek pozisyon.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import caprev_shadow as cs
import kural_katalogu as kk

RULE = "SOMA_E4X3"
MARKET = "XAUUSD"
HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "soma_e4x3_live_state.json"
POLL_EVERY_S = 10
MAX_LATE_S = 90
MAX_TICK_AGE_S = 120
HOLD_S = 480 * 60
SL_K = 1.0
KANAL_ATR = 0.25
GOVDE_MIN = 0.5
EMA_UZUN, EMA_KISA = 1440, 240
FETCH_M1 = 12000                       # EMA1440 ısınması (ilk değerin ağırlığı ≈ e^-12)
FETCH_H = 400                          # Wilder ATR14 ısınması
FRIDAY_CLOSE_NY_MIN = 16 * 60 + 50
FRIDAY_LAST_ENTRY_NY_MIN = 8 * 60 + 50  # 16:50 − 480 dk
FIRED_KEEP_D = 10

_last_poll = 0.0


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def ema(x: np.ndarray, span: int) -> np.ndarray:
    import pandas as pd
    return pd.Series(np.asarray(x, float)).ewm(span=span, adjust=False).mean().to_numpy()


def wilder_atr(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int = 14) -> np.ndarray:
    """Araştırma sc08_ozellik.tf_kur ile aynı: TR (önceki kapanış ilk barda kendisi) → Wilder (ewm alpha 1/n)."""
    import pandas as pd
    onc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h, onc) - np.minimum(l, onc)
    return pd.Series(tr).ewm(alpha=1 / n, adjust=False).mean().to_numpy()


def before_bucket(rates_t: np.ndarray, bar_t: float, sec: int) -> np.ndarray:
    """k barının içinde bulunduğu üst zaman dilimi mumundan ÖNCEKİ mumların maskesi (araştırma: searchsorted(kova)−1)."""
    return np.asarray(rates_t, float) < (int(bar_t) // sec) * sec


def evaluate(m1: dict, h4: dict, h1: dict) -> dict | None:
    """m1/h4/h1: SUNUCU SAATİNDE kapanmış barlar (dizi sözlüğü t,o,h,l,c; son eleman = son kapanmış bar).
    Dönüş: sinyal sözlüğü ya da None."""
    t, o, h, l, c = (np.asarray(m1[x], float) for x in ("t", "o", "h", "l", "c"))
    if len(c) < EMA_UZUN + 10 or len(h4["c"]) < 40 or len(h1["c"]) < 40:
        return None
    k = len(c) - 1
    e_u, e_k = ema(c, EMA_UZUN)[k], ema(c, EMA_KISA)[k]
    if not (c[k] > e_u and c[k] > e_k):
        return None
    gun = (t // 86400).astype(np.int64)
    bugun = gun == gun[k]
    if k == 0 or gun[k - 1] != gun[k]:
        return None                                                     # günün ilk barı (araştırma: ayni=False)
    onceki_tepe = h[bugun][:-1].max()
    if not h[k] > onceki_tepe:
        return None
    rng = max(h[k] - l[k], 1e-12)
    if (c[k] - o[k]) / rng < GOVDE_MIN:
        return None
    H4h, H4l, H4c = (np.asarray(h4[x], float) for x in ("h", "l", "c"))
    hh20 = H4h[-20:].max()
    atr4 = wilder_atr(H4h, H4l, H4c)[-1]
    if not (np.isfinite(atr4) and c[k] >= hh20 - KANAL_ATR * atr4):
        return None
    atr1 = wilder_atr(*(np.asarray(h1[x], float) for x in ("h", "l", "c")))[-1]
    if not (np.isfinite(atr1) and atr1 > 0):
        return None
    return {"bar_t": float(t[k]), "gun": int(gun[k]), "close": float(c[k]), "high": float(h[k]), "onceki_tepe": float(onceki_tepe),
            "ema1440": float(e_u), "ema240": float(e_k), "hh20_h4": float(hh20), "atr_h4": float(atr4), "atr_h1": float(atr1),
            "govde": float((c[k] - o[k]) / rng), "stop_dist": SL_K * float(atr1)}


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
        return {"fired_days": [], "pos": {}}


def _save_state(st: dict) -> None:
    kk.save_json(STATE_FILE, st)


def _arr(rates) -> dict:
    return {"t": np.asarray(rates["time"], float), "o": np.asarray(rates["open"], float), "h": np.asarray(rates["high"], float),
            "l": np.asarray(rates["low"], float), "c": np.asarray(rates["close"], float)}


# ═════════════════════════ MT5 ═════════════════════════

def manage_exits(mt5, config, log, send_order, offset_fn, resolve_symbol, now: float | None = None) -> None:
    """480 dk / Cuma 16:50 NY çıkışı. SL broker tarafında."""
    if not kk.is_enabled(config, RULE):
        return
    now = time.time() if now is None else now
    positions = kk.open_positions(mt5, config, RULE)
    if not positions:
        return
    st = _load_state()
    for pos in positions:
        meta = st.get("pos", {}).get(str(pos.ticket))
        t_in = float(meta["entry_t"]) if meta else float(pos.time) - offset_fn(pos.symbol)
        why = "480 dk zaman çıkışı" if now - t_in >= HOLD_S else ("Cuma kapanışı" if friday_close_due(now) else None)
        if why and kk.close(mt5, config, log, send_order, RULE, pos, why):
            st.get("pos", {}).pop(str(pos.ticket), None)
            _save_state(st)


def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_poll = now
    sym = resolve_symbol(MARKET)
    if not sym:
        return
    off = offset_fn(sym)
    st = _load_state()
    now_srv = now + off
    if int(now_srv // 86400) in st.get("fired_days", []):
        return                                                          # bugünün olayı zaten işlendi
    r1 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 1, FETCH_M1)     # 1 → koşan bar hariç
    if r1 is None or len(r1) < EMA_UZUN + 10:
        return
    m1 = _arr(r1)
    late = now_srv - (m1["t"][-1] + 60)
    key = int(m1["t"][-1])
    if late < 0 or late > MAX_LATE_S or st.get("last_bar") == key:
        return
    st["last_bar"] = key
    r4 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H4, 0, FETCH_H)
    rh = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, FETCH_H)
    if r4 is None or rh is None:
        return _save_state(st)
    h4, h1 = _arr(r4), _arr(rh)
    m4 = before_bucket(h4["t"], m1["t"][-1], 4 * 3600)
    mh = before_bucket(h1["t"], m1["t"][-1], 3600)
    h4 = {x: v[m4] for x, v in h4.items()}
    h1 = {x: v[mh] for x, v in h1.items()}
    sig = evaluate(m1, h4, h1)
    if sig is None:
        return _save_state(st)
    st["fired_days"] = [d for d in st.get("fired_days", []) if d >= sig["gun"] - FIRED_KEEP_D] + [sig["gun"]]
    _save_state(st)
    rec = {"market": MARKET, "bar_t_srv": sig["bar_t"], "latency_s": round(late, 1),
           **{x: round(sig[x], 3) for x in ("close", "onceki_tepe", "hh20_h4", "atr_h4", "atr_h1", "govde", "stop_dist")}}
    _try_enter(mt5, config, log, sym, sig, rec, st, now, off, send_order, mk_comment, autotrading_ok, log_trade)


def _try_enter(mt5, config, log, sym, sig, rec, st, now, off, send_order, mk_comment, autotrading_ok, log_trade) -> None:
    skip = lambda r: kk.append_event({"kind": "skip", "rule": RULE, "reason": r, **rec})
    if kk.open_positions(mt5, config, RULE, sym):
        return skip("açık SOMA E4X3 pozisyonu var (tek pozisyon)")
    if friday_no_entry(now):
        return skip("Cuma 08:50 NY sonrası (480 dk hafta sonuna taşar)")
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return skip("tick/sembol bilgisi yok")
    if abs(now - (float(tick.time) - off)) > MAX_TICK_AGE_S:
        return skip("bayat tick (piyasa kapalı?)")
    ask = round(float(tick.ask), info.digits)
    lot = kk.lot_of(config, RULE)
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        return skip(f"yoğunlaşma tavanı {open_lot}+{lot}>{cap}")
    if not autotrading_ok():
        log.error("SOMA E4X3 AutoTrading KAPALI — emir gönderilmedi")
        return skip("autotrading kapalı")
    sl = round(ask - sig["stop_dist"], info.digits)
    ok, ticket, rc = kk.buy(mt5, config, log, send_order, mk_comment, RULE, sym, lot, ask, sl, 0.0, "SOMA E4")
    kk.append_event({"kind": "entry", "rule": RULE, "ok": ok, "retcode": rc, "ticket": ticket, "ask": ask, "sl": sl,
                     "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ SOMA E4X3 emir reddedildi retcode=%s", rc)
        return
    st.setdefault("pos", {})[str(ticket)] = {"entry_t": now, "ask": ask, "sl": sl}
    _save_state(st)
    kk.announce_open(log, RULE, f"{sym} BUY {lot} lot @ {ask} · SL {sl} (1×ATR_H1) · TP yok · 480 dk · ticket {ticket}",
                     {"gecikme_s": rec["latency_s"], "atr_h1": rec["atr_h1"], "gövde": rec["govde"]})
    log_trade("LIVE", f"{MARKET}:BUY:SOMA_E4X3", sym, "BUY", ask, 0.0, sl, ["soma_e4x3"], f"ticket={ticket}")
