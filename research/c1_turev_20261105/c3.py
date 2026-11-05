import numpy as np, pandas as pd, yfinance as yf
from lab2 import *
from r4_core import series, feats
pd.set_option("display.width", 220)
sp, FIN = 1.3, 2.0
def run(sym="NAS100", tf="M30", dm=930, th=10, h=1, rsi_col="rsi2", sp=sp, fin=FIN, cond=None, stopk=None):
    s = series(sym, tf, dm); f = feats(s, sym); m = f[rsi_col] < th
    if cond is not None: m &= cond(f)
    e = s.E + sp; ex = s.E.shift(-h); r = (ex / e - 1) * 1e4 - fin * h
    if stopk:
        x = mt5_bars(sym, tf).set_index("ts_et")
        out = r.copy(); idx = s.index
        for i, d in enumerate(idx):
            if not m.iat[i] or i + h >= len(idx): continue
            t0 = d + pd.Timedelta(minutes=dm); t1 = idx[i + h] + pd.Timedelta(minutes=dm); w = x.loc[t0:t1 - pd.Timedelta(minutes=1)]
            st = e.iat[i] * (1 - stopk * f.dvol.iat[i] / 1e4)
            if len(w) and w.l.min() <= st:
                j = w.l.values <= st; px = min(st, w.o.values[np.argmax(j)]); out.iat[i] = (px / e.iat[i] - 1) * 1e4 - fin * h
        r = out
    return r[m].dropna(), r.dropna()
def rep(lab, x, b=None):
    u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (3000, len(u))); bm = S[ix].sum(1) / N[ix].sum(1); h = len(x) // 2; eq = x.cumsum()
    print(f"{lab:36s} n={len(x):3d} ort={x.mean():6.1f} med={x.median():6.1f} isabet={(x>0).mean():.3f} P={np.mean(bm>0):.3f} y1={x.iloc[:h].mean():5.1f} y2={x.iloc[h:].mean():5.1f} top_bp={x.sum():6.0f} en_kötü={x.min():6.0f} DD={ (eq-eq.cummax()).min():6.0f}" + (f" taban={b.mean():.1f}" if b is not None else ""))
x, b = run(); rep("ANA 15:30 rsi2<10 h1", x, b)
print(pd.DataFrame({"n": x.groupby(x.index.year).size(), "ort": x.groupby(x.index.year).mean().round(1), "isabet": x.groupby(x.index.year).apply(lambda s: round((s > 0).mean(), 2)), "taban": b.groupby(b.index.year).mean().round(1)}).T.to_string())
print("--- eşik"); [rep(f"rsi2<{t}", run(th=t)[0]) for t in (5, 10, 15, 20, 25)]
print("--- saat"); rep("M15 15:45", *run(tf="M15", dm=945)); rep("M5 15:55", *run(tf="M5", dm=955)); rep("M30 15:00", *run(dm=900)); rep("M30 14:00", *run(dm=840)); rep("M30 09:30", *run(dm=570))
print("--- süre"); [rep(f"h={h}", *run(h=h)) for h in (1, 2, 3, 5)]
print("--- spread/finans"); rep("spread 3,4 fin 3", run(sp=3.4, fin=3.0)[0]); rep("spread 5 fin 4", run(sp=5.0, fin=4.0)[0])
print("--- stop"); [rep(f"felaket stop {k}×dvol", run(stopk=k)[0]) for k in (1.0, 1.5, 2.0, 3.0)]
print("--- rejim"); rep("vix≥18,4", run(cond=lambda f: f.vix >= 18.4)[0]); rep("vix<18,4", run(cond=lambda f: f.vix < 18.4)[0]); rep("ma200+", run(cond=lambda f: f.ma200)[0]); rep("ma200−", run(cond=lambda f: ~f.ma200)[0])
print("--- gün"); [rep(f"giriş gün {dn}", x[x.index.dayofweek == i]) for i, dn in enumerate(["Pzt", "Sal", "Çar", "Per", "Cum"]) if (x.index.dayofweek == i).sum() > 5]
print("--- CAPREV çakışma"); s = series("NAS100", "M30", 930); f = feats(s, "NAS100"); st = ((f.r1 <= -150) | (f.r5 <= -400)) & (f.vix >= 18.4)
ov = st.reindex(x.index); rep("CAPREV stres günü", x[ov.fillna(False)]); rep("CAPREV dışı", x[~ov.fillna(False)])
print("--- permütasyon (yıl içi)"); rng = np.random.default_rng(1); by = {y: g.to_numpy() for y, g in b.groupby(b.index.year)}; cnt = x.groupby(x.index.year).size(); pm = np.array([np.mean(np.concatenate([rng.choice(by[y], c, replace=False) for y, c in cnt.items() if y in by])) for _ in range(5000)]); print("gerçek", round(x.mean(), 1), "plasebo", round(pm.mean(), 1), "p", float((pm >= x.mean()).mean()))
print("--- aktarım GER40"); 
for dm in (660, 930): rep(f"GER40 {dm//60}:{dm%60:02d}", *run("GER40", "M30", dm, sp=1.0)) if "GER40" in IVK else None
print("--- QQQ 1999-2018 bağlam (kapanış→kapanış, 4 bp)"); q = yf.Ticker("QQQ").history(start="1999-03-10", end="2026-11-05", auto_adjust=True); q.index = q.index.tz_localize(None); g = q.Close.diff(); up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean(); rs = 100 - 100 / (1 + up / (dn + 1e-12)); rr = (q.Close.shift(-1) / q.Close - 1) * 1e4 - 4
for a, b_ in (("1999", "2006"), ("2006", "2012"), ("2012", "2018"), ("2018", "2027")):
    z = rr[(rs < 10)].loc[a:b_].dropna(); rep(f"QQQ {a}-{b_}", z, rr.loc[a:b_].dropna())
