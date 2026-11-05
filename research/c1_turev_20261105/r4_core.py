import numpy as np, pandas as pd
from lab2 import *
def series(sym, tf, dm):
    x = mt5_bars(sym, tf); x["d"] = x.ts_et.dt.normalize(); x["m"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute
    x = x[x.ts_et.dt.dayofweek < 5].reset_index(drop=True)
    ent = x[x.m == dm].set_index("d")
    prev = x.c.shift(1)[x.m == dm]; prev.index = ent.index; gapok = (x.t.diff()[x.m == dm].to_numpy() <= 3 * int(tf[1:] if tf[0] == "M" else 60) * 60)
    s = pd.DataFrame({"S": prev.to_numpy(), "E": ent.o.to_numpy()}, index=ent.index)[gapok]; s = s[~s.index.duplicated()]; return s
def feats(s, sym):
    g = s.S.diff(); up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean(); f = pd.DataFrame(index=s.index)
    f["rsi2"] = 100 - 100 / (1 + up / (dn + 1e-12)); f["low5"] = s.S <= s.S.rolling(5).min(); f["high5"] = s.S >= s.S.rolling(5).max(); f["d3"] = (g < 0).rolling(3).sum() == 3; f["u3"] = (g > 0).rolling(3).sum() == 3
    f["r1"] = s.S.pct_change() * 1e4; f["r5"] = s.S.pct_change(5) * 1e4; f["ma200"] = s.S > s.S.rolling(200).mean(); f["dvol"] = s.S.pct_change().rolling(20).std() * 1e4
    idx = pd.DatetimeIndex(s.index); f["vix"] = MAC.vix.shift(1).reindex(idx, method="ffill").to_numpy(); iv = IV[IVK[sym]]; f["iv"] = iv.shift(1).reindex(idx, method="ffill").to_numpy(); f["ivm"] = iv.rolling(252, min_periods=120).median().shift(1).reindex(idx, method="ffill").to_numpy()
    return f
