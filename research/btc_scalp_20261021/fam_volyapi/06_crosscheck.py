"""(1) Perp yolu çapraz kontrolü (aynı spot sinyalleri, perp OHLC'de çözüm). (2) Plasebo-altı hücrelerin teşhisi:
kayma (5 bp) payı ve kaymasız brüt fark. Sonuçlar → results/crosscheck.csv, results/below_placebo_diag.csv"""
import warnings

import numpy as np
import pandas as pd

import common as C

warnings.simplefilter("ignore")
sig = np.load(f"{C.CACHE}/signals.npz")
SEL = pd.read_csv(f"{C.RES}/selection_card.csv")
cells = [(r.variant, r.dir, r.geom, "seçilen") for r in SEL.itertuples()]
cells += [("ST-S-0930", "S", "G2", "post-hoc"), ("ORB-US30", "S", "G4", "post-hoc"), ("ORB-US30", "L", "G3", "post-hoc"),
          ("VWREV-U3", "L", "G1", "post-hoc"), ("ORF-ASIA30", "S", "G3", "post-hoc"), ("LS-D", "L", "G3", "post-hoc")]

gs = C.Grid("spot"); gs.precompute("spot")
gp = C.Grid("perp"); gp.precompute("perp")


def trades(g, v, dr):
    t, d = sig[v]
    e = t + 1
    ok = (e > 0) & (e < g.N)
    e, d = e[ok], d[ok]
    ok = g.valid[e]
    e, d = e[ok], d[ok]
    if dr != "X":
        m = d == (1 if dr == "L" else -1)
        e, d = e[m], d[m]
    return e, d


rows = []
for v, dr, gm, tag in cells:
    r, H = C.GEOMS[gm]
    for nm, g in (("spot", gs), ("perp", gp)):
        e, d = trades(g, v, dr)
        res = g.resolve(e, d, r, H)
        R = C.net_R(res, "PEP")
        sp = g.split[e]
        for spn in ("DISC", "POST", "BLIND"):
            mk = (sp == "OOS") | (sp == "BLIND") if spn == "POST" else sp == spn
            rows.append({"cell": f"{v} {dr} {gm}", "tag": tag, "path": nm, "split": spn, "n": int(mk.sum()),
                         "meanR": R[mk].mean(), "bp_net": (res["g"][mk] - 1.85).mean()})
X = pd.DataFrame(rows)
X.to_csv(f"{C.RES}/crosscheck.csv", index=False)
pv = X.pivot_table(index=["cell", "tag"], columns=["split", "path"], values="meanR").round(3)
pd.set_option("display.width", 250)
print(pv.to_string())

# (2) plasebo-altı teşhis (DISC)
pl = C.Placebo(gs)
diag = []
for v, dr, gm in (("VS1-C", "L", "G1"), ("VS1-C", "S", "G1"), ("VWREV-D2", "S", "G1"), ("VWREV-D2", "L", "G1"),
                  ("VS2-C", "L", "G1"), ("LS-H", "L", "G1")):
    r, H = C.GEOMS[gm]
    e, d = trades(gs, v, dr)
    m = gs.split[e] == "DISC"
    e, d = e[m], d[m]
    res = gs.resolve(e, d, r, H)
    dr_ = pl.draw(e, 50, 11).ravel()
    pres = gs.resolve(dr_, np.tile(d, 50), r, H)
    for lab, rr in (("strateji", res), ("plasebo", pres)):
        slexit = rr["typ"] == -1
        hit = rr["x"][slexit]
        slip5 = np.mean(gs.slip_bp[hit] > 1) if slexit.any() else np.nan
        g_noslip = rr["g"] + np.where(slexit, gs.slip_bp[rr["x"]], 0)
        diag.append({"cell": f"{v} {dr} {gm}", "who": lab, "n": len(rr["e"]), "s_bp_med": np.median(rr["s"]),
                     "grossR": (rr["g"] / rr["s"]).mean(), "grossR_noslip": (g_noslip / rr["s"]).mean(),
                     "sl_rate": slexit.mean(), "tp_rate": (rr["typ"] == 1).mean(), "slip5_share_of_SL": slip5,
                     "costR": (1.85 / rr["s"]).mean()})
D = pd.DataFrame(diag)
D.to_csv(f"{C.RES}/below_placebo_diag.csv", index=False)
print(D.round(3).to_string())
