import numpy as np, pandas as pd, yfinance as yf
from lab2 import *
from r4_core import series, feats
MAC2 = yf.Ticker("^VIX").history(start="2008-01-01", end="2026-11-06")["Close"]; MAC2.index = MAC2.index.tz_localize(None).normalize()
vj = MAC2.pct_change().shift(1) * 100
def rep(lab, x, b):
    x = x.dropna(); b = b.dropna()
    if len(x) < 8: print(lab, "n", len(x)); return
    u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (4000, len(u))); bm = S[ix].sum(1) / N[ix].sum(1); h = len(x) // 2
    print(f"{lab:40s} n={len(x):3d} ort={x.mean():6.1f} isabet={(x>0).mean():.2f} taban={b.mean():5.1f} P(taban)={np.mean(bm>b.mean()):.3f} P(0)={np.mean(bm>0):.3f} y1={x.iloc[:h].mean():6.1f} y2={x.iloc[h:].mean():6.1f}")
def hs(sym, dm, a="2010-05-01", b="2018-05-20"):
    x = mt5_bars(sym, "H1"); x = x[(x.ts_et >= a) & (x.ts_et < b) & (x.ts_et.dt.dayofweek < 5)].reset_index(drop=True); x["d"] = x.ts_et.dt.normalize(); x["m"] = x.ts_et.dt.hour * 60
    k = x.m == dm; ent = x[k]; s = pd.DataFrame({"S": x.c.shift(1)[k].to_numpy(), "E": ent.o.to_numpy()}, index=ent.d); return s[~s.index.duplicated()]
def rsi2(S):
    g = S.diff(); up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean(); return 100 - 100 / (1 + up / (dn + 1e-12))
print("=== O1 petrol: VIX sıçrama kısa")
for hour in (900, 840, 960):
    s = hs("SpotCrude", hour); r = (s.E / (s.E.shift(-1) + .03) - 1) * 1e4 - .5; m = vj.reindex(s.index, method="ffill") > 10; rep(f"O1 2010-18 saat {hour//60}", r[m], r)
    y = {yy: r[m][r[m].index.year == yy].mean() for yy in range(2010, 2019)}; print("   yıl:", {k: round(v, 0) for k, v in y.items() if v == v})
print("=== X1 altın: RSI2<10 ∧ NAS100 RSI2>50")
for hour in (480, 540, 900):
    s = hs("XAUUSD", hour); n = hs("NAS100", hour); rn = rsi2(n.S).reindex(s.index, method="ffill"); rx = rsi2(s.S); r = ((s.E.shift(-1)) / (s.E + .25) - 1) * 1e4 - 2; rep(f"X1 2010-18 saat {hour//60}", r[(rx < 10) & (rn > 50)], r); rep(f"  yalnız RSI2<10", r[rx < 10], r)
print("=== C3 NDX 2010-18 H1 (görülmemiş broker)")
s = hs("NAS100", 900); r = (s.E.shift(-1) / (s.E + 1.3) - 1) * 1e4 - 2; rx = rsi2(s.S); rep("C3 NDX H1 2010-18", r[rx < 10], r)
print("=== T6 C1 × C3")
s = series("NAS100", "M30", 930); f = feats(s, "NAS100"); c3 = (f.rsi2 < 10).shift(1).fillna(False)
Ds = {nm: build2("NAS100", tf, 570, 955, a=a, b=b) for nm, tf, a, b in (("M30", "M30", "2018-05-25", "2026-11-05"), ("M15", "M15", "2022-08-15", "2026-11-05"), ("M5", "M5", "2025-06-15", "2026-11-05"))}
from lab2 import brk
for nm, days in Ds.items():
    bar, orl = {"M30": (30, 30), "M15": (15, 30), "M5": (5, 15)}[nm]
    for lab, fl in (("C1", lambda d: d.f["vix"] >= 18.4), ("C1∧dün C3", lambda d: d.f["vix"] >= 18.4 and bool(c3.get(pd.Timestamp(d.d), False))), ("C1∧dün C3 değil", lambda d: d.f["vix"] >= 18.4 and not bool(c3.get(pd.Timestamp(d.d), False))), ("ORB∧dün C3 (vix fark etmez)", lambda d: bool(c3.get(pd.Timestamp(d.d), False))), ("VIX altı∧dün C3", lambda d: d.f["vix"] < 18.4 and bool(c3.get(pd.Timestamp(d.d), False)))):
        rows = []
        for d in days:
            if fl(d):
                z = brk(d, bar, orl, 1, 570, 930, 955, 1.3)
                if z: rows.append((str(d.d), *z))
        print(nm, lab, metrics(rows))
