"""Fizibilite-3: logaritmik zaman piramidi vs ham pencere — kNN göreli kontrast + gevşek L∞ sayımı.

Piramit seviyeleri [1,1,1,2,4,8,16] → 33 mum, 7 'süper mum' × (tepe, dip, kapanış)−açılış, ATR14 ve √boyut ile ölçekli.
Kıyas: aynı normalizasyonla ham 33 mum ve ham 7 mum. SONUÇLARA BAKMAZ.
Çalıştır: python3 research/mum_eslestirme_20261012/fizibilite_3_piramit.py  (~1 dk)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import load, sources

LEVELS = [1, 1, 1, 2, 4, 8, 16]
SUBSET = [("NDX", "15m"), ("NDX", "1h"), ("DAX", "30m"), ("XAU", "30m"), ("OIL", "15m")]


def rc_of(W: np.ndarray, q_idx: np.ndarray, excl: int) -> float:
    good = np.isfinite(W).all(1); out = []
    for qj in q_idx:
        dd = np.sqrt(((W - W[qj]) ** 2).sum(1)); dd[~good] = np.inf
        dd[max(0, qj - excl):qj + excl + 1] = np.inf
        fin = dd[np.isfinite(dd)]
        out.append(np.median(fin) / np.partition(fin, 30)[30])
    return float(np.median(out))


def pyramid(o, h, l, c, atr, levels=LEVELS) -> np.ndarray:
    """P[e] = e'de biten piramidin özellikleri (yalnız e ve öncesi → nedensel)."""
    H, L, O, C = map(pd.Series, (h, l, o, c)); feats = []; a = 0
    for s in levels:
        Hs = H.rolling(s).max().shift(a); Ls = L.rolling(s).min().shift(a)
        Os = O.shift(a + s - 1); Cs = C.shift(a)
        for v in (Hs - Os, Ls - Os, Cs - Os):
            feats.append((v.to_numpy() / atr) / np.sqrt(s))
        a += s
    return np.stack(feats, 1).astype(np.float32)


def main() -> None:
    rng = np.random.default_rng(5); src = sources()
    for key in SUBSET:
        if key not in src:
            continue
        d = load(src[key]); o, h, l, c = (d[k].to_numpy(float) for k in ["open", "high", "low", "close"]); n = len(d)
        pc = np.r_[c[0], c[:-1]]; tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
        atr = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()
        P = pyramid(o, h, l, c, atr); cov = sum(LEVELS)

        def raw(X):
            Fh, Fl, Fc = [np.stack([np.r_[np.full(k, np.nan), v[:n - k]] for k in range(X)], 1) for v in (h - o, l - o, c - o)]
            return (np.concatenate([Fh, Fl, Fc], 1) / atr[:, None]).astype(np.float32)

        ly = np.flatnonzero((d.ts >= d.ts.max() - pd.Timedelta(days=365)).to_numpy() & np.isfinite(P).all(1))
        q = np.sort(rng.choice(ly[ly < n - 2], 60, replace=False))
        out = {"pyr7(33)": rc_of(P, q, cov), "raw33": rc_of(raw(cov), q, cov), "raw7": rc_of(raw(7), q, 7)}
        cnts = {}
        for tol in (0.3, 0.4, 0.5):
            v = []
            for qe in q:
                e = np.flatnonzero(np.all(np.abs(P - P[qe]) <= tol, axis=1))
                e = e[(np.abs(e - qe) > cov) & (e < n - 1)]
                cnt, last = 0, -10**9
                for x in e:
                    if x - last >= cov:
                        cnt += 1; last = x
                v.append(cnt)
            cnts[tol] = (float(np.median(v)), float(np.mean(np.array(v) >= 30)))
        print(key, {k: round(x, 2) for k, x in out.items()}, "pyr L∞ (medyan, %n≥30):", cnts, flush=True)


if __name__ == "__main__":
    main()
