from __future__ import annotations
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).parent; sys.path.insert(0, str(HERE))
import ortak as O
pd.set_option("display.width", 190)
B = O.Bars("OILb")
E0 = O.macro_events(); E0["u"] = E0.ts.astype("int64") // 10**9
def rx(t, lb=5):
    t0 = t - t % 300; a = np.searchsorted(B.t, t0); b = np.searchsorted(B.t, t0 + lb * 60)
    if a >= len(B.t) or b >= len(B.t) or a == b or B.t[a] != t0: return np.nan
    return (B.c[b - 1] / B.o[a] - 1) * 1e4
def tr(ts, side, h):
    i = np.searchsorted(B.t, ts); ii = np.minimum(i, len(B.t) - 1); ok = (i < len(B.t)) & (B.t[ii] - ts <= 420); j = np.searchsorted(B.t, B.t[ii] + h * 60) - 1; jj = np.minimum(j, len(B.t) - 1)
    e = np.where(side > 0, B.ao[ii], B.o[ii]); x = np.where(side > 0, B.c[jj], B.ac[jj]); v = side * (x - e) / e * 1e4; v[~ok | (jj <= ii) | (B.t[ii] + h * 60 - B.t[jj] > 900)] = np.nan; return v
def show(lab, e):
    e = e[e.z.abs() >= 1]
    sg = np.where(e.kind == "oil", -1, np.where(e.kind == "grow", 1, -1)) * np.sign(e.z.to_numpy()); r = np.array([rx(int(u)) for u in e.u]); rej = (np.sign(r) == -sg) & (r == r)
    t = (e.u.to_numpy() - e.u.to_numpy() % 300 + 300).astype(float)
    for nm, m, s in (("ret: sürpriz yönünde", rej, sg), ("kabul: sürpriz yönünde", (np.sign(r) == sg) & (r == r), sg)):
        rows = {}
        for h in (15, 60, 240):
            v = tr(t[m], s[m], h); rows[h] = (int(np.isfinite(v).sum()), round(float(np.nanmean(v)), 1) if np.isfinite(v).any() else None, round(float(np.nanmean(v > 0)), 2) if np.isfinite(v).any() else None)
        print(f"{lab:26s} {nm:24s}", rows)
for lab, m in (("EIA", E0.family == "EIA_CRUDE"), ("API", E0.family == "API_CRUDE"), ("Oil tüm", E0.kind == "oil"), ("Büyüme US", E0.family.str.startswith("US_") & E0.kind.isin(["grow", "grow_inv"]))):
    for per, a, b in (("2025", "2025-06-10", "2026-01-01"), ("2026", "2026-01-01", "2026-11-05"), ("2026 savaş öncesi", "2026-01-01", "2026-03-01"), ("2026-03+", "2026-03-01", "2026-11-05")):
        A, Z = pd.Timestamp(a, tz="UTC"), pd.Timestamp(b, tz="UTC"); show(f"{lab} {per}", E0[m & (E0.ts >= A) & (E0.ts < Z)].drop_duplicates("u"))
w = O.load_channel("WalterBloomberg"); w24 = w[w.text.str.contains(r"\b(?:EIA|API)\b.*\b(?:CRUDE|OIL)\b|\bCRUDE\b.*(?:INVENTOR|STOCK)", case=False, regex=True) & w.text.str.contains(r"\b(?:EST|EXP|VS|FORECAST)\b", case=False, regex=True)]
print("Walter EIA/API est", len(w24), w24.ts.dt.year.value_counts().to_dict()); print(w24.text.head(6).str[:110].to_list())
