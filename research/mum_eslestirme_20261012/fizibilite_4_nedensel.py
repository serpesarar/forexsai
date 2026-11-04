"""Fizibilite-4 (v0.2 düzeltmesi): tarihsel karar anında ERİŞİLEBİLİR eşleşme sayısı — SONUÇLARA BAKMAZ.

Codex incelemesindeki (docs/MUM_ESLESTIRME_TASARIM_INCELEMESI_CODEX.md §2.1–2.2) iki kusuru düzeltir:
  1. Nedensellik: aday pencere sonu e yalnız e + H_ref ≤ q (sonucu karar anında kapanmış) ise sayılır;
     karşılaştırma için eski "arşiv" sayımı (her iki taraf) da verilir.
  2. Ortak ölçek: penceredeki her mum PENCERE SONU ATR'sine bölünür (tasarım §6.1):
     G_k[e] = (H−O, L−O, C−O)[e−k] / A[e],  A[e] = mean(TR[e−14 … e−1])  (basit 14-bar TR ortalaması).
     Kullanıcı % tanımı (mumun kendi açılışına göre %) zaten ölçeksizdir; yalnız nedensel maske eklenir.
Bağımsız olay: seçilen pencere sonları arası ≥ max(X, H_ref) bar (açgözlü, kronolojik).
Uygunluk (PM): τ ≤ sorgu mumlarının medyan aralığı / 3 — sorguların ne kadarının uygun olduğu ayrıca raporlanır.
4h/1d: 1h'ten broker-saati hizasıyla (NY 17:00 gün sınırı) türetilir; 5 ve 10 yıllık kütüphane ayrı.
Çalıştır: python3 research/mum_eslestirme_20261012/fizibilite_4_nedensel.py   (~3–5 dk)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _common import HERE, load, nq, sources

H_REF = {"5m": 12, "15m": 16, "30m": 8, "1h": 8, "4h": 6, "1d": 5}     # tasarım §8 orta ufuk
XS = [1, 2, 3, 4, 5, 6, 8]
TOL_ATR = [0.10, 0.20, 0.30]
TOL_PCT = [0.01, 0.02]
MIN_N = 30


def derive(d1h: pd.DataFrame, tf: str) -> pd.DataFrame:
    """1h → 4h / 1d, broker gün sınırı NY 17:00 (MT5 sunucu gece yarısı)."""
    ny = d1h.ts.dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)  # 17:00 NY → 00:00
    key = ny.dt.floor("1D") if tf == "1d" else ny.dt.floor("4h")
    g = d1h.groupby(key)
    out = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(),
                        "close": g.close.last(), "nbar": g.size()})
    out = out[out.nbar >= (3 if tf == "4h" else 12)]                        # eksik kova at
    out["ts"] = pd.to_datetime(out.index).tz_localize("UTC")                # yaklaşık; yalnız dönem kesimi için
    return out.reset_index(drop=True)


def dedup_count(e: np.ndarray, gap: int) -> int:
    cnt, last = 0, -10**9
    for v in e:
        if v - last >= gap:
            cnt += 1; last = v
    return cnt


def run_cell(d: pd.DataFrame, tf: str, rng: np.random.Generator) -> list:
    o, h, l, c = (d[k].to_numpy(float) for k in ["open", "high", "low", "close"]); n = len(d)
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    A = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()                  # bar e için e−14…e−1
    raw = np.stack([h - o, l - o, c - o], 1)
    pct = np.stack([100 * (h / o - 1), 100 * (l / o - 1), 100 * (c / o - 1)], 1)
    xmax, H = max(XS), H_REF[tf]
    G = np.full((xmax, n, 3), np.nan)
    for k in range(xmax):
        G[k, k:] = raw[:n - k] / A[k:, None]                                  # ortak pencere-sonu ölçeği
    P = np.full((xmax, n, 3), np.nan)
    for k in range(xmax):
        P[k, k:] = pct[:n - k]
    ok = np.isfinite(G).all((0, 2))
    ly = (d.ts >= d.ts.max() - pd.Timedelta(days=365)).to_numpy()
    cand = np.flatnonzero(ly & ok); cand = cand[cand > 40]
    q_ends = np.sort(rng.choice(cand, size=min(nq(150), len(cand)), replace=False))
    rows = []
    for rep, Z, tols in (("atr", G, TOL_ATR), ("pct", P, TOL_PCT)):
        for tol in tols:
            acc = {(m, X): [] for m in ("tarihsel", "arsiv") for X in XS}; elig = {X: [] for X in XS}
            for qe in q_ends:
                alive = ok.copy()
                rng_q = (G[:, qe, 0] - G[:, qe, 1])                            # sorgu mumlarının aralığı (ATR)
                for k in range(xmax):
                    alive &= np.all(np.abs(Z[k] - Z[k, qe]) <= tol, axis=1)
                    X = k + 1
                    if X not in elig:
                        continue
                    e = np.flatnonzero(alive)
                    e_hist = e[e + H <= qe]
                    e_arch = e[(np.abs(e - qe) >= max(X, H)) & (e + H < n)]
                    acc[("tarihsel", X)].append(dedup_count(e_hist, max(X, H)))
                    acc[("arsiv", X)].append(dedup_count(e_arch, max(X, H)))
                    if rep == "atr":
                        elig[X].append(tol <= np.median(rng_q[:X]) / 3)
                    else:
                        elig[X].append(tol <= np.median(pct[qe - np.arange(X), 0] - pct[qe - np.arange(X), 1]) / 3)
            for X in XS:
                for m in ("tarihsel", "arsiv"):
                    v = np.array(acc[(m, X)])
                    rows.append(dict(rep=rep, tol=tol, X=X, mode=m, med=float(np.median(v)),
                                     p75=float(np.percentile(v, 75)), p90=float(np.percentile(v, 90)),
                                     p_ge30=float(np.mean(v >= MIN_N)),
                                     p_ge30_uygun=float(np.mean(v[np.array(elig[X])] >= MIN_N)) if np.any(elig[X]) else np.nan,
                                     uygun_orani=float(np.mean(elig[X]))))
    return rows


def main(out=HERE / "results/fizibilite_4_nedensel.csv") -> None:
    rng = np.random.default_rng(23); src = sources(); allrows = []
    cells = [(k, v, None) for k, v in src.items()]
    for sym in ("NDX", "DAX", "XAU", "OIL"):
        if (sym, "1h") in src:
            for tf in ("4h", "1d"):
                cells.append(((sym, tf), src[(sym, "1h")], tf))
    for (sym, tf), path, derive_tf in cells:
        if derive_tf is None:
            libs = {"5y": load(path)}
        else:
            full = pd.read_parquet(path)
            if "src" in full.columns:
                full = full[full.src == "broker"]
            full = full.sort_values("ts").reset_index(drop=True)
            if sym == "DAX":
                full = full[full.ts >= "2020-01-01"]                         # 2020 öncesi seyrek (ME-00)
            dd = derive(full, derive_tf)
            libs = {"5y": dd[dd.ts >= dd.ts.max() - pd.Timedelta(days=int(365.25 * 5))].reset_index(drop=True),
                    "10y": dd[dd.ts >= dd.ts.max() - pd.Timedelta(days=int(365.25 * 10))].reset_index(drop=True)}
        for lib_name, d in libs.items():
            rows = run_cell(d, tf, rng)
            for r in rows:
                r.update(sym=sym, tf=tf, lib=lib_name, n=len(d), start=str(d.ts.min())[:10], end=str(d.ts.max())[:10],
                         H_ref=H_REF[tf], max_bagimsiz_olay=len(d) // H_REF[tf])
            allrows += rows
            print(sym, tf, lib_name, len(d), flush=True)
    pd.DataFrame(allrows).to_csv(out, index=False)


if __name__ == "__main__":
    main(*sys.argv[1:2])
