"""knn.py — PROTOCOL §3: her giriş için YALNIZ GEÇMİŞTEKİ en benzer K oluşum; S1 (benzerler aynı TP'ye mi gitti) + S2 (işlem kuralı) + plasebo.
Çıktı results/knn.json, results/knn_scores.parquet"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
PER = {"BAGIMSIZ": (2018, 2021), "KESIF": (2022, 2023), "TEST": (2024, 2026)}
TH = 0.30
GAP = 86400


def per(y):
    return next(k for k, (a, b) in PER.items() if a <= y <= b)


def neighbors(df, X, K):
    """Ay ay genişleyen geçmiş: sorgu ayından önceki (ve ≥ 1 gün önce) girişler üzerinde K-NN. Döner: komşu indeks matrisi (−1 = yok)."""
    nb = np.full((len(df), K), -1, dtype=np.int64)
    months = pd.to_datetime(df.d).dt.to_period("M")
    for mth in months.unique():
        q = np.where(months == mth)[0]
        t0 = df.t.values[q].min() - GAP
        past = np.where(df.t.values < t0)[0]
        if len(past) < 500:
            continue
        nn = NearestNeighbors(n_neighbors=K, algorithm="brute").fit(X[past])
        _, ix = nn.kneighbors(X[q])
        nb[q] = past[ix]
    return nb


def evaluate(df, nb, label=""):
    ok = nb[:, 0] >= 0
    isb = (df.W.values == "BUY_TP").astype(float)
    iss = (df.W.values == "SELL_TP").astype(float)
    buy_rate = np.where(ok, isb[np.maximum(nb, 0)].mean(1), np.nan)
    sell_rate = np.where(ok, iss[np.maximum(nb, 0)].mean(1), np.nan)
    score = buy_rate - sell_rate
    side = np.where(score >= TH, 1, np.where(score <= -TH, -1, 0))
    pts = np.where(side > 0, df.buy_pts.values, np.where(side < 0, df.sell_pts.values, np.nan))
    return buy_rate, sell_rate, score, side, pts


def main() -> None:
    df = pd.read_parquet(OUT / "entries.parquet")
    X = np.load(OUT / "forms.npy")
    df["per"] = df.year.map(per)
    res = {}
    rng = np.random.default_rng(3)
    for K in (20, 50):
        nb = neighbors(df, X, K)
        br, sr, sc, side, pts = evaluate(df, nb)
        # geçmiş taban oranı (aynı sorgu için, rastgele K'nın beklenen değeri)
        isb = (df.W == "BUY_TP").astype(float).values
        iss = (df.W == "SELL_TP").astype(float).values
        cb, cs_ = np.cumsum(isb), np.cumsum(iss)
        past_n = np.searchsorted(df.t.values, df.t.values - GAP)          # df t'ye göre sıralı
        base_b = np.where(past_n > 0, cb[np.maximum(past_n - 1, 0)] / np.maximum(past_n, 1), np.nan)
        base_s = np.where(past_n > 0, cs_[np.maximum(past_n - 1, 0)] / np.maximum(past_n, 1), np.nan)
        d = df.assign(br=br, sr=sr, score=sc, side=side, pts=pts, base_b=base_b, base_s=base_s)
        s1 = {}
        for p in PER:
            g = d[(d.per == p) & d.br.notna()]
            exb = g[g.W == "BUY_TP"].br - g[g.W == "BUY_TP"].base_b
            exs = g[g.W == "SELL_TP"].sr - g[g.W == "SELL_TP"].base_s
            ctrl_b = g[g.W != "BUY_TP"].br - g[g.W != "BUY_TP"].base_b
            ctrl_s = g[g.W != "SELL_TP"].sr - g[g.W != "SELL_TP"].base_s
            s1[p] = {"BUY_TP_benzerlerin_BUY_TP_farki": float(exb.mean()), "diger_girislerde": float(ctrl_b.mean()),
                     "SELL_TP_benzerlerin_SELL_TP_farki": float(exs.mean()), "diger_girislerde_s": float(ctrl_s.mean()),
                     "n_BUY_TP": int(len(exb)), "n_SELL_TP": int(len(exs))}
        s2 = {}
        tr = d[d.side != 0]
        for p in PER:
            g = tr[tr.per == p]
            mo = pd.to_datetime(g.d).dt.to_period("M").astype(str).values
            s2[p] = {"n": int(len(g)), "net_puan": float(g.pts.mean()), "isabet": float((g.pts > 0).mean()),
                     "P": lib.block_boot_p(g.pts.values, mo), "spr_ort": float(g.spr.mean()),
                     "net_puan_s15": float((g.pts - 0.5 * g.spr).mean()), "buy_payi": float((g.side > 0).mean())}
        # plasebo: rastgele K geçmiş komşu
        pl = {p: [] for p in PER}
        for _ in range(100):
            nbr = np.full_like(nb, -1)
            for i in range(len(df)):
                if past_n[i] >= 500:
                    nbr[i] = rng.integers(0, past_n[i], size=K)
            *_, side_r, pts_r = evaluate(df, nbr)
            for p in PER:
                sel = (df.per.values == p) & (side_r != 0)
                pl[p].append(np.nanmean(pts_r[sel]) if sel.any() else np.nan)
        for p in PER:
            s2[p]["plasebo_ort"] = float(np.nanmean(pl[p]))
            s2[p]["plasebo_p95"] = float(np.nanpercentile(pl[p], 95))
            s2[p]["plasebo_yuzdelik"] = float(np.nanmean(np.array(pl[p]) < s2[p]["net_puan"]))
        s2["gecti"] = bool(all(s2[p]["net_puan"] > 0 for p in PER) and all(s2[p]["P"] >= 0.9 for p in ("TEST", "BAGIMSIZ"))
                           and all(s2[p]["net_puan"] > s2[p]["plasebo_p95"] for p in PER) and all(s2[p]["net_puan_s15"] > 0 for p in PER))
        s2["yil"] = {int(y): (int(len(g)), round(float(g.pts.mean()), 2), round(float((g.pts > 0).mean()), 3)) for y, g in tr.groupby("year")}
        res[f"K{K}"] = {"S1": s1, "S2": s2}
        if K == 20:
            d.to_parquet(OUT / "knn_scores.parquet")
    (OUT / "knn.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
