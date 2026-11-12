"""D3 — FOMC öncesi DAX: önceki işlem günü kapanışı → FOMC günü kapanışı (PROTOCOL.md §D3)."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
sys.path.insert(0, "research/dax_profesor_20261112")
from data_load import load
RNG = np.random.default_rng(3)
OUT = Path("research/dax_profesor_20261112/results")
cal = pd.read_csv("research/xau_best_days_20261015/makro/out/calendar.csv")
fomc = set(pd.to_datetime(cal[cal.event == "FOMC"].date))

def stats(close: pd.Series, label: str) -> dict:
    r = (close / close.shift() - 1).dropna() * 1e4
    f = r.index.normalize().isin(fomc)
    a, b = r[f], r[~f]
    yrs = r.index.year.values; uy = np.unique(yrs); ds = []
    for _ in range(4000):
        pick = RNG.choice(uy, len(uy)); s = pd.concat([r[yrs == y].to_frame().assign(f=f[yrs == y]) for y in pick])
        ds.append(s[s.f].iloc[:, 0].mean() - s[~s.f].iloc[:, 0].mean())
    h = len(a) // 2
    return dict(set=label, n=len(a), mean=a.mean(), other=b.mean(), diff=a.mean() - b.mean(), P=float((np.array(ds) > 0).mean()),
                hit=(a > 0).mean(), half1=a.iloc[:h].mean() - b.mean(), half2=a.iloc[h:].mean() - b.mean())

g = yf.download("^GDAXI", start="2007-12-01", progress=False, auto_adjust=False)["Close"].squeeze()
g = g[g.index >= "2008-01-01"]
d = load(); d = d[d.ber.dt.strftime("%H:%M") == "17:30"]
b = pd.Series(d.o.values, index=pd.DatetimeIndex(d.ber.dt.tz_localize(None).dt.normalize()))
res = [stats(g, "GDAXI 2008-2026"), stats(b, "BROKER GER40 2019-2026")]
print(json.dumps(res, indent=1, default=lambda x: round(float(x), 2)))
json.dump(res, open(OUT / "d3_ozet.json", "w"), indent=1, default=lambda x: round(float(x), 2))
