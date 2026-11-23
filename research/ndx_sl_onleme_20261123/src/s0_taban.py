"""Taban: piyasaları kur, TD-01 regresyonu, VAKA canlı eşleşmesi, sonuç-körü eşikler (ER / gürültü yüzdelikleri)."""
from __future__ import annotations

import json
import pickle

import numpy as np
import pandas as pd

from eng import HERE, Mkt2, dc, run2, PERIODS

RES = HERE.parent / "results"


def build():
    from eng import load_markets
    D = load_markets()
    M = {k: Mkt2(v, pct=(k == "eski")) for k, v in D.items()}
    SIG = {k: dc.signals(v, friday=False) for k, v in D.items()}
    pickle.dump((M, SIG), open(RES / "mkt.pkl", "wb"))
    return M, SIG


def summ(t: pd.DataFrame) -> str:
    if not len(t):
        return "n=0"
    return (f"n={len(t):4d} TP {int((t.why == 'TP').sum()):3d} SL {int((t.why == 'SL').sum()):3d} "
            f"ortR {t.R.mean():+.3f} ΣR {t.R.sum():+.1f}")


def main():
    M, SIG = build()
    allt = []
    for k in M:
        t, _ = run2(M[k], SIG[k])
        allt.append(t)
    T = pd.concat(allt)
    T = T[T.period != "-"]
    for p in PERIODS:
        x = T[T.period == p]
        print(f"{p:7s} hepsi {summ(x)} | DC {summ(x[x.fam == 'DC'])} | RE {summ(x[x.fam == 'RE'])}")
    v = T[T.period == "VAKA"]
    print("\nVAKA replay:")
    print(v[["fam", "et", "R", "why", "e", "sig"]].to_string())
    # sonuç-körü eşikler: Y25 karar anı ER ve gürültü dağılımı (taban işlemlerinin karar barları)
    y = T[T.period == "Y25"]
    q = {}
    mk = {"y25": M["y25"], "y26": M["y26"]}
    vals = {"er60": [], "er120": [], "noise": []}
    for r in y.itertuples():
        m = mk["y25"] if r.et < pd.Timestamp("2026-01-01", tz="UTC") else mk["y26"]
        k = int(m.k_of(int(np.datetime64(r.et.tz_convert(None), "m").astype("int64"))))
        vals["er60"].append(m.er[60][k - 1])
        vals["er120"].append(m.er[120][k - 1])
        vals["noise"].append(m.noise_at(k))
    for kq, arr in vals.items():
        a = np.array(arr, float)
        a = a[np.isfinite(a)]
        q[kq] = {str(p): float(np.percentile(a, p)) for p in (10, 20, 33)}
    print("\nEşikler (Y25, sonuç körü):", json.dumps(q, indent=1))
    json.dump(q, open(RES / "thresholds.json", "w"), indent=1)
    T.to_pickle(RES / "base.pkl")


if __name__ == "__main__":
    main()
