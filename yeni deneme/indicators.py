"""
indicators.py — kapsamlı teknik gösterge seti (numpy; MT5 zaten numpy çeker).
compute_all(o,h,l,c,v) → son kapalı mum için tüm indicator değerleri (flat dict).
Backend momentum filtresinin göstergeleri de dahil: dist_ema20_atr, sar_dist_atr,
stoch_k, macd_hist — böylece forensik/analiz birebir aynı tabandan beslenir.
"""
from __future__ import annotations
import numpy as np


def _ema(x: np.ndarray, p: int) -> np.ndarray:
    k = 2.0 / (p + 1)
    e = np.empty_like(x, dtype=float)
    e[0] = x[0]
    for i in range(1, len(x)):
        e[i] = x[i] * k + e[i - 1] * (1 - k)
    return e


def _rma(x: np.ndarray, p: int) -> np.ndarray:
    """Wilder smoothing (RMA) — RSI/ATR/ADX için."""
    r = np.empty_like(x, dtype=float)
    if len(x) == 0:
        return r
    r[0] = x[0]
    a = 1.0 / p
    for i in range(1, len(x)):
        r[i] = x[i] * a + r[i - 1] * (1 - a)
    return r


def _rsi(c: np.ndarray, p: int = 14) -> float:
    d = np.diff(c)
    up = np.where(d > 0, d, 0.0)
    dn = np.where(d < 0, -d, 0.0)
    ru = _rma(up, p)[-1]
    rd = _rma(dn, p)[-1]
    if rd == 0:
        return 100.0
    rs = ru / rd
    return float(100 - 100 / (1 + rs))


def _true_range(h, l, c) -> np.ndarray:
    pc = np.roll(c, 1); pc[0] = c[0]
    return np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))


def _atr(h, l, c, p: int = 14) -> float:
    tr = _true_range(h, l, c)
    return float(_rma(tr, p)[-1])


def _adx(h, l, c, p: int = 14):
    up = h[1:] - h[:-1]
    dn = l[:-1] - l[1:]
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = _true_range(h, l, c)[1:]
    atr = _rma(tr, p)
    atr_safe = np.where(atr == 0, np.nan, atr)
    plus_di = 100 * _rma(plus_dm, p) / atr_safe
    minus_di = 100 * _rma(minus_dm, p) / atr_safe
    dx = 100 * np.abs(plus_di - minus_di) / np.where((plus_di + minus_di) == 0, np.nan, plus_di + minus_di)
    dx = np.nan_to_num(dx)
    adx = _rma(dx, p)
    return float(adx[-1]), float(np.nan_to_num(plus_di[-1])), float(np.nan_to_num(minus_di[-1]))


def _stoch(h, l, c, k: int = 14, d: int = 3):
    if len(c) < k:
        return 50.0, 50.0
    ll = np.array([l[i - k + 1:i + 1].min() for i in range(k - 1, len(c))])
    hh = np.array([h[i - k + 1:i + 1].max() for i in range(k - 1, len(c))])
    rng = np.where((hh - ll) == 0, np.nan, hh - ll)
    kline = 100 * (c[k - 1:] - ll) / rng
    kline = np.nan_to_num(kline, nan=50.0)
    dline = np.convolve(kline, np.ones(d) / d, mode="valid")
    return float(kline[-1]), float(dline[-1] if len(dline) else kline[-1])


def _macd(c, fast=12, slow=26, sig=9):
    macd = _ema(c, fast) - _ema(c, slow)
    signal = _ema(macd, sig)
    return float(macd[-1]), float(signal[-1]), float(macd[-1] - signal[-1])


def _bollinger(c, p=20, k=2.0):
    if len(c) < p:
        p = len(c)
    window = c[-p:]
    mid = window.mean()
    sd = window.std()
    up, lo = mid + k * sd, mid - k * sd
    width = (up - lo) / mid if mid else 0.0
    pctb = (c[-1] - lo) / (up - lo) if (up - lo) else 0.5
    return float(up), float(mid), float(lo), float(width), float(pctb)


