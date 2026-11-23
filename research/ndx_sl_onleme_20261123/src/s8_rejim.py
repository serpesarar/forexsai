"""EK-5: aşırı oynak rejime (σ30 ≥ θ) özel BUY stratejileri — DIP / KIRILIM — K0 (mevcut DAYCOMBO V1) ve plaseboya karşı."""
from __future__ import annotations

import importlib.util
import json
import sys

import numpy as np
import pandas as pd

from eng import HERE, SL, run2

_sp = importlib.util.spec_from_file_location("my_s1", HERE / "s1_tarama.py")
S = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(S)
RES = HERE.parent / "results"
GEOS = [(1.0, 1.5), (1.5, 1.5), (1.0, 2.0)]
THETAS = (0.008, 0.010)
RNG = np.random.default_rng(23)


def arrays(m):
    if hasattr(m, "_rj"):
        return m._rj
    t = m.t
    tend5 = m.f5.tend.to_numpy()
    j = np.searchsorted(tend5, t + 1, side="right") - 1
    atr5 = np.where(j >= 0, m.f5.atr.to_numpy()[np.maximum(j, 0)], np.nan)
    sig = m.atr1 * np.sqrt(30) / m.c
    h = pd.Series(m.h)
    hh60 = h.rolling(60, min_periods=30).max().to_numpy()
    hh30p = h.shift(1).rolling(30, min_periods=20).max().to_numpy()
    mins = (t + 1) % 1440
    win = (mins >= 13 * 60 + 30) & (mins <= 20 * 60) & (m.wd < 4)
    m._rj = dict(atr5=atr5, sig=sig, hh60=hh60, hh30p=hh30p, win=win)
    return m._rj


def year_of(m, k):
    return int(m.b.ts.iloc[k].year)


def simulate(m, cond, theta, tp_m, sl_m, spread=1.5, slip=0.0):
    A = arrays(m)
    elig = A["win"] & (A["sig"] >= theta) & np.isfinite(A["atr5"]) & cond
    idx = np.flatnonzero(elig)
    out, free = [], -1
    for i in idx:
        if i <= free:
            continue
        k = i + 2
        if k >= len(m.t) or m.g[k] != m.g[i] or m.t[k] - m.t[i] > 5:
            continue
        sc = m.sc(k)
        a = A["atr5"][i]
        tend = int(m.t[i] - m.t[i] % 1440 + 20 * 60 + 50)
        x = m.out(k, tp_m * a, sl_m * a, e=None, spread=spread * sc, slip=slip * sc, tend=tend)
        if x is None:
            continue
        j, pts, why = x
        out.append((m.day[k], year_of(m, k), pts / (sl_m * a), why, int(i)))
        free = j + 5
    return pd.DataFrame(out, columns=["day", "yil", "R", "why", "i"])


def conds(m):
    A = arrays(m)
    green = m.c > m.o
    C = {}
    for mm in (1.0, 1.5, 2.0):
        C[f"K1 DIP m={mm}"] = (m.c <= A["hh60"] - mm * A["atr5"]) & green
    C["K3 KIRILIM 30dk"] = m.c > A["hh30p"]
    return C


def per(t):
    def blk(x):
        return dict(n=len(x), mR=round(float(x.R.mean()), 3) if len(x) else np.nan, SR=round(float(x.R.sum()), 1),
                    sl=round(float((x.why == "SL").mean()), 2) if len(x) else np.nan)
    return dict(A=blk(t[t.yil <= 2020]), B=blk(t[(t.yil >= 2021) & (t.yil <= 2023)]), SON=blk(t[t.yil >= 2024]),
                yil={int(y): round(float(g.R.sum()), 1) for y, g in t.groupby("yil")})


def boot(t, reps=3000):
    s = t.groupby("day").R.agg(["sum", "size"])
    p = RNG.integers(0, len(s), (reps, len(s)))
    mm = s["sum"].to_numpy()[p].sum(1) / s["size"].to_numpy()[p].sum(1)
    return float((mm > 0).mean())


