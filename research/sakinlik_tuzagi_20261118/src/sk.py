"""sk.py — uzun sakinlik → sert düşüş olasılığı (PROTOCOL). python sk.py"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
SRC = HERE.parent / "ndx_seri_opex_20261118/data/NDX_1985.parquet"
ERAS = (("1985_2007", "1985-01-01", "2007-12-31"), ("2008_2020", "2008-01-01", "2020-12-31"), ("2021_2026", "2021-01-01", "2026-12-31"))


def main() -> None:
    d = pd.read_parquet(SRC)
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    c = d["Close"].astype(float).dropna()
    c.index = pd.to_datetime(c.index).tz_localize(None)
    r = c.pct_change()
    rv = r.rolling(20).std()
    lo = rv.rolling(250, min_periods=200).quantile(0.20).shift(1)
    sma = c.rolling(50).mean()
    calm = (rv <= lo) & (c > sma)
    S = calm.astype(int).groupby((~calm).cumsum()).cumsum()
    fut = pd.concat([c.shift(-k) for k in range(1, 21)], axis=1)
    mdd = (fut.min(axis=1) / c - 1)
    f20 = c.shift(-20) / c - 1
    df = pd.DataFrame({"S": S, "calm": calm, "mdd": mdd, "f20": f20}).dropna()
    df["kova"] = np.select([~df.calm, df.S <= 20, df.S <= 60], ["sakin_degil", "S1_20", "S21_60"], "S60+")
    out = {}
    for nm, a, b in ERAS:
        z = df[(df.index >= a) & (df.index <= b)]
        out[nm] = {k: {"gun": int(len(g)), "P_dusus5": round(float((g.mdd <= -0.05).mean()), 3), "f20_bp": round(float(g.f20.mean() * 1e4), 1)}
                   for k, g in z.groupby("kova")}
        print(nm, json.dumps(out[nm], ensure_ascii=False))
    sup = [out[e].get("S60+", {}).get("P_dusus5", 0) > out[e]["sakin_degil"]["P_dusus5"] for e, _, _ in ERAS]
    out["hukum"] = "tez desteklenir (C+)" if all(sup) else ("son 5 yıla özgü iz" if sup[2] and not any(sup[:2]) else "tez desteklenmez (X)")
    print(out["hukum"])
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results/sakinlik.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
