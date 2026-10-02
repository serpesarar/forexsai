"""Gece-maruziyeti kapısı: beklenen çözülme süresi (TP·SL/σ²) NY 17:00 kapanışını aşıyor mu?"""
import numpy as np, pandas as pd
from evaluate import load, PER
from common import load_1m, block_boot
b = load_1m()
d = load(1)
# σ_1m (puan): son 60 dk 1m kapanış farklarının std'si (nedensel)
dc = b.close.diff()
sig = dc.rolling(60, min_periods=45).std().to_numpy()
d["sig1"] = sig[d.i.to_numpy()]
d["tau80"] = 80 * 110 / d.sig1**2            # dk
d["mins_to_close"] = (17 * 60 - d.ny_min).where(d.ny_min < 17 * 60, np.nan)
d["cross"] = d.tau80 > d.mins_to_close
d["nyh"] = d.ny_min // 60
pd.set_option("display.width", 250)
print("tau80 medyanı (dk) NY saatine göre:"); print(d.groupby("nyh").tau80.median().round(0).to_dict())
# SELL G80: dönem tabanına göre fark, NY saati × cross
for side in "SB":
    col = f"R_G80_{side}"
    d["y"] = d[col] - d.groupby("period")[col].transform("mean")
    t = d.groupby(["nyh", "cross", "period"]).y.mean().unstack("period")[PER]
    t["n"] = d.groupby(["nyh", "cross"]).size()
    print(f"\n{side}: G80 R − dönem ortalaması, NY saati × (çözülme kapanışı aşar mı)")
    print(t.round(3).to_string())
