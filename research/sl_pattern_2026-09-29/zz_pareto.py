"""Her kural için A+B birleşik: gerçek öldürme / kırpma / kurtarma sayıları + net R."""
import pickle, numpy as np, pandas as pd
from zz_grid import rules
A, B, C = pickle.load(open("zz_ds.pkl", "rb"))
FAM = {(1, 0): "K (klasik)", (1, -1): "Z→K", (2, 1): "K→Z→K", (2, -1): "Z→K→Z→K",
       (2, 0): "2.kâr", (3, 0): "3.kâr", (3, 1): "K→Z→K→Z→K", (3, -1): "Z→K→Z→K→Z→K"}
rows = []
for r in rules():
    r = dict(r, delay=2)
    tk = tr = sv = 0; dR = 0.0
    for ds in (A, B):
        R, _ = ds.run(**r); b = ds.base
        w = b > 0; l = b < 0
        tk += int((w & (R <= 0)).sum()); tr += int((w & (R > 0) & (R < b - 1e-9)).sum())
        sv += int((l & (R > 0)).sum()); dR += float((R - b).sum())
    rows.append({**r, "fam": FAM.get((r["n_p"], r["first"]), "?"), "true_kill": tk, "trimmed": tr,
                 "saved_win": sv, "dR": dR})
P = pd.DataFrame(rows); P.to_pickle("zz_pareto.pkl")
wins = int(((A.base > 0).sum() + (B.base > 0).sum()))
print("A+B kazanan sayısı:", wins)
for f, x in P.groupby("fam"):
    x = x[x.dR > 0]
    if not len(x): print(f, "net pozitif kural yok"); continue
    b0 = x[x.true_kill <= 5]
    print(f"{f:14s} net+ kural {len(x):5d} | en iyi net {x.dR.max():+.1f}R | ≤5 gerçek öldürmeyle en iyi net "
          f"{(b0.dR.max() if len(b0) else float('nan')):+.1f}R ({len(b0)} kural)")
