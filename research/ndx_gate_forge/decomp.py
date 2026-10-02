"""Yön/Yapı ayrışımı: S=(EV_B+EV_S)/2 (geometri-yapı uyumu), D=(EV_B-EV_S)/2 (yön)."""
import numpy as np, pandas as pd
from evaluate import load, PER
d = load(1)
d["nyb"] = (d.ny_min // 30) * 30
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
for g in ["G80", "GS", "GR"]:
    d[f"S_{g}"] = (d[f"R_{g}_B"] + d[f"R_{g}_S"]) / 2
    d[f"D_{g}"] = (d[f"R_{g}_B"] - d[f"R_{g}_S"]) / 2
# baz: her dönemin S ortalaması (maliyet + genel yapı)
print(d.groupby("period")[["S_G80", "S_GS", "S_GR", "D_G80"]].mean().round(4))
def tab(col, by):
    x = d.groupby([by, "period"])[col].mean().unstack()[PER]
    x = x - d.groupby("period")[col].mean()[PER]     # dönem tabanından fark
    x["min"] = x[PER].min(1); x["max"] = x[PER].max(1)
    x["same_sign"] = (np.sign(x[PER]).nunique(1) == 1)
    return x
for g in ["G80", "GR"]:
    print(f"\n=== S_{g} (yapı) − dönem tabanı, NY 30dk kovası ===")
    t = tab(f"S_{g}", "nyb"); t.index = [f"{i//60:02d}:{i%60:02d}" for i in t.index]
    print(t.round(3).to_string())
