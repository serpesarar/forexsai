"""KEŞİF taraması: tüm aileler × hücreler × 25 çift. KÖR verisine BAKMAZ (yalnız time < SPLIT işlemleri özetlenir).
Çıktı: results/kesif_havuz.csv, results/kesif_cift.csv, results/trades_<fam>.parquet (tüm dönem, sonraki adım için)."""
from __future__ import annotations

import sys

import pandas as pd

import core
import families as F

fams = sys.argv[1:] or list(F.FAMS)
for fam in fams:
    fn, grid = F.FAMS[fam]
    allt = []
    for pair in core.PAIRS:
        x = core.load(pair)
        for ci, cell in enumerate(grid):
            t = fn(x, cell)
            if len(t):
                t["pair"], t["cell"] = pair, ci
                allt.append(t)
        print(fam, pair, flush=True)
    T = pd.concat(allt, ignore_index=True)
    T.to_parquet(core.RES / f"trades_{fam}.parquet")
    K = T[T.time < core.SPLIT]
    rows = []
    for ci, g in K.groupby("cell"):
        rows.append({"fam": fam, "cell": ci, "def": str(grid[ci]), **core.summ(g)})
    pd.DataFrame(rows).to_csv(core.RES / f"kesif_havuz_{fam}.csv", index=False)
    rows = []
    for (ci, p), g in K.groupby(["cell", "pair"]):
        rows.append({"fam": fam, "cell": ci, "pair": p, "def": str(grid[ci]), **core.summ(g)})
    pd.DataFrame(rows).to_csv(core.RES / f"kesif_cift_{fam}.csv", index=False)
print("bitti")
