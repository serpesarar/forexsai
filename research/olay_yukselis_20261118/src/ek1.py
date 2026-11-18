"""EK-1: olay günü yükselişi SAT (H-a), habersiz yükseliş AL (H-b) — kör US30/US2000/US500."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oy  # noqa: E402

KD, G = oy.KD, oy.G


def main() -> None:
    cal = pd.read_csv(oy.ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(cal.date).dt.date)
    F = {"US30": KD.mt5_m30("US30"), "US2000": KD.mt5_m30("US2000"), "US500": KD.mt5_m30("US500", "2021-01-01")}
    fin = oy.hg.kk.FIN
    out, pool = {}, {"Ha": [], "Hb": []}
    for nm, b in F.items():
        df = oy.tab_up(b, 1800, ev)
        df["sat"] = -(df.xn16 + fin) - fin
        rec = {}
        for h, grp, col in (("Ha", True, "sat"), ("Hb", False, "xn16")):
            g = df[df.olay == grp]
            a, z = g[g.tag == "e0.006"], g[g.tag == "rnd"]
            rec[h] = {"n": int(len(a)), "ort": round(float(a[col].mean()), 1), "taban": round(float(z[col].mean()), 1),
                      "yil": {int(y): [int(len(q)), round(float(q[col].mean()), 1)] for y, q in a.groupby(pd.to_datetime(a.d).dt.year)}}
            pool[h].append((a[[col, "d"]].rename(columns={col: "v"}), z[[col, "d"]].rename(columns={col: "v"})))
        out[nm] = rec
        print(nm, json.dumps(rec, ensure_ascii=False), flush=True)
    for h in ("Ha", "Hb"):
        A = pd.concat([p[0] for p in pool[h]])
        Z = pd.concat([p[1] for p in pool[h]])
        P = G.KS.diff_p(A.v.values, A.d.astype(str).values, Z.v.values, Z.d.astype(str).values)
        k = sum(out[s][h]["ort"] > 0 and out[s][h]["ort"] > out[s][h]["taban"] for s in F)
        out[f"{h}_ozet"] = {"gecen": int(k), "havuz_P": round(float(P), 4), "havuz_ort": round(float(A.v.mean()), 1),
                            "hukum": "B" if k >= 2 and P >= 0.975 else ("C+" if k >= 2 else "X")}
        print(h, out[f"{h}_ozet"])
    (oy.RES / "ek1_kor.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
