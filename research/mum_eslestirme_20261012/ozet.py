"""Fizibilite özeti: her (sembol, TF) için ≥30 çakışmasız eşleşme (medyan) veren en uzun X + formül sınaması.

X_max ≈ ln(N / n_min) / ln(1 / p1)   (p1 = tek mumun rastgele bir mumla eşleşme olasılığı)
Çalıştır: python3 research/mum_eslestirme_20261012/ozet.py  → results/ozet.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import HERE

ORDER = [("NDX", "5m"), ("NDX", "15m"), ("NDX", "30m"), ("NDX", "1h"), ("DAX", "15m"), ("DAX", "30m"), ("DAX", "1h"),
         ("XAU", "5m"), ("XAU", "15m"), ("XAU", "30m"), ("XAU", "1h"), ("OIL", "5m"), ("OIL", "15m"), ("OIL", "30m"), ("OIL", "1h")]
N_MIN = 30


def xmax(df: pd.DataFrame, col: str) -> int:
    ok = df[df[col] >= N_MIN]
    return int(ok.X.max()) if len(ok) else 0


def main() -> None:
    a = pd.read_csv(HERE / "results/fizibilite_1_birebir.csv"); b = pd.read_csv(HERE / "results/fizibilite_2_huni_kismi_knn.csv")
    rows = []
    for s, t in ORDER:
        base = a[(a.sym == s) & (a.tf == t)]
        if base.empty:
            continue
        r = {"sembol": s, "TF": t, "N": int(base.n.iloc[0]), "aralik": f"{base.start.iloc[0][:7]}→{base.end.iloc[0][:7]}",
             "medyan_mum_pct": base.med_range_pct.iloc[0], "medyan_mum_pips": base.med_range_pips.iloc[0]}
        for tol in (0.01, 0.02, 0.05):
            x = base[(base.rep == "pct") & np.isclose(base.tol, tol)]
            r[f"pct{tol}_pips"] = x.tol_pips.iloc[0]; r[f"pct{tol}_Xmax"] = xmax(x, "med_nonovl")
        for tol in (0.1, 0.2, 0.3):
            r[f"atr{tol}_Xmax"] = xmax(base[(base.rep == "atr") & np.isclose(base.tol, tol)], "med_nonovl")
        for m in ("funnel", "partial80"):
            r[f"{m}_Xmax"] = xmax(b[(b.sym == s) & (b.tf == t) & (b.method == m)], "med")
        for rep, tol in (("pct", 0.02), ("atr", 0.2)):
            x = base[(base.rep == rep) & np.isclose(base.tol, tol)]
            p1 = x[x.X == 1].med_nonovl.iloc[0] / r["N"]
            r[f"p1_{rep}{tol}_pct"] = round(p1 * 100, 2)
            r[f"Xpred_{rep}{tol}"] = round(np.log(r["N"] / N_MIN) / np.log(1 / p1), 2) if p1 > 0 else 0.0
        rows.append(r)
    out = pd.DataFrame(rows); out.to_csv(HERE / "results/ozet.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
