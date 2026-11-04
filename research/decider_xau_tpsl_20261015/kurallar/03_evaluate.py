"""Adım 3: ön-kayıtlı değerlendirme (PROTOCOL.md). Çıktı: results/rules_table.csv, results/03_evaluate.txt"""
import numpy as np
import pandas as pd
import rules_lib as L

HERE = L.HERE; OUT = HERE / "results"
GN = list(L.GEOMS)
B_BOOT, K_C1, K_C2 = 4000, 4000, 300
rng = np.random.default_rng(20261015)
S = pd.read_pickle(HERE / "sim_decider.pkl")
C3 = pd.read_pickle(HERE / "sim_c3.pkl")
C2 = pd.read_pickle(HERE / "sim_c2_pool.pkl")
S["day"] = S.day.astype(str)

RULES = {
    "BUY": {"R1_guc_tetik": lambda d: d.trig_sign > 0, "R2_D2_temiz": lambda d: d.eq_block_buy == False,  # noqa: E712
            "R3_h1_ema50_ustu": lambda d: d.h1_above_ema50 == True, "R4_d1_yukari": lambda d: d.d1_up == True,  # noqa: E712
            "R5_ldn_ny": lambda d: d.sess_ldn_ny == True, "R6_vol_patlama_yok": lambda d: d.atr5_ratio < 1.5,  # noqa: E712
            "R7_20s_tepeye_yakin": lambda d: d.dist_hi20_h1_atr <= 1.0, "R8_boyut_ge_0.2": lambda d: d.size_factor >= 0.2},
    "SELL": {"R1_guc_tetik": lambda d: d.trig_sign < 0, "R2_D2_temiz": lambda d: d.eq_block_sell == False,  # noqa: E712
             "R3_h1_ema50_ustu": lambda d: d.h1_above_ema50 == False, "R4_d1_yukari": lambda d: d.d1_up == False,  # noqa: E712
             "R5_ldn_ny": lambda d: d.sess_ldn_ny == True, "R6_vol_patlama_yok": lambda d: d.atr5_ratio < 1.5,  # noqa: E712
             "R7_20s_tepeye_yakin": lambda d: d.dist_lo20_h1_atr <= 1.0, "R8_boyut_ge_0.2": lambda d: d.size_factor >= 0.2},
}
BE_WR = {GN[0]: 1.5 / 2.5, GN[1]: 0.75 / 2.0, GN[2]: None}


def day_boot_mean(v: np.ndarray, days: np.ndarray, B: int = B_BOOT) -> np.ndarray:
    u, inv = np.unique(days, return_inverse=True)
    s = np.bincount(inv, weights=v, minlength=len(u)); c = np.bincount(inv, minlength=len(u)).astype(float)
    W = rng.multinomial(len(u), np.ones(len(u)) / len(u), size=B).astype(float)
    return (W @ s) / (W @ c)


def single_position(d: pd.DataFrame, g: str) -> pd.Series:
    keep, last_exit = [], None
    dd = d.sort_values(g + "_entry")
    for idx, e, ex in zip(dd.index, dd[g + "_entry"], dd[g + "_exit"]):
        if last_exit is None or e >= last_exit:
            keep.append(idx); last_exit = ex
    return d.loc[keep, g]


def c2_percentile(d: pd.DataFrame, g: str, ev: float) -> float:
    grp = {k: v[g].values for k, v in C2.groupby("id")}
    ids = [i for i in d.id if i in grp]
    sims = np.empty(K_C2)
    for k in range(K_C2):
        sims[k] = np.mean([grp[i][rng.integers(len(grp[i]))] for i in ids])
    return float((sims < ev).mean()), float(sims.mean())


def stats(d: pd.DataFrame, g: str, full: pd.DataFrame) -> dict:
    v = d[g].values; days = d.day.values
    ev = v.mean()
    bt = day_boot_mean(v, days)
    cut = d.ts.quantile(0.5)
    h1, h2 = d[d.ts < cut][g].mean(), d[d.ts >= cut][g].mean()
    fv = full[g].values
    c1 = np.array([fv[rng.choice(len(fv), len(v), replace=False)].mean() for _ in range(K_C1)])
    c2p, c2m = c2_percentile(d, g, ev)
    ev_d1 = d[g + "_d1"].mean()
    usd = (d[g + "_usd_oz"] * d.lot_rule * 100).values
    sp = single_position(d, g)
    return dict(n=len(v), n_days=d.day.nunique(), EV_R=ev, WR=(v > 0).mean(), BE_WR=BE_WR[g],
                CI_lo=np.percentile(bt, 2.5), CI_hi=np.percentile(bt, 97.5), P_gt0=(bt > 0).mean(),
                H1=h1, H2=h2, C1_pct=(c1 < ev).mean(), C1_mean=c1.mean(), C2_pct=c2p, C2_mean=c2m,
                EV_delay1=ev_d1, EV_sp15=d[g + "_sp15"].mean(), EV_single=sp.mean(), n_single=len(sp),
                usd_per_trade=usd.mean(), usd_total=usd.sum(), se_iid=v.std(ddof=1) / np.sqrt(len(v)))


def c3_effect(dirn: str, rname: str, fn, g: str) -> tuple[float, float, int, int]:
    """C3 OPEN-olmayan danışmalarda (BUY simüle) kural − kural-dışı farkı. SELL için C3 BUY-simüle olduğundan
    yalnız BUY'da anlamlı."""
    if dirn != "BUY":
        return np.nan, np.nan, 0, 0
    c = C3[(C3.action != "OPEN") & ~C3.gap240]
    m = fn(c).fillna(False).astype(bool)
    return c[m][g].mean(), c[~m][g].mean(), int(m.sum()), int((~m).sum())


