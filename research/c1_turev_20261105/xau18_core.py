import numpy as np, pandas as pd
from lab2 import *
def seg(tf, h0m, h1m, a=None, b=None, sp_mult=1.0, sym="XAUUSD"):
    x = mt5_bars(sym, tf); x["d"] = x.ts_et.dt.normalize(); x["m"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute
    x = x[x.ts_et.dt.dayofweek.isin([6, 0, 1, 2, 3])]
    e = x[x.m == h0m].drop_duplicates("d").set_index("d"); 
    z = x[x.m == h1m].drop_duplicates("d").set_index("d")
    if h1m < h0m: z.index = z.index - pd.Timedelta(days=1)
    j = e.join(z, rsuffix="_x", how="inner")
    r = (j.o_x - j.sp_x * 0 ) / (j.o + sp_mult * j.sp) - 1
    r = r * 1e4 - sp_mult * 0
    if a: r = r[r.index >= a]
    if b: r = r[r.index < b]
    return r, j.sp.median(), j.sp.quantile(.9)
