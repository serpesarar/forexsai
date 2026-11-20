"""cd_ek1.py — PROTOCOL EK-1: tip skoru, DAX ayrışması, birleşim, örtüşme. python cd_ek1.py"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from cd_analiz import BLIND, TEST_MAIN, judge_filter, keep_mask, load, sharpe, x_stats
from cd_veri import HERE, ROOT

SIGNS = {"sma50": 1, "r5z": 1, "stres10": -1, "vix_pct": -1, "vix1": 1, "vade_egri": -1, "genislik": 1}
CELL = "X_5_3.0_kar"


def type_score(T: pd.DataFrame) -> tuple[pd.Series, float, dict]:
    K = T[T.set == "KESIF"]
    mu, sd = K[list(SIGNS)].mean(), K[list(SIGNS)].std()
    s = sum(SIGNS[f] * ((T[f] - mu[f]) / sd[f]).fillna(0) for f in SIGNS)
    thr = float(np.quantile(s[T.set == "KESIF"], 1 / 3))
    return s, thr, {"mu": mu.round(4).to_dict(), "sd": sd.round(4).to_dict()}


def recovery(T: pd.DataFrame) -> dict:
    out = {}
    for g in TEST_MAIN + ["MT5_NAS100"]:
        x = T[T.grp == g]
        lose = x[x["X_5_None_kar"].notna() & (x.base <= 0)]
        out[g] = {"d0_zarar": len(lose)}
        for m in (1, 2, 3, 5):
            c = f"X_{m}_None_kar"
            out[g][f"{m}g_karda"] = round(float((lose[c] > 0).mean()), 3)
        rec = lose["X_5_None_kar"]
        out[g]["donmeyen_ort"] = round(float(rec[rec <= 0].mean()), 1) if (rec <= 0).any() else None
        out[g]["donen_ort"] = round(float(rec[rec > 0].mean()), 1)
    return out


def overlap(T: pd.DataFrame) -> dict:
    sys.path.insert(0, str(ROOT / "research/caprev_tpsl_20261120/src"))
    from ek1 import live_days
    L = set().union(*live_days().values())
    x = T[T.grp == "DUKA_NDX"].copy()
    m = x.d.dt.date.isin(L)
    g = x[CELL] - x.base
    return {"ortusen": [int(m.sum()), round(float(g[m].mean()), 1)], "ortusmeyen": [int((~m).sum()), round(float(g[~m].mean()), 1)],
            "ortusmeyen_isabet": [round(float((x[~m].base > 0).mean()), 3), round(float((x[~m][CELL] > 0).mean()), 3)]}


def combo(T: pd.DataFrame, keep: pd.Series, name: str) -> dict:
    out = {}
    for g in TEST_MAIN + ["MT5_NAS100"] + BLIND:
        x = T[T.grp == g]
        k = keep[x.index]
        out[g] = {"taban": x_stats(x, "base") | {}, "filtre": round(float(x[k].base.mean()), 1), "filtre_x": x_stats(x[k], CELL)}
        out[g] = {"n": len(x), "kalan": int(k.sum()), "taban_ort_isabet": [round(float(x.base.mean()), 1), round(float((x.base > 0).mean()), 3)],
                  "birlesim_ort_isabet": [round(float(x[k][CELL].mean()), 1), round(float((x[k][CELL] > 0).mean()), 3)],
                  "birlesim_cvar5": out[g]["filtre_x"]["cvar5"][1], "kitap_sharpe": [sharpe(x.d, x.base), sharpe(x.d, x[CELL].where(k, 0.0))]}
    return {name: out}


def main() -> None:
    T = load()
    r = json.loads((HERE / "results/analiz.json").read_text())
    s, thr, z = type_score(T)
    T["tip"] = s
    res = {"tip_skoru": {"z": z, "esik": thr} | judge_filter(T, lambda x: x.tip >= thr, 0.983)}
    j = res["tip_skoru"]
    print("TIP", j["hukum"], j["olcut"], "P", j["havuz_P"], {g: (v["fark"], v["isabet"], v["atilan_ort"]) for g, v in j["olcum"].items()})
    res["dax_ayrisma"] = recovery(T)
    print("DONUS", json.dumps(res["dax_ayrisma"]))
    ar = r["F"]["hucre"][0]["kural"]
    res["birlesim"] = combo(T, keep_mask(T, ar), "aralik_ust") | combo(T, T.tip >= thr, "tip")
    print("BIRLESIM", json.dumps(res["birlesim"], ensure_ascii=False))
    res["ortusme"] = overlap(T)
    print("ORTUSME", res["ortusme"])
    (HERE / "results/ek1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
