"""QS-01 birebir (R): Dukascopy NDX 1m 2021-11→2026-11, 15:05 girişi (ve 15:00), %1 stop 1m diplerinde, 16:00 çıkış."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from qs01 import flags, stats, GAP, STOP  # noqa: F401

H = Path(__file__).resolve().parent
P = H.parent / "geri_cekilme_limit_20261109/data/path.parquet"


def days_1m(entry_min: int) -> pd.DataFrame:
    p = pd.read_parquet(P)
    et = pd.to_datetime(p.t, unit="s", utc=True).dt.tz_convert("America/New_York")
    p["d"] = et.dt.tz_localize(None).dt.normalize()
    p["m"] = et.dt.hour * 60 + et.dt.minute
    p = p[(et.dt.dayofweek < 5) & (p.m >= 570) & (p.m <= 960)]
    rows = []
    for d, g in p.groupby("d"):
        g = g.set_index("m")
        if not {570, 899, entry_min, 960}.issubset(g.index) or len(g) < 350:
            continue
        pre = g.loc[570:899]
        e = g.open[entry_min] + g.spr[entry_min]
        stop_px = e * (1 - STOP)
        hold = g.loc[entry_min:959]
        x = stop_px if (hold.low <= stop_px).any() else g.open[960]
        rows.append(dict(d=d, open=g.open[570], close=g.open[960], p15=g.close[899],
                         hi=pre.high.max(), lo=pre.low.min(), ret=(x / e - 1) * 1e4,
                         gross=(g.open[960] / g.open[entry_min] - 1) * 1e4, stopped=bool((hold.low <= stop_px).any())))
    return pd.DataFrame(rows).set_index("d")


if __name__ == "__main__":
    out = {}
    for em, tag in ((905, "giris_1505"), (900, "giris_1500")):
        x = flags(days_1m(em))
        out[tag] = {"kural": stats(x.ret[x.sig]), "brut": stats(x.gross[x.sig]), "T0": stats(x.ret),
                    "T1_c3c4": stats(x.ret[x.c3 & x.c4]), "c1c2": stats(x.ret[x.c1 & x.c2]),
                    "yil": {int(y): round(float(v.mean()), 1) for y, v in x.ret[x.sig].groupby(x[x.sig].index.year)},
                    "tarihler": [str(d.date()) for d in x.index[x.sig]]}
    (H / "results/duka.json").write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False))
    for k, v in out.items():
        print(k, {kk: vv for kk, vv in v.items() if kk != "tarihler"})
