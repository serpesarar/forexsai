"""EK-6 seçim (KEŞİF) + TEST/KÖR + plasebo. Aşama 1 yalnız KEŞİF'i yazdırır; 'tum' argümanıyla seçilenler TEST/KÖR'de."""
import json
import sys

import numpy as np
import pandas as pd

import core
import spike

pd.set_option("display.width", 250)
T = pd.read_parquet(core.RES / "trades_SPIKE.parquet")
O = T[T.grp == "OLAY"]
K = O[O.per == "KESIF"]
rows = [{"cell": ci, "def": spike.GRID[ci], **core.summ(g)} for ci, g in K.groupby("cell")]
H = pd.DataFrame(rows)
H.to_csv(core.RES / "kesif_SPIKE.csv", index=False)
print(H.sort_values("ort", ascending=False).head(16).to_string(index=False))
S = H[(H.wr >= 80) & (H.ort > 0) & (H.n >= 150)].sort_values("t", ascending=False).head(3)
print("SEÇİLEN", S.cell.tolist())
S.to_csv(core.RES / "secim_SPIKE.csv", index=False)
if len(sys.argv) > 1 and sys.argv[1] == "tum" and len(S):
    res = {}
    for ci in S.cell:
        g = O[O.cell == ci]
        d = {"def": str(spike.GRID[ci])}
        for nm in ("KESIF", "TEST", "KOR"):
            gg = g[g.per == nm]
            d[nm] = core.summ(gg, boot=True)
            d[nm + "_cift"] = {p: core.summ(x) for p, x in gg.groupby("pair")}
        # yön plasebosu: aynı olaylar, rastgele yön, aynı geometri yok → aynı hücrenin AYNA yönü bilgi olarak
        k, q, mode, tpk, slk, tmin = spike.GRID[ci]
        mir = [i for i, c in enumerate(spike.GRID) if c == (k, q, "GERI" if mode == "DEVAM" else "DEVAM", tpk, slk, tmin)][0]
        d["ayna_KOR"] = core.summ(O[(O.cell == mir) & (O.per == "KOR")])
        d["plasebo_T-60_tum"] = core.summ(T[(T.grp == "PLASEBO") & (T.cell == ci)])
        res[int(ci)] = d
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    (core.RES / "spike_kor.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
