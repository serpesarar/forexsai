"""grid_ek1.py — PROTOCOL EK-1: KEŞİF 2018–23, KÖR 2024–26; tekli + VIX×diğer koşullar. Çıktı results/grid_ek1.json"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid as G  # noqa: E402
import lib  # noqa: E402

OUT = G.OUT


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1); vixp = lib.vix_prev_map(D.d.tolist())
    R = pd.read_parquet(OUT / "returns.parquet")
    Cd = G.conditions(D, vixp)
    R["per"] = np.where(R.d <= date(2023, 12, 31), "KESIF", "KOR")
    R["yari"] = np.where(R.d <= date(2020, 12, 31), "K1", np.where(R.d <= date(2023, 12, 31), "K2", "KOR"))
    rng = np.random.default_rng(12)
    cells, perm_max = [], np.zeros(200)
    cache = {}
    for a in G.ANCH:
        for h in G.HOLDS:
            Rk = R[(R.a == a) & (R.h == h)].reset_index(drop=True)
            if len(Rk) < 300:
                continue
            M, names = G.cond_matrix(Rk, Cd, a)
            keep = [i for i, nm in enumerate(names) if "&" not in nm or nm.split("&")[0].startswith("VIX")]
            M, names = M[:, keep], [names[i] for i in keep]
            cache[(a, h)] = (Rk, M, names)
            kes = (Rk.per == "KESIF").values
            for side in ("L", "S"):
                r = Rk[side].values
                n, mean, t = G.tstats(M[kes], r[kes], np.isfinite(r[kes]))
                for ci, nm in enumerate(names):
                    if n[ci] >= 80:
                        cells.append({"a": a, "h": h, "yon": side, "kosul": nm, "ci": ci, "n_K": int(n[ci]), "ort_K": float(mean[ci]), "t_K": float(t[ci])})
                Mk, rk, okk = M[kes], r[kes], np.isfinite(r[kes])
                for p in range(200):
                    n2, _, t2 = G.tstats(Mk[rng.permutation(len(Mk))], rk, okk)
                    perm_max[p] = max(perm_max[p], np.where(n2 >= 80, t2, 0).max())
    C = pd.DataFrame(cells)
    Tstar = float(np.percentile(perm_max, 95))
    sel = C[C.t_K >= Tstar]
    rows = []
    for r_ in sel.itertuples():
        Rk, M, names = cache[(r_.a, r_.h)]
        mask = M[:, r_.ci]
        row = {k: getattr(r_, k) for k in ("a", "h", "yon", "kosul", "n_K", "ort_K", "t_K")}
        for y in ("K1", "K2"):
            row[f"ort_{y}"] = float(Rk[mask & (Rk.yari == y).values][r_.yon].mean())
        g = Rk[mask & (Rk.per == "KOR").values]
        x = g[r_.yon].dropna()
        mo = pd.to_datetime(g.loc[x.index, "d"]).dt.to_period("M").astype(str).values
        row.update({"n_KOR": int(len(x)), "ort_KOR": float(x.mean()) if len(x) else np.nan,
                    "P_KOR": lib.block_boot_p(x.values, mo) if len(x) > 5 else np.nan,
                    "ort15_KOR": float(g[r_.yon + "15"].dropna().mean()) if len(x) else np.nan})
        row["gecti"] = bool(row["ort_KOR"] > 0 and row["P_KOR"] >= 0.95 and row["ort15_KOR"] > 0 and row["ort_K1"] > 0 and row["ort_K2"] > 0)
        rows.append(row)
    V = pd.DataFrame(rows)
    res = {"n_hucre": int(len(C)), "T_yildiz": Tstar, "perm_max_ort": float(perm_max.mean()), "n_secilen": int(len(sel)),
           "ust10": C.nlargest(10, "t_K")[["a", "h", "yon", "kosul", "n_K", "ort_K", "t_K"]].to_dict("records"),
           "secilen": V.to_dict("records") if len(V) else [], "gecen": V[V.gecti].to_dict("records") if len(V) else []}
    C.to_parquet(OUT / "cells_ek1.parquet")
    (OUT / "grid_ek1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print("hücre", len(C), "T*", round(Tstar, 2), "perm ort", round(perm_max.mean(), 2), "seçilen", len(sel), "geçen", len(res["gecen"]))
    print(pd.DataFrame(res["ust10"]).round(2).to_string())
    if len(V):
        print(V.round(3).to_string())


if __name__ == "__main__":
    main()
