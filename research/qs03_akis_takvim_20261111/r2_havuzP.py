"""R2 ölçüt 1-2'nin ön-kayıtlı hâli: ABD 4 fon, kural günlerinde (getiri − dönem tabanı) tarih-blok bootstrap P."""
import json
import numpy as np, pandas as pd
from r2_r4 import D, preholiday, H
RNG = np.random.default_rng(47)
out = {}
for per, a, b in (("KESIF", "1999-01-01", "2012-12-31"), ("TEST", "2013-01-01", "2026-11-10")):
    ex = []
    for nm in ("SPY", "QQQ", "DIA", "IWM"):
        c = pd.read_parquet(D / f"{nm}.parquet")["Adj Close"]; c = c[(c.index >= a) & (c.index <= b)].dropna()
        r = (c / c.shift(1) - 1) * 1e4; ph = preholiday(c.index)
        ex.append((r[ph] - r.mean()).rename(nm))
    X = pd.concat(ex, axis=1).mean(1).dropna()   # tarih başına 4 fonun ortalama fazlası (tek gözlem/tarih)
    a_ = X.to_numpy(); bs = a_[RNG.integers(0, len(a_), (10000, len(a_)))].mean(1)
    h = len(a_) // 2
    out[per] = {"n_tarih": int(len(a_)), "fazla_bp": round(float(a_.mean()), 2), "P": round(float((bs > 0).mean()), 4),
                "y1": round(float(a_[:h].mean()), 2), "y2": round(float(a_[h:].mean()), 2)}
(H / "results/r2_havuzP.json").write_text(json.dumps(out, indent=1))
print(out)
