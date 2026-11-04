"""Nedensel gösterge kütüphanesi — TradingView resmî + topluluk ailelerinin temsilcileri (PROTOCOL §1, §3).

Her değer yalnız t anına kadarki barlarla hesaplanır (test_causality.py doğrular). Her gösterge boğa/ayı
çiftleri hâlinde ikili DURUM üretir; `fam` kodu topluluk_taramasi/classify.py ailelerine bağlanır.
Çıktı: Book(states: ad → bool dizisi, meta: ad → (gösterge kimliği, aile), feats: ad → float32 dizisi).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from scipy.signal import lfilter

EPS = 1e-12


# ── temel yardımcılar ────────────────────────────────────────────────────────
def S(x) -> pd.Series:
    return pd.Series(x, dtype="float64")


def ema(x, n):
    return S(x).ewm(span=n, adjust=False, min_periods=n).mean().values


def rma(x, n):
    return S(x).ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean().values


def sma(x, n):
    return S(x).rolling(n, min_periods=n).mean().values


def rsum(x, n):
    return S(x).rolling(n, min_periods=n).sum().values


def rstd(x, n):
    return S(x).rolling(n, min_periods=n).std(ddof=0).values


def rmax(x, n):
    return S(x).rolling(n, min_periods=n).max().values


def rmin(x, n):
    return S(x).rolling(n, min_periods=n).min().values


def shift(x, k):
    out = np.full(len(x), np.nan)
    if k < len(x):
        out[k:] = x[: len(x) - k]
    return out


def conv_ma(x, w):
    """Ağırlıklı kayan ortalama; w[0] en ESKİ bara, w[-1] güncel bara uygulanır."""
    x = np.asarray(x, float)
    n = len(w)
    valid = ~np.isnan(x)
    xv = np.where(valid, x, 0.0)
    num = np.convolve(xv, w[::-1], mode="full")[: len(x)]
    cnt = np.convolve(valid.astype(float), np.ones(n), mode="full")[: len(x)]
    out = num / w.sum()
    out[cnt < n] = np.nan
    return out


def wma(x, n):
    return conv_ma(x, np.arange(1, n + 1, dtype=float))


def true_range(h, l, c):
    pc = shift(c, 1)
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    tr[0] = h[0] - l[0]
    return tr


def atr(h, l, c, n=14):
    return rma(true_range(h, l, c), n)


def rsi(x, n=14):
    d = np.diff(x, prepend=np.nan)
    up, dn = np.where(d > 0, d, 0.0), np.where(d < 0, -d, 0.0)
    up[0] = dn[0] = np.nan
    ru, rd = rma(up, n), rma(dn, n)
    return 100.0 - 100.0 / (1.0 + ru / (rd + EPS))


def linreg_stats(y, n):
    """Kayan doğrusal regresyon: uç değer, eğim, korelasyon (y'nin zamanla)."""
    t = np.arange(n, dtype=float)
    St, Stt = t.sum(), (t * t).sum()
    Sy = rsum(y, n)
    Syy = rsum(np.asarray(y, float) ** 2, n)
    Sty = conv_ma(y, t) * St          # conv_ma ağırlık toplamına böler → geri çarp
    den = n * Stt - St * St
    b = (n * Sty - St * Sy) / den
    a = (Sy - b * St) / n
    end = a + b * (n - 1)
    r = (n * Sty - St * Sy) / np.sqrt(np.maximum(den * (n * Syy - Sy * Sy), EPS))
    return end, b, r


def window_view(x, n):
    v = sliding_window_view(np.asarray(x, float), n)
    pad = np.full((n - 1, n), np.nan)
    return np.vstack([pad, v])


def _lst(x):
    return [float(v) for v in x]


# ── kitap ────────────────────────────────────────────────────────────────────
@dataclass
class Book:
    states: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)
    feats: dict = field(default_factory=dict)

    def pair(self, ind: str, fam: str, name: str, bull, bear, valid=None):
        """Boğa/ayı çifti. NaN girişli barlar iki durumda da 0."""
        bull = np.asarray(bull)
        bear = np.asarray(bear)
        v = np.ones(len(bull), bool) if valid is None else np.asarray(valid, bool)
        self.add(ind, fam, f"{name}+", bull & v)
        self.add(ind, fam, f"{name}-", bear & v)

    def add(self, ind, fam, name, arr):
        a = np.nan_to_num(np.asarray(arr, float), nan=0.0) > 0.5
        key = f"{ind}:{name}"
        self.states[key] = a
        self.meta[key] = (ind, fam)

    def feat(self, name, x):
        self.feats[name] = np.asarray(x, np.float32)


def ok(*xs):
    m = np.ones(len(xs[0]), bool)
    for x in xs:
        m &= ~np.isnan(np.asarray(x, float))
    return m


def gt(a, b):
    return ok(a, b) & (np.nan_to_num(a) > np.nan_to_num(b))


def lt(a, b):
    return ok(a, b) & (np.nan_to_num(a) < np.nan_to_num(b))


def rising(x):
    return gt(x, shift(x, 1))


def falling(x):
    return lt(x, shift(x, 1))


# ── döngü gerektiren göstergeler ────────────────────────────────────────────
def supertrend(h, l, c, at, mult):
    n = len(c)
    hl2 = (h + l) / 2
    up_b, dn_b = _lst(hl2 - mult * at), _lst(hl2 + mult * at)
    cl = _lst(c)
    d = np.zeros(n)
    fu = fd = float("nan")
    di = 1
    for i in range(n):
        u, dn = up_b[i], dn_b[i]
        if u != u:
            continue
        if fu != fu:
            fu, fd = u, dn
        else:
            fu_new = max(u, fu) if cl[i - 1] > fu else u
            fd_new = min(dn, fd) if cl[i - 1] < fd else dn
            if di == -1 and cl[i] > fd:
                di = 1
            elif di == 1 and cl[i] < fu:
                di = -1
            fu, fd = fu_new, fd_new
        d[i] = di
    return d


def psar(h, l, af0=0.02, step=0.02, amax=0.2):
    n = len(h)
    H, L = _lst(h), _lst(l)
    d = np.zeros(n)
    bull, af, ep, sar = True, af0, H[0], L[0]
    for i in range(1, n):
        sar = sar + af * (ep - sar)
        if bull:
            sar = min(sar, L[i - 1], L[i - 2] if i >= 2 else L[i - 1])
            if L[i] < sar:
                bull, sar, ep, af = False, ep, L[i], af0
            elif H[i] > ep:
                ep, af = H[i], min(af + step, amax)
        else:
            sar = max(sar, H[i - 1], H[i - 2] if i >= 2 else H[i - 1])
            if H[i] > sar:
                bull, sar, ep, af = True, ep, H[i], af0
            elif L[i] < ep:
                ep, af = L[i], min(af + step, amax)
        d[i] = 1 if bull else -1
    return d


def atr_trail(src, at, mult):
    """UT Bot / Volatility Stop: ATR trailing stop; +1 fiyat stop üstünde."""
    x, a = _lst(src), _lst(at)
    n = len(x)
    d = np.zeros(n)
    stop = float("nan")
    for i in range(1, n):
        if a[i] != a[i]:
            continue
        loss = mult * a[i]
        if stop != stop:
            stop = x[i] - loss
        elif x[i] > stop and x[i - 1] > stop:
            stop = max(stop, x[i] - loss)
        elif x[i] < stop and x[i - 1] < stop:
            stop = min(stop, x[i] + loss)
        elif x[i] > stop:
            stop = x[i] - loss
        else:
            stop = x[i] + loss
        d[i] = 1 if x[i] > stop else -1
    return d


