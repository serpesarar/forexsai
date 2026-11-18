"""EK-1: ^NDX 1985–1999 bağımsız dönem (S N6 h5, O4)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import so  # noqa: E402

lib = so.lib
HERE = Path(__file__).resolve().parents[1]


def ndx() -> pd.DataFrame:
    d = pd.read_parquet(HERE / "data/NDX_1985.parquet")
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    x = pd.DataFrame({"c": d["Close"].astype(float)}).dropna()
    up = (x.c > x.c.shift(1)).astype(int)
    x["streak"] = up.groupby((up == 0).cumsum()).cumsum()
    days = x.index.to_series()
    x["f5"] = (x.c.shift(-5) / x.c - 1) * 1e4 - 2 - lib.FIN_BP_PER_DAY * (days.shift(-5) - days).dt.days.values
    return x


def main() -> None:
    x = ndx()
    out = {}
    for nm, a, b in (("1985_1999", "1985-01-01", "1999-02-28"), ("1999_2026", "1999-03-01", "2026-12-31")):
        z = x[(x.index >= a) & (x.index <= b)].dropna(subset=["f5"])
        m = (z.streak >= 6).values
        P = so.ath.bboot(z.f5.values[m], z.f5.values, 5)
        out[f"S_N6_h5_{nm}"] = {"n": int(m.sum()), "ort": round(float(z.f5[m].mean()), 1), "taban": round(float(z.f5.mean()), 1),
                                "fark": round(float(z.f5[m].mean() - z.f5.mean()), 1), "P": round(P, 4),
                                "yil": {int(y): [int(len(g)), round(float(g.f5.mean()), 1)] for y, g in z[m].groupby(z[m].index.year)}}
        w = so.weekly(x[(x.index >= a) & (x.index <= b)])
        m2 = w.after_q.values
        r = np.random.default_rng(3)
        A, B = w.r.values[m2], w.r.values[~m2]
        P2 = float((r.choice(A, (8000, len(A))).mean(1) - r.choice(B, (8000, len(B))).mean(1) < 0).mean())
        out[f"O4_{nm}"] = {"n": int(m2.sum()), "ort": round(float(A.mean()), 1), "taban": round(float(B.mean()), 1),
                           "fark": round(float(A.mean() - B.mean()), 1), "P_eksi": round(P2, 4)}
    s = out["S_N6_h5_1985_1999"]
    o = out["O4_1985_1999"]
    out["hukum_S"] = "NDX'e özgü B" if s["fark"] > 0 and s["P"] >= 0.95 else ("C+" if s["fark"] > 0 else "X")
    out["hukum_O4"] = "B (eksi)" if o["fark"] < 0 and o["P_eksi"] >= 0.95 else ("C+ kalır" if o["fark"] < 0 else "X")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    (HERE / "results/ek1_ndx1985.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
