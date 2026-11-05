from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).parent))
import ortak as O
ROOT = Path(__file__).resolve().parents[2]
NY = ZoneInfo("America/New_York")
q = yf.Ticker("QQQ").history(start="2005-01-01", end="2026-11-05", auto_adjust=False)
q.index = q.index.tz_convert(NY).normalize()
q["night"] = (q.Open.shift(-1) / q.Close - 1) * 1e4
eds = {}
for s in ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"):
    x = yf.Ticker(s).get_earnings_dates(limit=100)
    for ts in x.index:
        loc = ts.tz_convert(NY)
        if loc.hour >= 15:
            eds.setdefault(loc.normalize(), set()).add(s)
print("bilanço tarih aralığı", min(eds).date(), max(eds).date(), len(eds))
def rep(mask, name, per):
    p = q[(q.index >= per[0]) & (q.index < per[1])]
    m = mask.reindex(p.index).fillna(False).to_numpy(); n = p.night.to_numpy(); ok = np.isfinite(n)
    a, b = n[m & ok], n[~m & ok]
    days = np.arange(len(a)); o = len(a) // 2
    rng = np.random.default_rng(9); boots = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(5000)]
    print(f"{name:34s} {per[0][:4]}-{per[1][:4]} n={len(a):3d} ort={a.mean():6.1f} med={np.median(a):6.1f} isabet={(a>0).mean():.2f} diğer_ort={b.mean():5.1f} fark={a.mean()-b.mean():6.1f} P(fark>0)={np.mean(np.array(boots)>0):.3f} P(EV>2bp)={np.mean([rng.choice(a,len(a)).mean()>2 for _ in range(3000)]):.3f} y1={a[:o].mean():5.1f} y2={a[o:].mean():5.1f}")
big = pd.Series({d: bool(v & {"NVDA", "AAPL", "MSFT"}) for d, v in eds.items()}); allm = pd.Series({d: True for d in eds})
big = big[big]
for per in (("2012-01-01", "2024-01-01"), ("2012-01-01", "2018-01-01"), ("2018-01-01", "2024-01-01"), ("2024-01-01", "2026-01-01")):
    rep(big, "S13c NVDA/AAPL/MSFT gecesi", per)
    rep(allm, "S13b 7 şirket gecesi", per)
for s in ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"):
    rep(pd.Series({d: True for d, v in eds.items() if s in v}), f"  {s}", ("2012-01-01", "2024-01-01"))
# S14 NDX 1h
z = np.load(ROOT / "backend/data/candle_history/NDX_1h.npz")
d = pd.DataFrame({k: z[k] for k in z.files}); d["u"] = d.ts.astype("int64")
d["dt"] = pd.to_datetime(d.u, unit="s", utc=True)
gap_i = np.flatnonzero(d.u.diff().to_numpy() > 36 * 3600)
print("hafta sonu sayısı", len(gap_i), "ilk bar saati ET dağılım", d.dt.iloc[gap_i].dt.tz_convert(NY).dt.hour.value_counts().head(4).to_dict())
rows = []
for i in gap_i:
    g = (d.open.iat[i] / d.close.iat[i - 1] - 1) * 1e4
    t0 = d.dt.iat[i]
    if abs(g) < 20: continue
    target = (t0.tz_convert(NY) + pd.Timedelta(days=1)).normalize() + pd.Timedelta(hours=9)
    j = d.dt.searchsorted(target.tz_convert("UTC")) - 1
    if j <= i or (target.tz_convert("UTC") - d.dt.iat[j]).total_seconds() > 7200: continue
    side = np.sign(g); en, ex = d.close.iat[i], d.close.iat[j]
    spread = 3.0
    rows.append({"dt": t0, "g": g, "r": side * (ex - en) / en * 1e4 - spread / en * 1e4, "r_ilkbar": side * (d.close.iat[i] - d.open.iat[i]) / en * 1e4, "buy": side > 0})
r = pd.DataFrame(rows)
for a, b in (("2016-01-01", "2024-01-01"), ("2016-01-01", "2020-01-01"), ("2020-01-01", "2024-01-01"), ("2024-01-01", "2026-01-01")):
    s = r[(r.dt >= pd.Timestamp(a, tz="UTC")) & (r.dt < pd.Timestamp(b, tz="UTC"))]
    v = s.r.to_numpy(); o = len(v) // 2
    rng = np.random.default_rng(3); bs = np.array([rng.choice(v, len(v)).mean() for _ in range(5000)])
    print(f"S14 {a[:4]}-{b[:4]} n={len(v)} ort={v.mean():.1f} med={np.median(v):.1f} isabet={(v>0).mean():.2f} P={np.mean(bs>0):.3f} y1={v[:o].mean():.1f} y2={v[o:].mean():.1f} | BUY {s[s.buy].r.mean():.1f} (n{int(s.buy.sum())}) SELL {s[~s.buy].r.mean():.1f} (n{int((~s.buy).sum())}) | ilk bar {s.r_ilkbar.mean():.1f}")
# 1m sağlamlık 2024-25
B = O.Bars("NDX")
idx = np.flatnonzero(np.diff(B.t) > 40 * 3600)
for delay in (0, 5, 15, 60):
    for th in (10, 20, 40):
        ts, sd, hh = [], [], []
        for i in idx:
            if not (1704153600 <= B.t[i + 1] < 1767225600): continue
            g = (B.o[i + 1] / B.c[i] - 1) * 1e4
            if abs(g) < th: continue
            t0 = pd.Timestamp(B.t[i + 1], unit="s", tz="UTC").tz_convert(NY)
            target = (t0 + pd.Timedelta(days=1)).normalize() + pd.Timedelta(hours=9)
            ts.append(B.t[i + 1] + delay * 60 - 1); sd.append(int(np.sign(g))); hh.append(int((target.timestamp() - B.t[i + 1]) / 60) - delay)
        ts, sd = np.array(ts, float), np.array(sd)
        v = np.array([O.trades(B, np.array([t]), np.array([s]), int(h))[0] for t, s, h in zip(ts, sd, hh)])
        m = np.isfinite(v)
        print(f"1m gecikme={delay:2d} eşik={th:2d} n={m.sum():3d} ort={np.nanmean(v):6.1f} isabet={(v[m]>0).mean():.2f} P={O.boot_p(v[m], ts[m].astype('int64')//86400):.3f}")
