"""Dünkü 2 SL DAYCOMBO'nun profilinden türetilen 4 işaret (yön ve eşik ÖNCEDEN: alt/üst tertil, keşif=tüm 2025+2026
DAYCOMBO tertilleri) 356 yeniden üretilmiş DAYCOMBO'da (10-19'u içermez) sınanır; SQZ ile de birleştirilir.
python3 research/daycombo_kombo_20261020/dunku_isaret.py"""
from __future__ import annotations

import numpy as np
import pandas as pd

import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("dk_run2", Path(__file__).resolve().parent / "run.py")
K = importlib.util.module_from_spec(spec); sys.modules["dk_run2"] = K; spec.loader.exec_module(K)

SIGNS = {"pre_dist_ema50_1h": "alt", "pre_slope_ema50_1h": "alt", "pre_mtf_agree": "alt", "pre_vol_seas_15": "üst"}


def main() -> None:
    d = pd.read_parquet(K.OUT / "daycombo_feats.parquet")
    L = ["# Dünkü SL profilinden türetilen işaretler — 356 DAYCOMBO (2025 + 2026, 10-19 hariç)",
         "| işaret | dönem | n işaretli | ortR işaretli | ortR diğer | Δ | kurt_R |", "|---|---|---|---|---|---|---|"]
    masks = {}
    for f, side in SIGNS.items():
        x = d[f].to_numpy(float)
        q = np.nanquantile(x, 1 / 3 if side == "alt" else 2 / 3)
        masks[f] = (x <= q) if side == "alt" else (x >= q)
        if f == "pre_mtf_agree":
            masks[f] = x <= np.nanquantile(x, 1 / 3)
    masks["hepsi≥2 (en az iki işaret)"] = np.sum([masks[f] for f in SIGNS], axis=0) >= 2
    masks["SQZ<1 ∧ dist_ema50_1h alt"] = (d.atr_14_100 < 1).to_numpy() & masks["pre_dist_ema50_1h"]
    for name, m in masks.items():
        for lab, sel in (("2025", d.split == "keşif"), ("2026", d.split == "sınama")):
            s = sel.to_numpy()
            mm, R = m & s, d.R.to_numpy(float)
            L.append(f"| {name} | {lab} | {mm.sum()} | {R[mm].mean():+.3f} | {R[s & ~m].mean():+.3f} | "
                     f"{R[mm].mean() - R[s & ~m].mean():+.3f} | {-R[mm].sum():+.2f} |")
    txt = "\n".join(L)
    (K.OUT / "dunku_isaret.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
