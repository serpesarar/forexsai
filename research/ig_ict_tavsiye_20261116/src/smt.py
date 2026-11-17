"""IG-01 — SMT uyumsuzluğu + yapı teyidi, NAS100 vs US500 M5 (PROTOCOL.md T1)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MT5 = ROOT.parent / "yon_lab_20261114" / "data" / "mt5"
OUT = ROOT / "results"
SERVER_MINUS_NY_SEC = 7 * 3600
NAS_POINT = 0.1
RTH_OPEN, RTH_CLOSE, LAST_ENTRY = 9 * 60 + 30, 16 * 60, 15 * 60
CONFIRM_BARS = 12
FRACTAL_K = 2
TARGETS = (1.0, 2.0, 3.0)
N_BOOT = 4000
RNG = np.random.default_rng(20261116)


def load() -> pd.DataFrame:
    a = pd.read_csv(MT5 / "NAS100_M5.csv.gz")
    b = pd.read_csv(MT5 / "US500_M5.csv.gz")
    d = a.merge(b[["t", "h", "l"]], on="t", suffixes=("", "_s"))
    et = pd.to_datetime(d.t - SERVER_MINUS_NY_SEC, unit="s")
    d["et"] = et
    d["mins"] = et.dt.hour * 60 + et.dt.minute
    d["date"] = et.dt.normalize()
    d["spr"] = d.sp * NAS_POINT
    return d.sort_values("t").reset_index(drop=True)


def levels(d: pd.DataFrame) -> pd.DataFrame:
    """Her gün için iki sembolün PDH/PDL ve ONH/ONL seviyeleri (yalnız geçmiş barlardan)."""
    rth = d[(d.mins >= RTH_OPEN) & (d.mins < RTH_CLOSE)]
    g = rth.groupby("date").agg(H=("h", "max"), L=("l", "min"), Hs=("h_s", "max"), Ls=("l_s", "min"))
    days = g.index.to_list()
    rows = []
    for i in range(1, len(days)):
        day, prev = days[i], days[i - 1]
        on_start = prev + pd.Timedelta(hours=18)
        on_end = day + pd.Timedelta(minutes=RTH_OPEN)
        on = d[(d.et >= on_start) & (d.et < on_end)]
        if len(on) < 50:
            continue
        p = g.loc[prev]
        rows.append(dict(date=day, PD_H=p.H, PD_L=p.L, PD_Hs=p.Hs, PD_Ls=p.Ls,
                         ON_H=on.h.max(), ON_L=on.l.min(), ON_Hs=on.h_s.max(), ON_Ls=on.l_s.min()))
    return pd.DataFrame(rows).set_index("date")


def fractal_known(d: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Her bar kapanışında bilinen son teyitli fraktal dip/tepe (k bar sağ teyit)."""
    h, l = d.h.to_numpy(), d.l.to_numpy()
    n, k = len(d), FRACTAL_K
    last_lo, last_hi = np.full(n, np.nan), np.full(n, np.nan)
    cur_lo = cur_hi = np.nan
    for i in range(n):
        j = i - k
        if j >= k:
            win_l, win_h = l[j - k:j + k + 1], h[j - k:j + k + 1]
            if l[j] == win_l.min() and (win_l == l[j]).sum() == 1:
                cur_lo = l[j]
            if h[j] == win_h.max() and (win_h == h[j]).sum() == 1:
                cur_hi = h[j]
        last_lo[i], last_hi[i] = cur_lo, cur_hi
    return last_lo, last_hi


def events(d: pd.DataFrame, lv: pd.DataFrame) -> list[dict]:
    out = []
    for day, grp in d[(d.mins >= RTH_OPEN) & (d.mins < RTH_CLOSE)].groupby("date"):
        if day not in lv.index:
            continue
        r = lv.loc[day]
        idx = grp.index.to_numpy()
        for lvl in ("PD", "ON"):
            for side in ("H", "L"):
                a_lvl, s_lvl = r[f"{lvl}_{side}"], r[f"{lvl}_{side}s"]
                if side == "H":
                    a_x = grp.h.to_numpy() > a_lvl
                    s_x = grp.h_s.to_numpy() > s_lvl
                else:
                    a_x = grp.l.to_numpy() < a_lvl
                    s_x = grp.l_s.to_numpy() < s_lvl
                fa = np.argmax(a_x) if a_x.any() else None
                fs = np.argmax(s_x) if s_x.any() else None
                if fa is None and fs is None:
                    continue
                first = min(x for x in (fa, fs) if x is not None)
                both_same = fa is not None and fs is not None and fa == fs
                kind = "CTRL" if both_same else "SMT"
                leader = "both" if both_same else ("NAS" if fa == first else "SPX")
                direction = -1 if side == "H" else 1  # tepe süpürmesi → SAT
                out.append(dict(date=day, level=lvl, side=side, kind=kind, leader=leader,
                                i=int(idx[first]), dir=direction))
    return out


