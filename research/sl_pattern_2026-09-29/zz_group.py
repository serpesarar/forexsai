"""Grup-bazlı tam ızgara: her (sembol, yön) için 44k kural × 6 dilim (A tr/te, B h1/h2, C h1/h2).

Boş hipotez kontrolü: aynı grubun C verisinde yönü TERS çevrilmiş (BUY↔SELL) yollar
değil; bunun yerine kural etkilerinin dilimler arası bağımsızlık varsayımıyla beklenen
geçme oranı (1/64) ve komşuluk (plato) kontrolü raporlanır.
"""
import pickle
import sys
import time
import numpy as np
import pandas as pd
import zigzag as Z
from zz_grid import rules

A, B, C = pickle.load(open("zz_ds.pkl", "rb"))
SPLIT = pd.Timestamp("2026-08-01", tz="UTC")


def subset(ds, mask):
    idx = np.where(mask)[0]
    paths = []
    for k in idx:
        o, n = ds.off[k], ds.ln[k]
        paths.append(dict(fav=ds.FAV[o:o + n], adv=ds.ADV[o:o + n],
                          opn=ds.OPN[o:o + n], cls=ds.CLS[o:o + n]))
    return Z.DS(paths, ds.rr[idx], ds.meta.iloc[idx])


def split_of(ds):
    return (pd.to_datetime(ds.meta.t, utc=True) >= SPLIT).values


if __name__ == "__main__":
    groups = [("USOIL.FOREX", "BUY"), ("NDX.INDX", "SELL"), ("NDX.INDX", "BUY"), ("GDAXI.INDX", "BUY")]
    if len(sys.argv) > 1:
        groups = [tuple(g.split(":")) for g in sys.argv[1:]]
    for sym, d in groups:
        t0 = time.time()
        sets = {}
        for nm, ds in (("A", A), ("B", B), ("C", C)):
            m = ((ds.meta.sym == sym) & (ds.meta.dir == d)).values
            sub = subset(ds, m)
            sets[nm] = (sub, split_of(sub), sub.meta.usd_R.values if nm == "A" else None)
        rows = []
        for r in rules():
            r = dict(r, delay=2)
            row = dict(r)
            for nm, (ds, te, usd) in sets.items():
                R, _ = ds.run(**r); dd = R - ds.base
                row[f"{nm}_1"] = dd[~te].sum(); row[f"{nm}_2"] = dd[te].sum()
                row[f"{nm}_per100"] = dd.mean() * 100
                if usd is not None:
                    row["A_usd"] = (dd * usd).sum()
            rows.append(row)
        G = pd.DataFrame(rows)
        sl = ["A_1", "A_2", "B_1", "B_2", "C_1", "C_2"]
        G["pass6"] = (G[sl] > 0).all(axis=1)
        G["npos"] = (G[sl] > 0).sum(axis=1)
        G.to_pickle(f"zz_group_{sym[:4]}_{d}.pkl")
        n = {nm: len(s[0].rr) for nm, s in sets.items()}
        print(f"\n=== {sym} {d}  n={n}  ({time.time()-t0:.0f}s)")
        print(f"  6/6 dilim pozitif: {G.pass6.sum()} / {len(G)} (%{100*G.pass6.mean():.2f}; bağımsız-şans ≈ %1.6)")
        print("  pozitif dilim sayısı dağılımı:", G.npos.value_counts().sort_index().to_dict())
        if G.pass6.any():
            cols = ["n_p", "first", "P", "Pa", "L", "age", "lock", "lock_tp", "action"] + sl + ["A_usd", "C_per100"]
            print(G[G.pass6].sort_values("C_per100", ascending=False)[cols].head(12).round(2).to_string(index=False))
