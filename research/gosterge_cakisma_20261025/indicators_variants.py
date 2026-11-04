"""EK-6: parametre varyantı kütüphanesi — topluluk scriptlerinin büyük kısmı aynı ailenin farklı parametreleridir.

Ana kütüphanedeki (indicators.py) varsayılanların dışındaki yaygın parametre setleri. Aynı nedensel yardımcılar,
aynı boğa/ayı çifti biçimi; `fam` kodları aynı. Ayrı koşu: GCM_LIB=variants → results_V/.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indicators import (Book, EPS, atr, atr_trail, ema, fractals, gt, linreg_stats, lt, psar, qqe_trend, rising,
                        falling, rma, rmax, rmin, rsi, rstd, shift, sma, supertrend, wma)


def _ma_px(B, ind, fam, c, m):
    B.pair(ind, fam, "px", gt(c, m), lt(c, m))
    B.pair(ind, fam, "slope", rising(m), falling(m))


def compute_variants(d: pd.DataFrame, tf: str) -> Book:
    o, h, l, c = (d[k].values.astype(float) for k in ("open", "high", "low", "close"))
    B = Book()
    a14 = atr(h, l, c, 14)
    B.feat("atr_pct", a14 / c)
    # Hareketli ortalama uzunlukları ve kesişimleri
    for n in (5, 13, 34, 89, 100):
        _ma_px(B, f"vEMA{n}", "ma_general", c, ema(c, n))
    for n in (5, 10, 100):
        _ma_px(B, f"vSMA{n}", "ma_general", c, sma(c, n))
    for n in (9, 55):
        _ma_px(B, f"vHMA{n}", "ma_adaptive", c, wma(2 * wma(c, n // 2) - wma(c, n), int(np.sqrt(n))))
    for f_, s_ in ((5, 13), (8, 21), (13, 34), (20, 50)):
        B.pair(f"vXEMA{f_}_{s_}", "ma_basic_cross", "cross", gt(ema(c, f_), ema(c, s_)), lt(ema(c, f_), ema(c, s_)))
    for f_, s_ in ((10, 30), (20, 50)):
        B.pair(f"vXSMA{f_}_{s_}", "ma_basic_cross", "cross", gt(sma(c, f_), sma(c, s_)), lt(sma(c, f_), sma(c, s_)))
    # ATR trend takipçileri
    for p, m in ((7, 3.0), (10, 1.0), (14, 2.0), (20, 5.0), (22, 3.0)):
        st = supertrend(h, l, c, atr(h, l, c, p), m)
        B.pair(f"vST{p}_{m:g}", "supertrend", "dir", st == 1, st == -1)
    for a_, p in ((2.0, 10), (1.0, 14), (3.0, 10)):
        ut = atr_trail(c, atr(h, l, c, p), a_)
        B.pair(f"vUT{a_:g}_{p}", "halftrend_utbot", "dir", ut == 1, ut == -1)
    for a0, amax in ((0.01, 0.1), (0.04, 0.4)):
        sar = psar(h, l, a0, a0, amax)
        B.pair(f"vPSAR{a0:g}", "psar", "dir", sar == 1, sar == -1)
    # Osilatörler
    for n, hi, lo in ((3, 80, 20), (5, 80, 20), (9, 70, 30), (21, 70, 30), (28, 60, 40)):
        r = rsi(c, n)
        B.pair(f"vRSI{n}", "rsi", "zone", gt(r, hi), lt(r, lo))
        B.pair(f"vRSI{n}", "rsi", "mid", gt(r, 50), lt(r, 50))
    for kn, ks, dn in ((5, 3, 3), (9, 3, 3), (21, 5, 5)):
        k = sma((c - rmin(l, kn)) / (rmax(h, kn) - rmin(l, kn) + EPS) * 100, ks)
        dd = sma(k, dn)
        B.pair(f"vSTOCH{kn}", "stoch", "zone", gt(k, 80), lt(k, 20))
        B.pair(f"vSTOCH{kn}", "stoch", "kd", gt(k, dd), lt(k, dd))
    for f_, s_, g_ in ((5, 35, 5), (8, 17, 9), (19, 39, 9)):
        ml = ema(c, f_) - ema(c, s_)
        sg = ema(ml, g_)
        B.pair(f"vMACD{f_}_{s_}", "macd", "hist", gt(ml, sg), lt(ml, sg))
        B.pair(f"vMACD{f_}_{s_}", "macd", "zero", gt(ml, 0), lt(ml, 0))
    hlc3 = (h + l + c) / 3
    for n in (14, 50):
        m_ = sma(hlc3, n)
        mad = sma(np.abs(hlc3 - m_), n)                # yaklaşık ortalama sapma (nedensel)
        cci = (hlc3 - m_) / (0.015 * mad + EPS)
        B.pair(f"vCCI{n}", "cci", "zone", gt(cci, 100), lt(cci, -100))
    wr = -100 * (rmax(h, 21) - c) / (rmax(h, 21) - rmin(l, 21) + EPS)
    B.pair("vWILLR21", "other_osc", "zone", gt(wr, -20), lt(wr, -80))
    for n in (7, 21):
        up_m, dn_m = h - shift(h, 1), shift(l, 1) - l
        pdm = np.where((up_m > dn_m) & (up_m > 0), up_m, 0.0)
        mdm = np.where((dn_m > up_m) & (dn_m > 0), dn_m, 0.0)
        an = atr(h, l, c, n)
        pdi, mdi = 100 * rma(pdm, n) / (an + EPS), 100 * rma(mdm, n) / (an + EPS)
        adx = rma(100 * np.abs(pdi - mdi) / (pdi + mdi + EPS), n)
        B.pair(f"vADX{n}", "adx_dmi", "trend_dir", gt(adx, 25) & gt(pdi, mdi), gt(adx, 25) & lt(pdi, mdi))
    for n1, n2 in ((9, 12), (5, 10)):
        esa = ema(hlc3, n1)
        dwt = ema(np.abs(hlc3 - esa), n1)
        wt1 = ema((hlc3 - esa) / (0.015 * dwt + EPS), n2)
        wt2 = sma(wt1, 4)
        B.pair(f"vWT{n1}_{n2}", "wavetrend_cipher", "cross", gt(wt1, wt2), lt(wt1, wt2))
        B.pair(f"vWT{n1}_{n2}", "wavetrend_cipher", "zone", gt(wt1, 60), lt(wt1, -60))
    qd, _ = qqe_trend(c, 6, 3, 2.62)
    B.pair("vQQE6", "qqe", "trend", qd == 1, qd == -1)
    # Bantlar / kanallar
    for n, k in ((20, 1.5), (20, 2.5), (50, 2.0), (10, 2.0)):
        m_, s_ = sma(c, n), rstd(c, n)
        B.pair(f"vBB{n}_{k:g}", "bollinger", "band", gt(c, m_ + k * s_), lt(c, m_ - k * s_))
    for n, k in ((20, 1.5), (50, 2.0)):
        e_, a_ = ema(c, n), atr(h, l, c, n)
        B.pair(f"vKC{n}_{k:g}", "keltner", "band", gt(c, e_ + k * a_), lt(c, e_ - k * a_))
    for n in (10, 34, 100):
        B.pair(f"vDONCH{n}", "donchian_turtle", "brk", gt(c, shift(rmax(h, n), 1)), lt(c, shift(rmin(l, n), 1)))
    for n in (50, 200):
        end, slope, corr = linreg_stats(c, n)
        sres = rstd(c, n) * np.sqrt(np.maximum(1 - corr ** 2, 0))
        z = (c - end) / (sres + EPS)
        B.pair(f"vLRCH{n}", "regression_channel", "edge", gt(z, 2), lt(z, -2))
        B.pair(f"vLRCH{n}", "regression_channel", "slope", gt(slope, 0), lt(slope, 0))
    z100 = (c - sma(c, 100)) / (rstd(c, 100) + EPS)
    B.pair("vZ100", "zscore_meanrev", "ext", gt(z100, 2), lt(z100, -2))
    # Ichimoku (20, 60, 120) ve yapı (k=3, 10)
    ten = (rmax(h, 20) + rmin(l, 20)) / 2
    kij = (rmax(h, 60) + rmin(l, 60)) / 2
    spa, spb = shift((ten + kij) / 2, 60), shift((rmax(h, 120) + rmin(l, 120)) / 2, 60)
    B.pair("vICHI20", "ichimoku", "cloud", gt(c, np.fmax(spa, spb)), lt(c, np.fmin(spa, spb)))
    B.pair("vICHI20", "ichimoku", "tk", gt(ten, kij), lt(ten, kij))
    for kk in (3, 10):
        fh, fl = fractals(h, l, kk)
        B.pair(f"vBOS{kk}", "smc_structure", "brk", gt(c, fh), lt(c, fl))
        B.pair(f"vSWEEP{kk}", "liquidity", "rej", lt(l, fl) & gt(c, fl), gt(h, fh) & lt(c, fh))
    return B
