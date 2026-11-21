"""kq4_analiz.py — KQ-04 (PROTOCOL.md): KEŞİF'ten türeyen kapsam kuralı + donmuş KQ-03 hücresi, hiç kullanılmamış dört endekste.

python kq4_analiz.py → results/analiz4.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / "src"))
import kq2_veri as K2  # noqa: E402
import kq2_analiz as B  # noqa: E402

Q, V = K2.Q, K2.V
CA, A = B.CA, B.A
NEW = ["FTSE", "STOXX50E", "N225", "HSI"]
REF = ["NDX", "GSPC", "DJI", "RUT", "GDAXI"]
CELL = (3.0, 1.5, 0.5, 0.0, "G2_vixchg0.1")
SCOPE_MIN = 0.65
for n in NEW:
    V.G.KOR[n] = ROOT / f"research/kasa_trend_20261028/data/{n}.csv"
    Q.DAILY[n] = V.daily(n)


def recovery(P: list[dict]) -> float:
    los = [e for e in P if e["cl"][0] < e["E"]]
    return float(np.mean([any(c >= e["E"] for c in e["cl"][1:6]) for e in los])) if los else np.nan


def frame(P: list[dict]) -> pd.DataFrame:
    rows = [{"idx": e["idx"], "set": e["set"], "d": pd.Timestamp(e["d"]), "base": B.simulate(e, B.BASE)[0],
             "kar": B.simulate(e, B.KAR)[0], "koruma": B.simulate(e, CELL)[0]} for e in P]
    T = pd.DataFrame(rows)
    T["blk"] = T.idx + "|" + T.d.dt.to_period("M").astype(str)
    return T


def st(x: pd.DataFrame) -> dict:
    out = {"n": len(x)}
    for c in ("base", "kar", "koruma"):
        out[c] = {"ort": round(float(x[c].mean()), 1), "isabet": round(float((x[c] > 0).mean()), 3), "cvar5": round(CA.cvar5(x[c]), 0)}
    out["fark_koruma"] = round(float((x.koruma - x.base).mean()), 1)
    out["fark_kar"] = round(float((x.kar - x.base).mean()), 1)
    return out


def main() -> None:
    res = {"kapsam": {}, "tek": {}, "havuz": {}}
    T_all = []
    for n in NEW + REF:
        k = K2.daily_paths(n, "1990-01-01", "2015-12-31", "KESIF")
        t = K2.daily_paths(n, "2016-01-01", "2026-12-31", "TEST")
        rate = recovery(k)
        res["kapsam"][n] = {"kesif_olay": len(k), "toparlanma": round(rate, 3), "kapsam_ici": bool(rate >= SCOPE_MIN),
                            "dokunulmamis": n in NEW}
        Tk, Tt = frame(k), frame(t)
        res["tek"][n] = {"2016_26": st(Tt) if len(Tt) else None, "1990_2015": st(Tk) if len(Tk) else None}
        Tt["grp"] = n
        T_all.append(Tt)
    T = pd.concat(T_all)
    ins = [n for n in NEW if res["kapsam"][n]["kapsam_ici"]]
    outs = [n for n in NEW if not res["kapsam"][n]["kapsam_ici"]]
    for name, g in (("kapsam_ici", ins), ("kapsam_disi", outs)):
        x = T[T.grp.isin(g)]
        if len(x):
            res["havuz"][name] = st(x) | {"endeksler": g, "P": CA.boot((x.koruma - x.base).values, x.blk.values),
                                          "P_kar": CA.boot((x.kar - x.base).values, x.blk.values)}
    h = res["havuz"].get("kapsam_ici")
    if not h:
        res["hukum"] = "sınanamadı"
    else:
        ok = {"i_fark_P": h["fark_koruma"] > 0 and h["P"] >= 0.90,
              "ii_yari": sum(res["tek"][n]["2016_26"]["fark_koruma"] > 0 for n in ins) >= len(ins) / 2,
              "iii_cvar": h["koruma"]["cvar5"] >= 2 * h["base"]["cvar5"],
              "iv_yon": ("kapsam_disi" not in res["havuz"]) or res["havuz"]["kapsam_disi"]["fark_koruma"] < h["fark_koruma"]}
        res["olcut"] = ok
        res["hukum"] = "B" if all(ok.values()) else ("X" if h["fark_koruma"] <= 0 else "C")
    json.dump(res, open(HERE / "results/analiz4.json", "w"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()
