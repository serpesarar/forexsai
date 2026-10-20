"""PROTOCOL_ILERI.md §A — DX-02 kurallarının İLERİ (ts ≥ 2026-10-15) sınaması. python3 research/decider_xau_ileri_20261021/ileri.py"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CUT = pd.Timestamp("2026-10-15", tz="UTC")
GEOMS = ("G1_tp1.0_sl1.5", "G2_tp1.25_sl0.75", "G3_tp3.0_sl1.5_t120")
N_BOOT = 4000
RNG = np.random.default_rng(1015)
RULES = {  # DX-02 PROTOCOL (2026-10-15 04:41 UTC) birebir
    "R1_guc_tetik": lambda d: d.trig_sign > 0,
    "R2_D2_temiz": lambda d: d.eq_block_buy == False,  # noqa: E712
    "R3_h1_ema50_ustu": lambda d: d.h1_above_ema50 == True,  # noqa: E712
    "R4_d1_yukari": lambda d: d.d1_up == True,  # noqa: E712
    "R5_ldn_ny": lambda d: d.sess_ldn_ny == True,  # noqa: E712
    "R6_vol_patlama_yok": lambda d: d.atr5_ratio < 1.5,
    "R7_20s_tepeye_yakin": lambda d: d.dist_hi20_h1_atr <= 1.0,
    "R8_boyut_ge_0.2": lambda d: d.size_factor >= 0.2,
}


def boot(d: pd.DataFrame, m: np.ndarray, col: str) -> tuple[float, float]:
    days = d.day.astype(str).to_numpy()
    ud = np.unique(days)
    idx = {u: np.flatnonzero(days == u) for u in ud}
    R = d[col].to_numpy(float)
    ev, df = [], []
    for _ in range(N_BOOT):
        pick = np.concatenate([idx[u] for u in RNG.choice(ud, ud.size)])
        r, mm = R[pick], m[pick]
        if mm.sum() >= 2 and (~mm).sum() >= 2:
            ev.append(r[mm].mean())
            df.append(r[mm].mean() - r[~mm].mean())
    return float(np.mean(np.array(ev) > 0)), float(np.mean(np.array(df) > 0))


def main() -> None:
    S = pd.read_pickle(HERE / "kurallar" / "sim_decider.pkl")
    S = S[(S.direction == "BUY") & S.in_analysis_set.astype(bool)].copy()
    S["ts"] = pd.to_datetime(S.ts, utc=True)
    rows = []
    for part, d in (("ESKİ (<10-15)", S[S.ts < CUT]), ("İLERİ (≥10-15)", S[S.ts >= CUT])):
        d = d.reset_index(drop=True)
        for rn, f in RULES.items():
            m = f(d).fillna(False).to_numpy(bool)
            for g in GEOMS:
                ok = np.isfinite(d[g].to_numpy(float))
                dd, mm = d[ok].reset_index(drop=True), m[ok]
                if mm.sum() < 3 or (~mm).sum() < 3:
                    rows.append({"dönem": part, "kural": rn, "geo": g[:2], "n kural": int(mm.sum())})
                    continue
                pe, pdf = boot(dd, mm, g)
                rows.append({"dönem": part, "kural": rn, "geo": g[:2], "n kural": int(mm.sum()), "n dışı": int((~mm).sum()),
                             "gün": int(dd.day[mm].nunique()), "ortR kural": dd[g][mm].mean(), "ortR dışı": dd[g][~mm].mean(),
                             "ortR tümü": dd[g].mean(), "P(kural>0)": pe, "P(fark>0)": pdf})
    t = pd.DataFrame(rows)
    t.to_csv(HERE / "results" / "ileri.csv", index=False)
    pr = t[(t.kural == "R1_guc_tetik") & (t["dönem"].str.startswith("İLERİ"))]
    L = ["# DX-02 kuralları İLERİ sınama (ön-kayıt PROTOCOL_ILERI.md §A)",
         f"\nİleri küme: karar ≥ 2026-10-15 · BUY n={int((S.ts >= CUT).sum())}, gün {S[S.ts >= CUT].day.nunique()} · "
         f"eski n={int((S.ts < CUT).sum())}", "\n## Birincil: R1 (güç tetiği) — ileri", pr.to_string(index=False),
         "\n## Tüm kurallar × geometriler", t.to_string(index=False, float_format=lambda x: f"{x:+.3f}")]
    txt = "\n".join(L)
    (HERE / "results" / "ileri.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
