"""grid_ek2.py — PROTOCOL EK-2: en iyi 30 KEŞİF hücresinin KÖR tekrarı vs şans. Çıktı results/grid_ek2.json"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid as G  # noqa: E402
import lib  # noqa: E402

OUT = G.OUT


def evaluate(cells, R, Cd):
    rows = []
    for r_ in cells.itertuples():
        Rk = R[(R.a == r_.a) & (R.h == r_.h)].reset_index(drop=True)
        M, names = G.cond_matrix(Rk, Cd, r_.a)
        mask = M[:, names.index(r_.kosul)]
        row = {k: getattr(r_, k) for k in ("a", "h", "yon", "kosul", "n_K", "ort_K", "t_K")}
        for y in ("K1", "K2"):
            row[f"ort_{y}"] = float(Rk[mask & (Rk.yari == y).values][r_.yon].mean())
        g = Rk[mask & (Rk.per == "KOR").values]
        x = g[r_.yon].dropna()
        mo = pd.to_datetime(g.loc[x.index, "d"]).dt.to_period("M").astype(str).values
        row.update({"n_KOR": int(len(x)), "ort_KOR": float(x.mean()), "P_KOR": lib.block_boot_p(x.values, mo),
                    "ort15_KOR": float(g[r_.yon + "15"].dropna().mean()), "gunler": g.d.tolist()})
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1); vixp = lib.vix_prev_map(D.d.tolist())
    R = pd.read_parquet(OUT / "returns.parquet")
    Cd = G.conditions(D, vixp)
    R["per"] = np.where(R.d <= date(2023, 12, 31), "KESIF", "KOR")
    R["yari"] = np.where(R.d <= date(2020, 12, 31), "K1", np.where(R.d <= date(2023, 12, 31), "K2", "KOR"))
    C = pd.read_parquet(OUT / "cells_ek1.parquet")
    best = C.sort_values("t_K", ascending=False).drop_duplicates(["a", "yon", "kosul"])
    top, bot = best.head(30), C.sort_values("t_K").drop_duplicates(["a", "yon", "kosul"]).head(30)
    T, B = evaluate(top, R, Cd), evaluate(bot, R, Cd)
    T["tekrar"] = (T.ort_KOR > 0) & (T.P_KOR >= 0.90)
    B["ters_tekrar"] = (B.ort_KOR < 0) & (B.P_KOR <= 0.10)
    T["aday"] = T.tekrar & (T.P_KOR >= 0.95) & (T.ort15_KOR > 0) & (T.ort_K1 > 0) & (T.ort_K2 > 0)
    k = int(T.tekrar.sum())
    res = {"tekrar_sayisi": k, "beklenen": 3.0, "binom_p": float(binom.sf(k - 1, 30, 0.10)),
           "kotu30_ters_tekrar": int(B.ters_tekrar.sum()), "kotu30_binom_p": float(binom.sf(int(B.ters_tekrar.sum()) - 1, 30, 0.10)),
           "en_iyi30": T.drop(columns=["gunler"]).to_dict("records"), "adaylar": T[T.aday].drop(columns=["gunler"]).to_dict("records")}
    T.to_parquet(OUT / "ek2_top30.parquet")
    (OUT / "grid_ek2.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print("tekrar", k, "/30  binom p", round(res["binom_p"], 4), "| kötü30 ters tekrar", res["kotu30_ters_tekrar"], "p", round(res["kotu30_binom_p"], 4))
    print(T.drop(columns=["gunler"]).round(3).to_string())


if __name__ == "__main__":
    main()
