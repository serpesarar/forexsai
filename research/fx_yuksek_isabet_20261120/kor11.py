"""EK-11 seçilen hücre(ler): TEST/KÖR + olay-dışı gün plasebosu + çift kırılımı."""
import json, sys
import numpy as np, pandas as pd
import core
T = pd.read_parquet(core.RES / "trades_EK11.parquet")
cells = sys.argv[1:]
res = {}
rng = np.random.default_rng(5)
for c in cells:
    g = T[T.cell == c]
    d = {}
    for nm in ("KESIF", "TEST", "KOR"):
        e, k = g[g.ev & (g.per == nm)], g[~g.ev & (g.per == nm)]
        d[nm] = core.summ(e, boot=True)
        d[nm + "_kontrol"] = core.summ(k)
        d[nm + "_cift"] = {p: (core.summ(x)["wr"], core.summ(x)["ort"], len(x)) for p, x in e.groupby("pair")}
        if len(e) and len(k):
            a = e.groupby("day").net.mean().values; b = k.groupby("day").net.mean().values
            diff = np.array([rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(3000)])
            d[nm + "_fark"] = [round(e.net.mean() - k.net.mean(), 3), round(float((diff > 0).mean()), 3)]
        d[nm + "_yil"] = {int(y): (round(float((x.net > 0).mean() * 100), 1), round(float(x.net.mean()), 2), len(x)) for y, x in e.groupby(pd.to_datetime(e.time).dt.year)}
    res[c] = d
print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
(core.RES / "kor_EK11.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