def _sar(h, l, step=0.02, maxstep=0.2) -> float:
    n = len(h)
    if n < 2:
        return float(l[-1])
    sar = l[0]; ep = h[0]; af = step; up = True
    for i in range(1, n):
        prev = sar
        sar = prev + af * (ep - prev)
        if up:
            sar = min(sar, l[i - 1], l[i - 2] if i >= 2 else l[i - 1])
            if h[i] > ep:
                ep = h[i]; af = min(af + step, maxstep)
            if l[i] < sar:
                up = False; sar = ep; ep = l[i]; af = step
        else:
            sar = max(sar, h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            if l[i] < ep:
                ep = l[i]; af = min(af + step, maxstep)
            if h[i] > sar:
                up = True; sar = ep; ep = h[i]; af = step
    return float(sar)


def compute_all(o, h, l, c, v=None) -> dict:
    """Son kapalı mum için tüm göstergeler. Diziler kronolojik (eski→yeni)."""
    h = np.asarray(h, float); l = np.asarray(l, float); c = np.asarray(c, float)
    o = np.asarray(o, float)
    out: dict = {}
    if len(c) < 30:
        return {"insufficient": True, "n": int(len(c))}

    ema20 = _ema(c, 20)[-1]; ema50 = _ema(c, 50)[-1]
    ema200 = _ema(c, 200)[-1] if len(c) >= 200 else _ema(c, len(c))[-1]
    atr14 = _atr(h, l, c, 14)
    adx14, pdi, mdi = _adx(h, l, c, 14)
    stoch_k, stoch_d = _stoch(h, l, c, 14, 3)
    macd, macd_sig, macd_hist = _macd(c)
    bb_up, bb_mid, bb_lo, bb_w, bb_pct = _bollinger(c, 20, 2.0)
    sar = _sar(h, l)
    price = float(c[-1])

    out.update({
        "close": price, "ema20": float(ema20), "ema50": float(ema50), "ema200": float(ema200),
        "sma20": float(c[-20:].mean()), "rsi14": _rsi(c, 14),
        "macd": macd, "macd_signal": macd_sig, "macd_hist": macd_hist,
        "atr14": atr14, "adx14": adx14, "plus_di": pdi, "minus_di": mdi,
        "stoch_k": stoch_k, "stoch_d": stoch_d,
        "bb_upper": bb_up, "bb_mid": bb_mid, "bb_lower": bb_lo,
        "bb_width": bb_w, "bb_pct_b": bb_pct, "sar": sar,
        # türetilmiş (backend momentum filtresiyle aynı taban) + trend bayrakları
        "dist_ema20_atr": float((price - ema20) / atr14) if atr14 else 0.0,
        "dist_ema50_atr": float((price - ema50) / atr14) if atr14 else 0.0,
        "sar_dist_atr": float((price - sar) / atr14) if atr14 else 0.0,
        "ema_stack_up": bool(ema20 > ema50 > ema200),
        "ema_stack_dn": bool(ema20 < ema50 < ema200),
        "above_ema200": bool(price > ema200),
        "atr_pct": float(atr14 / price * 100) if price else 0.0,
    })
    # VWAP z (hacim-ağırlıklı ortalama, son 50 bar) — kanala EK mean-reversion sinyali
    m = min(50, len(c))
    vtp = (h[-m:] + l[-m:] + c[-m:]) / 3.0
    vv = np.asarray(v, float)[-m:] if v is not None else np.ones(m)
    svv = float(vv.sum()); vsd = float(vtp.std())
    out["vwap_z"] = float((price - (vtp * vv).sum() / svv) / vsd) if (svv > 0 and vsd > 0) else 0.0
    return {k: (round(val, 6) if isinstance(val, float) else val) for k, val in out.items()}
