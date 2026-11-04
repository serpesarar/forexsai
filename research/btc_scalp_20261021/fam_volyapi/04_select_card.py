"""prereg §4–§5: Holm (DISC), max-z seçim düzeltmesi, aile başına DISC seçimi, POST kartı ve verdikt."""
import json

import numpy as np
import pandas as pd
from scipy.stats import norm

import common as C

d = pd.read_csv(f"{C.RES}/cells.csv")
PM = np.load(f"{C.RES}/placebo_means.npz")
key = lambda r, sp: f"{r.variant}|{r.dir}|{r.geom}|{sp}"  # noqa: E731

disc = d[d.split == "DISC"].copy()
disc["p1"] = 1 - norm.cdf(disc["z"])
# Holm
out = {}
for m_tot in (208, 224):
    p = disc["p1"].fillna(1).to_numpy()
    o = np.argsort(p)
    passed = 0
    for i, j in enumerate(o):
        if p[j] <= 0.05 / (m_tot - i):
            passed += 1
        else:
            break
    out[f"holm_pass_m{m_tot}"] = passed
out["min_p1"] = float(disc["p1"].min())
out["min_p1_cell"] = disc.loc[disc["p1"].idxmin(), ["variant", "dir", "geom"]].tolist()

# max-z boş dağılımı (seçime aday hücreler: kontrol değil, n_DISC ≥ 50)
cand = disc[(~disc.control) & (disc.n >= 50)].copy()
cand["zsel"] = (cand.meanR - cand.pl_mean) / cand.pl_sd
Z = np.vstack([(PM[key(r, "DISC")] - r.pl_mean) / r.pl_sd for r in cand.itertuples()])  # (cells, 200)
maxz = Z.max(axis=0)
cand["p_sel"] = [float(np.mean(maxz >= z)) for z in cand.zsel]
out["maxz_null_p50_p90_p95"] = [float(np.percentile(maxz, q)) for q in (50, 90, 95)]

# aile başına seçim
sel = cand.sort_values("meanR", ascending=False).groupby("family").head(1)
post = d[d.split == "POST"].set_index(["variant", "dir", "geom"])
blind = d[d.split == "BLIND"].set_index(["variant", "dir", "geom"])
oos = d[d.split == "OOS"].set_index(["variant", "dir", "geom"])
rows = []
for r in sel.itertuples():
    k = (r.variant, r.dir, r.geom)
    P_, B_, O_ = post.loc[k], blind.loc[k], oos.loc[k]
    c = {
        "c1_n150": P_.n >= 150,
        "c2_ev_P90": (P_.meanR > 0) and (P_.P >= 0.90),
        "c3_halves": (P_.half1 >= 0) and (P_.half2 >= 0),
        "c4_stress": P_.STRESS > 0,
        "c5_exec": P_.exec_gap <= 0.5 * abs(P_.meanR),
        "c6_single": P_.sp > 0,
        "x7_placebo95": P_.pl_pct >= 0.95,
        "x8_blind": B_.meanR > 0,
        "x9_gross_edge": (P_.edge_gross >= 0.15) or (P_.edge_gross >= 2 * P_.costR),
        "x10_same": P_.same < 0.005,
        "x11_psel": r.p_sel <= 0.10,
    }
    card6 = sum(c[x] for x in list(c)[:6])
    if all(c.values()):
        verdict = "LIVE-aday"
    elif card6 >= 5 and P_.pl_pct >= 0.90 and B_.meanR > 0:
        verdict = "SHADOW"
    else:
        verdict = "RED"
    rows.append({"family": r.family, "variant": r.variant, "dir": r.dir, "geom": r.geom,
                 "DISC_n": r.n, "DISC_meanR": r.meanR, "DISC_pl_pct": r.pl_pct, "DISC_z": r.z, "p_sel": r.p_sel,
                 "OOS_meanR": O_.meanR, "BLIND_meanR": B_.meanR, "POST_n": P_.n, "POST_meanR": P_.meanR,
                 "POST_bp": P_.bp_net, "POST_P": P_.P, "POST_ci": f"[{P_.ci_lo:+.3f}, {P_.ci_hi:+.3f}]",
                 "POST_halves": f"{P_.half1:+.3f}/{P_.half2:+.3f}", "POST_stress": P_.STRESS,
                 "POST_exec_gap": P_.exec_gap, "POST_sp": P_.sp, "POST_pl_mean": P_.pl_mean, "POST_pl_pct": P_.pl_pct,
                 "POST_edge_gross": P_.edge_gross, "POST_costR": P_.costR, "POST_same": P_.same, "POST_tpd": P_.tpd,
                 "POST_years": P_.years, "card6": card6, **c, "verdict": verdict})
S = pd.DataFrame(rows)
S.to_csv(f"{C.RES}/selection_card.csv", index=False)
cand[["variant", "dir", "geom", "n", "meanR", "pl_mean", "pl_sd", "zsel", "p_sel", "z", "p1"]].sort_values(
    "p_sel").to_csv(f"{C.RES}/disc_maxz.csv", index=False)
json.dump(out, open(f"{C.RES}/multiple_testing.json", "w"), indent=1, default=str)
pd.set_option("display.width", 250)
print(json.dumps(out, indent=1, default=str))
print(S.drop(columns=["POST_years"]).round(3).T.to_string())
