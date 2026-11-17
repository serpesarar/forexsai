"""run_grid.py — PROTOCOL §5 keşif ızgarası + eşlenik zaman plasebosu ızgarası (NDX).

Her (TF, yön, örüntü, bölge, SL, TP, tutuş) için üst küme (S ≥ 3, hız ≥ 0) çözülür; S/hız/filtre alt kümeleri maskeyle.
Plasebo: her sinyal barına (TF, yön) başına tek sabit rastgele bar (aynı yıl × NY saati), aynı braket ATR katı.
"""
from __future__ import annotations

import itertools
import sys

import numpy as np
import pandas as pd

import fblib as F

PATTERNS = ["eng", "engf", "none"]
ZONES = ["altin", "sig382", "derin"]
SLS = ["L", "inv", "pat"]
TPS = ["H", "x1272", "x1618", "2R"]
HOLDS = [100, 300]
SMINS = [3.0, 4.0, 6.0]
SPMINS = [0.0, 0.5, 1.0]
FILTERS = ["tum", "ses:ASYA", "ses:AVRUPA", "ses:NY", "ses:KAPANIS_SONRASI",
           "gun:0", "gun:1", "gun:2", "gun:3", "gun:4"]
PERS = ["KESIF", "TEST", "KOR"]


def tstat(R: np.ndarray, d: np.ndarray) -> tuple[int, float, float]:
    n = len(R)
    if n < 2:
        return n, (float(R.mean()) if n else np.nan), np.nan
    u, inv = np.unique(d, return_inverse=True)
    s = np.bincount(inv, weights=R)
    c = np.bincount(inv)
    mu = R.mean()
    g = len(u)
    resid = s - mu * c
    se = np.sqrt((resid ** 2).sum() * g / max(g - 1, 1)) / n
    return n, float(mu), float(mu / se) if se > 0 else np.nan


def placebo_map(sig_t: np.ndarray, bars: F.Bars, p: F.Path1, seed: int) -> dict[int, int]:
    rng = np.random.default_rng(seed)
    bl = bars.last + 1
    okb = (bl < p.n) & (np.arange(len(bars.last)) > F.K_WIN + F.M_WIN) & (np.arange(len(bars.last)) < len(bars.last) - 2)
    loc = p.local[np.minimum(bl, p.n - 1)]
    dt = pd.to_datetime(loc, unit="s")
    key = dt.year.values * 100 + dt.hour.values
    idx = np.flatnonzero(okb)
    k = key[idx]
    o = np.argsort(k, kind="stable")
    ks = k[o]
    out = {}
    for t in np.unique(sig_t):
        kt = key[min(t, len(key) - 1)]
        a, b = np.searchsorted(ks, kt), np.searchsorted(ks, kt, side="right")
        out[int(t)] = int(idx[o[rng.integers(a, b)]]) if b > a else -1
    return out


def placebo_trades(tr: pd.DataFrame, pmap: dict, bars: F.Bars, p: F.Path1, hold: int) -> pd.DataFrame:
    tb = np.array([pmap.get(int(t), -1) for t in tr.t.values])
    ok = tb >= 0
    tb = np.where(ok, tb, 0)
    side = tr.side.values
    e1 = bars.last[tb] + 1
    e1 = np.minimum(e1, p.n - 1)
    entry = np.where(side > 0, p.o[e1] + p.spr[e1], p.o[e1])
    atr = bars.atr[tb]
    risk = tr.risk.values / tr.atr.values * atr
    reward = tr.reward.values / tr.atr.values * atr
    endbar = tb + 1 + hold
    end = np.where(endbar < len(bars.first), bars.first[np.minimum(endbar, len(bars.first) - 1)], p.n)
    pt = pd.DataFrame({"t": tb, "side": side, "e1": e1, "end": end, "entry": entry, "sl": entry - side * risk,
                       "tp": entry + side * reward, "risk": risk, "reward": reward, "spr_e": p.spr[e1], "atr": atr})
    ok &= risk >= F.MIN_RISK_SPR * pt.spr_e.values
    res = F.resolve(pt, p)
    res.loc[~ok, "R"] = np.nan
    return res


def filt_masks(tr: pd.DataFrame) -> dict[str, np.ndarray]:
    m = {"tum": np.ones(len(tr), bool)}
    for f in FILTERS[1:]:
        k, v = f.split(":")
        m[f] = (tr.session.values == v) if k == "ses" else (tr.dow.values == int(v))
    return m


def main(tfs: list[str]) -> None:
    p = F.load_main()
    F.RESULTS.mkdir(parents=True, exist_ok=True)
    for tf in tfs:
        m_, a_ = F.TFS_NDX[tf]
        bars = F.build_bars(p, m_, a_, tf)
        out = []
        for side in (1, -1):
            cand = F.detect(bars, side)
            sigs = {(pt, z): F.signals(cand, pt, z, 3.0, 0.0) for pt in PATTERNS for z in ZONES}
            all_t = np.concatenate([s.t.values for s in sigs.values()]) if sigs else np.array([], int)
            pmap = placebo_map(all_t, bars, p, seed=11 + side)
            for (pt, z), sig in sigs.items():
                for sl, tp, hold in itertools.product(SLS, TPS, HOLDS):
                    tr = F.resolve(F.setup_trades(sig, bars, p, sl, tp, hold, z), p)
                    if tr.empty:
                        continue
                    pl = placebo_trades(tr, pmap, bars, p, hold)
                    Rr, Rp = tr.R.values, pl.R.values
                    dr = tr.date.values.astype("datetime64[D]").astype(np.int64)
                    dpl = pl.date.values.astype("datetime64[D]").astype(np.int64)
                    per = tr.period.values
                    fm = filt_masks(tr)
                    for smin, spmin in itertools.product(SMINS, SPMINS):
                        base = (tr.S.values >= smin) & (tr.speed.values >= spmin)
                        for fn, fmask in fm.items():
                            mk = base & fmask
                            row = {"tf": tf, "side": side, "pattern": pt, "zone": z, "sl": sl, "tp": tp, "hold": hold,
                                   "smin": smin, "spmin": spmin, "filt": fn}
                            for pr in PERS:
                                mm = mk & (per == pr)
                                n, mu, t = tstat(Rr[mm], dr[mm])
                                row[f"n_{pr}"], row[f"R_{pr}"], row[f"t_{pr}"] = n, mu, t
                                mp = mm & ~np.isnan(Rp)
                                _, mup, tp_ = tstat(Rp[mp], dpl[mp])
                                row[f"pR_{pr}"], row[f"pt_{pr}"] = mup, tp_
                            out.append(row)
            print(tf, side, len(out), flush=True)
        pd.DataFrame(out).to_parquet(F.RESULTS / f"grid_{tf}.parquet")


if __name__ == "__main__":
    main(sys.argv[1:] or list(F.TFS_NDX))
