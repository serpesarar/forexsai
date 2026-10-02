"""Sistematik hücre taraması + dairesel-kaydırma plasebosu (ampirik FDR).

Hücre = (özellik, keşif-quintile'ı, bloklanan yön). Başarı = bloklanan kümenin
(dönem×yön×UTC-saati) tabanına göre farkı 4 dönemin dördünde negatif ve
keşif+doğrulama havuzlarında ≤ −DELTA. Plasebo: özellik dizisi rastgele gün
sayısı kadar dairesel kaydırılır (öz-korelasyon korunur, hizalama bozulur).
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from common import DATA, OUT
from evaluate import PER

DELTA = 0.03
NQ = 5
N_SHIFT = 200


def prepare(metric: str = "G80") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    L = pd.read_parquet(DATA / "labels.parquet")
    base = pd.read_parquet(DATA / "feat_tf1.parquet", columns=["wd", "utc_h", "period", "tday"]).iloc[L.i.to_numpy()].reset_index(drop=True)
    F = pd.read_parquet(DATA / "feat2.parquet").iloc[L.i.to_numpy()].reset_index(drop=True)
    u = (base.wd <= 3) & base.utc_h.between(7, 21) & base.period.isin(PER)
    base, F, L = base[u].reset_index(drop=True), F[u].reset_index(drop=True), L[u].reset_index(drop=True)
    y = {}
    for s in "BS":
        col = f"R_{metric}_{s}" if metric in ("G80", "GS", "GR") else f"{metric}_{s}"
        v = L[col].to_numpy(float)
        if metric.startswith("f"):
            v = L[col.replace("n_", "_")].to_numpy(float) / L.D.to_numpy() if "n_" in col else v
        k = pd.Series(v).groupby([base.period, base.utc_h]).transform("mean").to_numpy()
        y[s] = v - k
    return base, F, y


def cell_stats(q: np.ndarray, per_idx: np.ndarray, ys: dict) -> np.ndarray:
    """→ [side, cell, period] ortalama fark; q=-1 geçersiz."""
    ok = q >= 0
    out = np.full((2, NQ, 4), np.nan)
    key = q[ok] * 4 + per_idx[ok]
    for si, s in enumerate("BS"):
        v = ys[s][ok]
        good = ~np.isnan(v)
        sm = np.bincount(key[good], weights=v[good], minlength=NQ * 4)
        ct = np.bincount(key[good], minlength=NQ * 4)
        out[si] = (sm / np.maximum(ct, 1)).reshape(NQ, 4)
        out[si][ct.reshape(NQ, 4) < 300] = np.nan
    return out


def passes(st: np.ndarray) -> np.ndarray:
    """[side, cell] geçer mi: 4 dönemde <0 ve D25 ort ≤−Δ ve (C26,M26) ort ≤−Δ."""
    neg4 = np.all(st < 0, axis=2)
    disc = np.nanmean(st[:, :, :2], axis=2) <= -DELTA
    val = np.nanmean(st[:, :, 2:], axis=2) <= -DELTA
    return neg4 & disc & val & ~np.isnan(st).any(axis=2)


def run(metric: str = "G80") -> dict:
    base, F, y = prepare(metric)
    per_idx = base.period.map({p: i for i, p in enumerate(PER)}).to_numpy()
    disc = per_idx < 2
    rows_per_day = int(len(base) / base.tday.nunique())
    rng = np.random.default_rng(2026)
    shifts = rng.integers(5 * rows_per_day, 60 * rows_per_day, N_SHIFT)
    res, null_counts = [], np.zeros(N_SHIFT, int)
    for col in F.columns:
        x = F[col].to_numpy(float)
        edges = np.nanquantile(x[disc], np.linspace(0, 1, NQ + 1)[1:-1])
        if len(np.unique(edges)) < NQ - 1:
            continue
        q = np.where(np.isnan(x), -1, np.searchsorted(edges, x, side="right"))
        st = cell_stats(q, per_idx, y)
        ps = passes(st)
        # plasebo
        nullpass = np.zeros((N_SHIFT, 2, NQ), bool)
        null_val = np.zeros((N_SHIFT, 2, NQ))
        for k, sh in enumerate(shifts):
            qs = np.roll(q, sh)
            s2 = cell_stats(qs, per_idx, y)
            nullpass[k] = passes(s2)
            null_val[k] = np.nanmean(s2, axis=2)
        null_counts += nullpass.sum(axis=(1, 2))
        for si, s in enumerate("BS"):
            for c in range(NQ):
                allm = np.nanmean(st[si, c])
                res.append({"feature": col, "cell": c, "block": s,
                            "lo": float(edges[c - 1]) if c > 0 else None, "hi": float(edges[c]) if c < NQ - 1 else None,
                            **{P: float(st[si, c, i]) for i, P in enumerate(PER)},
                            "pass": bool(ps[si, c]),
                            "null_pass_rate": float(nullpass[:, si, c].mean()),
                            "p_emp": float(np.mean(null_val[:, si, c] <= allm))})
        print(col, int(ps.sum()), flush=True)
    r = pd.DataFrame(res)
    out = {"metric": metric, "n_cells": len(r), "real_pass": int(r["pass"].sum()),
           "null_pass_mean": float(null_counts.mean()), "null_pass_p95": float(np.percentile(null_counts, 95)),
           "null_counts": null_counts.tolist()}
    r.to_csv(OUT / f"scan_{metric}.csv", index=False)
    (OUT / f"scan_{metric}_summary.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "G80"
    o = run(m)
    print({k: v for k, v in o.items() if k != "null_counts"})
    r = pd.read_csv(OUT / f"scan_{m}.csv")
    pd.set_option("display.width", 250)
    print(r[r["pass"]].sort_values("p_emp").round(3).to_string())