def halftrend(h, l, c, at100, amp=2, dev=2.0):
    hp, lp = _lst(rmax(h, amp)), _lst(rmin(l, amp))
    hma_, lma_ = _lst(sma(h, amp)), _lst(sma(l, amp))
    H, L, Cl = _lst(h), _lst(l), _lst(c)
    n = len(c)
    d = np.zeros(n)
    trend, nxt = 0, 0
    max_low, min_high = L[0], H[0]
    for i in range(1, n):
        if hp[i] != hp[i] or hma_[i] != hma_[i]:
            continue
        if nxt == 1:
            max_low = max(lp[i], max_low)
            if hma_[i] < max_low and Cl[i] < L[i - 1]:
                trend, nxt, min_high = 1, 0, hp[i]
        else:
            min_high = min(hp[i], min_high)
            if lma_[i] > min_high and Cl[i] > H[i - 1]:
                trend, nxt, max_low = 0, 1, lp[i]
        d[i] = 1 if trend == 0 else -1
    return d


def range_filter(c, per=100, mult=3.0):
    rng = ema(ema(np.abs(np.diff(c, prepend=np.nan)), per), per * 2 - 1) * mult
    x, r = _lst(c), _lst(rng)
    n = len(c)
    d = np.zeros(n)
    f = float("nan")
    up = 0
    for i in range(n):
        if r[i] != r[i]:
            continue
        prev = x[i] if f != f else f
        if x[i] > prev:
            f = prev if x[i] - r[i] < prev else x[i] - r[i]
        else:
            f = prev if x[i] + r[i] > prev else x[i] + r[i]
        if f > prev:
            up = 1
        elif f < prev:
            up = -1
        d[i] = up
    return d


def chandelier(h, l, c, at, n=22, mult=3.0):
    ls_, ss_ = _lst(rmax(c, n) - mult * at), _lst(rmin(c, n) + mult * at)
    x = _lst(c)
    N = len(c)
    d = np.zeros(N)
    lstop = sstop = float("nan")
    di = 1
    for i in range(1, N):
        if ls_[i] != ls_[i]:
            continue
        if lstop != lstop:
            lstop, sstop = ls_[i], ss_[i]
        else:
            lstop = max(ls_[i], lstop) if x[i - 1] > lstop else ls_[i]
            sstop = min(ss_[i], sstop) if x[i - 1] < sstop else ss_[i]
        if x[i] > sstop:
            di = 1
        elif x[i] < lstop:
            di = -1
        d[i] = di
    return d


def kama(c, n=10, fast=2, slow=30):
    ch = np.abs(c - shift(c, n))
    vol = rsum(np.abs(np.diff(c, prepend=np.nan)), n)
    er = ch / (vol + EPS)
    sc = (er * (2 / (fast + 1) - 2 / (slow + 1)) + 2 / (slow + 1)) ** 2
    x, s = _lst(c), _lst(sc)
    out = np.full(len(c), np.nan)
    k = float("nan")
    for i in range(len(c)):
        if s[i] != s[i]:
            continue
        k = x[i] if k != k else k + s[i] * (x[i] - k)
        out[i] = k
    return out


def mcginley(c, n=14):
    x = _lst(c)
    out = np.full(len(c), np.nan)
    m = x[0]
    for i in range(1, len(c)):
        ratio = x[i] / m if m else 1.0
        m = m + (x[i] - m) / (n * ratio ** 4)
        out[i] = m
    out[:n] = np.nan
    return out


def qqe_trend(c, n=14, sf=5, q=4.236):
    rsima = ema(rsi(c, n), sf)
    atr_rsi = np.abs(np.diff(rsima, prepend=np.nan))
    dar = ema(ema(atr_rsi, 2 * n - 1), 2 * n - 1) * q
    r, dd = _lst(rsima), _lst(dar)
    N = len(c)
    d = np.zeros(N)
    lb = sb = float("nan")
    tr = 0
    for i in range(1, N):
        if dd[i] != dd[i] or r[i - 1] != r[i - 1]:
            continue
        nl, ns = r[i] - dd[i], r[i] + dd[i]
        plb, psb = lb, sb
        if plb != plb:
            lb, sb = nl, ns
        else:
            lb = max(plb, nl) if (r[i - 1] > plb and r[i] > plb) else nl
            sb = min(psb, ns) if (r[i - 1] < psb and r[i] < psb) else ns
            if r[i - 1] <= psb < r[i]:
                tr = 1
            elif r[i - 1] >= plb > r[i]:
                tr = -1
        d[i] = tr
    return d, rsima


def laguerre_rsi(c, g=0.5):
    x = _lst(c)
    out = np.full(len(c), np.nan)
    l0 = l1 = l2 = l3 = x[0]
    for i in range(len(c)):
        p0, p1, p2 = l0, l1, l2
        l0 = (1 - g) * x[i] + g * l0
        l1 = -g * l0 + p0 + g * l1
        l2 = -g * l1 + p1 + g * l2
        l3 = -g * l2 + p2 + g * l3
        cu = max(l0 - l1, 0) + max(l1 - l2, 0) + max(l2 - l3, 0)
        cd = max(l1 - l0, 0) + max(l2 - l1, 0) + max(l3 - l2, 0)
        out[i] = cu / (cu + cd) if cu + cd else 0.5
    out[:10] = np.nan
    return out


def kalman_ab(c, alpha=0.2, beta=0.02):
    x = _lst(c)
    lvl, vel = x[0], 0.0
    L, V = np.full(len(c), np.nan), np.full(len(c), np.nan)
    for i in range(1, len(c)):
        pred = lvl + vel
        res = x[i] - pred
        lvl, vel = pred + alpha * res, vel + beta * res
        L[i], V[i] = lvl, vel
    L[:20] = V[:20] = np.nan
    return L, V


def supersmoother(x, p=10):
    a1 = np.exp(-1.414 * np.pi / p)
    b1 = 2 * a1 * np.cos(1.414 * np.pi / p)
    c2, c3 = b1, -a1 * a1
    c1 = 1 - c2 - c3
    xv = np.nan_to_num(np.asarray(x, float), nan=0.0)
    out = lfilter([c1 / 2, c1 / 2], [1, -c2, -c3], xv)
    out[: 4 * p] = np.nan
    return out


def highpass(x, p=48):
    a = (np.cos(0.707 * 2 * np.pi / p) + np.sin(0.707 * 2 * np.pi / p) - 1) / np.cos(0.707 * 2 * np.pi / p)
    b0 = (1 - a / 2) ** 2
    xv = np.nan_to_num(np.asarray(x, float), nan=0.0)
    out = lfilter([b0, -2 * b0, b0], [1, -2 * (1 - a), (1 - a) ** 2], xv)
    out[: 2 * p] = np.nan
    return out


def streak(c):
    s = np.sign(np.diff(c, prepend=c[0]))
    out = np.zeros(len(c))
    run = 0.0
    for i in range(1, len(c)):
        if s[i] == 0:
            run = 0.0
        elif s[i] == np.sign(run) or run == 0:
            run += s[i]
        else:
            run = s[i]
        out[i] = run
    return out


