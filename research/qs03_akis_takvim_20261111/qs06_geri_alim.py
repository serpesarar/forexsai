"""QS-06 C: hisse geri alım yasağı penceresi (PROTOCOL_QS06.md §C). AÇIK − YASAK günlük getiri farkı, ABD vs yabancı plasebo."""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from r1_dengeleme import px, H
from qs04_e4 import load, CSV, PQ

RNG = np.random.default_rng(67)


def groups(close: pd.Series) -> pd.DataFrame:
    c = close.dropna(); c = c[c > 0]; idx = c.index
    r = (c / c.shift(1) - 1) * 1e4
    pos = pd.Series(np.arange(len(idx)), index=idx)
    last = pos.groupby(idx.to_period("M")).max()
    excl = np.zeros(len(idx), bool); black = np.zeros(len(idx), bool)
    for per, D in last.items():
        excl[max(0, D - 3): min(len(idx), D + 4)] = True          # ay dönümü + R1 penceresi (D−3 … D+3)
        if per.month in (3, 6, 9, 12):
            black[max(0, D - 10): min(len(idx), D + 16)] = True    # [Q−10, Q+15]
    df = pd.DataFrame({"r": r.values, "excl": excl, "black": black, "m": idx.to_period("M")}, index=idx).iloc[1:]
    return df[~df.excl]


def diff_stats(df: pd.DataFrame, a: str, b: str) -> dict:
    d = df[(df.index >= a) & (df.index < b)]
    if len(d) < 200:
        return {"n": int(len(d))}
    op, bl = d.r[~d.black], d.r[d.black]
    months = d.m.unique(); g = {m: x for m, x in d.groupby("m")}
    sums = np.array([[x.r[~x.black].sum(), (~x.black).sum(), x.r[x.black].sum(), x.black.sum()] for x in g.values()])
    bs = []
    for _ in range(3000):
        s = sums[RNG.integers(0, len(sums), len(sums))].sum(0)
        if s[1] > 0 and s[3] > 0:
            bs.append(s[0] / s[1] - s[2] / s[3])
    bs = np.array(bs)
    return {"acik_ort": round(float(op.mean()), 2), "yasak_ort": round(float(bl.mean()), 2), "fark": round(float(op.mean() - bl.mean()), 2),
            "P_fark>0": round(float((bs > 0).mean()), 3), "n_acik": int(len(op)), "n_yasak": int(len(bl))}


def main():
    res = {"ABD": {}, "yabanci_2004_26": {}}
    for nm in ("SPY", "QQQ"):
        g = groups(px(nm))
        res["ABD"][nm] = {"2004_14": diff_stats(g, "2004-01-01", "2015-01-01"), "2015_26": diff_stats(g, "2015-01-01", "2026-11-01")}
    res["ABD"]["SPY"]["1993_2003"] = diff_stats(groups(px("SPY")), "1993-02-01", "2004-01-01")
    for nm in CSV + PQ:
        res["yabanci_2004_26"][nm] = diff_stats(groups(load(nm)), "2004-01-01", "2026-11-01")
    us = [res["ABD"][n][p]["fark"] for n in ("SPY", "QQQ") for p in ("2004_14", "2015_26")]
    fo = [v["fark"] for v in res["yabanci_2004_26"].values() if "fark" in v]
    c1 = all(res["ABD"][n][p]["fark"] > 0 for n in ("SPY", "QQQ") for p in ("2004_14", "2015_26")) and \
        all(np.mean([res["ABD"][n][p]["P_fark>0"] for n in ("SPY", "QQQ")]) >= .9 for p in ("2004_14", "2015_26"))
    c2 = np.mean(fo) < 0.5 * np.mean(us)
    c3 = res["ABD"]["SPY"]["1993_2003"]["fark"] < np.mean([res["ABD"]["SPY"][p]["fark"] for p in ("2004_14", "2015_26")])
    res["ozet"] = {"ABD_fark_ort": round(float(np.mean(us)), 2), "yabanci_fark_ort": round(float(np.mean(fo)), 2),
                   "yabanci_arti": f"{sum(x > 0 for x in fo)}/{len(fo)}", "1": bool(c1), "2": bool(c2), "3": bool(c3),
                   "sinif": "B-" if c1 and c2 and c3 else ("C" if c1 else "X")}
    (H / "results/qs06_geri_alim.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
