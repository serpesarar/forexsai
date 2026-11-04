"""cells.csv + null_p1.json + holdout.csv → kart ölçütleri, seçim düzeltmesi, verdikt (PROTOCOL §5)."""
from __future__ import annotations
import json, os
import numpy as np, pandas as pd
from scipy_free import norm_sf

ROOT = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(ROOT, "results")


def main():
    c = pd.read_csv(os.path.join(RES, "cells.csv"))
    null = json.load(open(os.path.join(RES, "null_p1.json")))
    ho = pd.read_csv(os.path.join(RES, "holdout.csv")).set_index("cell") if os.path.exists(os.path.join(RES, "holdout.csv")) else None
    B = c[c.side == "BUY"].copy()
    # seçim düzeltmeli max-z (P1 boşuna karşı)
    reps = min(len(null[x]) for x in B.cell)
    Z = np.array([(np.array(null[x][:reps]) - np.mean(null[x])) / np.std(null[x]) for x in B.cell])  # (cells, reps)
    zr = ((B.ortR - B.p1_mean) / B.p1_sd).to_numpy()
    maxnull = Z.max(0)
    B["z_p1"] = zr
    B["p_sel"] = [(maxnull >= z).mean() for z in zr]
    # Holm (gün-kümeli t, tek yönlü)
    p = norm_sf(B.t.to_numpy())
    order = np.argsort(p); m = len(p); holm = np.zeros(m, bool); still = True
    for rank, i in enumerate(order):
        if still and p[i] <= 0.05 / (m - rank):
            holm[i] = True
        else:
            still = False
    B["p_t"] = p; B["holm"] = holm
    rows = []
    for _, r in B.iterrows():
        k1 = r.n >= 150
        k2 = (r.ortR > 0) and (r.P >= 0.90)
        k3 = (r.h1 >= 0) and (r.h2 >= 0)
        k4 = r.ortR_stress > 0
        k5 = abs(r.ortR_optim - r.ortR) <= 0.5 * abs(r.ortR)
        k6 = r.ortR_1pos > 0
        k7 = (r.ortR > r.p1_mean) and (r.p1_pct >= 0.95)
        k8 = r.era_0815 > 0
        k9 = bool(r.holm)
        k10 = bool(ho is not None and r.cell in ho.index and ho.loc[r.cell, "ortR_1m"] > 0)
        card = [k1, k2, k3, k4, k5, k6]; extra = [k7, k8, k9, k10]
        if r.ortR <= r.p1_mean or sum(not x for x in card) >= 2:  # PROTOCOL §5 aynen (önceki taslaktaki "or not k1" ek kuralı kaldırıldı)
            v = "RED"
        elif all(card) and all(extra):
            v = "LIVE"
        else:
            v = "SHADOW"
        rows.append(dict(cell=r.cell, k=("".join("✓" if x else "✗" for x in card + extra)), verdikt=v))
    V = pd.DataFrame(rows).set_index("cell")
    B = B.set_index("cell").join(V)
    if ho is not None:
        B = B.join(ho.add_prefix("ho_"))
    cols = ["n", "per_week", "wr", "be_wr", "ortR", "ci_lo", "ci_hi", "P", "h1", "h2", "ortR_stress", "ortR_sprB", "ortR_optim",
            "ortR_samebarwin", "n_1pos", "ortR_1pos", "era_0815", "n_0815", "era_1626", "p1_mean", "p1_pct", "p2_mean", "p2_pct",
            "z_p1", "p_sel", "t", "holm", "sl_usd_med", "med_hold", "k", "verdikt"]
    cols += [x for x in B.columns if x.startswith("ho_")]
    B[cols].to_csv(os.path.join(RES, "verdicts.csv"))
    S = c[c.side == "SELL"].set_index("cell")
    with open(os.path.join(RES, "summary.txt"), "w") as f:
        pd.set_option("display.width", 250)
        f.write("BUY hücreleri (spread A=$0,12)\n")
        f.write(B[["n", "per_week", "wr", "ortR", "ci_lo", "ci_hi", "P", "h1", "h2", "ortR_stress", "ortR_optim", "ortR_1pos",
                   "era_0815", "era_1626", "p1_mean", "p1_pct", "p2_mean", "z_p1", "p_sel", "t", "k", "verdikt"]].round(3).to_string())
        f.write("\n\nBUY ek: spread B (Duka gerçek), aynı-bar=WIN sınırı, kasa\n")
        f.write(B[["ortR_sprB", "ortR_samebarwin", "sl_usd_med", "med_hold"] + [x for x in B.columns if x.startswith("ho_")]].round(3).to_string())
        f.write("\n\nSELL kontrolleri\n")
        f.write(S[["n", "wr", "ortR", "P", "h1", "h2", "ortR_1pos", "era_0815", "era_1626", "p1_mean", "p1_pct"]].round(3).to_string())
        f.write(f"\n\nmax-z boş dağılımı (P1, {reps} tekrar): medyan {np.median(maxnull):.2f}, %95 {np.percentile(maxnull, 95):.2f}\n")
    print(open(os.path.join(RES, "summary.txt")).read())


if __name__ == "__main__":
    main()
