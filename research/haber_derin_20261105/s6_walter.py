from __future__ import annotations
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
import ortak as O
pd.set_option("display.width", 200); pd.set_option("display.max_colwidth", 40)
A = int(pd.Timestamp("2024-01-02", tz="UTC").timestamp()); Z = int(pd.Timestamp("2026-01-01", tz="UTC").timestamp())
B = O.Bars("NDX")
w = O.load_channel("WalterBloomberg"); w["u"] = w.ts.astype("int64") // 10**9; print("Walter", len(w), w.ts.min(), w.ts.max()); print("yıl", w.ts.dt.year.value_counts().sort_index().to_dict())
nw = w[(w.u >= A) & (w.u < Z)].sort_values("u").reset_index(drop=True)
REL = re.compile(r"\b(?:fed|fomc|powell|tariffs?|trump|cpi|inflation|payrolls?|nasdaq|nvidia|apple|microsoft|china|iran|war|strike|attack|treasury|yields?)\b", re.I)
rel = nw[nw.text.str.contains(REL)].u.to_numpy(); print("keşif başlık", len(nw), "ilgili", len(rel))
ret5 = np.full(len(B.t), np.nan); ret5[5:] = np.log(B.c[5:] / B.c[:-5]) * 1e4; ok = (B.t[5:] - B.t[:-5]) <= 420; ret5[5:][~ok] = np.nan
hr = ((B.t // 3600) % 24).astype(int); inp = (B.t >= A) & (B.t < Z); med = np.array([np.nanmedian(np.abs(ret5[(hr == h) & inp])) for h in range(24)])
cal = pd.read_csv(O.HERE.parents[1] / "research/xau_best_days_20261015/makro/out/calendar.csv"); cu = pd.to_datetime(cal.ts_utc, utc=True).astype("int64").to_numpy() // 10**9
sh = np.flatnonzero(inp & (np.abs(ret5) >= 5 * med[hr])); keep, last = [], 0
for i in sh:
    if B.t[i] - last >= 1800 and np.abs(cu - B.t[i]).min() > 1800: keep.append(i); last = B.t[i]
ix = np.array(keep); t0 = B.t[ix] + 60; onset = B.t[ix] - 240; sd = np.sign(ret5[ix]).astype(int)
def dist(ts, arr):
    out = []
    for s in ts:
        j = np.searchsorted(arr, s - 1800); k = np.searchsorted(arr, s + 1800); c = arr[j:k]; out.append(np.nan if not len(c) else c[np.argmin(np.abs(c - s))] - s)
    return np.array(out, float)
d = dist(onset, rel); rng = np.random.default_rng(3); pl = dist(B.t[rng.choice(np.flatnonzero(inp), 4000)], rel)
def prof(a):
    n = len(a); f = a[np.isfinite(a)]; return {"yok": round(1 - len(f) / n, 3), "önce>5dk": round((f < -300).sum() / n, 3), "-5..-1": round(((f >= -300) & (f < -60)).sum() / n, 3), "±1": round((np.abs(f) <= 60).sum() / n, 3), "+1..5": round(((f > 60) & (f <= 300)).sum() / n, 3), "+5..30": round((f > 300).sum() / n, 3)}
print("D3 şok", len(ix), prof(d)); print("D3 plasebo", prof(pl))
has = np.array([((rel >= t - 600) & (rel <= t)).any() for t in t0]); print("şok", len(ix), "haberli", int(has.sum()))
c = []
for h in (15, 60, 240):
    c += [{"name": f"S6 haberli devam {h}", "ts": t0[has].astype(float), "side": sd[has], "h": h}, {"name": f"S6 habersiz söndür {h}", "ts": t0[~has].astype(float), "side": -sd[~has], "h": h}, {"name": f"ayna haberli söndür {h}", "ts": t0[has].astype(float), "side": -sd[has], "h": h}, {"name": f"ayna habersiz devam {h}", "ts": t0[~has].astype(float), "side": sd[~has], "h": h}]
print(O.family(B, c, N=1000).to_string(index=False))
TOP = {"tarife_art": (r"\b(?:raises?|impose[sd]?|hikes?|new|additional)\b.{0,40}\btariffs?\b", -1), "tarife_anlas": (r"\b(?:tariff|trade)\b.{0,40}\b(?:pause|delay|deal|truce|exempt|agreement|reduce)", 1),
       "fed_guvercin": (r"\b(?:fed|powell|fomc)\b.{0,60}\b(?:rate cuts?|dovish|ease)\b", 1), "fed_sahin": (r"\b(?:fed|powell|fomc)\b.{0,60}\b(?:hawkish|higher for longer|no rush|rate hikes?)\b", -1)}
c = []
for k, (rx, sg) in TOP.items():
    x = nw[nw.text.str.contains(rx, case=False, regex=True)]; x = x[x.u.diff().fillna(1e9) >= 1800]
    for h in (5, 15, 60, 240): c.append({"name": f"S8 {k} {h}", "ts": x.u.to_numpy().astype(float), "side": np.full(len(x), sg), "h": h})
print(O.family(B, c, N=1000).to_string(index=False))
# hacim: 60 dk ilgili başlık sayısı → sonraki 60 dk |getiri|
cnt = np.searchsorted(rel, B.t[inp]) - np.searchsorted(rel, B.t[inp] - 3600); fw = np.full(len(B.t), np.nan); fw[:-60] = np.abs(np.log(B.c[60:] / B.c[:-60])) * 1e4; f60 = fw[inp]; hh = hr[inp]
q = pd.DataFrame({"cnt": cnt, "fw": f60, "hr": hh}).dropna(); q["taban"] = q.groupby("hr").fw.transform("median"); q["oran"] = q.fw / q.taban; q["kova"] = pd.cut(q.cnt, [-1, 0, 2, 5, 10, 20, 1000])
print(q.groupby("kova", observed=True).oran.agg(["size", "median", "mean"]).round(2).to_string())
