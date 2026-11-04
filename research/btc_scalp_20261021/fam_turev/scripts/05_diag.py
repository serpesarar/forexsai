"""Bilgi amaçlı tanı (verdikti değiştirmez): her hücrenin BRÜT R'si − aynı yıl×saat×bölme taban brüt R'si (beklenen plasebo),
bp karşılığı; DV02 asimetrisi (E41); DV04c-U yakın ıska ayrıntısı. → out/gross_edge_cells.csv, out/diag.json
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

OUTS = {H: np.load(C.CACHE / f"out_H{H}.npz") for H in C.HS}
CACHEA: dict = {}


def A(H, nm):
    k = (H, nm)
    if k not in CACHEA:
        CACHEA[k] = OUTS[H][nm]
    return CACHEA[k]


def keyof(e):
    return C.seg_of(e).astype(np.int64) * 10**6 + C.year_of(e).astype(np.int64) * 100 + (e % 1440) // 60


BASEL: dict = {}


def baseline(H, d, r):
    if (H, d, r) not in BASEL:
        v = np.where(A(H, "valid"))[0]
        k = keyof(v)
        s = A(H, "s_bp")[v].astype(np.float64)
        gb = A(H, f"gb_d{d}_r{r}")[v].astype(np.float64)
        df = pd.DataFrame({"k": k, "gR": gb / s, "gbp": gb})
        BASEL[(H, d, r)] = df.groupby("k")[["gR", "gbp"]].mean()
    return BASEL[(H, d, r)]


def main():
    sig = pickle.load(open(C.CACHE / "signals.pkl", "rb"))
    rows = []
    for si, s in enumerate(sig):
        e0 = s["t"] + 1
        for H in s["Hset"]:
            v = A(H, "valid")[e0]
            e = e0[v]
            for r in C.RS:
                key = f"d{s['dir']}_r{r}"
                sbp = A(H, "s_bp")[e].astype(np.float64)
                gb = A(H, f"gb_{key}")[e].astype(np.float64)
                bl = baseline(H, s["dir"], r).reindex(keyof(e))
                row = {"hid": s["hid"], "par": s["par"], "dir": s["dir"], "r": r, "H": H}
                sg = C.seg_of(e)
                for i, nm in enumerate(["DISC", "OOS", "BLIND"]):
                    m = sg == i
                    row[f"{nm}_n"] = int(m.sum())
                    if m.sum():
                        row[f"{nm}_gR_edge"] = float((gb[m] / sbp[m]).mean() - bl["gR"].to_numpy()[m].mean())
                        row[f"{nm}_gbp_edge"] = float(gb[m].mean() - bl["gbp"].to_numpy()[m].mean())
                rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(C.OUT / "gross_edge_cells.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    ok = df[(df["DISC_n"] >= 50)]
    cons = ok[(ok["DISC_gR_edge"] > 0) & (ok["OOS_gR_edge"] > 0) & (ok["BLIND_gR_edge"] > 0)]
    print("brüt kenarı (taban üstü) üç bölmede de + olan hücre:", len(cons), "/", len(ok))
    print(cons.sort_values("OOS_gR_edge", ascending=False).round(3).head(25).to_string())
    big = ok[(ok[["DISC_gR_edge", "OOS_gR_edge", "BLIND_gR_edge"]].min(axis=1) >= 0.05)]
    print("üç bölmede de ≥ +0,05R brüt kenar:", len(big))
    # ID düzeyi: hücre ortalaması (geometri ortalaması) ile işaret tutarlılığı
    agg = ok.groupby("hid")[["DISC_gR_edge", "OOS_gR_edge", "BLIND_gR_edge", "DISC_gbp_edge", "OOS_gbp_edge", "BLIND_gbp_edge"]].mean()
    print(agg.round(3).to_string())
    agg.to_csv(C.OUT / "gross_edge_by_hid.csv")
    # E41 asimetri (DV02): long-liq fade vs short-liq fade, her geometri, brüt taban-üstü kenar
    asy = []
    for px in ("P5", "P1", "P1o"):
        for r in C.RS:
            for H in (15, 60):
                L = df[(df.hid == f"DV02-{px}L-F") & (df.r == r) & (df.H == H)].iloc[0]
                S_ = df[(df.hid == f"DV02-{px}S-F") & (df.r == r) & (df.H == H)].iloc[0]
                for nm in ("DISC", "OOS", "BLIND"):
                    asy.append({"proxy": px, "r": r, "H": H, "seg": nm, "Lfade_gR_edge": L[f"{nm}_gR_edge"],
                                "Sfade_gR_edge": S_[f"{nm}_gR_edge"], "diff": L[f"{nm}_gR_edge"] - S_[f"{nm}_gR_edge"]})
    asy = pd.DataFrame(asy)
    asy.to_csv(C.OUT / "dv02_asymmetry.csv", index=False)
    print(asy.groupby(["proxy", "seg"])[["Lfade_gR_edge", "Sfade_gR_edge", "diff"]].mean().round(3).to_string())


if __name__ == "__main__":
    main()