def simulate(d: pd.DataFrame, ev: dict, entry_i: int, tgt: float, spr_mult: float) -> float | None:
    h, l, o, c = d.h.to_numpy(), d.l.to_numpy(), d.o.to_numpy(), d.c.to_numpy()
    mins, dates = d.mins.to_numpy(), d.date.to_numpy()
    if entry_i >= len(d) or dates[entry_i] != dates[ev["i"]] or mins[entry_i] > LAST_ENTRY:
        return None
    e, s = o[entry_i], ev["dir"]
    seg = slice(ev["i"], entry_i)
    stop = h[seg].max() if s < 0 else l[seg].min()
    risk = (stop - e) if s < 0 else (e - stop)
    spr = d.spr.iat[entry_i] * spr_mult
    if risk <= 2 * d.spr.iat[entry_i]:
        return None
    cost = spr / risk
    j = entry_i
    while j < len(d) and dates[j] == dates[entry_i] and mins[j] < RTH_CLOSE:
        if s < 0:
            if h[j] >= stop:
                return -1 - cost
            if l[j] <= e - tgt * risk:
                return tgt - cost
        else:
            if l[j] <= stop:
                return -1 - cost
            if h[j] >= e + tgt * risk:
                return tgt - cost
        j += 1
    last = j - 1
    return s * (c[last] - e) / risk - cost


def confirm_entry(d: pd.DataFrame, ev: dict, lo_k: np.ndarray, hi_k: np.ndarray) -> int | None:
    i, c = ev["i"], d.c.to_numpy()
    ref = lo_k[i] if ev["dir"] < 0 else hi_k[i]
    if np.isnan(ref):
        return None
    for j in range(i + 1, min(i + 1 + CONFIRM_BARS, len(d))):
        if d.date.iat[j] != d.date.iat[i]:
            return None
        if (ev["dir"] < 0 and c[j] < ref) or (ev["dir"] > 0 and c[j] > ref):
            return j + 1
    return None


def boot_p(x: pd.Series, days: pd.Series) -> float:
    g = pd.DataFrame({"x": x, "d": days}).groupby("d").x.sum()
    cnt = pd.DataFrame({"x": x, "d": days}).groupby("d").x.size()
    gs, cs = g.to_numpy(), cnt.to_numpy()
    k = len(gs)
    sel = RNG.integers(0, k, size=(N_BOOT, k))
    means = gs[sel].sum(1) / cs[sel].sum(1)
    return float((means > 0).mean())


def summarize(t: pd.DataFrame) -> dict:
    if len(t) == 0:
        return {"n": 0}
    mid = t.date.sort_values().iloc[len(t) // 2]
    a, b = t[t.date < mid], t[t.date >= mid]
    return dict(n=len(t), days=int(t.date.nunique()), mean=round(t.R.mean(), 4),
                win=round((t.R > 0).mean(), 3), P=round(boot_p(t.R, t.date), 3),
                h1=round(a.R.mean(), 4), h2=round(b.R.mean(), 4))


def diff_p(a: pd.DataFrame, b: pd.DataFrame) -> tuple[float, float]:
    ma, mb = a.R.to_numpy(), b.R.to_numpy()
    sa = RNG.integers(0, len(ma), size=(N_BOOT, len(ma)))
    sb = RNG.integers(0, len(mb), size=(N_BOOT, len(mb)))
    dd = ma[sa].mean(1) - mb[sb].mean(1)
    return round(ma.mean() - mb.mean(), 4), round(float((dd > 0).mean()), 3)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    d = load()
    lv = levels(d)
    lo_k, hi_k = fractal_known(d)
    evs = events(d, lv)
    rows = []
    for ev in evs:
        for mode in ("U", "K"):
            ent = ev["i"] + 1 if mode == "U" else confirm_entry(d, ev, lo_k, hi_k)
            if ent is None:
                continue
            for tgt in TARGETS:
                for sm in (1.0, 1.5):
                    r = simulate(d, ev, ent, tgt, sm)
                    if r is not None:
                        rows.append({**ev, "mode": mode, "tgt": tgt, "spr_mult": sm, "R": r})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "smt_islemler.csv", index=False)
    res: dict = {"span": [str(d.et.iloc[0]), str(d.et.iloc[-1])], "days": int(lv.shape[0]),
                 "events": pd.DataFrame(evs).groupby("kind").size().to_dict(), "cells": {}}
    for (kind, mode, tgt, sm), g in t.groupby(["kind", "mode", "tgt", "spr_mult"]):
        res["cells"][f"{kind}|{mode}|{tgt}R|spr{sm}"] = summarize(g)
    base = t[(t.tgt == 2.0) & (t.spr_mult == 1.0)]
    ks, kc = base[(base.kind == "SMT") & (base["mode"] == "K")], base[(base.kind == "CTRL") & (base["mode"] == "K")]
    us = base[(base.kind == "SMT") & (base["mode"] == "U")]
    res["K_SMT_minus_K_CTRL"] = diff_p(ks, kc)
    res["K_SMT_minus_U_SMT"] = diff_p(ks, us)
    res["by_leader_K2R"] = {k: summarize(g) for k, g in ks.groupby("leader")}
    res["by_level_K2R"] = {k: summarize(g) for k, g in ks.groupby(["level", "side"])}
    res["by_level_K2R"] = {"|".join(k): v for k, v in res["by_level_K2R"].items()}
    (OUT / "smt_ozet.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
    print(json.dumps(res, indent=1, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
