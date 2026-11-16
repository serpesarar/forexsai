"""build.py — PROTOCOL §1–2: günde 10 rastgele giriş, BUY/SELL 20 puan braket sonuçları, 30×1m oluşum vektörü. Çıktı results/entries.parquet + forms.npy"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
SEED, N_DAY, TP, W, HOLD = 20261118, 10, 20.0, 30, 240


def side_result(m1, j, side, k_end):
    """j açılışında gir; 20 puan TP/SL; aynı bar → SL. (sonuç, net puan, çıkış dakikası)."""
    o, h, l, s = m1.o, m1.h, m1.l, m1.spr
    if side > 0:
        e = o[j] + s[j]
        tp, sl = e + TP, e - TP
        for k in range(j, k_end):
            if l[k] <= sl:
                return "SL", -TP, k - j
            if h[k] >= tp:
                return "TP", TP, k - j
        return "YOK", o[k_end] - e, k_end - j
    e = o[j]
    tp, sl = e - TP, e + TP
    for k in range(j, k_end):
        if h[k] + s[k] >= sl:
            return "SL", -TP, k - j
        if l[k] + s[k] <= tp:
            return "TP", TP, k - j
    return "YOK", e - (o[k_end] + s[k_end]), k_end - j


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1)
    rs = np.random.default_rng(SEED)
    t, m = m1.t, m1.m
    rows, forms = [], []
    for d in D.d:
        a, b = int(np.searchsorted(t, lib.utc(d, -360))), int(np.searchsorted(t, lib.utc(d, 975)))
        cand = np.arange(a, b)
        cand = cand[(cand > W + 5)]
        if len(cand) < 200:
            continue
        for j in np.sort(rs.choice(cand, size=N_DAY, replace=False)):
            if t[j] - t[j - W] > (W + 5) * 60:            # oluşum penceresi kesintisiz olmalı
                continue
            k_end = int(np.searchsorted(t, t[j] + HOLD * 60))
            if k_end >= len(t) or k_end - j < HOLD * 0.6:
                continue
            bres, bpts, bmin = side_result(m1, j, 1, k_end)
            sres, spts, smin = side_result(m1, j, -1, k_end)
            W_ = "BUY_TP" if bres == "TP" else ("SELL_TP" if sres == "TP" else "YOK")
            if bres == "TP" and sres == "TP":                  # iki yön de TP (önce biri SL'siz değilse) → daha erken olan
                W_ = "BUY_TP" if bmin <= smin else "SELL_TP"
            ref = m1.c[j - 1]
            f = np.c_[m1.o[j - W:j] - ref, m1.h[j - W:j] - ref, m1.l[j - W:j] - ref, m1.c[j - W:j] - ref].ravel()
            rows.append({"d": d, "t": int(t[j]), "j": int(j), "minute": int(m[j]), "px": float(m1.o[j]), "spr": float(m1.spr[j]),
                         "buy": bres, "buy_pts": bpts, "buy_min": bmin, "sell": sres, "sell_pts": spts, "sell_min": smin, "W": W_})
            forms.append(f.astype(np.float32))
    df = pd.DataFrame(rows)
    df["year"] = pd.to_datetime(df.d).dt.year
    OUT.mkdir(exist_ok=True)
    df.to_parquet(OUT / "entries.parquet")
    np.save(OUT / "forms.npy", np.array(forms))
    print(len(df))
    print(df.groupby("year").W.value_counts(normalize=True).unstack().round(3))
    print(df.groupby("year")[["buy_pts", "sell_pts", "spr", "px"]].mean().round(2))


if __name__ == "__main__":
    main()
