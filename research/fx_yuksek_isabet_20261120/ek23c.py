"""EK-23c: COT-G2 A + VIX kriz filtresi (sonradan, en çok C+)."""
import json
import numpy as np, pandas as pd
import core, d1, ek18b, ek23

VIX = d1._vix()
ek18b.HIST = True
Zt, Zl = ek18b.tff(), ek18b.legacy()
Zl = Zl[Zl.rep < "2010-01-01"]
T = pd.concat([ek23.g2(Zt, ek23.GEO["A"]).assign(src="TFF"), ek23.g2(Zl, ek23.GEO["A"]).assign(src="LEG")], ignore_index=True)
v = VIX.reindex(VIX.index.union(pd.to_datetime(T.day).unique())).sort_index().ffill().shift(1)
T["vix"] = pd.to_datetime(T.day).map(v).values
res = {}
for thr in (None, 30, 25):
    g0 = T if thr is None else T[T.vix < thr]
    r = {}
    for nm, m in (("LEG_1993_2009", (g0.src == "LEG")), ("TFF_2007_10", (g0.src == "TFF") & (pd.to_datetime(g0.day) < "2010-06-01")),
                  ("TFF_2010_17", (g0.src == "TFF") & (pd.to_datetime(g0.day) >= "2010-06-01") & (pd.to_datetime(g0.day).dt.year <= 2017)),
                  ("TFF_2018_26", (g0.src == "TFF") & (pd.to_datetime(g0.day).dt.year >= 2018))):
        g = g0[m.values]
        if len(g) == 0: continue
        s = core.summ(g, boot=True); mo = max(1.0, (pd.to_datetime(g.day).max() - pd.to_datetime(g.day).min()).days / 30.44)
        r[nm] = {k: s[k] for k in ("n", "wr", "ort", "P", "yari", "stres15")} | {"frq": round(g.day.nunique() / mo, 2), "en_kotu": round(float(g.net.min()), 1)}
    res[str(thr)] = r
    print("VIX<", thr, json.dumps(r, default=str))
(core.RES / "ek23c.json").write_text(json.dumps(res, indent=1, default=str))
