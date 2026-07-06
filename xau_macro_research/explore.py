"""Exploratory: do macro factors PREDICT forward gold returns? And did the
relationship break between 2021-23 and 2024-26? Honest foundation before modeling.

For each feature we report Spearman corr with forward H-day gold return, full
sample and split by era. A predictor stable across eras is usable; a sign-flip
means the textbook relationship broke and can't be trusted forward.
"""
from __future__ import annotations
import warnings; warnings.simplefilter("ignore")
import numpy as np, pandas as pd
from scipy.stats import spearmanr

df = pd.read_csv("xau_macro_research/macro_panel.csv", parse_dates=["date"]).set_index("date")

# ── features (all causal at day t) ──
f = pd.DataFrame(index=df.index)
f["real_yield"]   = df["DFII10"]
f["d_real_5"]     = df["DFII10"].diff(5)
f["d_real_20"]    = df["DFII10"].diff(20)
f["dollar"]       = df["DTWEXBGS"]
f["d_dollar_5"]   = df["DTWEXBGS"].pct_change(5)
f["d_dollar_20"]  = df["DTWEXBGS"].pct_change(20)
f["vix"]          = df["VIXCLS"]
f["d_vix_5"]      = df["VIXCLS"].diff(5)
f["nominal_10"]   = df["DGS10"]
f["d_nom_20"]     = df["DGS10"].diff(20)
f["term_spread"]  = df["DGS10"] - df["DGS2"]
f["breakeven"]    = df["T10YIE"]
f["d_break_20"]   = df["T10YIE"].diff(20)
f["gold_mom_20"]  = df["gold"].pct_change(20)
f["gold_mom_60"]  = df["gold"].pct_change(60)

def fwd_ret(h):
    return df["gold"].shift(-h) / df["gold"] - 1

eras = {
    "FULL  21-26": df.index >= "2000",
    "21-23 (pre)": (df.index >= "2021") & (df.index < "2024"),
    "24-26 (post)": df.index >= "2024",
}

for H in (5, 20):
    y = fwd_ret(H)
    print(f"\n===== Spearman corr of feature(t) with forward {H}-day gold return =====")
    print(f"{'feature':14} " + " ".join(f"{e:>13}" for e in eras))
    for col in f.columns:
        cells = []
        for emask in eras.values():
            m = emask & f[col].notna() & y.notna()
            r, p = spearmanr(f[col][m], y[m]) if m.sum() > 30 else (np.nan, 1)
            star = "*" if p < 0.05 else " "
            cells.append(f"{r:+.2f}{star}")
        print(f"{col:14} " + " ".join(f"{c:>13}" for c in cells))
    print("  (* p<0.05; SIGN FLIP between pre/post = relationship broke, untrustworthy)")
