"""EK-1 F6 — üst TF FVG'leri likidite (mıknatıs) mı (madde 6).

Her 15 dk ızgara noktasında en yakın dolmamış üst/alt FVG kenarı (U, D); seans sonuna kadar hangisine önce dokunulur.
Sıfır: sürüklenmesiz fiyatta P(önce üst) = D/(U+D). Fark gün kümeli t ile, KEŞİF ve TEST ayrı.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from derin_lib import CLOSE, M1_CACHE, OUT, SPLIT, load_mat

TFS = {"5m": (300, 0), "1H": (3600, 0), "4H": (14400, 18 * 3600)}
GRID = {"03:00-09:30": range(180, 570, 15), "AM": range(570, 720, 15), "PM": range(810, 946, 15)}
AGE_1D = 86400


def load_m1() -> pd.DataFrame:
    d = pd.read_parquet(M1_CACHE, columns=["t", "high", "low", "close", "d", "m"]).sort_values("t").reset_index(drop=True)
    d["et"] = (d.d.values.astype("datetime64[D]").astype(np.int64) * 86400 + d.m.astype(np.int64) * 60)
    return d


def sparse(a: np.ndarray, fn) -> list[np.ndarray]:
    st = [a.astype(np.float32)]
    k = 1
    while 2 * k <= len(a):
        prev = st[-1]
        st.append(fn(prev[:-k], prev[k:]))
        k *= 2
    return st


def first_reach(st: list[np.ndarray], start: int, x: float, below: bool) -> int:
    """start'tan itibaren ilk indeks: below → değer ≤ x (min tablosu), değilse ≥ x (max tablosu)."""
    n, pos = len(st[0]), start
    if pos >= n:
        return n
    for k in range(len(st) - 1, -1, -1):
        span = 1 << k
        if pos + span <= n and pos < len(st[k]):
            v = st[k][pos]
            if (v > x) if below else (v < x):
                pos += span
    return pos


