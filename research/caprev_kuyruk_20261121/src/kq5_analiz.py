"""kq5_analiz.py — KQ-05 (PROTOCOL.md): D0 zararda kısmi tutuş h ∈ {0,5; 1,0} × KQ-02 ızgarası; ABD KEŞİF'inde seç,
NDX beslemeleri + dokunulmamış dört endeks + canlıya alma kartıyla sına.

python kq5_analiz.py → results/analiz5.json
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
import kq3_analiz as K3  # noqa: E402
import kq4_analiz as K4  # noqa: E402  (dört yeni endeksi kaydeder)

B, A, CA = K3.B, K3.A, K3.CA
HS = (0.5, 1.0)
BASECELLS = dict(B.CELLS) | {"KAR_korumasiz": B.KAR}
CELLS = {("KAR_korumasiz" if c == "KAR_korumasiz" and h == 1.0 else f"{c}|h{h}"): (cell, h)
         for c, cell in BASECELLS.items() for h in HS}


def sim(ev: dict, cell: tuple, h: float) -> tuple[float, int]:
    r, s, _ = B.simulate(ev, cell)
    if s > 0 and h < 1.0:                       # D0'dan sonra tutuldu → (1−h) D0 kapanışında kapandı
        r = (1 - h) * ev["res"][0] + h * r
    return r, s


def frame(P: list[dict], cells: dict) -> pd.DataFrame:
    rows = []
    for ev in P:
        if ev["idx"] == "GDAXI":
            continue
        r = {"set": ev["set"], "idx": ev["idx"], "feed": ev["feed"], "d": ev["d"], "base": B.simulate(ev, B.BASE)[0],
             "kar": B.simulate(ev, B.KAR)[0], "sp_bp": ev.get("sp_bp", np.nan),
             "opt_bp": (ev["E"] / ev["e_opt"] - 1) * 1e4 if ev.get("e_opt") else np.nan}
        for c, (cell, h) in cells.items():
            r[c], r[c + "#s"] = sim(ev, cell, h)
        rows.append(r)
    T = pd.DataFrame(rows)
    T["d"] = pd.to_datetime(T.d)
    T["grp"] = np.where(T.set == "G2016", "G2016_" + T.idx, T.set)
    T["blk"] = T.grp + "|" + T.d.dt.to_period("M").astype(str)
    return T


def untouched(cells: dict) -> dict:
    P = []
    for n in K4.NEW:
        P += K4.K2.daily_paths(n, "2016-01-01", "2026-12-31", "YENI")
    T = frame(P, cells)
    T["blk"] = T.idx + "|" + T.d.dt.to_period("M").astype(str)
    out = {}
    for c in cells:
        out[c] = {"n": len(T), "fark": round(float((T[c] - T.base).mean()), 1), "P": CA.boot((T[c] - T.base).values, T.blk.values),
                  "cvar5": [round(CA.cvar5(T.base), 0), round(CA.cvar5(T[c]), 0)],
                  "endeks_fark": {n: round(float((g[c] - g.base).mean()), 1) for n, g in T.groupby("idx")}}
        o = out[c]
        o["ok"] = o["fark"] > 0 and o["P"] >= 0.90 and o["cvar5"][1] >= 2 * o["cvar5"][0]
    return out


def main() -> None:
    P = [e for e in pickle.load(open(HERE / "cache/yollar2.pkl", "rb")) if e["set"] != "KESIF" or e["idx"] in K3.US]
    T = frame(P, CELLS)
    K3.CELLS = CELLS                          # seçim / sınama yardımcıları hücre adlarını buradan okur
    sel = K3.select(T)
    chosen = sel["secilen"]
    out = {"secim": sel, "hucre": {}}
    un = untouched({c: CELLS[c] for c in chosen})
    for c in chosen:
        j = K3.judge(T, c)
        j["kart"] = K3.card(T, c)
        j["dokunulmamis"] = un[c]
        all_ok = all(j["olcut"].values()) and un[c]["ok"] and j["kart"]["verdikt"] == "LIVE"
        j["hukum_kq05"] = "B" if all_ok else ("X" if j["olcum"]["DUKA_NDX"]["fark"] <= 0 else "C")
        j["yillar_ndx"] = K3.yearly(T, c)
        out["hucre"][c] = j
    json.dump(out, open(HERE / "results/analiz5.json", "w"), ensure_ascii=False, indent=1, default=float)
    T[["set", "idx", "feed", "d", "grp", "base", "kar"] + chosen + [c + "#s" for c in chosen]].to_pickle(HERE / "cache/sonuc5.pkl")
    print(json.dumps({"secilen": chosen, "uygun": sel["uygun"],
                      "hukum": {c: (v["hukum_kq05"], v["olcut"], v["havuz_P"], v["kart"]["verdikt"], v["dokunulmamis"]) for c, v in out["hucre"].items()},
                      "ndx": {c: v["olcum"]["DUKA_NDX"] for c, v in out["hucre"].items()}}, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()
