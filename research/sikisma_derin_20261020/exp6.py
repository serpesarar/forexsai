"""Sıkışma — altıncı tur: saat-içi tabakalı Δ (sıkışma saatin vekili mi?) + saat tablosu → results/rapor6.md
Tabakalı Δ = Σ_h w_h (ortR_sıkışık,h − ortR_diğer,h), w_h = min(n_s,h, n_d,h) (her iki grup ≥2 olan saatler).
Gün-blok bootstrap P(Δ_tab<0)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import core as C
import exp4 as X4

OUT = C.HERE / "results"
HB = {"00-07": range(0, 7), "07-13": range(7, 13), "13-15": range(13, 15), "15-17": range(15, 17), "17-20": range(17, 20),
      "20-24": range(20, 24)}


def hbin(h: np.ndarray) -> np.ndarray:
    out = np.empty(h.size, object)
    for k, rg in HB.items():
        out[np.isin(h, list(rg))] = k
    return out


def strat(R, sq, hb) -> float:
    num = den = 0.0
    for k in np.unique(hb):
        m = hb == k
        a, b = m & sq, m & ~sq
        if a.sum() >= 2 and b.sum() >= 2:
            w = min(a.sum(), b.sum())
            num += w * (R[a].mean() - R[b].mean())
            den += w
    return num / den if den else np.nan


def run(d: pd.DataFrame, lab: str) -> dict:
    d = d[np.isfinite(d.R) & d.atr_14_100.notna()].reset_index(drop=True)
    R, sq = d.R.to_numpy(float), (d.atr_14_100 < 1).to_numpy()
    hb = hbin(pd.to_datetime(d.t, utc=True).dt.hour.to_numpy())
    days = C.day_ids(d.t)
    ud, inv = np.unique(days, return_inverse=True)
    vals = []
    for p in C.RNG.integers(0, ud.size, (C.N_BOOT, ud.size)):
        idx = np.concatenate([np.flatnonzero(inv == j) for j in p])
        vals.append(strat(R[idx], sq[idx], hb[idx]))
    vals = np.array(vals)
    return {"küme": lab, "n": len(d), "ham Δ": R[sq].mean() - R[~sq].mean(), "saat-içi Δ": strat(R, sq, hb),
            "P(saat-içi Δ<0)": float(np.nanmean(vals < 0))}


def main() -> None:
    b = pd.read_parquet(OUT / "ev_S1_bot.parquet")
    nd = b[(b.sym == "NDX.INDX") & (~b.fam.isin(["DECIDER", "MANUEL"]))]
    der = (nd.t >= X4.DER_LO) & (nd.t < X4.DER_HI)
    oos, back, fwd = nd[~der], nd[nd.t < X4.DER_LO], nd[nd.t >= X4.DER_HI]
    rows = [run(x, l) for l, x in (("dış birleşik", oos), ("GERİ", back), ("İLERİ", fwd), ("dış · SELL", oos[oos.s < 0]),
                                   ("dış · VIXREG", oos[oos.fam == "VIXREG"]))]
    for f, l in (("ev_S3_panel", "S3 panel"), ("ev_S9_panel_old", "S9 panel bot-öncesi"), ("ev_S2_skipped", "S2 engellenen")):
        rows.append(run(pd.read_parquet(OUT / f"{f}.parquet"), l))
    L = ["# Sıkışma — altıncı tur: saat-içi tabakalı fark (exp6.py)", C.md(pd.DataFrame(rows))]
    for lab, d in (("GERİ", back), ("İLERİ", fwd)):
        d = d[np.isfinite(d.R) & d.atr_14_100.notna()]
        hb = hbin(pd.to_datetime(d.t, utc=True).dt.hour.to_numpy())
        g = pd.DataFrame({"saat": hb, "sq": d.atr_14_100.lt(1).to_numpy(), "R": d.R.to_numpy()})
        tab = g.groupby(["saat", "sq"]).R.agg(["size", "mean"]).unstack()
        tab.columns = [f"{a} {'sıkışık' if b else 'diğer'}" for a, b in tab.columns]
        L.append(f"\n### {lab} — saat dilimi × sıkışma (n, ortR)")
        L.append(C.md(tab.reset_index(), "{:+.2f}"))
    txt = "\n".join(L)
    (OUT / "rapor6.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
