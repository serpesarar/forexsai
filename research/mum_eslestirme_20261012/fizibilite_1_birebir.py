"""Fizibilite-1: kullanıcı tanımı — mum-mum ±pay (tepe/dip/kapanış, açılışa göre) birebir eşleşme sayısı.

Temsil 'pct' = %, mumun kendi açılışına göre (kullanıcının %0,01–0,02 payı); 'atr' = aynı üç fark / ATR14 (önceki 14 mum).
Her (sembol, TF) için son 1 yıldan rastgele NQ sorgu bitişi; kütüphane = mevcut 5 yıl. Öz-eşleşme ve kaydırmaları hariç,
çakışmasız (aralık ≥ X) sayım. SONUÇLARA BAKMAZ.
Çalıştır:  python3 research/mum_eslestirme_20261012/fizibilite_1_birebir.py   (~3 dk)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _common import HERE, PIP, load, nq, sources

XS = [1, 2, 3, 4, 5, 6, 8, 10, 12]
TOL_PCT = [0.01, 0.02, 0.05]
TOL_ATR = [0.10, 0.20, 0.30]
MIN_N = 30


def count_matches(F: np.ndarray, X_list: list, tol: float, q_ends: np.ndarray, excl: int):
    """F [n×3]; her sorgu için X=1..max eşleşme sayısı (ham ve çakışmasız)."""
    n = len(F); xmax = max(X_list)
    res = {X: [] for X in X_list}; res_no = {X: [] for X in X_list}
    for qe in q_ends:
        alive = np.ones(n, bool)            # alive[e] → e'de biten pencere şu ana kadar tutuyor
        for k in range(xmax):               # k=0 son mum, k=1 bir önceki ...
            m = np.all(np.abs(F - F[qe - k]) <= tol, axis=1)
            shifted = np.zeros(n, bool); shifted[k:] = m[:n - k] if k > 0 else m
            alive &= shifted
            X = k + 1
            if X in res:
                e = np.flatnonzero(alive)
                e = e[(e >= X - 1) & (np.abs(e - qe) >= max(X, excl))]
                e = e[e < n - 1]
                res[X].append(len(e))
                cnt, last = 0, -10**9
                for v in e:
                    if v - last >= X:
                        cnt += 1; last = v
                res_no[X].append(cnt)
    return res, res_no


def main(out=HERE / "results/fizibilite_1_birebir.csv") -> None:
    rng = np.random.default_rng(7); rows = []
    for (sym, tf), path in sources().items():
        d = load(path)
        o, h, l, c = (d[k].to_numpy(float) for k in ["open", "high", "low", "close"])
        Fp = np.stack([100 * (h / o - 1), 100 * (l / o - 1), 100 * (c / o - 1)], 1)
        tr = np.maximum(h - l, np.maximum(np.abs(h - np.r_[c[0], c[:-1]]), np.abs(l - np.r_[c[0], c[:-1]])))
        atr = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()
        Fa = np.stack([(h - o) / atr, (l - o) / atr, (c - o) / atr], 1)
        valid = np.isfinite(Fa).all(1); Fa[~valid] = 1e9
        n = len(d); last_year = d.ts >= d.ts.max() - pd.Timedelta(days=365)
        cand = np.flatnonzero(last_year.to_numpy() & valid); cand = cand[(cand > 20) & (cand < n - 2)]
        q_ends = np.sort(rng.choice(cand, size=min(nq(150), len(cand)), replace=False))
        price = c[-1]
        base = dict(sym=sym, tf=tf, n=n, start=str(d.ts.min().date()), end=str(d.ts.max().date()),
                    price=round(price, 2), med_range_pct=round(float(np.median(Fp[:, 0] - Fp[:, 1])), 4),
                    med_body_pct=round(float(np.median(np.abs(Fp[:, 2]))), 4),
                    med_range_pips=round(float(np.median(h - l)) / PIP[sym], 1))
        for rep, F, tols in (("pct", Fp, TOL_PCT), ("atr", Fa, TOL_ATR)):
            for tol in tols:
                r, rn = count_matches(F, XS, tol, q_ends, excl=1)
                for X in XS:
                    rows.append({**base, "rep": rep, "tol": tol,
                                 "tol_pips": round(price * tol / 100 / PIP[sym], 2) if rep == "pct" else None, "X": X,
                                 "med_raw": float(np.median(r[X])), "med_nonovl": float(np.median(rn[X])),
                                 "p_ge30": float(np.mean(np.array(rn[X]) >= MIN_N))})
        print(sym, tf, base, flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)


if __name__ == "__main__":
    main(*sys.argv[1:2])
