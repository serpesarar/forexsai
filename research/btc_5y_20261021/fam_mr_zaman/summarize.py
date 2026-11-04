"""Aile özeti: Holm(110, KEŞİF), literatür Holm(12, OOS∪KÖR), verdikt. Ön-kayıt §2."""
from __future__ import annotations

import numpy as np
import pandas as pd

import common as c
import run_timing as rt

tim = pd.read_csv(f"{c.OUT}/timing_cells.csv")
ch = pd.read_csv(f"{c.OUT}/channel_cells.csv")
df = pd.concat([ch, tim], ignore_index=True)
assert len(df) == 110, len(df)
df["p_kesif"] = [c.norm_sf(t) for t in df["KESIF_t"]]
df["holm110"] = c.holm(df["p_kesif"].to_numpy())

# literatür hücreleri: yayın sonrası (OOS ∪ KÖR) tek yönlü p, Holm(12)
lit = df["fam"].isin(["Q", "FUND", "TOC"])
cells = {x[0]: x for x in rt.build_cells()}
pl = {}
for nm in df.loc[lit, "cell"]:
    _, _, t, x, d, sw, _ = cells[nm]
    w = c.window_trades(np.asarray(t), np.asarray(x), d, swap=sw)
    w = w[w["t"] >= c.tmin("2024-01-11")]
    pl[nm] = (c.norm_sf(c.cluster_t(w["t"].to_numpy(), w["R"].to_numpy())), w["R"].mean(), len(w))
df["p_postpub"] = df["cell"].map({k: v[0] for k, v in pl.items()})
df["postpub_meanR"] = df["cell"].map({k: v[1] for k, v in pl.items()})
df.loc[lit, "holm_lit12"] = c.holm(df.loc[lit, "p_postpub"].to_numpy())

corr = np.where(lit, df["holm_lit12"], df["holm110"])
df["corr_p"] = corr
df["e7_plac"] = df["plac_TAM"] >= 95
df["e8_kor"] = df["KOR_meanR"] > 0
df["e9_corr"] = df["corr_p"] <= 0.10
df["e10_oos"] = df["OOS_meanR"] > 0
live = (df["card_pass"] == 6) & df["e7_plac"] & df["e8_kor"] & df["e9_corr"] & df["e10_oos"]
shadow = (df["card_pass"] >= 5) & df["e10_oos"] & df["e8_kor"]
df["verdict"] = np.where(live, "LIVE-aday", np.where(shadow, "SHADOW", "RED"))
df["sl_flag"] = df["min_sl_pct"] < 0.3
df.to_csv(f"{c.OUT}/all_cells_verdict.csv", index=False)

cols = ["cell", "n", "wr", "be_wr", "meanR", "bp", "ci_lo", "ci_hi", "P", "half1", "half2", "stressR", "abs15R",
        "optR", "exec_gap", "spR", "plac_TAM", "plac_TAM_mean", "KESIF_meanR", "KESIF_t", "OOS_meanR", "KOR_meanR",
        "KOR_bp", "card_pass", "p_kesif", "holm110", "maxz_p", "p_postpub", "holm_lit12", "verdict", "med_sl_pct"]
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 200)
print(df[cols].round(4).to_string())
print(df["verdict"].value_counts())