def zones(m1: pd.DataFrame, tf: int, anchor: int) -> pd.DataFrame:
    key = ((m1.et - anchor) // tf).to_numpy()
    bar = np.r_[0, np.cumsum(key[1:] != key[:-1])]
    g = pd.DataFrame({"bar": bar, "h": m1.high.to_numpy(), "l": m1.low.to_numpy()}).groupby("bar")
    h, l = g.h.max().to_numpy(), g.l.min().to_numpy()
    last = np.r_[np.flatnonzero(bar[1:] != bar[:-1]), len(bar) - 1]
    i = np.arange(2, len(h))
    bull = l[i] > h[i - 2]
    bear = h[i] < l[i - 2]
    z = pd.concat([pd.DataFrame({"bot": h[i - 2][bull], "top": l[i][bull], "c": last[i][bull], "typ": 1}),
                   pd.DataFrame({"bot": h[i][bear], "top": l[i - 2][bear], "c": last[i][bear], "typ": -1})])
    return z.reset_index(drop=True)


def fill_index(z: pd.DataFrame, st_lo: list, st_hi: list) -> np.ndarray:
    out = np.empty(len(z), dtype=np.int64)
    for r, (bot, top, c, typ) in enumerate(z[["bot", "top", "c", "typ"]].itertuples(index=False)):
        out[r] = first_reach(st_lo, int(c) + 1, top, True) if typ == 1 else first_reach(st_hi, int(c) + 1, bot, False)
    return out


def race_points(m, m1: pd.DataFrame, z: pd.DataFrame, t_arr: np.ndarray) -> pd.DataFrame:
    key = pd.Series(np.arange(len(m1)), index=m1.d.values.astype("datetime64[D]").astype(np.int64) * 1440 + m1.m.values)
    key = key[~key.index.duplicated()]
    H, L, C = m1.high.to_numpy(), m1.low.to_numpy(), m1.close.to_numpy()
    zc, zf, zb, zt = z.c.to_numpy(), z.f.to_numpy(), z.bot.to_numpy(), z.top.to_numpy()
    rows = []
    for di, day in enumerate(m.days):
        base = day.astype("datetime64[D]").astype(np.int64) * 1440
        end = key.get(base + CLOSE - 1)
        start = key.get(base + 180)
        if end is None or start is None:
            continue
        sub = (zc <= end) & (zf > start)
        if not sub.any():
            continue
        sc, sf, sb, stp = zc[sub], zf[sub], zb[sub], zt[sub]
        sage = t_arr[np.minimum(sc, len(t_arr) - 1)]
        for sl, mins in GRID.items():
            for p in mins:
                g = key.get(base + p)
                if g is None:
                    continue
                P = C[g - 1]
                act = (sc <= g - 1) & (sf > g - 1)
                if not act.any():
                    continue
                for age_name, age_ok in (("hepsi", act), ("<=1g", act & (t_arr[g] - sage <= AGE_1D))):
                    up_e = sb[age_ok & (sb > P)]
                    dn_e = stp[age_ok & (stp < P)]
                    if len(up_e) == 0 or len(dn_e) == 0:
                        continue
                    U, D = up_e.min() - P, P - dn_e.max()
                    hu = H[g:end + 1] >= P + U
                    hd = L[g:end + 1] <= P - D
                    ju = np.argmax(hu) if hu.any() else 10 ** 9
                    jd = np.argmax(hd) if hd.any() else 10 ** 9
                    if ju == jd:
                        continue
                    # hayalet: aynı noktada mesafeler aynalanır (üst D, alt U) → sürüklenme etkisi
                    gu = H[g:end + 1] >= P + D
                    gd = L[g:end + 1] <= P - U
                    kgu = np.argmax(gu) if gu.any() else 10 ** 9
                    kgd = np.argmax(gd) if gd.any() else 10 ** 9
                    ghost = float(kgu < kgd) - U / (U + D) if kgu != kgd else np.nan
                    rows.append(dict(di=di, sl=sl, yas=age_name, up=float(ju < jd), exp=D / (U + D),
                                     U=U, D=D, K=bool(day < SPLIT), ghost_fark=ghost))
    return pd.DataFrame(rows)


def summarize(r: pd.DataFrame) -> list[dict]:
    out = []
    for keys, g in r.groupby(["tf", "yas", "sl", "K"]):
        d = (g.up - g.exp).groupby(g.di).mean()
        net = (g.up - g.exp - g.ghost_fark).groupby(g.di).mean()
        bins = pd.cut(g.exp, [0, 0.2, 0.4, 0.6, 0.8, 1.0])
        out.append(dict(tf=keys[0], yas=keys[1], sl=keys[2], K=keys[3], n=len(g), gun=len(d),
                        gozlenen=g.up.mean(), beklenen=g.exp.mean(), fark=d.mean(),
                        t=d.mean() / d.std(ddof=1) * np.sqrt(len(d)),
                        hayalet_fark=g.ghost_fark.mean(), fvg_eksi_hayalet=net.mean(),
                        t_net=net.mean() / net.std(ddof=1) * np.sqrt(len(net)),
                        kova=(g.groupby(bins, observed=True).apply(lambda x: round(x.up.mean() - x.exp.mean(), 4))).rename(index=str).to_dict()))
    return out


def main() -> None:
    m = load_mat()
    m1 = load_m1()
    st_lo = sparse(m1.low.to_numpy(), np.minimum)
    st_hi = sparse(m1.high.to_numpy(), np.maximum)
    t_arr = m1.t.to_numpy()
    allr = []
    for name, (tf, anc) in TFS.items():
        z = zones(m1, tf, anc)
        z["f"] = fill_index(z, st_lo, st_hi)
        r = race_points(m, m1, z, t_arr)
        r["tf"] = name
        allr.append(r)
        print(name, "zones", len(z), "points", len(r), flush=True)
    r = pd.concat(allr)
    r.to_parquet(OUT / "f6_noktalar.parquet")
    s = summarize(r)
    (OUT / "derin_f6.json").write_text(json.dumps(s, indent=1, default=str, ensure_ascii=False))
    print(pd.DataFrame(s).drop(columns="kova").round(4).to_string())


if __name__ == "__main__":
    main()
