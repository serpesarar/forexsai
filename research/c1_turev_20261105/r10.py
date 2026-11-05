import numpy as np, pandas as pd, yfinance as yf
from c3b_core import sim
def rep(l, tr, idx, base):
    if len(tr) < 8: print(f"{l:34s} n={len(tr)}"); return
    x = pd.Series([t[2] for t in tr], index=[idx[t[0]] for t in tr]); hd = np.mean([t[1] - t[0] for t in tr]); ex = x - base * hd; eq = x.cumsum()
    u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S_, N_ = np.bincount(inv, ex.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (3000, len(u))); h = len(x) // 2
    print(f"{l:34s} n={len(x):3d} ort={x.mean():6.1f} taban×süre={base*hd:6.1f} fazla={ex.mean():6.1f} P(fazla)={((S_[ix].sum(1)/N_[ix].sum(1))>0).mean():.3f} isabet={(x>0).mean():.3f} y1={ex.iloc[:h].mean():6.1f} y2={ex.iloc[h:].mean():6.1f} süre={hd:.1f} kötü={x.min():6.0f} DD={(eq-eq.cummax()).min():6.0f}")
def load(t, a="2001-01-01", b="2018-05-20"):
    q = yf.Ticker(t).history(start=a, end=b, auto_adjust=False)["Close"].dropna(); q.index = q.index.tz_localize(None); return q
def rsi2(s):
    g = s.diff(); u = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); d = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean(); return 100 - 100 / (1 + u / (d + 1e-12))
def fam(tk, lst, a="2001-01-01", b="2018-05-20", cost=3e-4):
    q = load(tk, a, b); S = q.to_numpy(); I = q.index; base = float(((q.shift(-1) / q - 1) * 1e4).mean()) - 2; print(f"\n=== {tk} {a[:4]}-{b[:4]} n={len(q)} taban/gün(fin sonrası)={base:.2f}")
    sp = float(np.mean(S)) * cost
    up = lambda i, mh=5: next((k for k in range(i + 1, min(i + mh + 1, len(S))) if S[k] > S[k - 1]), min(i + mh, len(S) - 1))
    for nm, c, ex in lst:
        if nm == "C3b": e = (rsi2(q) < 10).to_numpy(); rep("C3b", sim(S, S, e, up, sp, 2, 5), I, base); continue
        if nm == "C3": e = (rsi2(q) < 10).to_numpy(); rep("C3 h1", sim(S, S, e, lambda i: i + 1, sp, 2, 1), I, base); continue
        if nm == "tom":
            ii = pd.Series(I); tm = ii.groupby([I.year, I.month]).cumcount().to_numpy(); tmr = ii.groupby([I.year, I.month]).cumcount(ascending=False).to_numpy(); rep("ay dönümü h1", sim(S, S, (tmr < 2) | (tm < 3), lambda i: i + 1, sp, 2, 1), I, base); continue
        N = c
        hi = (q >= q.rolling(N).max()).to_numpy(); lo = (q <= q.rolling(N).min()).to_numpy()
        rep(nm, sim(S, S, hi if "zirve" in nm else lo, lambda i, h=ex: i + h, sp, 2, ex), I, base)
fam("GC=F", [("20g zirve h1", 20, 1), ("20g zirve h3", 20, 3), ("55g zirve h5", 55, 5), ("20g dip h5", 20, 5), ("10g dip h3", 10, 3), ("5g dip h5", 5, 5), ("tom", 0, 0), ("C3b", 0, 0), ("C3", 0, 0)])
fam("CL=F", [("55g zirve h5", 55, 5), ("55g zirve h10", 55, 10), ("20g zirve h3", 20, 3), ("10g dip h5", 10, 5), ("5g dip h10", 5, 10), ("C3b", 0, 0), ("C3", 0, 0)])
for t in ("SPY", "DIA", "IWM", "EFA"):
    fam(t, [("C3b", 0, 0), ("C3", 0, 0)], a="2003-01-01", b="2026-11-05", cost=1.5e-4)
fam("GC=F", [("C3b", 0, 0)], a="2018-05-20", b="2026-11-05"); fam("CL=F", [("C3b", 0, 0)], a="2018-05-20", b="2026-11-05")
