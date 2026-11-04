"""Ek A2 post-hoc incelemeler (kanıt değeri düşük; ön-kayıtlı verdikti değiştirmez)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ofl  # noqa: E402

N = ofl.N
df = ofl.load_frame()
g = ofl.build_grid(df)
fc_next, blocked = ofl.rollover_cap()
hcap = fc_next - np.arange(N)
entry_ok = ofl.valid_entries(g) & ~blocked & (hcap >= 5)
atr5 = ofl.lib.atr_5m(g)
entry_ok &= ~np.isnan(atr5)
a0, a1 = ofl.SEG["DISC"]
absret = np.abs(np.diff(np.log(g["close_ff"]), prepend=np.nan)) * 1e4
eng = ofl.Engine(g, atr5, entry_ok, hcap, float(np.nanpercentile(absret[a0:a1], 99)))
E = np.where(entry_ok)[0]
YR, HR = ofl.year_hour(np.arange(N))
YH = (YR - 2021) * 24 + HR
NB = YH.max() + 1
DAY = np.arange(N) // 1440
F = ofl.features(df)
F["dp1sign"] = np.sign(2 * df["perp_taker_buy_base"].to_numpy().astype(float) - df["perp_volume"].to_numpy().astype(float))
GEO = [("S1", 1.0, 15), ("S2", 2.0, 60)]
MU = {}
for geom in GEO:
    for s in (1, -1):
        o = eng.outcome(E, np.full(len(E), s, dtype=np.int8), geom)
        r, _ = ofl.net_R(o, "PEP")
        rg = o["ret"]
        cnt = np.maximum(np.bincount(YH[E], minlength=NB), 1)
        MU[(geom, s, "R")] = np.bincount(YH[E], weights=r, minlength=NB) / cnt
        MU[(geom, s, "bp")] = np.bincount(YH[E], weights=rg, minlength=NB) / cnt


def evalc(t, d, mode, geom):
    e = t + 1
    sd = (d * mode).astype(np.int8)
    o = eng.outcome(e, sd, geom)
    r, bp = ofl.net_R(o, "PEP")
    xr = r - np.where(sd == 1, MU[(geom, 1, "R")][YH[e]], MU[(geom, -1, "R")][YH[e]])
    xb = o["ret"] - np.where(sd == 1, MU[(geom, 1, "bp")][YH[e]], MU[(geom, -1, "bp")][YH[e]])
    return e, sd, r, bp, o, xr, xb


out = {}
# (1) emilim platosu
rows = []
for w in [1, 5, 15]:
    for th in [3, 4, 5, 6]:
        cond = (np.abs(F[f"zDp{w}"]) >= th) & (np.abs(F[f"zr{w}"]) <= 0.5) & ~F[f"pbad{w}"] & ~F[f"sbad{w}"]
        t, d = ofl.events_from_dir(np.sign(F[f"zDp{w}"]), cond, entry_ok)
        for geom in GEO:
            e, sd, r, bp, o, xr, xb = evalc(t, d, -1, geom)
            if len(e) == 0:
                continue
            row = {"W": w, "th": th, "geom": ofl.gname(geom), "n": len(e), "meanR": r.mean(), "mean_bp": bp.mean(),
                   "gross_bp": o["ret"].mean(), "excessR": xr.mean(), "excess_bp": xb.mean(),
                   "buy_share": (sd == 1).mean()}
            for sg, (a, b) in ofl.SEG.items():
                m = (e >= a) & (e < b)
                row[f"n_{sg}"] = int(m.sum())
                row[f"R_{sg}"] = r[m].mean() if m.any() else np.nan
            _, _, z = ofl.cluster_z(xr, DAY[e])
            row["z_all"] = z
            dd = pd.Series(r).groupby(DAY[e]).sum().sort_values(ascending=False)
            row["top5day_share"] = dd.head(5).sum() / r.sum() if r.sum() > 0 else np.nan
            row["n_days"] = len(dd)
            for y in range(2021, 2027):
                m = YR[e] == y
                row[f"y{y}"] = r[m].mean() if m.any() else np.nan
            rows.append(row)
            if w == 15 and th == 5:
                ev = pd.DataFrame({"entry": ofl.T0 + pd.to_timedelta(e, unit="m"), "side": sd, "R": r, "bp": bp,
                                   "cls": o["cls"], "sl_bp": o["sl"]})
                ev.to_csv(os.path.join(ofl.RES, f"of02_W15_th5_events_{ofl.gname(geom)}.csv"), index=False)
PL = pd.DataFrame(rows)
PL.to_csv(os.path.join(ofl.RES, "posthoc_absorption_plateau.csv"), index=False)
print(PL[["W", "th", "geom", "n", "meanR", "mean_bp", "excessR", "z_all", "n_DISC", "R_DISC", "n_OOS", "R_OOS",
          "n_BLIND", "R_BLIND", "top5day_share", "buy_share"]].round(3).to_string())

# (2) çeyrek-saat özgüllüğü
rows = []
for name, mins in [("QH_00_15_30_45", [0, 15, 30, 45]), ("CTRL_07_22_37_52", [7, 22, 37, 52])]:
    cond = np.isin(F["minute"], mins) & ~F["pbad1"] & (F["dp1sign"] != 0)
    t, d = ofl.events_from_dir(F["dp1sign"], cond, entry_ok)
    for geom in GEO:
        e, sd, r, bp, o, xr, xb = evalc(t, d, -1, geom)
        for y in range(2021, 2027):
            m = YR[e] == y
            _, _, z = ofl.cluster_z(xb[m], DAY[e][m])
            rows.append({"set": name, "geom": ofl.gname(geom), "year": y, "n": int(m.sum()),
                         "gross_bp": o["ret"][m].mean(), "excess_gross_bp": xb[m].mean(), "z": z,
                         "net_bp": bp[m].mean(), "netR": r[m].mean()})
QH = pd.DataFrame(rows)
QH.to_csv(os.path.join(ofl.RES, "posthoc_quarter_hour.csv"), index=False)
print(QH.round(3).to_string())
