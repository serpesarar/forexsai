import numpy as np, pandas as pd
from xau18_core import seg
for tf, m0 in (("M15", 1095), ("M5", 1095), ("M30", 1110)):
    r, _, _ = seg(tf, m0, 1320)
    print(tf, f"{m0//60}:{m0%60:02d}", "n", len(r), "ort", round(r.mean(), 2), "med", round(r.median(), 2), "kırpılmış %2", round(r.clip(*r.quantile([.01, .99])).mean(), 2), "en iyi %1 hariç", round(r[r < r.quantile(.99)].mean(), 2))
    print("  yıl:", r.groupby(r.index.year).mean().round(1).to_dict())
    print("  gün:", r.groupby(r.index.dayofweek).mean().round(1).to_dict(), "(6=Paz açılış)")
r30, _, _ = seg("M30", 1110, 1320); x = pd.read_parquet("results/iv.parquet").gvz; m = x.rolling(252, min_periods=120).median(); hi = (x.shift(1) >= m.shift(1)).reindex(r30.index, method="ffill")
print("gvz yüksek", round(r30[hi.fillna(False)].mean(), 2), "düşük", round(r30[~hi.fillna(False)].mean(), 2))
# 24 saatlik pay: gece mi her yerde mi
y, _, _ = seg("M30", 1110, 1320)
for a, b, l in ((1320, 180, "22-03"), (180, 510, "03-08:30"), (510, 780, "08:30-13"), (780, 1020, "13-17")):
    q, _, _ = seg("M30", a, b); print(l, "ort", round(q.mean(), 2), "P>0", round((q > 0).mean(), 3), "yıl", q.groupby(q.index.year).mean().round(1).to_dict())