def verdict(r: dict) -> str:
    if r["n"] < 60 or r["n_days"] < 10:
        return "RED(güçsüz)"
    if r["EV_R"] <= 0 or r["H1"] < 0 or r["H2"] < 0:
        return "RED"
    c2 = r["P_gt0"] >= 0.90
    c4 = r["C1_pct"] >= 0.90 and r["C2_pct"] >= 0.90
    c5 = r["EV_delay1"] > 0 and (r["EV_R"] - r["EV_delay1"]) <= 0.5 * r["EV_R"]
    if not (c2 and c4 and c5):
        return "C"
    c6 = r["p_FW"] < 0.10
    c7 = (r["c3_rule"] - r["c3_not"]) > 0 if np.isfinite(r.get("c3_rule", np.nan)) else False
    return "A" if (c6 and c7) else "B"


def family_pvalues(full: pd.DataFrame, masks: dict, K: int = 4000) -> dict:
    """Seçim düzeltmeli: sonuç satırları karıştırılır, maskeler sabit; her test için z=(EV−μ)/σ_perm, max z."""
    keys = [(r, g) for r in masks for g in GN]
    Y = {g: full[g].values for g in GN}
    obs = {k: Y[k[1]][masks[k[0]]].mean() for k in keys}
    perm = {k: np.empty(K) for k in keys}
    n = len(full)
    for b in range(K):
        p = rng.permutation(n)
        for g in GN:
            yp = Y[g][p]
            for r in masks:
                perm[(r, g)][b] = yp[masks[r]].mean()
    mu = {k: perm[k].mean() for k in keys}; sd = {k: perm[k].std(ddof=1) for k in keys}
    zmax = np.max(np.vstack([(perm[k] - mu[k]) / sd[k] for k in keys]), axis=0)
    out = {}
    for k in keys:
        z = (obs[k] - mu[k]) / sd[k]
        out[k] = (z, float((zmax >= z).mean()))
    return out


lines = []
def P(s=""): lines.append(str(s)); print(s)

rows = []
for dirn in ("BUY", "SELL"):
    full = S[S.direction == dirn].reset_index(drop=True)
    P(f"\n=== {dirn}: n={len(full)} gün={full.day.nunique()}")
    for g in GN:
        r = stats(full, g, full)
        P(f"  TABAN {g}: EV {r['EV_R']:+.3f} [{r['CI_lo']:+.3f},{r['CI_hi']:+.3f}] P{r['P_gt0']:.2f} WR {r['WR']:.3f} "
          f"yarılar {r['H1']:+.3f}/{r['H2']:+.3f} C2 taban {r['C2_mean']:+.3f} (yüzd {r['C2_pct']:.2f}) +1dk {r['EV_delay1']:+.3f} "
          f"$/işlem {r['usd_per_trade']:+.2f} toplam {r['usd_total']:+.1f}")
        rows.append(dict(direction=dirn, rule="TABAN", geom=g, **r))
    masks = {rn: fn(full).fillna(False).astype(bool).values for rn, fn in RULES[dirn].items()}
    fam = family_pvalues(full, masks)
    for rn, fn in RULES[dirn].items():
        m = masks[rn]
        d = full[m]; dc = full[~m]
        for g in GN:
            if len(d) < 5:
                continue
            r = stats(d, g, full)
            r["z_perm"], r["p_FW"] = fam[(rn, g)]
            r["c3_rule"], r["c3_not"], r["c3_n_rule"], r["c3_n_not"] = c3_effect(dirn, rn, fn, g)
            r["comp_EV"] = dc[g].mean() if len(dc) else np.nan
            r["comp_n"] = len(dc)
            r["verdict"] = verdict(r)
            rows.append(dict(direction=dirn, rule=rn, geom=g, **r))
T = pd.DataFrame(rows)
T.to_csv(OUT / "rules_table.csv", index=False)

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
for dirn in ("BUY", "SELL"):
    t = T[(T.direction == dirn) & (T.rule != "TABAN")]
    P(f"\n##### {dirn} — kural × geometri")
    for x in t.itertuples():
        P(f"{x.rule:22s} {x.geom:20s} n={x.n:3d} g={x.n_days:2d} EV {x.EV_R:+.3f} [{x.CI_lo:+.3f},{x.CI_hi:+.3f}] P{x.P_gt0:.2f} "
          f"WR {x.WR:.3f}/{(x.BE_WR or float('nan')):.3f} yarı {x.H1:+.3f}/{x.H2:+.3f} | C1 {x.C1_pct:.2f} C2 {x.C2_pct:.2f}(μ{x.C2_mean:+.3f}) "
          f"| +1dk {x.EV_delay1:+.3f} sp×1.5 {x.EV_sp15:+.3f} tek-poz {x.EV_single:+.3f}(n{x.n_single}) | z {x.z_perm:+.2f} pFW {x.p_FW:.2f} "
          f"| C3 kural {x.c3_rule:+.3f}(n{x.c3_n_rule}) dışı {x.c3_not:+.3f}(n{x.c3_n_not}) | tamamlayıcı {x.comp_EV:+.3f}(n{x.comp_n}) "
          f"| $/işlem {x.usd_per_trade:+.2f} top {x.usd_total:+.1f} → {x.verdict}")
(OUT / "03_evaluate.txt").write_text("\n".join(lines))
