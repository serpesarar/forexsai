"""Tüm hücreler (224) × bölmeler: metrikler + plasebo (200) → results/cells.csv, results/placebo_means.npz."""
import time
import warnings

import numpy as np
import pandas as pd

import common as C
import signals as S

warnings.simplefilter("ignore")
t0 = time.time()
g = C.Grid()
g.precompute()
pl = C.Placebo(g)
V = S.all_variants(g)
np.savez_compressed(f"{C.CACHE}/signals.npz", **{k: np.vstack([v[0], v[1]]) for k, v in V.items()})
print(f"hazır {time.time()-t0:.0f}s")

SPL = ["DISC", "OOS", "BLIND", "POST", "ALL"]
cal_days = {k: (C.tm(b) - C.tm(a)) / 1440 for k, (a, b) in C.SPLITS.items()}
cal_days["POST"] = cal_days["OOS"] + cal_days["BLIND"]
cal_days["ALL"] = cal_days["POST"] + cal_days["DISC"]


def split_mask(sp: np.ndarray, name: str) -> np.ndarray:
    if name == "POST":
        return (sp == "OOS") | (sp == "BLIND")
    if name == "ALL":
        return sp != ""
    return sp == name


def metrics(res, idx, plR, plG, name, ydays):
    m = {}
    R = C.net_R(res, "PEP")[idx]
    n = len(R)
    m["n"] = n
    if n == 0:
        return m
    e = res["e"][idx]
    day = e // 1440
    m["ndays"] = len(np.unique(day))
    m["tpd"] = n / ydays
    m["WR"] = float(np.mean(R > 0))
    m["meanR"] = float(R.mean())
    m["bp_net"] = float((res["g"][idx] - C.COSTS["PEP"]).mean())
    m["bp_gross"] = float(res["g"][idx].mean())
    m["grossR"] = float((res["g"][idx] / res["s"][idx]).mean())
    m["s_bp_med"] = float(np.median(res["s"][idx]))
    m["costR"] = float((C.COSTS["PEP"] / res["s"][idx]).mean())
    p, lo, hi = C.day_boot(R, day)
    m["P"], m["ci_lo"], m["ci_hi"] = p, lo, hi
    m["z"] = C.cluster_z(R, day)
    o = np.argsort(e, kind="stable")
    h = n // 2
    m["half1"] = float(R[o[:h]].mean()) if h else np.nan
    m["half2"] = float(R[o[h:]].mean())
    for cst in ("STRESS", "FIX15", "MAKER", "TAKER"):
        m[cst] = float(C.net_R(res, cst)[idx].mean())
    m["heur"] = float(C.net_R(res, "PEP", "g_heur")[idx].mean())
    m["opt"] = float(C.net_R(res, "ZERO", "g_opt")[idx].mean())
    m["exec_gap"] = abs(m["opt"] - m["meanR"])
    m["same"] = float(res["same"][idx].mean())
    keep = C.single_position(e, res["x"][idx])
    m["n_sp"] = int(keep.sum())
    m["sp"] = float(R[keep].mean())
    m["tp_rate"] = float(np.mean(res["typ"][idx] == 1))
    m["sl_rate"] = float(np.mean(res["typ"][idx] == -1))
    pm = plR[:, idx].mean(axis=1)
    m["pl_mean"] = float(pm.mean())
    m["pl_sd"] = float(pm.std(ddof=1))
    m["pl_pct"] = float(np.mean(pm < m["meanR"]))
    m["pl_gross"] = float(plG[:, idx].mean())
    m["edge_gross"] = m["grossR"] - m["pl_gross"]
    yrs = g.year[e]
    m["years"] = " ".join(f"{y}:{R[yrs == y].mean():+.3f}({(yrs == y).sum()})" for y in np.unique(yrs))
    m["years_pos"] = int(sum(R[yrs == y].mean() > 0 for y in np.unique(yrs)))
    m["years_n"] = int(len(np.unique(yrs)))
    return m, pm


rows = []
PM = {}
seed = 100
for vname, (t, d, fam, ctrl) in V.items():
    e_all = t + 1
    ok = (e_all < g.N) & (e_all > 0)
    e_all, d_all = e_all[ok], d[ok]
    okv = g.valid[e_all]
    ndrop = int((~okv).sum())
    e_all, d_all = e_all[okv], d_all[okv]
    dirs = [("X", np.ones(len(e_all), bool))] if fam == "MA" else [("L", d_all == 1), ("S", d_all == -1)]
    for dname, dm in dirs:
        e, dd = e_all[dm], d_all[dm]
        o = np.argsort(e, kind="stable")
        e, dd = e[o], dd[o]
        if len(e) == 0:
            continue
        seed += 1
        draws = pl.draw(e, C.N_PLACEBO, seed)  # (200, n)
        for gname, (r, H) in C.GEOMS.items():
            res = g.resolve(e, dd, r, H)
            pres = g.resolve(draws.ravel(), np.tile(dd, C.N_PLACEBO), r, H)
            plR = C.net_R(pres, "PEP").reshape(C.N_PLACEBO, -1)
            plG = (pres["g"] / pres["s"]).reshape(C.N_PLACEBO, -1)
            sp = g.split[e]
            for spn in SPL:
                idx = np.where(split_mask(sp, spn))[0]
                out = metrics(res, idx, plR, plG, spn, cal_days[spn])
                if isinstance(out, tuple):
                    m, pm = out
                    PM[f"{vname}|{dname}|{gname}|{spn}"] = pm
                else:
                    m = out
                m.update({"variant": vname, "family": fam, "control": ctrl, "dir": dname, "geom": gname,
                          "r": r, "H": H, "split": spn, "n_dropped_invalid": ndrop})
                rows.append(m)
    print(f"{vname:14s} n={len(e_all):6d} drop={ndrop:4d}  {time.time()-t0:.0f}s", flush=True)

df = pd.DataFrame(rows)
lead = ["variant", "family", "control", "dir", "geom", "r", "H", "split"]
df = df[lead + [c for c in df.columns if c not in lead]]
df.to_csv(f"{C.RES}/cells.csv", index=False)
np.savez_compressed(f"{C.RES}/placebo_means.npz", **PM)
print(f"bitti {time.time()-t0:.0f}s, satır {len(df)}")
