"""Tanı: 30m (broker candle_cache) ile 1m (Dukascopy/cache/MT5) kaynakları çakışan günlerde tutarlı mı?"""
import numpy as np, pandas as pd
from run_1_discovery import build
T30, T1m = build("30m", 30), build("1m", 1)
j = T30.join(T1m, lsuffix="_30", rsuffix="_1m", how="inner")
for a, b in [("P930", "LH"), ("P900", "SLH"), ("P600", "ONFH")]:
    pass
lh30 = j.P960_30 / j.P930_30 - 1; lh1 = j.P960_1m / j.P930_1m - 1
sl30 = j.P930_30 / j.P900_30 - 1; sl1 = j.P930_1m / j.P900_1m - 1
print("çakışan gün", len(j))
print("LH getirisi korelasyonu 30m vs 1m:", round(lh30.corr(lh1), 3), " SLH:", round(sl30.corr(sl1), 3))
print("P930 fark (puan) medyan/|p90|:", round((j.P930_30 - j.P930_1m).median(), 2), round((j.P930_30 - j.P930_1m).abs().quantile(.9), 2))
print("30m: O930 - P930 boşluğu |medyan|, p90:", round((T30.O930 - T30.P930).abs().median(), 2), round((T30.O930 - T30.P930).abs().quantile(.9), 2))
print("1m : O930 - P930 boşluğu |medyan|, p90:", round((T1m.O930 - T1m.P930).abs().median(), 2), round((T1m.O930 - T1m.P930).abs().quantile(.9), 2))
# SLH->LH korelasyonu dönemlere göre (30m)
c = pd.DataFrame({"sl": T30.P930 / T30.P900 - 1, "lh": T30.P960 / T30.P930 - 1, "lho": T30.P960 / T30.O930 - 1})
print(c.groupby(c.index.year).apply(lambda g: pd.Series({"n": len(g), "corr_close": g.sl.corr(g.lh), "corr_open": g.sl.corr(g.lho)})).round(3))
print("Spearman SLH-LH 30m:", round(c.sl.corr(c.lh, method="spearman"), 3))
d = pd.DataFrame({"sl": sl1, "lh": lh1, "sl30": sl30, "lh30": lh30})
print("çakışan günlerde corr(SLH,LH): 1m", round(d.sl.corr(d.lh), 3), " 30m", round(d.sl30.corr(d.lh30), 3))
