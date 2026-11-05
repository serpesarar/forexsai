import numpy as np, pandas as pd, yfinance as yf
from lab2 import *
pd.set_option("display.width", 200)
def g(t):
    s = yf.Ticker(t).history(start="2017-01-01", end="2026-11-05", auto_adjust=True)["Close"]; s.index = s.index.tz_localize(None).normalize(); return s
P = pd.DataFrame({t: g(t) for t in ("QQQ", "SPY", "IWM", "^VIX", "^TNX", "DX-Y.NYB")}).ffill(); ch = P.pct_change() * 100; ch["^TNX"] = P["^TNX"].diff(); ch["SPY/QQQ"] = np.log(P.QQQ / P.SPY).diff() * 100; ch["IWM/QQQ"] = np.log(P.QQQ / P.IWM).diff() * 100
Z = (ch - ch.rolling(60).mean().shift(1)) / ch.rolling(60).std().shift(1)
PER = (("k", "2022-08-15", "2025-01-01"), ("b", "2018-05-25", "2022-08-15"), ("s", "2025-01-01", "2027-01-01"))
def run(sym, sig, cond, side, h, exm, sp, entm=1110):
    x = mt5_bars(sym, "M30"); x["d"] = x.ts_et.dt.normalize(); x["m"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute; O = x.pivot_table(index="d", columns="m", values="o", aggfunc="first")
    e = O[entm].dropna(); xx = O[exm]; idx = e.index
    xit = pd.Series(xx.reindex(idx).shift(-h).to_numpy(), index=idx)   # D+h uzlaşma saati
    r = ((xit / (e + sp) - 1) if side > 0 else (e / (xit + sp) - 1)) * 1e4 - (2 * h if side > 0 else .5 * h)
    m = cond(Z[sig]).reindex(idx).fillna(False)
    out = {}
    for p, a, b in PER:
        i = (idx >= a) & (idx < b); q = r[i & m.to_numpy()].dropna(); bs = r[i].dropna()
        if len(q) < 8: out[p] = (len(q), None, None, None); continue
        u, inv = np.unique(q.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, q.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (2000, len(u))); bm = S[ix].sum(1) / N[ix].sum(1)
        out[p] = (len(q), round(q.mean(), 1), round(bs.mean(), 1), round(float((bm > bs.mean()).mean()), 3))
    return out
L = [("X2 VIX z≤−1,5 uzun", "XAUUSD", "^VIX", lambda z: z <= -1.5, 1, 1, 780, .25), ("X2b VIX z≤−2 uzun", "XAUUSD", "^VIX", lambda z: z <= -2, 1, 1, 780, .25), ("X3 DXY z≥1,5 kısa", "XAUUSD", "DX-Y.NYB", lambda z: z >= 1.5, -1, 1, 780, .25), ("X4 QQQ z≤−2 kısa", "XAUUSD", "QQQ", lambda z: z <= -2, -1, 1, 780, .25), ("X5 TNX z≤−2 uzun", "XAUUSD", "^TNX", lambda z: z <= -2, 1, 1, 780, .25), ("X5b TNX z≤−2 uzun h3", "XAUUSD", "^TNX", lambda z: z <= -2, 1, 3, 780, .25),
     ("O2 SPY/QQQ z≤−2 kısa h3", "SpotCrude", "SPY/QQQ", lambda z: z <= -2, -1, 3, 870, .03), ("O2 SPY/QQQ z≤−2 kısa h1", "SpotCrude", "SPY/QQQ", lambda z: z <= -2, -1, 1, 870, .03), ("O3 DXY z≤−2 kısa h1", "SpotCrude", "DX-Y.NYB", lambda z: z <= -2, -1, 1, 870, .03), ("O4 IWM/QQQ z≤−2 kısa h3", "SpotCrude", "IWM/QQQ", lambda z: z <= -2, -1, 3, 870, .03)]
for lab, sym, sig, c, sd, h, exm, sp in L:
    o = run(sym, sig, c, sd, h, exm, sp); print(f"{lab:28s}", " | ".join(f"{p}: n={v[0]} ort={v[1]} taban={v[2]} P={v[3]}" for p, v in o.items()))
print("--- aynı adaylar, sızıntılı hizayla (uzlaşma→uzlaşma, karşılaştırma)")
for lab, sym, sig, c, sd, h, exm, sp in L[:6]:
    o = run(sym, sig, c, sd, h, exm, sp, entm=exm); print(f"{lab:28s}", " | ".join(f"{p}: n={v[0]} ort={v[1]} P={v[3]}" for p, v in o.items()))
