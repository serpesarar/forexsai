"""build.py — PROTOCOL §1–3: seans dengeli rastgele girişler, sonuç etiketleri, giriş öncesi 26 özellik. Çıktı results/entries.parquet"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
SEED = 20261117
N_PER = 10
SESS = {"ASYA": (-360, 180), "AVRUPA": (180, 570), "NY": (570, 960)}     # NY gün dakikası; −360 = önceki gün 18:00
H = 60
PER = {"KESIF": (date(2022, 1, 1), date(2023, 12, 31)), "TEST": (date(2024, 1, 1), date(2026, 12, 31)),
       "BAGIMSIZ": (date(2018, 1, 1), date(2021, 12, 31))}


def per(d):
    return next((k for k, (a, b) in PER.items() if a <= d <= b), "?")


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1)
    vixp = lib.vix_prev_map(D.d.tolist())
    o, h, l, c, t, spr = m1.o, m1.h, m1.l, m1.c, m1.t, m1.spr
    rng_ = h - l
    a60 = pd.Series(rng_).rolling(60).mean().shift(1).values
    a1440 = pd.Series(rng_).rolling(1440, min_periods=600).mean().shift(1).values
    clv = np.where(rng_ > 0, (c - l) / np.where(rng_ > 0, rng_, 1), 0.5)
    uw, lw = h - np.maximum(o, c), np.minimum(o, c) - l
    body = np.abs(c - o)
    up = (c > o).astype(float)
    cs = lambda x: np.r_[0.0, np.cumsum(x)]
    C_clv, C_uw, C_lw, C_rng, C_body, C_up = map(cs, (clv, uw, lw, rng_, body, up))
    flip = np.r_[0.0, (up[1:] != up[:-1]).astype(float)]
    C_flip = cs(flip)
    prev_close = dict(zip(D.d, D.close.shift(1)))
    rs = np.random.default_rng(SEED)
    rows = []
    for d in D.d:
        for s, (m0, m1_) in SESS.items():
            a, b = int(np.searchsorted(t, lib.utc(d, m0))), int(np.searchsorted(t, lib.utc(d, m1_)))
            if b - a < 100:
                continue
            for j in np.sort(rs.choice(np.arange(a, b), size=N_PER, replace=False)):
                if j < 1500 or not np.isfinite(a60[j]) or a60[j] <= 0 or not np.isfinite(a1440[j]):
                    continue
                U = 4 * a60[j]
                k = int(np.searchsorted(t, t[j] + H * 60))
                if k >= len(t) or k - j < 50 or t[k] - t[j] > H * 60 + 300:
                    continue
                base = o[j]
                hi_hit = np.where(h[j:k] >= base + U)[0]
                lo_hit = np.where(l[j:k] <= base - U)[0]
                fu = hi_hit[0] if len(hi_hit) else 10 ** 9
                fd = lo_hit[0] if len(lo_hit) else 10 ** 9
                yon = 1 if fu < fd else (-1 if fd < fu else 0)
                r60 = (o[k] - base) / U
                mx, mn = (h[j:k].max() - base) / U, (l[j:k].min() - base) / U
                yapi = ("TREND" if abs(r60) >= 2 else "KARARSIZ" if (mx >= 1 and mn <= -1 and abs(r60) < 1)
                        else "SAKIN" if (mx - mn) < 1.5 else "ARA")
                w = lambda C_, n: (C_[j] - C_[j - n]) / n
                ss = int(np.searchsorted(t, lib.utc(d, m0)))
                s_hi, s_lo = (h[ss:j].max(), l[ss:j].min()) if j > ss else (np.nan, np.nan)
                run = 0
                col = up[j - 1]
                while run < 30 and up[j - 1 - run] == col:
                    run += 1
                pc = prev_close.get(d)
                rows.append({
                    "d": d, "per": per(d), "seans": s, "t": int(t[j]), "j": int(j), "U": U, "yon": yon, "yapi": yapi, "r60": r60,
                    "spr_U": spr[j] / U, "spr_k_U": spr[k] / U,
                    "clv1": clv[j - 1], "clv5": w(C_clv, 5), "clv15": w(C_clv, 15), "clv60": w(C_clv, 60),
                    "uw5": (C_uw[j] - C_uw[j - 5]) / max(1e-9, C_rng[j] - C_rng[j - 5]),
                    "lw5": (C_lw[j] - C_lw[j - 5]) / max(1e-9, C_rng[j] - C_rng[j - 5]),
                    "uw15": (C_uw[j] - C_uw[j - 15]) / max(1e-9, C_rng[j] - C_rng[j - 15]),
                    "lw15": (C_lw[j] - C_lw[j - 15]) / max(1e-9, C_rng[j] - C_rng[j - 15]),
                    "run_signed": run * (1 if col else -1),
                    "body5": (C_body[j] - C_body[j - 5]) / max(1e-9, C_rng[j] - C_rng[j - 5]),
                    "flip15": w(C_flip, 15),
                    "r5": (c[j - 1] - c[j - 6]) / U, "r15": (c[j - 1] - c[j - 16]) / U, "r60b": (c[j - 1] - c[j - 61]) / U,
                    "r240": (c[j - 1] - c[j - 241]) / U,
                    "rng60": (h[j - 60:j].max() - l[j - 60:j].min()) / U, "volreg": a60[j] / a1440[j],
                    "sess_pos": (c[j - 1] - s_lo) / (s_hi - s_lo) if j > ss and s_hi > s_lo else 0.5,
                    "dist_pc": (c[j - 1] - pc) / U if pc and np.isfinite(pc) else 0.0,
                    "min_sess": int((t[j] - t[ss]) // 60), "seans_kod": list(SESS).index(s), "dow": d.weekday(),
                    "vix": vixp.get(d, np.nan),
                })
    df = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    df.to_parquet(OUT / "entries.parquet")
    print(len(df), df.groupby(["per", "seans"]).size().unstack())
    print(df.groupby("seans").yapi.value_counts(normalize=True).unstack().round(3))
    print(df.groupby("seans").yon.value_counts(normalize=True).unstack().round(3))


if __name__ == "__main__":
    main()
