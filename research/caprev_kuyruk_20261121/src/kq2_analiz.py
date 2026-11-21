"""kq2_analiz.py — KQ-02 (PROTOCOL.md): D0 kapanışı tutma şartı × stop takvimi × s≥1 koruması; KEŞİF'te seç, TEST + taze beslemede sına.

python kq2_analiz.py → results/analiz2.json
"""
from __future__ import annotations

import itertools
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
import kq_analiz as A  # noqa: E402

CA, M = A.CA, A.CA  # metrik yardımcıları
FIN = __import__("kq_veri").M.FIN
TEST_MAIN, BLIND, FRESH = A.TEST_MAIN, A.BLIND, ["EET30", "NQ", "MT5_GER40"]
MAXS = 5
C0, C1, AA, QQ, GG = (1.0, 3.0), (1.5, 2.0, 3.0), (0.5, 0.75, 1.0, None), (0.0, 0.15, 0.25), (None, "G8_sekmeme", "G2_vixchg0.1")
CELLS = {f"c0{c0}_c1{c1}_a{a}_q{q}_{g}": (c0, c1, a, q, g) for c0, c1, a, q, g in itertools.product(C0, C1, AA, QQ, GG)}
BASE = (1.0, 1.0, 0.0, 9.0, None)            # canlı kural: D0 stop 1×, D0 kapanışında her durumda çık
KAR = (3.0, 3.0, None, -1.0, None)           # CD-04 korumasız (canlı NDX kâr çıkışı)


def simulate(ev: dict, cell: tuple) -> tuple[float, int, str]:
    c0, c1, a, q, g = cell
    E, dv, lo, op, dd, seg, fac = ev["E"], ev["dvol"], ev["lo"], ev["op"], ev["dd"], ev["seg"], ev["fac"]
    n = len(ev["cl"])
    start = 0
    for s in range(n):
        sl = E * (1 - (c0 if s == 0 else c1) * dv)
        seg_lo = lo[start:seg[s]]
        hit = np.flatnonzero(seg_lo <= sl)
        if hit.size:
            j = start + int(hit[0])
            fill = min(sl, op[j]) * fac
            return (fill / E - 1) * 1e4 - FIN * dd[j], s, "stop"
        start = seg[s]
        f = ev["pf"][s]
        if ev["cl"][s] >= E:
            return ev["res"][s], s, "kar"
        if s == MAXS or s == n - 1:
            return ev["res"][s], s, "sure"
        if s == 0:
            hold = (a is None or f["z"] > -a) and (not np.isfinite(f["clv"]) or f["clv"] > q)
            if not hold:
                return ev["res"][0], 0, "tutma_yok"
        elif g and A.SINGLE[g][1](f):
            return ev["res"][s], s, "koruma"
    return ev["res"][n - 1], n - 1, "sure"


def frame(P: list[dict]) -> pd.DataFrame:
    rows = []
    for ev in P:
        r = {"set": ev["set"], "idx": ev["idx"], "feed": ev["feed"], "d": ev["d"], "dvol": ev["dvol"],
             "base": simulate(ev, BASE)[0], "kar": simulate(ev, KAR)[0], "base_motor": ev.get("base_motor", np.nan)}
        for c, cell in CELLS.items():
            r[c] = simulate(ev, cell)[0]
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
    return {"kesif_taban": {"isabet": round(h0, 3), "cvar5": round(cv0, 0), "ort": round(float(K.base.mean()), 1)},
            "kesif_kar": A.stats(K, "kar"), "cvar_esik": lim, "uygun": len(elig), "secilen": rank[:2],
            "kesif_ilk20": {c: {k: round(v, 3) for k, v in tab[c].items()} for c in rank[:20]}}


def judge(T: pd.DataFrame, c: str) -> dict:
    j = A.judge(T, c)
    res = {g: A.stats(T[T.grp == g], c) for g in FRESH}
    j["olcum"].update(res)
    j["olcut"]["taze_3_3"] = all(res[g]["fark"] > 0 and res[g]["cvar5"][2] >= 2 * res[g]["cvar5"][0] for g in FRESH)
    neg = any(j["olcum"][g]["fark"] <= 0 for g in TEST_MAIN)
    j["hukum"] = "B" if all(j["olcut"].values()) else ("X" if neg else "C")
    return j


def main() -> None:
    P = pickle.load(open(HERE / "cache/yollar2.pkl", "rb"))
    T = frame(P)
    old = CA.load()
    chk = {g: {"base_yeni": round(float(T[T.grp == g].base.mean()), 1), "base_eski": round(float(old[old.grp == g].base.mean()), 1),
               "kar_yeni": round(float(T[T.grp == g].kar.mean()), 1), "kar_eski": round(float(old[old.grp == g]["X_5_3.0_kar"].mean()), 1)}
           for g in TEST_MAIN + ["MT5_NAS100", "KESIF"]}
    chk["motor_base_fark"] = {f: round(float((T[T.feed == f].base - T[T.feed == f].base_motor).abs().max()), 3)
                              for f in TEST_MAIN + FRESH}
    sel = select(T)
    out = {"tutarlilik": chk, "secim": sel, "hucre": {c: judge(T, c) for c in sel["secilen"]},
           "kar_taze": {g: A.stats(T[T.grp == g], "kar") for g in FRESH}}
    json.dump(out, open(HERE / "results/analiz2.json", "w"), ensure_ascii=False, indent=1, default=float)
    T[["set", "idx", "feed", "d", "grp", "blk", "dvol", "base", "kar"] + sel["secilen"]].to_pickle(HERE / "cache/sonuc2.pkl")
    print(json.dumps({"chk": chk, "secilen": sel["secilen"], "esik": sel["cvar_esik"], "uygun": sel["uygun"],
                      "hukum": {c: (v["hukum"], v["olcut"], v["havuz_P"]) for c, v in out["hucre"].items()}}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
