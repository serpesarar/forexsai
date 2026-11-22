"""EK-1 KEŞİF seçimi (yalnız KESIF dönemi)."""
import pandas as pd, numpy as np, core, d1
pd.set_option('display.width', 250)
T = pd.read_parquet(core.RES / "trades_G.parquet")
K = T[T.per == "KESIF"]
def s(g):
    v = g.net.values
    sd = v.std(ddof=1) if len(v) > 2 else np.nan
    return pd.Series({"n": len(v), "gun": g.day.nunique(), "wr": (v > 0).mean() * 100, "ort": v.mean(), "ortR": g.R.mean(),
                      "t": v.mean() / (sd / np.sqrt(len(v))) if sd > 0 else np.nan, "brut": g.gross.mean(), "mal": g.cost.mean()})
H = K.groupby(["sig", "mode", "g"]).apply(s).reset_index()
H["geom"] = H.g.map(lambda i: d1.GEOM[i])
H.to_csv(core.RES / "kesif_havuz_G.csv", index=False)
print(H.sort_values("ort", ascending=False).head(20).round(2).to_string(index=False))
sel_h = H[(H.wr >= 80) & (H.ort > 0) & (H.n >= 200)]
print("HAVUZ seçilen", len(sel_h)); print(sel_h.round(2).to_string(index=False))
C = K.groupby(["sig", "mode", "g", "pair"]).apply(s).reset_index()
C["geom"] = C.g.map(lambda i: d1.GEOM[i])
C.to_csv(core.RES / "kesif_cift_G.csv", index=False)
cand = C[(C.wr >= 80) & (C.ort > 0) & (C.t >= 2) & (C.n >= 60)]
sel_c = cand.sort_values("t", ascending=False).groupby("sig").head(10)
print("ÇİFT aday", len(cand), "seçilen", len(sel_c)); print(sel_c.round(2).to_string(index=False))
sel_h.assign(pair="HAVUZ").to_csv(core.RES / "secim_G_havuz.csv", index=False)
sel_c.to_csv(core.RES / "secim_G_cift.csv", index=False)
