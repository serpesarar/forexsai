from __future__ import annotations
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
import ortak as O
B = O.Bars("NDX")
A = int(pd.Timestamp("2024-01-02", tz="UTC").timestamp()); Z = int(pd.Timestamp("2026-01-01", tz="UTC").timestamp())
w = O.load_channel("WalterBloomberg"); w["u"] = w.ts.astype("int64") // 10**9; w = w.sort_values("u")
REL = re.compile(r"\b(?:fed|fomc|powell|tariffs?|trump|cpi|inflation|payrolls?|nasdaq|nvidia|apple|microsoft|china|iran|war|strike|attack|treasury|yields?)\b", re.I)
rel = w[w.text.str.contains(REL)].u.to_numpy()
ret5 = np.full(len(B.t), np.nan); ret5[5:] = np.log(B.c[5:] / B.c[:-5]) * 1e4; ok = (B.t[5:] - B.t[:-5]) <= 420; ret5[5:][~ok] = np.nan
hr = ((B.t // 3600) % 24).astype(int); inp = (B.t >= A) & (B.t < Z); med = np.array([np.nanmedian(np.abs(ret5[(hr == h) & inp])) for h in range(24)])
cal = pd.read_csv(O.HERE.parents[1] / "research/xau_best_days_20261015/makro/out/calendar.csv"); cu = pd.to_datetime(cal.ts_utc, utc=True).astype("int64").to_numpy() // 10**9
def shocks(a, b):
    k = (B.t >= a) & (B.t < b); sh = np.flatnonzero(k & (np.abs(ret5) >= 5 * med[hr])); keep, last = [], 0
    for i in sh:
        if B.t[i] - last >= 1800 and np.abs(cu - B.t[i]).min() > 1800: keep.append(i); last = B.t[i]
    ix = np.array(keep); t0 = B.t[ix] + 60; sd = np.sign(ret5[ix]).astype(int); has = np.array([((rel >= t - 600) & (rel <= t)).any() for t in t0]); return t0, sd, has
ts = lambda s: int(pd.Timestamp(s, tz="UTC").timestamp())
for lab, a, b in (("DOĞRULAMA 2026-02-08→06-30", "2026-02-08", "2026-07-01"), ("KÖR 2026-07-01→11-04", "2026-07-01", "2026-11-05")):
    t0, sd, has = shocks(ts(a), ts(b))
    print(lab, "şok", len(t0), "haberli", int(has.sum()), "(haberli pay", round(has.mean(), 3), ")")
    c = [{"name": "S6 haberli devam 60", "ts": t0[has].astype(float), "side": sd[has], "h": 60}, {"name": "habersiz devam 60 (kıyas)", "ts": t0[~has].astype(float), "side": sd[~has], "h": 60}]
    print(O.family(B, c, N=1000).to_string(index=False))
