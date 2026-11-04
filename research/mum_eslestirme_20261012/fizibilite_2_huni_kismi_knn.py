"""Fizibilite-2: kullanıcı tanımını uzatma girişimleri — ATR birimli mum özellikleriyle.

  funnel    : huni toleransı — son mum ≤0,15 ATR, her geri adımda +0,05 ATR (L∞, üç farkın hepsi)
  partial80 : son 2 mum ≤0,20 ATR şart + penceredeki mumların ≥%80'i ≤0,20 ATR
  knn_RC    : Öklid kNN göreli kontrastı = medyan mesafe / 30. komşu mesafesi (1'e yaklaştıkça 'en yakın' = rastgele)
SONUÇLARA BAKMAZ.  Çalıştır: python3 research/mum_eslestirme_20261012/fizibilite_2_huni_kismi_knn.py  (~4 dk)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

from _common import HERE, load, nq, sources

XS = [2, 3, 4, 5, 6, 8, 10, 12, 16, 20]


def feats(d: pd.DataFrame):
    o, h, l, c = (d[k].to_numpy(float) for k in ["open", "high", "low", "close"])
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    atr = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()
    F = np.stack([(h - o) / atr, (l - o) / atr, (c - o) / atr], 1)
    ok = np.isfinite(F).all(1); F[~ok] = 1e9
    return F, ok


def main(out=HERE / "results/fizibilite_2_huni_kismi_knn.csv") -> None:
    rng = np.random.default_rng(11); rows = []
    for (sym, tf), path in sources().items():
        d = load(path); F, ok = feats(d); n = len(F)
        ly = (d.ts >= d.ts.max() - pd.Timedelta(days=365)).to_numpy()
        cand = np.flatnonzero(ly & ok); cand = cand[(cand > 40) & (cand < n - 2)]
        q_ends = np.sort(rng.choice(cand, size=min(nq(120), len(cand)), replace=False))
        xmax = max(XS)
        res = {(m, X): [] for m in ("funnel", "partial80") for X in XS}
        for qe in q_ends:
            mk = []
            for k in range(xmax):
                mm = np.abs(F - F[qe - k]).max(1)                      # L∞ mesafe (ATR)
                s = np.full(n, np.inf); s[k:] = mm[:n - k] if k else mm
                mk.append(s)                                           # s[e] → e'de biten pencerenin k. geri mumu
            mk = np.array(mk); e_all = np.arange(n)
            for X in XS:
                sub = mk[:X]
                fun = np.all(sub <= (0.15 + 0.05 * np.arange(X))[:, None], axis=0)
                hit = sub <= 0.20
                par = hit[0] & hit[1] & (hit.sum(0) >= np.ceil(0.8 * X))
                for name, msk in (("funnel", fun), ("partial80", par)):
                    e = e_all[msk]; e = e[(e >= X - 1) & (np.abs(e - qe) >= X) & (e < n - 1)]
                    cnt, last = 0, -10**9
                    for v in e:
                        if v - last >= X:
                            cnt += 1; last = v
                    res[(name, X)].append(cnt)
        for (name, X), v in res.items():
            rows.append(dict(sym=sym, tf=tf, method=name, X=X, med=float(np.median(v)),
                             p_ge30=float(np.mean(np.array(v) >= 30))))
        Fz = F.astype(np.float32).copy(); Fz[~ok] = np.nan
        for X in [3, 5, 8, 12, 20, 30]:
            W = swv(Fz, (X, 3)).reshape(-1, X * 3)                    # W[j] = j..j+X-1
            good = np.isfinite(W).all(1); rc = []
            for qe in q_ends[:60]:
                qj = qe - X + 1
                dd = np.sqrt(((W - W[qj]) ** 2).sum(1)); dd[~good] = np.inf
                dd[max(0, qj - X + 1):qj + X] = np.inf; dd[-1] = np.inf
                fin = dd[np.isfinite(dd)]
                rc.append(np.median(fin) / np.partition(fin, 30)[30])
            rows.append(dict(sym=sym, tf=tf, method="knn_RC", X=X, med=float(np.median(rc)), p_ge30=np.nan))
        print(sym, tf, "ok", flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)


if __name__ == "__main__":
    main(*sys.argv[1:2])
