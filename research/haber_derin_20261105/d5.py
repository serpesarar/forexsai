from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
import ortak as O
pd.set_option("display.width", 180)
B = O.Bars("NDX"); e = O.macro_events(); e["u"] = e.ts.astype("int64") // 10**9
US = e[e.family.isin(["US_CPI_MOM", "US_CORE_CPI_MOM", "US_CPI_YOY", "US_NFP", "US_UNEMP", "US_PPI", "US_RETAIL", "US_CLAIMS", "US_ISM_MFG", "US_ISM_SVC", "US_CORE_PCE", "US_GDP"])].copy()
et = US.ts.dt.tz_convert("America/New_York"); US["sn"] = et.dt.minute % 30 * 60 + et.dt.second; US["top"] = (US.u - US.sn).astype(int)
print("FJ başlığının resmi saatten gecikmesi (sn), yalnız :00/:30'a ≤5 dk:"); g = US[US.sn <= 300]
print(g.groupby("family").sn.describe()[["count", "25%", "50%", "75%", "max"]].round(0).to_string()); print("toplam p50", g.sn.median(), "p90", g.sn.quantile(.9))
# hareket zaman profili: resmi an t0'dan itibaren, |sürpriz| büyük olaylar, en önemli aile
big = g[g.z.abs() >= 1].drop_duplicates("top")
rows = []
for t in big.top.to_numpy():
    a = np.searchsorted(B.t, t)
    if a >= len(B.t) or B.t[a] != t or a + 241 >= len(B.t) or a < 2: continue
    p0 = B.o[a]; path = {m: (B.c[a + m - 1] / p0 - 1) * 1e4 for m in (1, 2, 5, 15, 60, 240)}; rows.append(path)
P = pd.DataFrame(rows); print("olay", len(P), "\nortalama |hareket| bp:", P.abs().mean().round(1).to_dict())
print("240 dk yön = ilk N dk yön oranı:", {m: round(float((np.sign(P[m]) == np.sign(P[240])).mean()), 3) for m in (1, 2, 5, 15, 60)})
r1 = P[1]; print("1 dk kapanışa göre sonraki yön: uy → 15/60/240 dk ort bp", {m: round(float((np.sign(r1) * (P[m] - r1)).mean()), 2) for m in (2, 5, 15, 60, 240)})
print("1. dk |hareket| / 5 dk |hareket| medyan", round(float((P[1].abs() / (P[5].abs() + 1e-9)).median()), 2), " 60 dk'ya oran", round(float((P[1].abs() / (P[60].abs() + 1e-9)).median()), 2))
# kaçan ilk dakika: tek başına bilgiyle saniye düzeyinde girseydik: spread 3,4 pt ~ bp
print("1. dk ortalama |hareket|", round(float(r1.abs().mean()), 1), "bp; olay dakikası spread ≈", round(3.4 / float(B.c[-1]) * 1e4, 1), "bp")
ok = (np.sign(pd.Series([np.nan] * 0)))
# sürpriz işaret ↔ ilk dakika işaret tutarlılığı
s = big.iloc[:0]
big2 = big.copy(); rr = []
for t in big2.top.to_numpy():
    a = np.searchsorted(B.t, t); rr.append((B.c[a] / B.o[a] - 1) * 1e4 if a < len(B.t) and B.t[a] == t else np.nan)
big2["r1"] = rr; big2["sg"] = np.where(big2.kind == "grow_inv", 1, -1) * np.sign(big2.z); b3 = big2.dropna(subset=["r1"]); print("öncül işaret ↔ 1. dk tepki uyumu", round(float((np.sign(b3.r1) == b3.sg).mean()), 3), "n", len(b3)); print(b3.groupby("family").apply(lambda q: round(float((np.sign(q.r1) == q.sg).mean()), 2)).to_dict())