def fractals(h, l, k):
    """Williams fraktalı (k sol/sağ). Onay sağ kanat kapanınca → değer t-k'de, bilinme anı t."""
    n = len(h)
    hv, lv = window_view(h, 2 * k + 1), window_view(l, 2 * k + 1)
    mid = k
    fh = (hv[:, mid] == np.nanmax(hv, axis=1)) & ~np.isnan(hv[:, 0])
    fl = (lv[:, mid] == np.nanmin(lv, axis=1)) & ~np.isnan(lv[:, 0])
    # satır t penceresi [t-2k, t]; fraktal t-k barında, t'de onaylı
    last_h = pd.Series(np.where(fh, shift(h, k), np.nan)).ffill().values
    last_l = pd.Series(np.where(fl, shift(l, k), np.nan)).ffill().values
    return last_h, last_l


def prior_day_levels(d: pd.DataFrame, tf: str):
    """Önceki UTC gününün H/L/C'si (1d TF'de önceki bar)."""
    if tf == "1d":
        return shift(d.high.values, 1), shift(d.low.values, 1), shift(d.close.values, 1)
    day = d.ts.dt.floor("1D")
    g = d.groupby(day).agg(H=("high", "max"), L=("low", "min"), C=("close", "last"))
    g = g.shift(1)
    m = g.reindex(pd.DatetimeIndex(day))
    return m.H.values, m.L.values, m.C.values


def anchored_avg(d: pd.DataFrame, price, weight):
    day = d.ts.dt.floor("1D").values
    pw = pd.Series(price * weight).groupby(day).cumsum().values
    w = pd.Series(weight).groupby(day).cumsum().values
    return pw / (w + EPS)


# ── ana hesap ───────────────────────────────────────────────────────────────
def compute(d: pd.DataFrame, tf: str) -> Book:
    import config
    if config.LIB == "variants":                       # EK-6
        from indicators_variants import compute_variants
        return compute_variants(d, tf)
    return compute_main(d, tf)


