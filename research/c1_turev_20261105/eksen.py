"""Broker saati denetimi: yıl yıl, beklenen olay barı (ET) en oynak ilk üçte mi? NDX 09:30, XAU 08:30, USOIL 10:30 Çrş / 09:00, GER40 09:00 Berlin≈03:00 ET."""
import numpy as np, pandas as pd
from lab import *
EXP = {"NAS100": ["09:30"], "XAUUSD": ["08:30", "08:00"], "SpotCrude": ["10:30", "09:00", "09:30"], "GER40": ["03:00", "02:00", "09:30"]}
for sym in EXP:
    for tf, mn in (("H1", 60), ("M30", 30), ("M15", 15), ("M5", 5)):
        x = mt5_bars(sym, tf); x = x[x.ts_et.dt.dayofweek < 5].copy(); x["r"] = np.log(x.c / x.o).abs()
        x["y"] = x.ts_et.dt.year; x["hm"] = x.ts_et.dt.strftime("%H:%M")
        out = []
        for y, g in x.groupby("y"):
            if len(g) < 500: continue
            p = g.groupby("hm").r.mean().sort_values(ascending=False); out.append(f"{y%100:02d}:{p.index[0]}")
        print(sym, tf, " ".join(out))
    x = mt5_bars(sym, "M5"); print("  spread medyan (M5)", round(x.sp.median(), 3), "| son 30g 09:30-16:00 ET", round(x[(x.ts_et >= x.ts_et.max() - pd.Timedelta(days=30)) & (x.ts_et.dt.hour.between(10, 15))].sp.median(), 3))
