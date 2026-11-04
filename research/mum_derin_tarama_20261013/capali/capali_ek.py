"""capali_ek.py — SONRADAN (post-hoc) TANIMSAL ekler; aday ailesine GİRMEZ (PROTOCOL.md §6).

1. MIM yayımlanmış regresyon biçimi: r13 (son yarım saat; 1h'te son saat) ~ r1 (önceki 16:00 → 10:00), getiri %,
   OLS eğim + Newey-West t (gecikme 5), R², iki kronolojik yarı.
2. (f) mekanizması tanımsal: gece getirisi (16:00 → ertesi 09:30; 1h 09:00) son yarım saat (1h son saat) aşağı vs yukarı
   kapanış sonrası — yükseliş oranı ve ortalama puan, fark için 5 günlük blok bootstrap.
3. (a) 30m rest-of-session K50: komşu oyu kovası (pu) × gerçekleşen yükseliş oranı — bilgi var mı, %50'yi geçiyor mu.
Çıktı: results/ek_tanimsal.json ; konsola tablo.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capali_test import MIN_LIB, base_of, calls_of, y_of  # noqa: E402
from capali_veri import HERE, Grid, load_daily, utc_ns  # noqa: E402

RES = HERE / "results"
rng = np.random.default_rng(7)


def nw_t(x: np.ndarray, y: np.ndarray, lag: int = 5) -> tuple[float, float, float]:
    X = np.c_[np.ones(len(x)), x]
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    XtXi = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for L in range(1, lag + 1):
        w = 1 - L / (lag + 1)
        G = (X[L:] * e[L:, None]).T @ (X[:-L] * e[:-L, None])
        S += w * (G + G.T)
    V = XtXi @ S @ XtXi
    r2 = 1 - e.var() / y.var()
    return float(b[1]), float(b[1] / np.sqrt(V[1, 1])), float(r2)


def block_diff(a_mask: np.ndarray, v: np.ndarray, day: np.ndarray, B: int = 2000) -> tuple[float, float]:
    blk = day // 5
    u, inv = np.unique(blk, return_inverse=True)
    sa = np.bincount(inv, weights=np.where(a_mask, v, 0), minlength=len(u)); na = np.bincount(inv, weights=a_mask.astype(float), minlength=len(u))
    sb = np.bincount(inv, weights=np.where(~a_mask, v, 0), minlength=len(u)); nb = np.bincount(inv, weights=(~a_mask).astype(float), minlength=len(u))
    pick = rng.integers(0, len(u), (B, len(u)))
    d = sa[pick].sum(1) / na[pick].sum(1) - sb[pick].sum(1) / nb[pick].sum(1)
    return float(np.mean(d > 0)), float(np.std(d))


def main() -> None:
    daily = load_daily()
    out = {}
    for tf in ("5m", "15m", "30m", "1h"):
        G = Grid(tf, daily)
        ok = ~G.early & ~G.prev_early & (G.prev_dn > 0)
        dd = np.flatnonzero(ok); dn = G.days[dd]
        CP = G.px(utc_ns(G.prev_dn[dd], 960))
        r1 = 100 * (G.px(utc_ns(dn, 600)) / CP - 1)
        a = 930 if tf != "1h" else 900
        pA = G.px(utc_ns(dn, a)); p16 = G.px(utc_ns(dn, 960))
        rl = 100 * (p16 / pA - 1)
        m = np.isfinite(r1) & np.isfinite(rl)
        b, t, r2 = nw_t(r1[m], rl[m])
        h = m.sum() // 2; ix = np.flatnonzero(m)
        b1, t1, _ = nw_t(r1[ix[:h]], rl[ix[:h]]); b2, t2, _ = nw_t(r1[ix[h:]], rl[ix[h:]])
        out[f"MIM_{tf}"] = dict(n=int(m.sum()), beta=b, t_nw=t, R2_pct=100 * r2, half1_beta=b1, half1_t=t1, half2_beta=b2, half2_t=t2,
                                hedef="son yarım saat" if tf != "1h" else "son saat")
        # (f) tanımsal
        nxt = np.minimum(dd + 1, len(G.days) - 1)
        on_end = utc_ns(G.days[nxt], 570 if tf != "1h" else 540)
        on = G.px(on_end) - p16
        on = np.where((dd + 1 < len(G.days)) & np.isfinite(rl) & (rl != 0), on, np.nan)
        mm = np.isfinite(on) & (on != 0)
        dn_close = rl[mm] < 0
        v = on[mm]
        P, sd = block_diff(dn_close, v, dd[mm])
        Pu, _ = block_diff(dn_close, (v > 0).astype(float), dd[mm])
        out[f"F_{tf}"] = dict(n=int(mm.sum()), up_after_down_close=100 * float(np.mean(v[dn_close] > 0)),
                              up_after_up_close=100 * float(np.mean(v[~dn_close] > 0)),
                              mean_pts_after_down=float(v[dn_close].mean()), mean_pts_after_up=float(v[~dn_close].mean()),
                              P_mean_diff_pos=P, P_uprate_diff_pos=Pu, n_down=int(dn_close.sum()))
    # (a) 30m hROS K50: oy kovası
    fam = pickle.load(open(RES / "aile_kur.pkl", "rb"))
    GR = {tf: Grid(tf, daily) for tf in ("5m", "15m", "30m", "1h")}
    for c in fam:
        if c["idea"] == "a" and c["tf"] == "30m" and c["hzlab"] == "hROS" and c["K"] == 50:
            y = y_of(c, 0, GR)
            NB = c["NB"]; yy = np.where(NB >= 0, y[np.maximum(NB, 0)], np.nan)
            up = (yy > 0).sum(1); tot = (yy > 0).sum(1) + (yy < 0).sum(1)
            pu = up / np.maximum(tot, 1)
            m = (c["L"] >= MIN_LIB) & np.isfinite(y) & (y != 0)
            bins = [0, 0.4, 0.5, 0.6, 0.7, 1.01]
            k = np.digitize(pu[m], bins) - 1
            tab = {f"{bins[i]:.1f}-{bins[i + 1]:.1f}": dict(n=int((k == i).sum()), up=100 * float(np.mean(y[m][k == i] > 0)) if (k == i).any() else None,
                                                             mean_pts=float(np.mean(y[m][k == i])) if (k == i).any() else None)
                   for i in range(len(bins) - 1)}
            out[f"A30_ROS_{c['name']}"] = tab
    json.dump(out, open(RES / "ek_tanimsal.json", "w"), indent=1, default=float)
    for k, v in out.items():
        print(k, json.dumps(v, default=float))


if __name__ == "__main__":
    main()
