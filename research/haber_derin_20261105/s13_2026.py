from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).parent))
import ortak as O
NY = ZoneInfo("America/New_York")
q = yf.Ticker("QQQ").history(start="2025-12-01", end="2026-11-05", auto_adjust=False); q.index = q.index.tz_convert(NY).normalize()
q["n"] = (q.Open.shift(-1) / q.Close - 1) * 1e4
eds = {}
for s in ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"):
    for ts in yf.Ticker(s).get_earnings_dates(limit=30).index:
        l = ts.tz_convert(NY)
        if l.hour >= 15 and pd.Timestamp("2026-01-01", tz=NY) <= l < pd.Timestamp("2026-11-05", tz=NY):
            eds.setdefault(l.normalize(), set()).add(s)
B = O.Bars("NDX")
rows = []
for D in sorted(eds):
    if D not in q.index: print("gelecek/işlem günü değil", D.date(), eds[D]); continue
    i = q.index.get_loc(D)
    if i + 1 >= len(q.index): print("ertesi gün yok", D.date()); continue
    nx = q.index[i + 1]
    t0 = D + pd.Timedelta(hours=15, minutes=55); t1 = nx + pd.Timedelta(hours=9, minutes=35)
    h = int((t1 - t0).total_seconds() / 60)
    v = O.trades(B, np.array([t0.timestamp()]), np.array([1]), h, 2.0)[0]
    rows.append({"D": D.date(), "kim": ",".join(sorted(eds[D])), "qqq": round(q.n.iat[i], 1), "ndx1m_net": None if not np.isfinite(v) else round(float(v), 1), "dönem": "DOĞR" if D < pd.Timestamp("2026-07-01", tz=NY) else "KÖR"})
r = pd.DataFrame(rows); print(r.to_string(index=False))
for p in ("DOĞR", "KÖR"):
    s = r[r["dönem"] == p]; a = s.qqq.to_numpy(float); m = s.ndx1m_net.dropna().to_numpy(float)
    rng = np.random.default_rng(1)
    pa = np.mean([rng.choice(a, len(a)).mean() > 0 for _ in range(5000)]) if len(a) else None
    pm = np.mean([rng.choice(m, len(m)).mean() > 0 for _ in range(5000)]) if len(m) else None
    print(p, f"QQQ n={len(a)} ort={a.mean():.1f} isabet={(a>0).mean():.2f} P={pa:.3f}", f"| NDX 1m net n={len(m)} ort={m.mean():.1f} isabet={(m>0).mean():.2f} P={pm:.3f}")
oth = q.n[~q.index.isin(pd.DatetimeIndex(sorted(eds)))]
print("2026 diğer geceler ort", round(float(oth.mean()), 1), "n", int(oth.notna().sum()))
