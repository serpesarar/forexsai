"""Fizibilite-4 özeti (v0.2): tarihsel erişilebilir X_max tabloları → results/ozet_v2.csv + ekrana.

X_max(medyan)  = sorguların yarısında ≥30 bağımsız olay veren en uzun X
X_max(%25)     = sorguların en az %25'inde ≥30 veren en uzun X (dağılımın üst çeyreği — "medyan 0 ≠ hep 0")
X_max(uygun)   = uygunluk kuralını (τ ≤ sorgu mumlarının medyan aralığı / 3) geçen sorguların yarısında ≥30 veren en uzun X
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import HERE

ORDER_TF = ["5m", "15m", "30m", "1h", "4h", "1d"]


def xmax(df: pd.DataFrame, col: str, thr: float) -> int:
    ok = df[df[col] >= thr]
    return int(ok.X.max()) if len(ok) else 0


def main() -> None:
    d = pd.read_csv(HERE / "results/fizibilite_4_nedensel.csv")
    rows = []
    for (sym, tf, lib), g in d.groupby(["sym", "tf", "lib"]):
        r = {"sembol": sym, "TF": tf, "kütüphane": lib, "N": int(g.n.iloc[0]), "H_ref": int(g.H_ref.iloc[0])}
        for rep, tol in (("pct", 0.01), ("pct", 0.02), ("atr", 0.1), ("atr", 0.2), ("atr", 0.3)):
            h = g[(g.rep == rep) & np.isclose(g.tol, tol) & (g["mode"] == "tarihsel")]
            a = g[(g.rep == rep) & np.isclose(g.tol, tol) & (g["mode"] == "arsiv")]
            key = f"{'%' if rep == 'pct' else ''}{tol}{'ATR' if rep == 'atr' else ''}"
            r[f"{key} med"] = xmax(h.assign(m=(h.p_ge30 >= 0.5).astype(float)), "m", 1)
            r[f"{key} %25"] = xmax(h.assign(m=(h.p_ge30 >= 0.25).astype(float)), "m", 1)
            if rep == "atr" and tol == 0.2:
                r["0.2ATR uygun"] = xmax(h.assign(m=(h.p_ge30_uygun >= 0.5).astype(float)), "m", 1)
                r["0.2ATR arşiv med"] = xmax(a.assign(m=(a.p_ge30 >= 0.5).astype(float)), "m", 1)
                r["0.2ATR X2 medyan olay"] = float(h[h.X == 2].med.iloc[0])
                r["0.2ATR X3 medyan olay"] = float(h[h.X == 3].med.iloc[0])
                r["uygun oranı X3"] = round(float(h[h.X == 3].uygun_orani.iloc[0]), 2)
        rows.append(r)
    out = pd.DataFrame(rows)
    out["_o"] = out.TF.map({t: i for i, t in enumerate(ORDER_TF)})
    out = out.sort_values(["sembol", "_o", "kütüphane"]).drop(columns="_o")
    out.to_csv(HERE / "results/ozet_v2.csv", index=False)
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
