from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from zoneinfo import ZoneInfo
H = Path(__file__).parent; sys.path[:0] = [str(H), str(H.parent / "dts_uyarlama_20261104")]
import ortak as O
import dts02_orb as D
from takvim_truth import cal
NY = ZoneInfo("America/New_York")
B = O.Bars("NDX")
eds = {}
for s in ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"):
    for ts in yf.Ticker(s).get_earnings_dates(limit=40).index:
        l = ts.tz_convert(NY)
        if l.hour >= 15 and pd.Timestamp("2024-01-01", tz=NY) <= l < pd.Timestamp("2026-01-01", tz=NY):
            eds.setdefault(l.normalize(), set()).add(s)
days = sorted(eds)
tp = pd.Timestamp
def et(d, h, m): return tp(d.year, d.month, d.day, h, m, tz=NY).timestamp()
nxt = lambda d: d + pd.tseries.offsets.BDay(1)
# S18
cell = {"ts": [], "side": [], "h": []}
for d in days:
    t0, t1 = et(d, 16, 0), et(d, 16, 30)
    a, b = np.searchsorted(B.t, t0), np.searchsorted(B.t, t1)
    if b >= len(B.t) or a >= b or B.t[b] - t1 > 300: continue
    r = (B.c[b - 1] / B.c[a] - 1) * 1e4
    if abs(r) < 15: continue
    cell["ts"].append(t1 + 60); cell["side"].append(int(np.sign(r))); cell["h"].append(int((et(nxt(d), 9, 35) - t1 - 60) / 60))
t, s = np.array(cell["ts"]), np.array(cell["side"])
v = np.array([O.trades(B, np.array([x]), np.array([y]), h, 2.0)[0] for x, y, h in zip(t, s, cell["h"])]); m = np.isfinite(v)
print(f"S18 tepkiye uy n={m.sum()} ort={np.nanmean(v):.1f} isabet={(v[m]>0).mean():.2f} P={O.boot_p(v[m], t[m].astype('int64')//86400):.3f}; y1={np.nanmean(v[m][:m.sum()//2]):.1f} y2={np.nanmean(v[m][m.sum()//2:]):.1f}")
print(f"S18 ayna brüt yaklaşık ort={-np.nanmean(v)-6:.1f}")
# S19
t, s = [], []
for d in days:
    n = nxt(d); a = np.searchsorted(B.t, et(d, 15, 55)); b = np.searchsorted(B.t, et(n, 9, 35))
    if b >= len(B.t) or abs(B.t[b] - et(n, 9, 35)) > 120: continue
    g = (B.c[b - 1] / B.c[a] - 1) * 1e4
    if abs(g) >= 30: t.append(et(n, 9, 35)); s.append(int(np.sign(g)))
t, s = np.array(t), np.array(s)
fam = O.family(B, [{"name": "S19 boşluğa uy", "ts": t, "side": s, "h": 380}, {"name": "S19 boşluğa ters", "ts": t, "side": -s, "h": 380}], N=1000)
print(fam.to_string(index=False))
# S12 ORB
d = pd.read_parquet(O.DATA / "NDX_1m.parquet")
d = d.assign(ts=pd.to_datetime(d.t, unit="s", utc=True)).set_index("ts")
m5 = d.resample("5min", label="left", closed="left").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna().reset_index()
D.ATR = D.atr14(m5)
dd, mins = D.days_of(m5, "NDX"); o0, f0 = D.hm("09:30"), D.hm("15:55")
c = cal(); vd = {pd.Timestamp(x).date() for x in c.date}; ed = {nxt(x).date() for x in days}
rows = []
for dt in sorted(dd):
    r = D.trade(m5, dd[dt], mins, o0, f0, 15, 5, "or_mid", 2.0, "long", 1.3, False)
    if r is not None:
        rows.append({"d": dt, "r": r, "yil": dt.year, "tur": "veri" if dt in vd else "bilanço+1" if dt in ed else "diğer"})
R = pd.DataFrame(rows)
print(R.groupby("yil").r.agg(["size", "mean", lambda x: (x > 0).mean()]).round(3))
for y in (2024, 2025):
    print(y, R[R.yil == y].groupby("tur").r.agg(["size", "mean"]).round(3).to_dict("index"))
a = R[R.yil == 2024].r.to_numpy(); rng = np.random.default_rng(2); print("2024 P", np.mean([rng.choice(a, len(a)).mean() > 0 for _ in range(5000)]), "yarılar", a[:len(a)//2].mean().round(3), a[len(a)//2:].mean().round(3))
