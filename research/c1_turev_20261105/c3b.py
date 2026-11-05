import numpy as np, pandas as pd, yfinance as yf
from lab2 import *
from r4_core import series, feats
pd.set_option("display.width", 220)
def sim(S, E, entry, exit_fn, sp, fin, maxh):
    tr, i, n = [], 0, len(S)
    while i < n:
        if entry[i]:
            j = exit_fn(i); j = min(j, n - 1)
            if j > i:
                tr.append((i, j, (E[j] / (E[i] + sp) - 1) * 1e4 - fin * (j - i))); i = j; continue
        i += 1
    return tr
def rep(l, tr, idx, base=None):
    x = pd.Series([t[2] for t in tr], index=[idx[t[0]] for t in tr]); hd = np.mean([t[1] - t[0] for t in tr]); eq = x.cumsum()
    u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S_, N_ = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (3000, len(u))); h = len(x) // 2
    print(f"{l:36s} n={len(x):3d} ort={x.mean():6.1f} med={x.median():6.1f} isabet={(x>0).mean():.3f} P={((S_[ix].sum(1)/N_[ix].sum(1))>0).mean():.3f} y1={x.iloc[:h].mean():6.1f} y2={x.iloc[h:].mean():6.1f} süre={hd:.1f}g top={x.sum():6.0f} kötü={x.min():6.0f} DD={(eq-eq.cummax()).min():6.0f}" + (f" taban/gün×süre={base*hd:.1f}" if base is not None else ""))
    return x
s = series("NAS100", "M30", 930); f = feats(s, "NAS100"); S = s.S.to_numpy(); E = s.E.to_numpy(); idx = s.index; base = float(((s.E.shift(-1) / s.E - 1) * 1e4).mean())
up_exit = lambda i, mh=5: next((k for k in range(i + 1, min(i + mh + 1, len(S))) if S[k] > S[k - 1]), min(i + mh, len(S) - 1))
m = (f.rsi2 < 10).to_numpy()
print("taban gün", round(base, 2))
x0 = rep("C3 h=1", sim(S, E, m, lambda i: i + 1, 1.3, 2, 1), idx, base)
x1 = rep("C3b ilk yükselen ≤5g", sim(S, E, m, up_exit, 1.3, 2, 5), idx, base)
print(x1.groupby(x1.index.year).agg(["size", "mean", lambda q: (q > 0).mean()]).round(2).T.to_string())
rep("C3b ≤3g", sim(S, E, m, lambda i: up_exit(i, 3), 1.3, 2, 3), idx, base); rep("C3b ≤10g", sim(S, E, m, lambda i: up_exit(i, 10), 1.3, 2, 10), idx, base)
rep("C3b spread×3 fin 3", sim(S, E, m, up_exit, 3.9, 3, 5), idx, base)
ma5 = pd.Series(S).rolling(5).mean().to_numpy(); ex_ma = lambda i: next((k for k in range(i + 1, min(i + 11, len(S))) if S[k] > ma5[k]), min(i + 10, len(S) - 1)); rep("C3c S>MA5 ≤10g (Connors)", sim(S, E, m, ex_ma, 1.3, 2, 10), idx, base)
low55 = (s.S <= s.S.rolling(55).min()).to_numpy(); low20 = (s.S <= s.S.rolling(20).min()).to_numpy()
y4 = rep("C4 55g dip h=10", sim(S, E, low55, lambda i: i + 10, 1.3, 2, 10), idx, base); print(y4.round(0).groupby(y4.index.year).agg(["size", "mean"]).round(0).T.to_string())
rep("C4 55g dip h=5", sim(S, E, low55, lambda i: i + 5, 1.3, 2, 5), idx, base); rep("C4 55g dip h=20", sim(S, E, low55, lambda i: i + 20, 1.3, 2, 20), idx, base); rep("C4 20g dip h=10", sim(S, E, low20, lambda i: i + 10, 1.3, 2, 10), idx, base)
print("--- QQQ bağımsız (kapanış→kapanış, 4 bp giriş + 2 bp/gece)")
q = yf.Ticker("QQQ").history(start="1999-03-10", end="2026-11-05", auto_adjust=True); q.index = q.index.tz_localize(None); Sq = q.Close.to_numpy(); iq = q.index
g = q.Close.diff(); up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean(); r2 = (100 - 100 / (1 + up / (dn + 1e-12))).to_numpy()
upq = lambda i, mh=5: next((k for k in range(i + 1, min(i + mh + 1, len(Sq))) if Sq[k] > Sq[k - 1]), min(i + mh, len(Sq) - 1))
lowq = (q.Close <= q.Close.rolling(55).min()).to_numpy()
for a, b in (("1999", "2003"), ("2003", "2009"), ("2009", "2014"), ("2014", "2018"), ("2018", "2027")):
    k = (iq >= a) & (iq < b); ids = np.flatnonzero(k); lo, hi = ids[0], ids[-1] + 1; S_ = Sq[lo:hi]; r_ = r2[lo:hi]; l_ = lowq[lo:hi]; i_ = iq[lo:hi]; bq = (Sq[lo + 1:hi] / Sq[lo:hi - 1] - 1).mean() * 1e4
    u_ = lambda i: next((k_ for k_ in range(i + 1, min(i + 6, len(S_))) if S_[k_] > S_[k_ - 1]), min(i + 5, len(S_) - 1))
    rep(f"QQQ C3b {a}-{b}", sim(S_, S_, r_ < 10, u_, S_.mean() * 2e-4, 2, 5), i_, bq); rep(f"QQQ C4 {a}-{b}", sim(S_, S_, l_, lambda i: i + 10, S_.mean() * 2e-4, 2, 10), i_, bq)