def compute_main(d: pd.DataFrame, tf: str) -> Book:
    o, h, l, c = (d[k].values.astype(float) for k in ("open", "high", "low", "close"))
    has_vol = "volume" in d.columns and np.nanmax(d["volume"].values) > 0
    v = d["volume"].values.astype(float) if has_vol else None
    B = Book()
    a14, a10, a20, a100 = atr(h, l, c, 14), atr(h, l, c, 10), atr(h, l, c, 20), atr(h, l, c, 100)
    hl2, hlc3 = (h + l) / 2, (h + l + c) / 3
    B.feat("atr_pct", a14 / c)

    def ma_states(ind, fam, m):
        B.pair(ind, fam, "px", gt(c, m), lt(c, m))
        B.pair(ind, fam, "slope", rising(m), falling(m))
        B.feat(f"dist_{ind}", (c - m) / (a14 + EPS))

    # 1) Hareketli ortalamalar
    for n in (20, 50, 200):
        ma_states(f"SMA{n}", "ma_general", sma(c, n))
    for n in (9, 21, 50, 200):
        ma_states(f"EMA{n}", "ma_general", ema(c, n))
    ma_states("WMA20", "ma_general", wma(c, 20))
    ma_states("HMA21", "ma_adaptive", wma(2 * wma(c, 10) - wma(c, 21), 4))
    e1 = ema(c, 20)
    e2 = ema(e1, 20)
    ma_states("DEMA20", "ma_adaptive", 2 * e1 - e2)
    ma_states("TEMA20", "ma_adaptive", 3 * e1 - 3 * e2 + ema(e2, 20))
    zl = c + (c - shift(c, 9))
    ma_states("ZLEMA20", "ma_adaptive", ema(zl, 20))
    m_, s_ = 0.85 * 8, 9 / 6.0
    ma_states("ALMA9", "ma_adaptive", conv_ma(c, np.exp(-((np.arange(9) - m_) ** 2) / (2 * s_ * s_))))
    ma_states("KAMA10", "ma_adaptive", kama(c))
    ma_states("MCG14", "ma_adaptive", mcginley(c))
    b_ = 0.7
    t1 = ema(c, 5)
    t2 = ema(t1, 5)
    t3_ = ema(t2, 5)
    t4 = ema(t3_, 5)
    t5 = ema(t4, 5)
    t6 = ema(t5, 5)
    ma_states("T3_5", "ma_adaptive", -b_ ** 3 * t6 + (3 * b_ ** 2 + 3 * b_ ** 3) * t5
              + (-6 * b_ ** 2 - 3 * b_ - 3 * b_ ** 3) * t4 + (1 + 3 * b_ + b_ ** 3 + 3 * b_ ** 2) * t3_)
    lsma, lslope, lcorr = linreg_stats(c, 25)
    ma_states("LSMA25", "regression_channel", lsma)
    if has_vol:
        ma_states("VWMA20", "ma_general", rsum(c * v, 20) / (rsum(v, 20) + EPS))
    e9, e21, e50, e200 = ema(c, 9), ema(c, 21), ema(c, 50), ema(c, 200)
    B.pair("XEMA9_21", "ma_basic_cross", "cross", gt(e9, e21), lt(e9, e21))
    B.pair("XEMA50_200", "ma_basic_cross", "golden", gt(e50, e200), lt(e50, e200))
    s50, s200 = sma(c, 50), sma(c, 200)
    B.pair("XSMA50_200", "ma_basic_cross", "golden", gt(s50, s200), lt(s50, s200))
    e20 = ema(c, 20)
    B.pair("RIBBON", "ma_basic_cross", "stack", gt(e20, e50) & gt(e50, e200), lt(e20, e50) & lt(e50, e200))

    # 2) ATR tabanlı trend takipçileri
    for p, m in ((10, 3.0), (10, 2.0)):
        st = supertrend(h, l, c, atr(h, l, c, p), m)
        B.pair(f"ST{p}_{m:g}", "supertrend", "dir", st == 1, st == -1)
    sar = psar(h, l)
    B.pair("PSAR", "psar", "dir", sar == 1, sar == -1)
    ut = atr_trail(c, a10, 1.0)
    B.pair("UTBOT", "halftrend_utbot", "dir", ut == 1, ut == -1)
    vs = atr_trail(c, a20, 2.0)
    B.pair("VOLSTOP", "atr_trailing", "dir", vs == 1, vs == -1)
    ht = halftrend(h, l, c, a100)
    B.pair("HALFTREND", "halftrend_utbot", "dir", ht == 1, ht == -1)
    rf = range_filter(c)
    B.pair("RANGEFILT", "halftrend_utbot", "dir", rf == 1, rf == -1)
    sh, sl_ = sma(h, 10), sma(l, 10)
    hlv = pd.Series(np.where(gt(c, sh), 1.0, np.where(lt(c, sl_), -1.0, np.nan))).ffill().values
    B.pair("SSL10", "halftrend_utbot", "dir", hlv == 1, hlv == -1)
    ce = chandelier(h, l, c, atr(h, l, c, 22))
    B.pair("CHANDELIER", "atr_trailing", "dir", ce == 1, ce == -1)
    fhs, fls = rmax(h, 10) - a10, rmin(l, 10) + a10
    stop_s, stop_l = rmax(fhs, 9), rmin(fls, 9)
    B.pair("CKSTOP", "atr_trailing", "brk", gt(c, stop_s), lt(c, stop_l))

    # 3) Ichimoku, Alligator, Aroon, Vortex, ADX, Choppiness, trend gücü
    ten = (rmax(h, 9) + rmin(l, 9)) / 2
    kij = (rmax(h, 26) + rmin(l, 26)) / 2
    spa, spb = shift((ten + kij) / 2, 26), shift((rmax(h, 52) + rmin(l, 52)) / 2, 26)
    top, bot = np.fmax(spa, spb), np.fmin(spa, spb)
    B.pair("ICHI", "ichimoku", "cloud", gt(c, top), lt(c, bot))
    B.pair("ICHI", "ichimoku", "tk", gt(ten, kij), lt(ten, kij))
    B.pair("ICHI", "ichimoku", "kumo_ahead", gt((ten + kij) / 2, (rmax(h, 52) + rmin(l, 52)) / 2),
           lt((ten + kij) / 2, (rmax(h, 52) + rmin(l, 52)) / 2))
    jaw, teeth, lips = shift(rma(hl2, 13), 8), shift(rma(hl2, 8), 5), shift(rma(hl2, 5), 3)
    B.pair("ALLIGATOR", "trend_followers_other", "stack", gt(lips, teeth) & gt(teeth, jaw), lt(lips, teeth) & lt(teeth, jaw))
    hv, lv = window_view(h, 26), window_view(l, 26)
    valid26 = ~np.isnan(hv[:, 0])
    au = np.where(valid26, 100 * np.nanargmax(np.nan_to_num(hv, nan=-np.inf), axis=1) / 25.0, np.nan)
    ad = np.where(valid26, 100 * np.nanargmin(np.nan_to_num(lv, nan=np.inf), axis=1) / 25.0, np.nan)
    B.pair("AROON25", "other_osc", "dom", gt(au, 70) & lt(ad, 30), gt(ad, 70) & lt(au, 30))
    B.feat("aroon_osc", au - ad)
    tr = true_range(h, l, c)
    vip = rsum(np.abs(h - shift(l, 1)), 14) / (rsum(tr, 14) + EPS)
    vim = rsum(np.abs(l - shift(h, 1)), 14) / (rsum(tr, 14) + EPS)
    B.pair("VORTEX14", "other_osc", "dom", gt(vip, vim), lt(vip, vim))
    B.feat("vortex_diff", vip - vim)
    up_m, dn_m = h - shift(h, 1), shift(l, 1) - l
    pdm = np.where((up_m > dn_m) & (up_m > 0), up_m, 0.0)
    mdm = np.where((dn_m > up_m) & (dn_m > 0), dn_m, 0.0)
    pdi, mdi = 100 * rma(pdm, 14) / (a14 + EPS), 100 * rma(mdm, 14) / (a14 + EPS)
    adx = rma(100 * np.abs(pdi - mdi) / (pdi + mdi + EPS), 14)
    B.pair("DMI14", "adx_dmi", "di", gt(pdi, mdi), lt(pdi, mdi))
    B.pair("ADX14", "adx_dmi", "trend_dir", gt(adx, 25) & gt(pdi, mdi), gt(adx, 25) & lt(pdi, mdi))
    B.feat("adx", adx)
    B.feat("di_diff", pdi - mdi)
    chop = 100 * np.log10(rsum(tr, 14) / (rmax(h, 14) - rmin(l, 14) + EPS)) / np.log10(14)
    B.pair("CHOP14", "regime_entropy", "regime", lt(chop, 38.2) & rising(e20), lt(chop, 38.2) & falling(e20))
    B.feat("chop", chop)
    _, _, corr20 = linreg_stats(c, 20)
    B.pair("TSIDX20", "trend_followers_other", "corr", gt(corr20, 0.8), lt(corr20, -0.8))
    er = np.abs(c - shift(c, 10)) / (rsum(np.abs(np.diff(c, prepend=np.nan)), 10) + EPS)
    B.pair("ER10", "regime_entropy", "eff_dir", gt(er, 0.5) & gt(c, shift(c, 10)), gt(er, 0.5) & lt(c, shift(c, 10)))
    B.feat("er10", er)

    # 4) Osilatörler
    for n in (14, 7, 2):
        r = rsi(c, n)
        hi, lo = (90, 10) if n == 2 else (70, 30)
        B.pair(f"RSI{n}", "rsi", "zone", gt(r, hi), lt(r, lo))
        B.pair(f"RSI{n}", "rsi", "mid", gt(r, 50), lt(r, 50))
        B.feat(f"rsi{n}", r)
    r14 = rsi(c, 14)
    sto_r = (r14 - rmin(r14, 14)) / (rmax(r14, 14) - rmin(r14, 14) + EPS) * 100
    srk = sma(sto_r, 3)
    srd = sma(srk, 3)
    B.pair("STOCHRSI", "stoch", "zone", gt(srk, 80), lt(srk, 20))
    B.pair("STOCHRSI", "stoch", "kd", gt(srk, srd), lt(srk, srd))
    k = sma((c - rmin(l, 14)) / (rmax(h, 14) - rmin(l, 14) + EPS) * 100, 3)
    dd = sma(k, 3)
    B.pair("STOCH14", "stoch", "zone", gt(k, 80), lt(k, 20))
    B.pair("STOCH14", "stoch", "kd", gt(k, dd), lt(k, dd))
    B.feat("stoch_k", k)
    wr = -100 * (rmax(h, 14) - c) / (rmax(h, 14) - rmin(l, 14) + EPS)
    B.pair("WILLR14", "other_osc", "zone", gt(wr, -20), lt(wr, -80))
    B.feat("willr", wr)
    tpv = window_view(hlc3, 20)
    mad = np.nanmean(np.abs(tpv - np.nanmean(tpv, axis=1, keepdims=True)), axis=1)
    cci = (hlc3 - sma(hlc3, 20)) / (0.015 * mad + EPS)
    B.pair("CCI20", "cci", "zone", gt(cci, 100), lt(cci, -100))
    B.pair("CCI20", "cci", "mid", gt(cci, 0), lt(cci, 0))
    B.feat("cci", cci / 100)
    ml = ema(c, 12) - ema(c, 26)
    sg = ema(ml, 9)
    B.pair("MACD", "macd", "hist", gt(ml, sg), lt(ml, sg))
    B.pair("MACD", "macd", "zero", gt(ml, 0), lt(ml, 0))
    B.feat("macd_hist_atr", (ml - sg) / (a14 + EPS))
    ppo = ml / (ema(c, 26) + EPS) * 100
    B.pair("PPO", "macd", "sig", gt(ppo, ema(ppo, 9)), lt(ppo, ema(ppo, 9)))
    tx = ema(ema(ema(np.log(c), 15), 15), 15)
    trix = (tx - shift(tx, 1)) * 1e4
    B.pair("TRIX15", "other_osc", "sig", gt(trix, ema(trix, 9)), lt(trix, ema(trix, 9)))
    B.feat("trix", trix)
    pc = np.diff(c, prepend=np.nan)
    tsi = 100 * ema(ema(pc, 25), 13) / (ema(ema(np.abs(pc), 25), 13) + EPS)
    B.pair("TSI", "other_osc", "sig", gt(tsi, ema(tsi, 13)), lt(tsi, ema(tsi, 13)))
    B.pair("TSI", "other_osc", "zero", gt(tsi, 0), lt(tsi, 0))
    B.feat("tsi", tsi)
    roc10 = 100 * (c / shift(c, 10) - 1)
    B.pair("ROC10", "momentum_roc", "zero", gt(roc10, 0), lt(roc10, 0))
    B.feat("roc10", roc10)
    mom = (c - shift(c, 10)) / (a14 + EPS)
    B.pair("MOM10", "momentum_roc", "strong", gt(mom, 2), lt(mom, -2))
    B.feat("mom10_atr", mom)
    su, sd_ = rsum(np.where(pc > 0, pc, 0), 14), rsum(np.where(pc < 0, -pc, 0), 14)
    cmo = 100 * (su - sd_) / (su + sd_ + EPS)
    B.pair("CMO14", "other_osc", "zone", gt(cmo, 50), lt(cmo, -50))
    B.feat("cmo", cmo)
    ao = sma(hl2, 5) - sma(hl2, 34)
    B.pair("AO", "other_osc", "zero", gt(ao, 0), lt(ao, 0))
    B.pair("AO", "other_osc", "color", rising(ao), falling(ao))
    acc = ao - sma(ao, 5)
    B.pair("AC", "other_osc", "zero", gt(acc, 0), lt(acc, 0))
    B.feat("ao_atr", ao / (a14 + EPS))
    bp = c - np.fmin(l, shift(c, 1))
    uo = 100 * (4 * rsum(bp, 7) / (rsum(tr, 7) + EPS) + 2 * rsum(bp, 14) / (rsum(tr, 14) + EPS)
                + rsum(bp, 28) / (rsum(tr, 28) + EPS)) / 7
    B.pair("UO", "other_osc", "zone", gt(uo, 70), lt(uo, 30))
    B.feat("uo", uo)
    rc = lambda n: 100 * (c / shift(c, n) - 1)
    kst = sma(rc(10), 10) + 2 * sma(rc(15), 10) + 3 * sma(rc(20), 10) + 4 * sma(rc(30), 15)
    B.pair("KST", "other_osc", "sig", gt(kst, sma(kst, 9)), lt(kst, sma(kst, 9)))
    cop = wma(rc(14) + rc(11), 10)
    B.pair("COPPOCK", "other_osc", "zero", gt(cop, 0), lt(cop, 0))
    dpo = c - shift(sma(c, 21), 21 // 2 + 1)
    B.pair("DPO21", "other_osc", "zero", gt(dpo, 0), lt(dpo, 0))
    mn9, mx9 = rmin(hl2, 9), rmax(hl2, 9)
    xv = np.clip(np.nan_to_num(((hl2 - mn9) / (mx9 - mn9 + EPS) - 0.5) * 0.66), -0.999, 0.999)
    vv = np.clip(lfilter([1.0], [1, -0.67], xv), -0.999, 0.999)
    fish = lfilter([0.5], [1, -0.5], np.log((1 + vv) / (1 - vv)))
    fish[:20] = np.nan
    B.pair("FISHER9", "fisher_schaff", "sig", gt(fish, shift(fish, 1)), lt(fish, shift(fish, 1)))
    B.pair("FISHER9", "fisher_schaff", "zone", gt(fish, 2), lt(fish, -2))
    B.feat("fisher", fish)
    m_ = ema(c, 23) - ema(c, 50)
    v1, v2 = rmin(m_, 10), rmax(m_, 10) - rmin(m_, 10)
    f1 = pd.Series(np.where(v2 > 0, (m_ - v1) / (v2 + EPS) * 100, np.nan)).ffill().fillna(50).values
    pf = lfilter([0.5], [1, -0.5], f1)
    v3, v4 = rmin(pf, 10), rmax(pf, 10) - rmin(pf, 10)
    f2 = pd.Series(np.where(v4 > 0, (pf - v3) / (v4 + EPS) * 100, np.nan)).ffill().fillna(50).values
    stc = lfilter([0.5], [1, -0.5], f2)
    stc[:80] = np.nan
    B.pair("STC", "fisher_schaff", "zone", gt(stc, 75), lt(stc, 25))
    B.pair("STC", "fisher_schaff", "dir", rising(stc), falling(stc))
    B.feat("stc", stc)
    num = ((c - o) + 2 * (shift(c, 1) - shift(o, 1)) + 2 * (shift(c, 2) - shift(o, 2)) + (shift(c, 3) - shift(o, 3))) / 6
    den = ((h - l) + 2 * (shift(h, 1) - shift(l, 1)) + 2 * (shift(h, 2) - shift(l, 2)) + (shift(h, 3) - shift(l, 3))) / 6
    rvi = sma(num, 10) / (sma(den, 10) + EPS)
    rsig = (rvi + 2 * shift(rvi, 1) + 2 * shift(rvi, 2) + shift(rvi, 3)) / 6
    B.pair("RVIG", "other_osc", "sig", gt(rvi, rsig), lt(rvi, rsig))
    bop = sma((c - o) / (h - l + EPS), 14)
    B.pair("BOP14", "other_osc", "zero", gt(bop, 0), lt(bop, 0))
    B.feat("bop", bop)
    e13 = ema(c, 13)
    B.pair("ELDERRAY", "other_osc", "power", gt(l, e13) & rising(e13), lt(h, e13) & falling(e13))
    pr = S(np.diff(c, prepend=np.nan) / c).rolling(100, min_periods=100).rank(pct=True).values * 100
    crsi = (rsi(c, 3) + rsi(streak(c), 2) + pr) / 3
    B.pair("CRSI", "rsi", "zone", gt(crsi, 90), lt(crsi, 10))
    B.feat("crsi", crsi)
    hh10, ll10 = rmax(h, 10), rmin(l, 10)
    smi = 100 * ema(ema(c - (hh10 + ll10) / 2, 3), 3) / (0.5 * ema(ema(hh10 - ll10, 3), 3) + EPS)
    B.pair("SMI", "other_osc", "zone", gt(smi, 40), lt(smi, -40))
    B.pair("SMI", "other_osc", "sig", gt(smi, ema(smi, 3)), lt(smi, ema(smi, 3)))
    B.feat("smi", smi)
    esa = ema(hlc3, 10)
    dwt = ema(np.abs(hlc3 - esa), 10)
    wt1 = ema((hlc3 - esa) / (0.015 * dwt + EPS), 21)
    wt2 = sma(wt1, 4)
    B.pair("WAVETREND", "wavetrend_cipher", "cross", gt(wt1, wt2), lt(wt1, wt2))
    B.pair("WAVETREND", "wavetrend_cipher", "zone", gt(wt1, 60), lt(wt1, -60))
    B.feat("wt1", wt1)
    qd, rsima = qqe_trend(c)
    B.pair("QQE", "qqe", "trend", qd == 1, qd == -1)
    B.pair("QQE", "qqe", "mid", gt(rsima, 50), lt(rsima, 50))
    lag = laguerre_rsi(c)
    B.pair("LAGRSI", "ehlers_dsp", "zone", gt(lag, 0.8), lt(lag, 0.2))
    B.feat("laguerre", lag)

    # 5) Oynaklık / bantlar / istatistik
    m20, s20 = sma(c, 20), rstd(c, 20)
    bbu, bbl = m20 + 2 * s20, m20 - 2 * s20
    B.pair("BB20", "bollinger", "band", gt(c, bbu), lt(c, bbl))
    B.pair("BB20", "bollinger", "mid", gt(c, m20), lt(c, m20))
    pctb = (c - bbl) / (bbu - bbl + EPS)
    B.feat("bb_pctb", pctb)
    bbw = (bbu - bbl) / (m20 + EPS)
    bbw_q = S(bbw).rolling(120, min_periods=120).quantile(0.2).values
    B.pair("BBW", "bollinger", "squeeze_dir", lt(bbw, bbw_q) & gt(c, m20), lt(bbw, bbw_q) & lt(c, m20))
    kcu, kcl = e20 + 2 * a20, e20 - 2 * a20
    B.pair("KC20", "keltner", "band", gt(c, kcu), lt(c, kcl))
    B.feat("kc_pos", (c - e20) / (2 * a20 + EPS))
    sq_on = lt(bbu, e20 + 1.5 * a20) & gt(bbl, e20 - 1.5 * a20)
    dm = c - ((rmax(h, 20) + rmin(l, 20)) / 2 + m20) / 2
    sqm, _, _ = linreg_stats(dm, 20)
    B.pair("TTMSQZ", "squeeze", "on_mom", sq_on & gt(sqm, 0), sq_on & lt(sqm, 0))
    B.pair("TTMSQZ", "squeeze", "mom", gt(sqm, 0) & rising(sqm), lt(sqm, 0) & falling(sqm))
    B.feat("sqz_mom_atr", sqm / (a14 + EPS))
    dh20, dl20 = shift(rmax(h, 20), 1), shift(rmin(l, 20), 1)
    B.pair("DONCH20", "donchian_turtle", "brk", gt(c, dh20), lt(c, dl20))
    dh55, dl55 = shift(rmax(h, 55), 1), shift(rmin(l, 55), 1)
    B.pair("DONCH55", "donchian_turtle", "brk", gt(c, dh55), lt(c, dl55))
    B.feat("donch_pos", (c - dl20) / (dh20 - dl20 + EPS))
    end100, slope100, corr100 = linreg_stats(c, 100)
    sres = rstd(c, 100) * np.sqrt(np.maximum(1 - corr100 ** 2, 0))
    chz = (c - end100) / (sres + EPS)
    B.pair("LRCH100", "regression_channel", "edge", gt(chz, 2), lt(chz, -2))
    B.pair("LRCH100", "regression_channel", "slope", gt(slope100, 0), lt(slope100, 0))
    B.feat("chan_z", chz)
    B.feat("lr_slope_atr", slope100 / (a14 + EPS))
    z20 = (c - m20) / (s20 + EPS)
    B.pair("Z20", "zscore_meanrev", "ext", gt(z20, 2), lt(z20, -2))
    z50 = (c - sma(c, 50)) / (rstd(c, 50) + EPS)
    B.pair("Z50", "zscore_meanrev", "ext", gt(z50, 2), lt(z50, -2))
    B.feat("z50", z50)
    ar = a14 / (a100 + EPS)
    B.pair("ATRR", "atr_vol", "regime_dir", gt(ar, 1.2) & gt(c, e20), gt(ar, 1.2) & lt(c, e20))
    B.feat("atr_ratio", ar)
    lr = np.diff(np.log(c), prepend=np.nan)
    hvr = rstd(lr, 20) / (rstd(lr, 100) + EPS)
    B.pair("HVR", "atr_vol", "contract_dir", lt(hvr, 0.7) & gt(c, e20), lt(hvr, 0.7) & lt(c, e20))
    B.feat("hv_ratio", hvr)
    rng_e = ema(h - l, 9)
    mass = rsum(rng_e / (ema(rng_e, 9) + EPS), 25)
    B.pair("MASS", "atr_vol", "bulge_dir", gt(mass, 27) & gt(c, e20), gt(mass, 27) & lt(c, e20))
    sdu = ema(np.where(pc > 0, rstd(c, 10), 0), 14)
    sdd = ema(np.where(pc < 0, rstd(c, 10), 0), 14)
    rvol_i = 100 * sdu / (sdu + sdd + EPS)
    B.pair("RVOLIDX", "atr_vol", "zone", gt(rvol_i, 60), lt(rvol_i, 40))
    ui = np.sqrt(sma((100 * (c - rmax(c, 14)) / (rmax(c, 14) + EPS)) ** 2, 14))
    B.feat("ulcer", ui)

    # 6) Ehlers / Kalman / kernel
    ss = supersmoother(c, 10)
    B.pair("SSMOOTH10", "ehlers_dsp", "px", gt(c, ss), lt(c, ss))
    B.pair("SSMOOTH10", "ehlers_dsp", "slope", rising(ss), falling(ss))
    roof = supersmoother(highpass(c, 48), 10)
    B.pair("ROOFING", "ehlers_dsp", "zero", gt(roof, 0), lt(roof, 0))
    B.pair("ROOFING", "ehlers_dsp", "dir", rising(roof), falling(roof))
    B.feat("roof_atr", roof / (a14 + EPS))
    kl, kv = kalman_ab(c)
    B.pair("KALMAN", "kalman", "vel", gt(kv, 0), lt(kv, 0))
    B.pair("KALMAN", "kalman", "px", gt(c, kl), lt(c, kl))
    w = np.exp(-(np.arange(50)[::-1] ** 2) / (2 * 8.0 ** 2))
    nw = conv_ma(c, w)
    mae = sma(np.abs(c - nw), 50) * 3
    B.pair("NWENV", "kernel_regression", "band", gt(c, nw + mae), lt(c, nw - mae))
    B.pair("NWENV", "kernel_regression", "slope", rising(nw), falling(nw))

    # 7) Hacim (yalnız hacim varsa) + VWAP/TWAP
    twap = anchored_avg(d, hlc3, np.ones(len(c)))
    B.pair("TWAP", "vwap", "px", gt(c, twap), lt(c, twap))
    if has_vol:
        vwap = anchored_avg(d, hlc3, v)
        dev = np.sqrt(np.maximum(anchored_avg(d, hlc3 ** 2, v) - vwap ** 2, 0))
        B.pair("VWAP", "vwap", "px", gt(c, vwap), lt(c, vwap))
        B.pair("VWAP", "vwap", "band2", gt(c, vwap + 2 * dev), lt(c, vwap - 2 * dev))
        obv = np.cumsum(np.sign(np.nan_to_num(pc)) * v)
        B.pair("OBV", "volume_classic", "ema", gt(obv, ema(obv, 20)), lt(obv, ema(obv, 20)))
        mf = hlc3 * v
        dtp = np.diff(hlc3, prepend=np.nan)
        mfr = rsum(np.where(dtp > 0, mf, 0), 14) / (rsum(np.where(dtp < 0, mf, 0), 14) + EPS)
        mfi = 100 - 100 / (1 + mfr)
        B.pair("MFI14", "volume_classic", "zone", gt(mfi, 80), lt(mfi, 20))
        B.feat("mfi", mfi)
        clv = ((c - l) - (h - c)) / (h - l + EPS)
        cmf = rsum(clv * v, 20) / (rsum(v, 20) + EPS)
        B.pair("CMF20", "volume_classic", "zone", gt(cmf, 0.1), lt(cmf, -0.1))
        B.feat("cmf", cmf)
        adl = np.cumsum(clv * v)
        cho = ema(adl, 3) - ema(adl, 10)
        B.pair("CHAIKINOSC", "volume_classic", "zero", gt(cho, 0), lt(cho, 0))
        pvt = np.cumsum(np.nan_to_num(pc / shift(c, 1)) * v)
        B.pair("PVT", "volume_classic", "ema", gt(pvt, ema(pvt, 20)), lt(pvt, ema(pvt, 20)))
        efi = ema(np.nan_to_num(pc) * v, 13)
        B.pair("EFI13", "volume_classic", "zero", gt(efi, 0), lt(efi, 0))
        eom = sma((hl2 - shift(hl2, 1)) / (v / 1e4 / (h - l + EPS) + EPS), 14)
        B.pair("EOM14", "volume_classic", "zero", gt(eom, 0), lt(eom, 0))
        trend_k = np.where(hlc3 > shift(hlc3, 1), 1.0, -1.0)
        kvo = ema(trend_k * v, 34) - ema(trend_k * v, 55)
        B.pair("KLINGER", "volume_classic", "sig", gt(kvo, ema(kvo, 13)), lt(kvo, ema(kvo, 13)))
        pvo = 100 * (ema(v, 12) - ema(v, 26)) / (ema(v, 26) + EPS)
        B.pair("PVO", "relative_volume", "expand_dir", gt(pvo, 0) & gt(c, o), gt(pvo, 0) & lt(c, o))
        rv = v / (sma(v, 20) + EPS)
        B.pair("RVOL", "relative_volume", "spike_bar", gt(rv, 2) & gt(c, o), gt(rv, 2) & lt(c, o))
        B.feat("rvol", rv)

    # 8) Seviyeler: pivot, önceki gün uçları
    PH, PL, PC = prior_day_levels(d, tf)
    P = (PH + PL + PC) / 3
    R1, S1 = 2 * P - PL, 2 * P - PH
    B.pair("PIVOT", "pivot_points", "p", gt(c, P), lt(c, P))
    B.pair("PIVOT", "pivot_points", "r1s1", gt(c, R1), lt(c, S1))
    B.pair("PDHL", "prior_levels_orb", "brk", gt(c, PH), lt(c, PL))
    B.feat("pivot_dist", (c - P) / (a14 + EPS))

    # 9) Piyasa yapısı (nedensel fraktal), likidite süpürmesi, FVG
    for kk in (2, 5):
        fh, fl = fractals(h, l, kk)
        B.pair(f"BOS{kk}", "smc_structure", "brk", gt(c, fh), lt(c, fl))
        brk = np.where(gt(c, fh), 1.0, np.where(lt(c, fl), -1.0, np.nan))
        struct = pd.Series(brk).ffill().values
        B.pair(f"STRUCT{kk}", "smc_structure", "trend", struct == 1, struct == -1)
        B.pair(f"SWEEP{kk}", "liquidity", "rej", lt(l, fl) & gt(c, fl), gt(h, fh) & lt(c, fh))
        B.feat(f"swing{kk}_pos", (c - fl) / (fh - fl + EPS))
    gap_min = 0.1 * a14
    B.pair("FVG", "fvg", "new", gt(l - shift(h, 2), gap_min), gt(shift(l, 2) - h, gap_min))

    # 10) Mum formasyonları + Heikin Ashi
    body, rng_ = np.abs(c - o), h - l + EPS
    uw, lw = h - np.fmax(o, c), np.fmin(o, c) - l
    po, pcl = shift(o, 1), shift(c, 1)
    B.pair("ENGULF", "candlestick", "pat", gt(c, o) & lt(pcl, po) & (c >= po) & (o <= pcl),
           lt(c, o) & gt(pcl, po) & (c <= po) & (o >= pcl))
    B.pair("HAMMER", "candlestick", "pat", (lw > 2 * body) & (uw < body) & (body / rng_ > 0.1),
           (uw > 2 * body) & (lw < body) & (body / rng_ > 0.1))
    B.pair("PINBAR", "candlestick", "pat", lw / rng_ > 0.66, uw / rng_ > 0.66)
    B.pair("MARUBOZU", "candlestick", "pat", (body / rng_ > 0.9) & (c > o), (body / rng_ > 0.9) & (c < o))
    ins = (h < shift(h, 1)) & (l > shift(l, 1))
    B.pair("INSIDE", "candlestick", "dir", ins & gt(c, o), ins & lt(c, o))
    outs = (h > shift(h, 1)) & (l < shift(l, 1))
    B.pair("OUTSIDE", "candlestick", "dir", outs & gt(c, o), outs & lt(c, o))
    up3 = gt(c, o) & gt(shift(c, 1), shift(o, 1)) & gt(shift(c, 2), shift(o, 2)) & gt(c, pcl) & gt(pcl, shift(c, 2))
    dn3 = lt(c, o) & lt(shift(c, 1), shift(o, 1)) & lt(shift(c, 2), shift(o, 2)) & lt(c, pcl) & lt(pcl, shift(c, 2))
    B.pair("3SOLDIERS", "candlestick", "pat", up3, dn3)
    B.add("DOJI", "candlestick", "doji", body / rng_ < 0.1)
    hac = (o + h + l + c) / 4
    hao = _ha_open(o, c, hac)              # HA_open_t = (HA_open_{t-1} + HA_close_{t-1}) / 2
    B.pair("HEIKIN", "heikin_renko", "color", gt(hac, hao), lt(hac, hao))
    ha_l, ha_h = np.fmin(l, np.fmin(hao, hac)), np.fmax(h, np.fmax(hao, hac))
    B.pair("HEIKIN", "heikin_renko", "strong", gt(hac, hao) & (np.abs(np.fmin(hao, hac) - ha_l) < 1e-9 * c + EPS),
           lt(hac, hao) & (np.abs(ha_h - np.fmax(hao, hac)) < 1e-9 * c + EPS))
    extended(B, d, tf, o, h, l, c, v, a14)
    return B


# ── EK-1: kapsam genişletmesi (fraktal yapı, profil, seviye aileleri) ───────
def fractal_points(h, l, k):
    """Onaylı fraktallar: (onay barı t, pivot barı t-k, değer) listeleri — t anında bilinir."""
    hv, lv = window_view(h, 2 * k + 1), window_view(l, 2 * k + 1)
    fh = (hv[:, k] == np.nanmax(hv, axis=1)) & ~np.isnan(hv[:, 0])
    fl = (lv[:, k] == np.nanmin(lv, axis=1)) & ~np.isnan(lv[:, 0])
    th, tl = np.flatnonzero(fh), np.flatnonzero(fl)
    return (th, th - k, h[th - k]), (tl, tl - k, l[tl - k])


def _last_two(conf_t, piv, val, n):
    """Her bar için son iki onaylı fraktalın (pivot indeksi, değeri)."""
    p1, v1, p2, v2 = (np.full(n, np.nan) for _ in range(4))
    for a, (t, p, v) in enumerate(zip(conf_t, piv, val)):
        end = conf_t[a + 1] if a + 1 < len(conf_t) else n
        p2[t:end], v2[t:end] = p, v
        if a > 0:
            p1[t:end], v1[t:end] = piv[a - 1], val[a - 1]
    return p1, v1, p2, v2


def _divergence(conf_t, piv, val, osc, n, bear, hold=5):
    st = np.zeros(n, bool)
    for a in range(1, len(conf_t)):
        p0, p1 = piv[a - 1], piv[a]
        if np.isnan(osc[p0]) or np.isnan(osc[p1]):
            continue
        price_ext = val[a] > val[a - 1] if bear else val[a] < val[a - 1]
        osc_wk = osc[p1] < osc[p0] if bear else osc[p1] > osc[p0]
        if price_ext and osc_wk:
            st[conf_t[a]: conf_t[a] + hold] = True
    return st


def _order_blocks(o, h, l, c, bos_up, bos_dn, life=100, look=10):
    n = len(c)
    bull, bear = np.zeros(n, bool), np.zeros(n, bool)
    zone_b = zone_s = None
    for t in range(1, n):
        if bos_up[t] and not bos_up[t - 1]:
            js = [j for j in range(max(0, t - look), t) if c[j] < o[j]]
            zone_b = (l[js[-1]], h[js[-1]], t) if js else zone_b
        if bos_dn[t] and not bos_dn[t - 1]:
            js = [j for j in range(max(0, t - look), t) if c[j] > o[j]]
            zone_s = (l[js[-1]], h[js[-1]], t) if js else zone_s
        if zone_b and t > zone_b[2]:
            if c[t] < zone_b[0] or t - zone_b[2] > life:
                zone_b = None
            elif l[t] <= zone_b[1]:
                bull[t] = True
        if zone_s and t > zone_s[2]:
            if c[t] > zone_s[1] or t - zone_s[2] > life:
                zone_s = None
            elif h[t] >= zone_s[0]:
                bear[t] = True
    return bull, bear


def _profile_poc(price, w, win=100, bins=24):
    n = len(price)
    poc = np.full(n, np.nan)
    for t in range(win, n):
        p, ww = price[t - win + 1: t + 1], w[t - win + 1: t + 1]
        lo, hi = p.min(), p.max()
        if hi <= lo:
            continue
        hist, edges = np.histogram(p, bins=bins, range=(lo, hi), weights=ww)
        k = int(hist.argmax())
        poc[t] = (edges[k] + edges[k + 1]) / 2
    return poc


def _double_tops(h, l, a14, k=5):
    """Son iki fraktal tepe ≤0,5 ATR farklı ve kapanış aradaki dibin altında → ayı; aynası boğa."""
    n = len(h)
    (th, ph, vh), (tl, pl, vl) = fractal_points(h, l, k)
    neck_dn, neck_up = np.full(n, np.nan), np.full(n, np.nan)
    for a in range(1, len(th)):
        p0, p1 = ph[a - 1], ph[a]
        if abs(vh[a] - vh[a - 1]) <= 0.5 * np.nan_to_num(a14[th[a]]) and p1 - p0 >= 2:
            end = th[a + 1] if a + 1 < len(th) else n
            neck_dn[th[a]:end] = np.min(l[p0:p1 + 1])
    for a in range(1, len(tl)):
        p0, p1 = pl[a - 1], pl[a]
        if abs(vl[a] - vl[a - 1]) <= 0.5 * np.nan_to_num(a14[tl[a]]) and p1 - p0 >= 2:
            end = tl[a + 1] if a + 1 < len(tl) else n
            neck_up[tl[a]:end] = np.max(h[p0:p1 + 1])
    return neck_up, neck_dn


def extended(B, d, tf, o, h, l, c, v, a14):
    n = len(c)
    (th, ph, vh), (tl, pl, vl) = fractal_points(h, l, 5)
    hp1, hv1, hp2, hv2 = _last_two(th, ph, vh, n)
    lp1, lv1, lp2, lv2 = _last_two(tl, pl, vl, n)
    r14 = rsi(c, 14)
    B.pair("RSIDIV", "divergence", "div", _divergence(tl, pl, vl, r14, n, bear=False),
           _divergence(th, ph, vh, r14, n, bear=True))
    B.pair("SRPROX", "sr_zones", "touch", lt(np.abs(c - lv2), 0.3 * a14) & gt(c, lv2),
           lt(np.abs(c - hv2), 0.3 * a14) & lt(c, hv2))
    pos = (c - lv2) / (hv2 - lv2 + EPS)
    B.pair("PREMDISC", "premium_discount", "zone", lt(pos, 0.3) & gt(pos, 0), gt(pos, 0.7) & lt(pos, 1))
    B.pair("SWINGLEG", "zigzag_swing", "leg", gt(hp2, lp2), lt(hp2, lp2))   # son pivot tepe → yükseliş bacağı bitti
    up_leg = gt(hp2, lp2)
    rng_leg = hv2 - lv2
    retr_up = (hv2 - c) / (rng_leg + EPS)
    retr_dn = (c - lv2) / (rng_leg + EPS)
    B.pair("FIBGP", "fibonacci", "pocket", up_leg & gt(retr_up, 0.5) & lt(retr_up, 0.786),
           ~up_leg & ok(hp2, lp2) & gt(retr_dn, 0.5) & lt(retr_dn, 0.786))
    width = (rmax(h, 20) - rmin(l, 20)) / (a14 + EPS)
    tight = lt(shift(width, 1), 4.0)
    B.pair("DARVAS", "range_consolidation", "brk", tight & gt(c, shift(rmax(h, 20), 1)),
           tight & lt(c, shift(rmin(l, 20), 1)))
    B.pair("NBARREV", "reversal_detect", "rev", gt(c, shift(h, 1)) & lt(shift(c, 1), shift(c, 2)) & lt(shift(c, 2), shift(c, 3)),
           lt(c, shift(l, 1)) & gt(shift(c, 1), shift(c, 2)) & gt(shift(c, 2), shift(c, 3)))
    fh2, fl2 = fractals(h, l, 2)
    obb, obs = _order_blocks(_lst(o), _lst(h), _lst(l), _lst(c), gt(c, fh2), lt(c, fl2))
    B.pair("ORDERBLOCK", "order_block", "retest", obb, obs)
    slope_h = (hv2 - hv1) / (hp2 - hp1 + EPS)
    line_h = hv2 + slope_h * (np.arange(n) - hp2)
    slope_l = (lv2 - lv1) / (lp2 - lp1 + EPS)
    line_l = lv2 + slope_l * (np.arange(n) - lp2)
    B.pair("TRENDLINE", "trendlines", "brk", lt(slope_h, 0) & gt(c, line_h), gt(slope_l, 0) & lt(c, line_l))
    neck_up, neck_dn = _double_tops(h, l, a14)
    B.pair("DBLTOPBOT", "chart_patterns", "neck", gt(c, neck_up), lt(c, neck_dn))
    w = v if v is not None else np.ones(n)
    poc = _profile_poc((h + l + c) / 3, w)
    B.pair("PROFILEPOC", "volume_profile", "px", gt(c, poc), lt(c, poc))
    B.feat("poc_dist", (c - poc) / (a14 + EPS))
    pr100 = S(c).rolling(100, min_periods=100).rank(pct=True).values
    B.pair("PCTRANK100", "stats_prob", "ext", gt(pr100, 0.9), lt(pr100, 0.1))
    if v is not None:
        cd = np.cumsum(np.sign(c - o) * v)
        B.pair("SYNDELTA", "orderflow_delta", "ema", gt(cd, ema(cd, 20)), lt(cd, ema(cd, 20)))
    if tf == "1d":
        per = d.ts.dt.to_period("W").astype(str).values
    else:
        per = d.ts.dt.floor("1D").values
    popen = pd.Series(o).groupby(per).transform("first").values
    B.pair("HTFOPEN", "htf_overlay", "px", gt(c, popen), lt(c, popen))
    step = 10.0 ** (np.floor(np.log10(np.maximum(c, EPS))) - 2)
    frac = (c % step) / step
    B.pair("ROUNDNUM", "gann_round", "near", lt(frac, 0.15), gt(frac, 0.85))


def _ha_open(o, c, hac):
    n = len(o)
    out = np.empty(n)
    out[0] = (o[0] + c[0]) / 2
    hc = _lst(hac)
    prev = out[0]
    for i in range(1, n):
        prev = (prev + hc[i - 1]) / 2
        out[i] = prev
    return out