def placebo(m_list, real: pd.DataFrame, theta, tp_m, sl_m, reps=200):
    """Aynı gün, aynı sayıda, rastgele rejim dakikası; tek tek (bağımsız) simülasyon."""
    pools = []
    for m in m_list:
        A = arrays(m)
        elig = np.flatnonzero(A["win"] & (A["sig"] >= theta) & np.isfinite(A["atr5"]))
        pools.append((m, pd.Series(elig).groupby(m.day[elig]).apply(np.array).to_dict()))
    need = real.groupby("day").size().to_dict()
    sims = []
    for _ in range(reps):
        Rs = []
        for d, n in need.items():
            for m, pool in pools:
                if d in pool:
                    for i in RNG.choice(pool[d], min(n, len(pool[d])), replace=False):
                        k = i + 2
                        if k >= len(m.t) or m.g[k] != m.g[i]:
                            continue
                        a = arrays(m)["atr5"][i]
                        tend = int(m.t[i] - m.t[i] % 1440 + 20 * 60 + 50)
                        x = m.out(k, tp_m * a, sl_m * a, e=None, spread=1.5 * m.sc(k), slip=0.0, tend=tend)
                        if x is not None:
                            Rs.append(x[1] / (sl_m * a))
                    break
        sims.append(np.mean(Rs) if Rs else np.nan)
    sims = np.array(sims)
    return float(np.nanmedian(sims)), float(np.nanmean(sims >= real.R.mean()))


def k0(theta):
    """Mevcut sistem: DAYCOMBO+REENTRY V1 2,5×ATR5, lag 1 — kararı rejimde olanlar."""
    def vb(m_, kk, f, c):
        x = f["atr5"]
        sl = SL if not np.isfinite(x) else max(SL, 2.5 * x / c["sc"])
        return {"kind": "mkt", "sl": sl, "tp": sl * 80 / 110}
    rows = []
    for mk in S.MK:
        m = S.M[mk]
        t, _ = run2(m, S.SIG[mk], rule=vb, lag=1)
        A = arrays(m)
        for r in t.itertuples():
            i = int(r.kk) - 1
            if A["sig"][i] >= theta:
                rows.append((m.day[r.kk], year_of(m, r.kk), r.R, r.why))
    return pd.DataFrame(rows, columns=["day", "yil", "R", "why"])


def main():
    only = sys.argv[1:]
    res = []
    for theta in THETAS:
        b = k0(theta)
        print(f"\n### θ=%{theta * 100:.1f}  K0 mevcut DAYCOMBO V1: n {len(b)} ortR {b.R.mean():+.3f} ΣR {b.R.sum():+.1f} SL %{100 * (b.why == 'SL').mean():.0f} | {per(b)}", flush=True)
        for mk in S.MK:
            arrays(S.M[mk])
        cn = {mk: conds(S.M[mk]) for mk in S.MK}
        for cname in cn[S.MK[0]]:
            if only and not any(o in cname for o in only):
                continue
            for tp_m, sl_m in GEOS:
                t = pd.concat([simulate(S.M[mk], cn[mk][cname], theta, tp_m, sl_m) for mk in S.MK])
                t15 = pd.concat([simulate(S.M[mk], cn[mk][cname], theta, tp_m, sl_m, spread=2.25, slip=0.2) for mk in S.MK])
                p = per(t)
                k1 = all(p[x]["mR"] > 0 for x in ("A", "B", "SON"))
                P = boot(t) if len(t) else np.nan
                s4 = all(p["yil"].get(y, 0) > 0 for y in (2023, 2024, 2025, 2026))
                row = dict(theta=theta, aday=cname, tp=tp_m, sl=sl_m, n=len(t), mR=round(float(t.R.mean()), 3),
                           SR=round(float(t.R.sum()), 1), SLpay=round(float((t.why == "SL").mean()), 2),
                           TPpay=round(float((t.why == "TP").mean()), 2), sp15=round(float(t15.R.mean()), 3), P=round(P, 3),
                           k1=k1, s4=s4, **{f"{x}_mR": p[x]["mR"] for x in ("A", "B", "SON")},
                           **{f"y{y}": p["yil"].get(y, 0) for y in range(2018, 2027)})
                if k1 and P >= 0.9 and row["sp15"] > 0:
                    ms = [S.M[mk] for mk in S.MK]
                    med, pp = placebo(ms, t, theta, tp_m, sl_m)
                    row.update(plasebo_med=round(med, 3), plasebo_p=round(pp, 3))
                res.append(row)
                print(f"  {cname:16s} TP{tp_m}/SL{sl_m} n {len(t):4d} ortR {row['mR']:+.3f} ΣR {row['SR']:+6.1f} "
                      f"SL %{100 * row['SLpay']:.0f} TP %{100 * row['TPpay']:.0f} | A {p['A']['mR']:+.3f} B {p['B']['mR']:+.3f} "
                      f"SON {p['SON']['mR']:+.3f} | P {P:.2f} sp15 {row['sp15']:+.3f} K1 {'✓' if k1 else '✗'} S4 {'✓' if s4 else '✗'} "
                      f"| yıl {p['yil']}" + (f" | plasebo med {row['plasebo_med']:+.3f} p {row['plasebo_p']:.3f}" if 'plasebo_p' in row else ""),
                      flush=True)
    pd.DataFrame(res).to_csv(RES / "rejim_tarama.csv", index=False)


if __name__ == "__main__":
    main()
