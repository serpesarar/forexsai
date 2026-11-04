"""Tüm hücrelerin değerlendirmesi, DISCOVERY seçimi, max-z boş dağılımı, kart.

Çıktılar results/: all_cells.csv, cards_all.csv, selected.json, maxz_null.json, selected_detail.csv
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ofl  # noqa: E402

t0 = time.time()
RES = ofl.RES
N = ofl.N
df = ofl.load_frame()
g = ofl.build_grid(df)
del df
fc_next, blocked = ofl.rollover_cap()
valid = ofl.valid_entries(g)
hcap = fc_next - np.arange(N)
entry_ok = valid & ~blocked & (hcap >= 5)
atr5 = ofl.lib.atr_5m(g)
entry_ok &= ~np.isnan(atr5)
E = np.where(entry_ok)[0]
# kayma eşiği: DISCOVERY'deki |1m getiri| %99 yüzdeliği
a0, a1 = ofl.SEG["DISC"]
cff = g["close_ff"]
absret = np.abs(np.diff(np.log(cff), prepend=np.nan)) * 1e4
slip_thr = float(np.nanpercentile(absret[a0:a1], 99))
print(f"slip eşiği {slip_thr:.2f} bp; giriş {len(E):,}")
eng = ofl.Engine(g, atr5, entry_ok, hcap, slip_thr)
print(f"motor {time.time()-t0:.0f}s")

YR, HR = ofl.year_hour(np.arange(N))
DAY = np.arange(N) // 1440
YH = (YR - 2021) * 24 + HR  # kova anahtarı
NB = YH.max() + 1

# ---------------- tüm geçerli girişler için R (PEP net, gerçekçi) ve kova ortalamaları
RF, XF, MU, MUG = {}, {}, {}, {}
for geom in ofl.GEOMS:
    for s in (1, -1):
        o = eng.outcome(E, np.full(len(E), s, dtype=np.int8), geom)
        r, _ = ofl.net_R(o, "PEP")
        rg = o["ret"] / o["sl"]
        mu = np.bincount(YH[E], weights=r, minlength=NB) / np.maximum(np.bincount(YH[E], minlength=NB), 1)
        mug = np.bincount(YH[E], weights=rg, minlength=NB) / np.maximum(np.bincount(YH[E], minlength=NB), 1)
        a = np.full(N, np.nan, dtype=np.float32)
        a[E] = r
        RF[(geom, s)] = a
        x = np.full(N, np.nan, dtype=np.float32)
        x[E] = r - mu[YH[E]]
        XF[(geom, s)] = x
        MU[(geom, s)] = mu
        MUG[(geom, s)] = mug
print(f"tam R dizileri {time.time()-t0:.0f}s")

# rastgele giriş referansı (ortalama net R, segment başına) — bağlam için
rand_rows = []
for geom in ofl.GEOMS:
    for s in (1, -1):
        for sg, (a, b) in ofl.SEG.items():
            m = (E >= a) & (E < b)
            rand_rows.append({"geom": ofl.gname(geom), "side": s, "seg": sg, "meanR_pep": float(RF[(geom, s)][E[m]].mean())})
pd.DataFrame(rand_rows).to_csv(os.path.join(RES, "random_entry_baseline.csv"), index=False)

# ---------------- olaylar
Z = np.load(os.path.join(RES, "events.npz"))
CELLS = sorted({k.split("__")[0] for k in Z.files})
PRIMARY = {"OF01": -1, "OF02": -1, "OF03": 1, "OF04a": -1, "OF04b": 1, "OF05": 1, "OF06": -1}


def hyp(c):
    return c.split("_")[0]


EVT = {}
for c in CELLS:
    t, d = Z[f"{c}__t"], Z[f"{c}__d"].astype(np.int8)
    okk = entry_ok[t + 1]
    t, d = t[okk], d[okk]
    for mode in (1, -1):
        EVT[(c, mode)] = (t + 1, (d * mode).astype(np.int8))

SEGS = list(ofl.SEG.items())


def zstat(x, day):
    n = len(x)
    if n < 2:
        return np.nan, np.nan
    m = x.mean()
    S = np.bincount(day, weights=x - m, minlength=2000)
    se = np.sqrt((S ** 2).sum()) / n
    return m, (m / se if se > 0 else np.nan)


# ---------------- tüm hücreler × segment
rows = []
for (c, mode), (e, sd) in EVT.items():
    for geom in ofl.GEOMS:
        o = eng.outcome(e, sd, geom)
        r, bp = ofl.net_R(o, "PEP")
        x = r - np.where(sd == 1, MU[(geom, 1)][YH[e]], MU[(geom, -1)][YH[e]])
        for sg, (a, b) in SEGS + [("POST", (ofl.SEG["OOS"][0], ofl.SEG["BLIND"][1]))]:
            m = (e >= a) & (e < b)
            n = int(m.sum())
            if n == 0:
                rows.append({"cell": c, "hyp": hyp(c), "mode": mode, "primary": PRIMARY[hyp(c)] == mode,
                             "geom": ofl.gname(geom), "seg": sg, "n": 0})
                continue
            mx, zx = zstat(x[m], DAY[e[m]])
            rows.append({"cell": c, "hyp": hyp(c), "mode": mode, "primary": PRIMARY[hyp(c)] == mode,
                         "geom": ofl.gname(geom), "seg": sg, "n": n, "WR": float((r[m] > 0).mean()),
                         "meanR": float(r[m].mean()), "mean_bp": float(bp[m].mean()),
                         "gross_bp": float(o["ret"][m].mean()), "excessR": float(mx), "z": float(zx),
                         "amb": float(o["amb"][m].mean()), "sl_bp_med": float(np.median(o["sl"][m])),
                         "tp_share": float((o["cls"][m] == 1).mean()), "sl_share": float((o["cls"][m] == -1).mean())})
ALL = pd.DataFrame(rows)
ALL.to_csv(os.path.join(RES, "all_cells.csv"), index=False)
print(f"tüm hücreler {time.time()-t0:.0f}s ({len(ALL)} satır)")

# ---------------- seçim (DISCOVERY)
D = ALL[(ALL.seg == "DISC")].copy()
elig = D[D.primary & (D.n >= 100) & (D.amb < 0.005)]
SEL = {}
for h in PRIMARY:
    sub = elig[elig.hyp == h].sort_values("z", ascending=False)
    if len(sub):
        r0 = sub.iloc[0]
        SEL[h] = {"cell": r0.cell, "mode": int(r0["mode"]), "geom": r0.geom, "z_disc": float(r0.z),
                  "n_disc": int(r0.n), "meanR_disc": float(r0.meanR), "excess_disc": float(r0.excessR)}
print(json.dumps(SEL, indent=1))
obs_max_all = float(D["z"].max())
obs_max_30 = float(D[D.n >= 30]["z"].max())

# ---------------- max-z boş dağılımı: DISCOVERY içinde tam-gün dairesel kaydırma
m0, m1 = ofl.SEG["DISC"]
L = m1 - m0
ndays = L // 1440
rng = np.random.default_rng(2026)
GI = {ofl.gname(gm): gm for gm in ofl.GEOMS}
nullmax_all, nullmax_30 = [], []
disc_ev = {}
for (c, mode), (e, sd) in EVT.items():
    m = (e >= m0) & (e < m1)
    disc_ev[(c, mode)] = (e[m] - 1, sd[m])  # karar dakikası
NS = 200
for it in range(NS):
    k = int(rng.integers(30, ndays - 30)) * 1440
    best_all, best_30 = -np.inf, -np.inf
    for (c, mode), (t, sd) in disc_ev.items():
        if len(t) < 2:
            continue
        ts = m0 + ((t - m0 + k) % L)
        e2 = ts + 1
        okk = entry_ok[e2]
        e2, s2 = e2[okk], sd[okk]
        if len(e2) < 2:
            continue
        dd = DAY[e2]
        isL = s2 == 1
        for geom in ofl.GEOMS:
            x = np.where(isL, XF[(geom, 1)][e2], XF[(geom, -1)][e2]).astype(float)
            _, zz = zstat(x, dd)
            if np.isfinite(zz):
                best_all = max(best_all, zz)
                if len(e2) >= 30:
                    best_30 = max(best_30, zz)
    nullmax_all.append(best_all)
    nullmax_30.append(best_30)
    if it % 20 == 0:
        print(f"  null {it}: {best_all:.2f} / {best_30:.2f}  ({time.time()-t0:.0f}s)")
nullmax_all = np.array(nullmax_all)
nullmax_30 = np.array(nullmax_30)
psel = {h: {"p_sel_all": float((nullmax_all >= v["z_disc"]).mean()),
            "p_sel_n30": float((nullmax_30 >= v["z_disc"]).mean())} for h, v in SEL.items()}
json.dump({"obs_max_all": obs_max_all, "obs_max_n30": obs_max_30,
           "null_all_q": np.percentile(nullmax_all, [50, 90, 95, 99]).tolist(),
           "null_n30_q": np.percentile(nullmax_30, [50, 90, 95, 99]).tolist(),
           "p_obs_max_all": float((nullmax_all >= obs_max_all).mean()),
           "p_obs_max_n30": float((nullmax_30 >= obs_max_30).mean()), "psel": psel,
           "null_all": nullmax_all.tolist(), "null_n30": nullmax_30.tolist()},
          open(os.path.join(RES, "maxz_null.json"), "w"), indent=1)
print(f"max-z {time.time()-t0:.0f}s", psel)


# ---------------- kart
POST = (ofl.SEG["OOS"][0], ofl.SEG["BLIND"][1])


BUCK = {}
for kk in np.unique(YH[E]):
    BUCK[kk] = E[YH[E] == kk]


def placebo_pct(e, sd, geom, r_mean, B=1000, seed=5):
    rng = np.random.default_rng(seed)
    keys = YH[e]
    tot = np.zeros(B)
    for kk in np.unique(keys):
        idx = np.where(keys == kk)[0]
        C = BUCK[kk]
        dr = C[rng.integers(0, len(C), size=(B, len(idx)))]
        sides = sd[idx]
        vals = np.where(sides[None, :] == 1, RF[(geom, 1)][dr], RF[(geom, -1)][dr])
        tot += vals.sum(1)
    pm = tot / len(e)
    return float((pm < r_mean).mean() * 100), float(pm.mean())


def card(c, mode, gname, seg=POST, B=2000, plac=True):
    geom = GI[gname]
    e, sd = EVT[(c, mode)]
    m = (e >= seg[0]) & (e < seg[1])
    e, sd = e[m], sd[m]
    out = {"cell": c, "mode": mode, "geom": gname, "n": int(len(e))}
    if len(e) < 10:
        return out
    o = eng.outcome(e, sd, geom)
    r, bp = ofl.net_R(o, "PEP")
    day = DAY[e]
    pe, lo, hi = ofl.day_boot(r, day, B)
    half = len(e) // 2
    oo = np.argsort(e)
    h1, h2 = r[oo[:half]].mean(), r[oo[half:]].mean()
    rs, _ = ofl.net_R(o, "STRESS")
    rf, _ = ofl.net_R(o, "FIX15")
    rmk, _ = ofl.net_R(o, "BMAKER")
    rtk, _ = ofl.net_R(o, "BTAKER")
    oopt = eng.outcome(e, sd, geom, amb_mode="tp", slip=False)
    ropt = oopt["ret"] / oopt["sl"]
    oh = eng.outcome(e, sd, geom, amb_mode="heur")
    rh, _ = ofl.net_R(oh, "PEP")
    ot = eng.outcome(e, sd, geom, amb_mode="tp")
    rt, _ = ofl.net_R(ot, "PEP")
    keep = ofl.single_position(e, o["tau"])
    rgross = o["ret"] / o["sl"]
    mug = np.where(sd == 1, MUG[(geom, 1)][YH[e]], MUG[(geom, -1)][YH[e]])
    x = r - np.where(sd == 1, MU[(geom, 1)][YH[e]], MU[(geom, -1)][YH[e]])
    _, zz = zstat(x, day)
    yrs = YR[e]
    bl = (e >= ofl.SEG["BLIND"][0]) & (e < ofl.SEG["BLIND"][1])
    oos = (e >= ofl.SEG["OOS"][0]) & (e < ofl.SEG["OOS"][1])
    ndays_seg = (seg[1] - seg[0]) / 1440
    out.update({
        "WR": float((r > 0).mean()), "meanR": float(r.mean()), "mean_bp": float(bp.mean()),
        "gross_bp": float(o["ret"].mean()), "grossR": float(rgross.mean()),
        "gross_excessR": float((rgross - mug).mean()), "excessR": float(x.mean()), "z": float(zz),
        "CI_lo": lo, "CI_hi": hi, "P_EV": pe, "half1": float(h1), "half2": float(h2),
        "stressR": float(rs.mean()), "fix15R": float(rf.mean()), "bmakerR": float(rmk.mean()), "btakerR": float(rtk.mean()),
        "optR": float(ropt.mean()), "exec_gap": float(abs(ropt.mean() - r.mean())), "heurR": float(rh.mean()),
        "ambTP_R": float(rt.mean()), "amb_rate": float(o["amb"].mean()),
        "single_n": int(keep.sum()), "singleR": float(r[keep].mean()),
        "OOS_R": float(r[oos].mean()) if oos.any() else np.nan, "BLIND_R": float(r[bl].mean()) if bl.any() else np.nan,
        "n_OOS": int(oos.sum()), "n_BLIND": int(bl.sum()),
        "trades_per_day": float(len(e) / ndays_seg), "sl_bp_med": float(np.median(o["sl"])),
        "per_year": {int(y): round(float(r[yrs == y].mean()), 4) for y in np.unique(yrs)},
        "per_year_bp": {int(y): round(float(bp[yrs == y].mean()), 2) for y in np.unique(yrs)},
        "buy_n": int((sd == 1).sum()), "buyR": float(r[sd == 1].mean()) if (sd == 1).any() else np.nan,
        "sellR": float(r[sd == -1].mean()) if (sd == -1).any() else np.nan,
    })
    if plac:
        out["placebo_pct"], out["placebo_meanR"] = placebo_pct(e, sd, geom, r.mean())
    crit = [out["n"] >= 150, out["meanR"] > 0 and pe >= 0.90, h1 >= 0 and h2 >= 0, out["stressR"] > 0,
            out["exec_gap"] <= 0.5 * abs(out["meanR"]), out["singleR"] > 0]
    out["card"] = [bool(v) for v in crit]
    out["card_n"] = int(sum(crit))
    return out


# tüm hücrelerin POST kartı (plasebo analitik z, bootstrap B=500)
cards = []
for (c, mode) in EVT:
    for gn in GI:
        cd = card(c, mode, gn, B=500, plac=False)
        cards.append({k: v for k, v in cd.items() if k not in ("per_year", "per_year_bp", "card")})
CA = pd.DataFrame(cards)
CA.to_csv(os.path.join(RES, "cards_all_post.csv"), index=False)
print(f"tüm kartlar {time.time()-t0:.0f}s; 6/6 olan hücre: {(CA.card_n == 6).sum()}, POST meanR>0: {(CA.meanR > 0).sum()}/{len(CA)}")

# seçilenlerin tam kartı + Holm
from scipy.stats import norm  # noqa: E402

det = {}
for h, v in SEL.items():
    cd = card(v["cell"], v["mode"], v["geom"])
    cd["p_one"] = float(1 - norm.cdf(cd["z"])) if np.isfinite(cd.get("z", np.nan)) else 1.0
    cd["disc"] = v
    cd["p_sel"] = psel[h]
    # DISC kartı da (aynı ölçütler) bilgi için
    cdd = card(v["cell"], v["mode"], v["geom"], seg=ofl.SEG["DISC"], B=1000, plac=True)
    cd["disc_card"] = {k: cdd[k] for k in ("n", "meanR", "mean_bp", "P_EV", "placebo_pct", "excessR", "gross_excessR",
                                           "amb_rate", "per_year", "card_n")}
    # ikincil mod aynı hücre+geometri (E49)
    sec = card(v["cell"], -v["mode"], v["geom"], B=500, plac=False)
    cd["secondary_mode"] = {k: sec.get(k) for k in ("n", "meanR", "mean_bp", "excessR", "z", "OOS_R", "BLIND_R")}
    det[h] = cd
ps = sorted(det.items(), key=lambda kv: kv[1]["p_one"])
mtests = len(ps)
for i, (h, cd) in enumerate(ps):
    cd["holm_p"] = float(min(1.0, max(cd["p_one"] * (mtests - j) for j, (_, c2) in enumerate(ps[: i + 1]))))
for h, cd in det.items():
    extra = {"placebo>=95": cd.get("placebo_pct", 0) >= 95, "BLIND>0": (cd.get("BLIND_R") or -1) > 0,
             "gross>=0.15R_or_2xcost": (cd.get("gross_excessR", -1) >= 0.15) or (cd.get("gross_bp", -1) >= 3.7),
             "holm<0.05": cd["holm_p"] < 0.05, "p_sel<=0.10": cd["p_sel"]["p_sel_all"] <= 0.10,
             "amb<0.5%": cd.get("amb_rate", 1) < 0.005}
    cd["extra"] = extra
    if cd["card_n"] == 6 and all(extra.values()):
        verdict = "LIVE"
    elif cd["card_n"] >= 4 and cd["meanR"] > 0 and cd.get("placebo_pct", 0) >= 90 and (cd.get("BLIND_R") or -1) > 0:
        verdict = "SHADOW"
    else:
        verdict = "RED"
    cd["verdict"] = verdict
json.dump(det, open(os.path.join(RES, "selected.json"), "w"), indent=1, default=float)
for h, cd in det.items():
    print(h, cd["cell"], cd["mode"], cd["geom"], "n", cd["n"], "R", round(cd["meanR"], 3), "bp", round(cd["mean_bp"], 2),
          "P", round(cd["P_EV"], 2), "plac", cd.get("placebo_pct"), "card", cd["card_n"], "holm", round(cd["holm_p"], 3),
          "psel", cd["p_sel"], cd["verdict"])
print(f"bitti {time.time()-t0:.0f}s")
