"""R1 duyarlılık (betimsel, sonradan): eşik × tahvil (TLT/IEF/sentetik) × sinyal günü, QQQ 2002-08→2026-10."""
import json
import numpy as np, pandas as pd
import r1_dengeleme as R
from r1_dengeleme import px, build, st, synth_bond, H
inst = {"QQQ": px("QQQ")}
out = {}
for bname, bond in (("TLT", px("TLT")), ("IEF", px("IEF") if (R.D / "IEF.parquet").exists() else None), ("sentetik10y", synth_bond(px("TNX", "Close")))):
    if bond is None:
        continue
    for th in (0.01, 0.015, 0.02, 0.03):
        R.TH = th
        for lag in (3, 4, 5):
            M = build(px("SPY"), bond, inst, lag=lag); q = M[(M.side != 0) & (M.d_s >= "2002-08-01")]
            v = (q.side * q.r_QQQ - R.COST).to_numpy()
            out[f"{bname} esik{th} D-{lag}"] = {k: st(v)[k] for k in ("n", "ort", "P")}
R.TH = 0.02
(H / "results/r1_duyarlilik.json").write_text(json.dumps(out, indent=1))
for k, v in out.items(): print(f"{k:28s} {v}")
