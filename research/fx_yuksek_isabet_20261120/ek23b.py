"""EK-23b: G2 kesitsel COT-TERS, TFF 2006-06 → 2010-05 (görülmemiş, aynı sınıflandırma)."""
import json
import pandas as pd
import core, ek18b, ek23

ek18b.HIST = True
Z = ek18b.tff()
print("TFF ilk", Z.rep.min().date())
res = {}
for gn, geo in ek23.GEO.items():
    T = ek23.g2(Z, geo)
    T = T[pd.to_datetime(T.day) < "2010-06-01"]
    s = core.summ(T, boot=True)
    mo = max(1.0, (pd.to_datetime(T.day).max() - pd.to_datetime(T.day).min()).days / 30.44)
    res[gn] = {**s, "frq": round(T.day.nunique() / mo, 2), "ilk": str(pd.to_datetime(T.day).min().date()), "en_kotu": round(float(T.net.min()), 1),
               "yil": {int(y): round(float(g.net.mean()), 1) for y, g in T.groupby(pd.to_datetime(T.day).dt.year)}}
    print(gn, json.dumps(res[gn], default=str))
(core.RES / "ek23b.json").write_text(json.dumps(res, indent=1, default=str))
