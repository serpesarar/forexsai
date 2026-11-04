"""Haftalık medyan-aralık tepe dakikası (UTC) — anomali pencerelerini incelemek için.
Kullanım: axis_weekly.py <tf> <bas> <son>"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
GF = Path("/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data")
tf, a, b = sys.argv[1:4]
d = pd.read_parquet(GF / f"dax_{tf}.parquet")
d = d[(d.ts >= a) & (d.ts <= b) & (d.ts.dt.weekday <= 4)].copy()
d["um"] = d.ts.dt.hour * 60 + d.ts.dt.minute
d["rng"] = d.high - d.low
d["wk"] = d.ts.dt.to_period("W")
for wk, x in d.groupby("wk"):
    noon = x.ts.iloc[len(x)//2]
    be, ny = bool(noon.tz_convert("Europe/Berlin").dst()), bool(noon.tz_convert("America/New_York").dst())
    t = 420 if be else 480
    g = x[(x.um >= 300) & (x.um <= 600)].groupby("um").rng.median()
    top = g.sort_values(ascending=False).head(3)
    print(wk, f"BER{'yaz' if be else 'kis'} NY{'yaz' if ny else 'kis'} gercek_acilis={t//60:02d}:{t%60:02d}",
          "tepe:", ", ".join(f"{int(m)//60:02d}:{int(m)%60:02d}={v:.0f}" for m, v in top.items()),
          f"kayma={int(top.index[0])-t:+d}")
