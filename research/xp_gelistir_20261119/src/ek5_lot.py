import json
from pathlib import Path
import numpy as np, pandas as pd
import kural as KR, ek3_kademe as K3
HERE = Path(__file__).resolve().parents[1]
D = KR.D
out = {}
for f in ["DUKA_NDX", "MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000"]:
    z = D[D.besleme == f].copy()
    for nm, x in (("rv20", z.rv20.values), ("vix", z.vix.values), ("max", np.fmax(z.rv20.values, z.vix.values))):
        x = np.where(np.isfinite(x), x, np.nanmedian(x)); raw = 1.0 / x
        K = (z.donem == "KESIF").values
        # c: KEŞİF toplam kâr = taban (tavan/taban sonrası iteratif)
        c = 1.0
        for _ in range(30):
            w = np.clip(c * raw, 0.25, 2.0)
            r = z.net.values[K].sum() / (w[K] * z.net.values[K]).sum()
            c *= r
        w = np.clip(c * raw, 0.25, 2.0)
        rec = {}
        for e in ("KESIF", "TEST"):
            m = (z.donem == e).values; zz = z[m]
            rec[e] = K3.rel(K3.m(zz.net.values * w[m], zz.d.values), K3.m(zz.net.values, zz.d.values))
            rec[e]["ort_lot"] = round(float(w[m].mean()), 2)
        out[f"{f}_{nm}"] = rec
        print(f, nm, rec)
(HERE / "results/ek5_lot.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
