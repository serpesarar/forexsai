"""b_extend.py — PROTOCOL §3: komşuluk haritası (plato mu tepe mi?) + "iki dönemde de daha iyi" geliştirme adayı taraması.
Ölçü: ay başına toplam (R veya bp) — işlem sayısı değişen türevlerde doğru kıyas (E110). Fark P = ay-blok bootstrap."""
from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd

import lib
import rules


def monthly(df: pd.DataFrame, col: str, months: pd.Index) -> pd.Series:
    if df.empty:
        return pd.Series(0.0, index=months)
    m = pd.to_datetime(df.d).dt.to_period("M")
    return df.groupby(m)[col].sum().reindex(months, fill_value=0.0)


def diff_p(a: pd.Series, b: pd.Series, n_boot: int = 4000, seed: int = 11) -> float:
    x = (a - b).values
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    return float((x[idx].mean(1) > 0).mean())


def grid(name: str, f, combos: list[dict], live: dict, col: str, months: pd.Index) -> list[dict]:
    base = lib.to_frame(f(**live))
    out = []
    bm = {e: monthly(base[base.era == e], col, months[months_era(months) == e]) for e in ("ESKI", "YENI")}
    for p in combos:
        df = lib.to_frame(f(**p))
        row = {"rule": name, **p, "is_live": p == live}
        for e in ("ESKI", "YENI"):
            g = df[df.era == e] if not df.empty else df
            mm = monthly(g, col, months[months_era(months) == e])
            row[f"n_{e}"] = int(len(g))
            row[f"mean_{e}"] = float(g[col].mean()) if len(g) else np.nan
            row[f"mo_{e}"] = float(mm.mean())
            row[f"dP_{e}"] = diff_p(mm, bm[e])
        out.append(row)
    return out


def months_era(months: pd.Index) -> np.ndarray:
    return np.where(months.to_timestamp().date <= lib.ESKI_END, "ESKI", "YENI")


def main() -> None:
    m1 = lib.load_m1()
    D = lib.daily_table(m1)
    vixp = lib.vix_prev_map(D.d.tolist())
    H = rules.h1_utc(m1)
    months = pd.period_range("2018-01", "2026-11", freq="M")
    rows: list[dict] = []

    orb = lambda **p: rules.orb(m1, D, vixp, **p)
    rows += grid("ORBVIX", orb, [dict(or_min=a, tp_r=b, vix_min=c, tf=t) for a, b, c, t in
                                 itertools.product((5, 15, 30), (1.5, 2.0, 3.0), (16.0, 18.4, 22.0, 25.0), (1, 5))],
                 dict(or_min=15, tp_r=2.0, vix_min=18.4, tf=5), "R", months)
    cap = lambda **p: rules.caprev(m1, D, vixp, **p)
    rows += grid("CAPREV", cap, [dict(tf=a, exit_next_day=b, vix_min=c) for a, b, c in
                                 itertools.product((60, 30, 15, 5), (False, True), (18.4, 22.0, 25.0))],
                 dict(tf=60, exit_next_day=False, vix_min=18.4), "R", months)
    c3 = lambda **p: rules.c3b(m1, D, **p)
    rows += grid("C3B", c3, [dict(rsi_th=a, max_hold=b, entry_min=c) for a, b, c in
                             itertools.product((5.0, 10.0, 15.0), (3, 5, 8), (930, 960))],
                 dict(rsi_th=10.0, max_hold=5, entry_min=930), "net_bp", months)
    ks = lambda **p: rules.ksg(m1, D, **p)
    rows += grid("KSG", ks, [dict(sig_from=a, exit_min=b) for a, b in itertools.product(("O1430", "O15", "O1530"), (570, 600))],
                 dict(sig_from="O15", exit_min=570), "net_bp", months)
    ck = lambda **p: rules.cekic(m1, H, **p)
    rows += grid("CEKIC", ck, [dict(lw_min=a, tp_r=b, hold_h=c) for a, b, c in itertools.product((0.6, 0.7, 0.8), (3.0, 5.0), (16, 24))],
                 dict(lw_min=0.7, tp_r=5.0, hold_h=24), "R", months)

    df = pd.DataFrame(rows)
    df.to_csv(lib.RESULTS / "b_grid.csv", index=False)
    summ = {}
    for r, g in df.groupby("rule"):
        both_pos = ((g.mean_ESKI > 0) & (g.mean_YENI > 0)).mean()
        cand = g[(~g.is_live) & (g.dP_ESKI >= 0.90) & (g.dP_YENI >= 0.90)]
        live = g[g.is_live].iloc[0].to_dict()
        summ[r] = {"n_combos": int(len(g)), "plato_iki_donem_arti": float(both_pos),
                   "live": {k: live[k] for k in ("mean_ESKI", "mean_YENI", "mo_ESKI", "mo_YENI")},
                   "adaylar": cand.drop(columns=["rule"]).to_dict("records")}
    (lib.RESULTS / "b_extend.json").write_text(json.dumps(summ, indent=1, default=str), encoding="utf-8")
    for r, s in summ.items():
        print(r, "kombinasyon", s["n_combos"], "iki dönemde artı oranı", round(s["plato_iki_donem_arti"], 2),
              "canlı", {k: round(v, 3) for k, v in s["live"].items()})
        for c in s["adaylar"]:
            print("   ADAY", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in c.items()})


if __name__ == "__main__":
    main()
