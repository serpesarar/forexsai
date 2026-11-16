"""q_daily.py — PROTOCOL EK-2: 1m anatomisinin günlük izi → gece / ertesi gün. Çıktı results/q_daily.json, q_daily.parquet"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
PER = {"KESIF": (date(2022, 1, 1), date(2023, 12, 31)), "TEST": (date(2024, 1, 1), date(2026, 12, 31)),
       "BAGIMSIZ": (date(2018, 1, 1), date(2021, 12, 31))}


def per(d):
    return next((k for k, (a, b) in PER.items() if a <= d <= b), "?")


def build(m1, D) -> pd.DataFrame:
    full = D[D.full].reset_index(drop=True)
    days = D.d.tolist()
    nxt = {days[i]: days[i + 1] for i in range(len(days) - 1)}
    rows = []
    for r in full.itertuples():
        a, b = int(np.searchsorted(m1.t, lib.utc(r.d, 570))), int(np.searchsorted(m1.t, lib.utc(r.d, 960)))
        o, h, l, c, mm = m1.o[a:b], m1.h[a:b], m1.l[a:b], m1.c[a:b], m1.m[a:b]
        rng = h - l
        if len(o) < 300 or rng.sum() <= 0 or r.d not in nxt:
            continue
        lw, uw = np.minimum(o, c) - l, h - np.maximum(o, c)
        last = mm >= 900
        clv = np.where(rng > 0, (c - l) / np.where(rng > 0, rng, 1), np.nan)
        dh, dl = h.max(), l.min()
        nd = nxt[r.d]
        g = lib.time_trade(m1, "G", r.d, lib.utc(r.d, 960), lib.utc(nd, 570), +1)
        q = lib.time_trade(m1, "Q", r.d, lib.utc(r.d, 960), lib.utc(nd, lib.nyse.cash_close_minutes(nd)), +1)
        if g is None or q is None:
            continue
        rows.append({"d": r.d, "per": per(r.d), "W_gun": (lw.sum() - uw.sum()) / rng.sum(), "CLV_gun": float(np.nanmean(clv)),
                     "W_son": (lw[last].sum() - uw[last].sum()) / max(1e-9, rng[last].sum()),
                     "r_gun": c[-1] / o[0] - 1, "IBS": (c[-1] - dl) / (dh - dl) if dh > dl else 0.5,
                     "gece": g.net_bp(), "gun": q.net_bp()})
    return pd.DataFrame(rows)


def ols_t(df, f, y):
    X = np.c_[np.ones(len(df)), *[(df[k] - df[k].mean()) / df[k].std() for k in (f, "r_gun", "IBS")]]
    b, *_ = np.linalg.lstsq(X, df[y].values, rcond=None)
    res = df[y].values - X @ b
    s2 = res @ res / (len(df) - X.shape[1])
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    return float(b[1]), float(b[1] / se[1])


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1)
    q = build(m1, D)
    q.to_parquet(OUT / "q_daily.parquet")
    out = {}
    for f in ("W_gun", "CLV_gun", "W_son"):
        e = list(q[q.per == "KESIF"][f].quantile([1 / 3, 2 / 3]))
        out[f] = {"esik": e}
        for y in ("gece", "gun"):
            cell = {}
            for p in PER:
                g = q[q.per == p]
                top, bot = g[g[f] > e[1]], g[g[f] <= e[0]]
                mo = pd.to_datetime(top.d).dt.to_period("M").astype(str).values
                b, t = ols_t(g, f, y)
                cell[p] = {"n_ust": len(top), "ust": float(top[y].mean()), "alt": float(bot[y].mean()), "tum": float(g[y].mean()),
                           "P_ust": lib.block_boot_p(top[y].values, mo), "ols_b": b, "ols_t": t}
            bs = [cell[p]["ols_b"] for p in PER]
            tp = ols_t(q, f, y)[1]
            cell["havuz_t"] = tp
            cell["gecti"] = bool(all(cell[p]["ust"] > 0 for p in PER) and cell["TEST"]["P_ust"] >= 0.9 and cell["BAGIMSIZ"]["P_ust"] >= 0.9
                                 and all(cell[p]["ust"] > cell[p]["alt"] for p in PER)
                                 and (all(x > 0 for x in bs) or all(x < 0 for x in bs)) and abs(tp) >= 2)
            out[f][y] = cell
    (OUT / "q_daily.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for f, v in out.items():
        for y in ("gece", "gun"):
            c = v[y]
            print(f, y, {p: (c[p]["n_ust"], round(c[p]["ust"], 1), round(c[p]["alt"], 1), round(c[p]["tum"], 1), round(c[p]["P_ust"], 2), round(c[p]["ols_t"], 2)) for p in PER},
                  "havuz_t", round(c["havuz_t"], 2), "GEÇTİ", c["gecti"])


if __name__ == "__main__":
    main()
