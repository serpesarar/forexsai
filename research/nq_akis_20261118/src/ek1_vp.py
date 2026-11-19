"""EK-1: VP1 kopya kontrolü."""
import json
import numpy as np
import pandas as pd
import gunluk as U

def pct(s):
    return s.rolling(504, min_periods=252).apply(lambda a: (a[:-1] < a[-1]).mean() if np.isfinite(a[-1]) else np.nan, raw=True)

out = {}
for nm in ("NDX", "QQQ"):
    x = U.frame(U.load(nm))
    v = U.load("VXN").reindex(x.index)
    pv, pl = pct(v - 100 * x.rv20), pct(v)
    r20 = x.c / x.c.shift(20) - 1
    eras = [("KESIF", "2001-01-01", "2021-10-31"), ("TEST", "2021-11-01", "2026-12-31")]
    cells = {"a_VXN_duzey": pl >= 0.8, "b_VP1_duzey_dusuk": (pv >= 0.8) & (pl < 0.8), "c_VP1_r20_arti": (pv >= 0.8) & (r20 >= 0),
             "VP1": pv >= 0.8}
    out[nm] = {k: {h: U.by_era(x, m, h, 1, eras) for h in (5, 20)} for k, m in cells.items()}
    print(nm)
    for k, r in out[nm].items():
        for h, e in r.items():
            print(" ", k, h, {en: (z.get("n"), z.get("fark_yonlu"), z.get("P"), z.get("yil_arti")) for en, z in e.items()})
U.RES.joinpath("ek1_vp.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
