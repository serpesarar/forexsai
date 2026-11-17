"""SONRADAN TANI (hüküm dışı, en fazla C): SMT/kontrol süpürmesinin DEVAM yönü, temkinli (aynı barda önce stop).

Giriş: olay barından sonraki bar açılışı, süpürme yönünde. Stop mesafesi = girişin süpürme ucuna uzaklığı
(SMT işlemiyle aynı risk), stop girişin karşı tarafında; hedef k × risk; pencere sonunda kapat.
"Ters = −brüt" yaklaşımı aynı-bar belirsizliğinde devamı iyimser sayıyordu (E142).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from smt_grid import OUT, TEST_START, build_events_only

KS = (1.0, 2.0, 3.0)


def sim_cont(ev: dict, d: pd.DataFrame, k: float) -> float | None:
    H, L, O, C, S = (d[c].to_numpy() for c in ("h", "l", "o", "c", "spr"))
    e_i = ev["i"] + 1
    if e_i > ev["end"]:
        return None
    s = -ev["dir"]  # tepe süpürmesi → AL (devam)
    e = O[e_i]
    ext = H[ev["i"]] if s > 0 else L[ev["i"]]
    risk = abs(e - ext)
    if risk <= 2 * S[e_i]:
        return None
    stop, tgt, cost = e - s * risk, e + s * k * risk, S[e_i] / risk
    for j in range(e_i, ev["end"] + 1):
        if (s > 0 and L[j] <= stop) or (s < 0 and H[j] >= stop):
            return -1.0 - cost
        if (s > 0 and H[j] >= tgt) or (s < 0 and L[j] <= tgt):
            return k - cost
    return s * (C[ev["end"]] - e) / risk - cost


def main() -> None:
    rows = []
    for tf in ("M30", "M5"):
        d, evs = build_events_only(tf)
        for ev in evs:
            for k in KS:
                r = sim_cont(ev, d, k)
                if r is not None:
                    per = "B" if tf == "M5" else ("K" if ev["sdate"] < TEST_START else "T")
                    rows.append(dict(w=ev["w"], level=ev["level"], kind=ev["kind"], k=k, per=per, R=r, sdate=ev["sdate"]))
    t = pd.DataFrame(rows)
    t.to_parquet(OUT / "smt_devam_islemler.parquet")
    g = t.groupby(["kind", "k", "per"]).R.agg(["size", "mean", "std"])
    g["t"] = g["mean"] / g["std"] * np.sqrt(g["size"])
    print(g[["size", "mean", "t"]].unstack("per").round(3).to_string())
    c = t.groupby(["w", "level", "kind", "k", "per"]).R.agg(["size", "mean"]).unstack("per")
    c = c[(c[("size", "K")] >= 15) & (c[("size", "T")] >= 30)]
    allpos = ((c["mean"][["K", "T", "B"]] > 0).all(1))
    c.columns = [f"{a}_{b}" for a, b in c.columns]
    res = dict(hucre=int(len(c)), uc_donemde_arti=int(allpos.sum()),
               havuz=g[["size", "mean", "t"]].round(4).reset_index().to_dict("records"),
               arti_hucreler=c[allpos].round(3).reset_index().astype(str).to_dict("records"))
    (OUT / "smt_devam.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("hücre", res["hucre"], "üç dönemde artı", res["uc_donemde_arti"])
    print(c[allpos].round(3).to_string())


if __name__ == "__main__":
    main()
