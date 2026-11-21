"""kq3_analiz.py — KQ-03 (PROTOCOL.md): NDX kapsamı; ABD KEŞİF'inde seç, NDX + kör ABD + taze NDX beslemelerinde sına, canlıya alma kartı.

python kq3_analiz.py → results/analiz3.json
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
import kq2_analiz as B  # noqa: E402

A, CA = B.A, B.CA
US = ["NDX", "GSPC", "DJI", "RUT"]
NDX_MAIN, BLIND, FRESH = ["DUKA_NDX", "MT5_NAS100"], B.BLIND, ["EET30", "NQ"]
CARD_POOL = ["DUKA_NDX"] + BLIND
CELLS = dict(B.CELLS) | {"KAR_korumasiz": B.KAR}


def frame(P: list[dict]) -> pd.DataFrame:
    rows = []
    for ev in P:
        if ev["idx"] == "GDAXI":
            continue
        r = {"set": ev["set"], "idx": ev["idx"], "feed": ev["feed"], "d": ev["d"], "base": B.simulate(ev, B.BASE)[0],
             "kar": B.simulate(ev, B.KAR)[0], "sp_bp": ev.get("sp_bp", np.nan),
             "opt_bp": (ev["E"] / ev["e_opt"] - 1) * 1e4 if ev.get("e_opt") else np.nan}
        for c, cell in CELLS.items():
            r[c], r[c + "#s"], _ = B.simulate(ev, cell)
        rows.append(r)
    T = pd.DataFrame(rows)
    T["d"] = pd.to_datetime(T.d)
    T["grp"] = np.where(T.set == "G2016", "G2016_" + T.idx, T.set)
    T["blk"] = T.grp + "|" + T.d.dt.to_period("M").astype(str)
    return T


def select(T: pd.DataFrame) -> dict:
    K = T[T.set == "KESIF"]
    h0, cv0 = (K.base > 0).mean(), CA.cvar5(K.base)
    tab = {c: {"fark": float((K[c] - K.base).mean()), "isabet": float((K[c] > 0).mean()), "cvar5": CA.cvar5(K[c])} for c in CELLS}
    for lim in (1.5, 2.0):
        elig = [c for c in CELLS if tab[c]["isabet"] >= h0 + 0.10 and tab[c]["cvar5"] >= lim * cv0]
        if elig:
            break
    rank = sorted(elig, key=lambda c: tab[c]["fark"], reverse=True)
    return {"kesif_taban": {"n": len(K), "isabet": round(h0, 3), "cvar5": round(cv0, 0), "ort": round(float(K.base.mean()), 1)},
            "kesif_korumasiz": {k: round(v, 3) for k, v in tab["KAR_korumasiz"].items()},
            "cvar_esik": lim, "uygun": len(elig), "secilen": rank[:2],
            "kesif_ilk10": {c: {k: round(v, 3) for k, v in tab[c].items()} for c in rank[:10]}}


def judge(T: pd.DataFrame, c: str) -> dict:
    groups = NDX_MAIN + BLIND + FRESH + [f"G2016_{u}" for u in US]
    res = {g: A.stats(T[T.grp == g], c) for g in groups}
    pool = T[T.grp.isin(["DUKA_NDX"] + [f"G2016_{u}" for u in US])]
    P = CA.boot((pool[c] - pool.base).values, pool.blk.values)
    ok = {"ndx_mt5": all(res[g]["fark"] > 0 and res[g]["isabet"][2] > res[g]["isabet"][0] for g in NDX_MAIN),
          "havuz_P": P >= 0.975, "kor_2_3": sum(res[g]["fark"] > 0 for g in BLIND) >= 2,
          "sharpe": res["DUKA_NDX"]["sharpe"][2] > res["DUKA_NDX"]["sharpe"][0],
          "cvar5_2x": all(res[g]["cvar5"][2] >= 2 * res[g]["cvar5"][0] for g in NDX_MAIN),
          "cvar5_kar": c == "KAR_korumasiz" or res["DUKA_NDX"]["cvar5"][2] > res["DUKA_NDX"]["cvar5"][1],
          "taze": all(res[g]["fark"] > 0 and res[g]["cvar5"][2] >= 2 * res[g]["cvar5"][0] for g in FRESH)}
    neg = res["DUKA_NDX"]["fark"] <= 0
    return {"olcum": res, "havuz_P": P, "olcut": ok, "hukum": "B" if all(ok.values()) else ("X" if neg else "C")}


def one_position(x: pd.DataFrame, c: str) -> pd.Series:
    x = x.sort_values(["d", "grp"])
    busy_until = pd.Timestamp("1900-01-01")
    keep = []
    for _, r in x.iterrows():
        if r.d <= busy_until:
            keep.append(False)
            continue
        keep.append(True)
        busy_until = pd.Timestamp(np.busday_offset(r.d.date(), int(r[c + "#s"]), roll="forward"))
    return x.loc[keep, c]


def card(T: pd.DataFrame, c: str) -> dict:
    x = T[T.grp.isin(CARD_POOL)].sort_values("d")
    v = x[c]
    half = len(x) // 2
    stress = v - 0.5 * x.sp_bp
    op = one_position(x, c)
    P = CA.boot(v.values, x.blk.values)
    nd = T[T.grp == "DUKA_NDX"]
    out = {"n": len(x), "ort": round(float(v.mean()), 1), "P_EV": P, "yari": [round(float(v.iloc[:half].mean()), 1),
                                                                                 round(float(v.iloc[half:].mean()), 1)],
           "spread_x1_5": round(float(stress.mean()), 1), "icra_iyimser_fark_bp": round(float(x.opt_bp.mean()), 1),
           "tek_pozisyon": {"n": len(op), "ort": round(float(op.mean()), 1)},
           "ndx_yari": [round(float(nd.sort_values("d")[c].iloc[:len(nd) // 2].mean()), 1),
                        round(float(nd.sort_values("d")[c].iloc[len(nd) // 2:].mean()), 1)]}
    out["olcut"] = {"1_hacim": out["n"] >= 150, "2_beklenti": out["ort"] > 0 and P >= 0.90, "3_kararlilik": min(out["yari"]) >= 0,
                    "4_surtunme": out["spread_x1_5"] > 0, "5_icra": abs(out["icra_iyimser_fark_bp"]) <= out["ort"] / 2,
                    "6_tek_pozisyon": out["tek_pozisyon"]["ort"] > 0}
    out["verdikt"] = "LIVE" if all(out["olcut"].values()) else "SHADOW"
    return out


def yearly(T: pd.DataFrame, c: str) -> dict:
    x = T[T.grp == "DUKA_NDX"]
    return {int(y): {"n": len(g), "taban": round(float(g.base.mean()), 1), "kar": round(float(g.kar.mean()), 1),
                     "koruma": round(float(g[c].mean()), 1), "en_kotu_kar": round(float(g.kar.min())), "en_kotu_koruma": round(float(g[c].min()))}
            for y, g in x.groupby(x.d.dt.year)}


def main() -> None:
    P = [e for e in pickle.load(open(HERE / "cache/yollar2.pkl", "rb")) if e["set"] != "KESIF" or e["idx"] in US]
    T = frame(P)
    sel = select(T)
    cells = sel["secilen"] + (["KAR_korumasiz"] if "KAR_korumasiz" not in sel["secilen"] else [])
    out = {"secim": sel, "hucre": {c: judge(T, c) for c in cells}}
    for c in cells:
        out["hucre"][c]["kart"] = card(T, c)
        out["hucre"][c]["yillar_ndx"] = yearly(T, c)
    json.dump(out, open(HERE / "results/analiz3.json", "w"), ensure_ascii=False, indent=1, default=float)
    T.to_pickle(HERE / "cache/sonuc3.pkl")
    print(json.dumps({"secilen": sel["secilen"], "uygun": sel["uygun"], "esik": sel["cvar_esik"],
                      "hukum": {c: (v["hukum"], v["olcut"], v["havuz_P"], v["kart"]["verdikt"], v["kart"]["olcut"]) for c, v in out["hucre"].items()}},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
