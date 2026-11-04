"""ADIM 2 (PROTOCOL §3–5): C1 seçim düzeltmesi (aile max-|z|, yıl-içi dairesel kaydırma), C2 P1-F plasebo DiD,
C3 çağ kararlılığı + bir-çağ-hariç. Çıktı: results/c1_family.csv, results/c1_tail_family.csv, results/c2_p1f.csv,
results/c3_eras.csv, results/02_log.txt"""
from __future__ import annotations
import json, os
import numpy as np, pandas as pd
from common import RES, ERAS, circ_shift

REPS = int(os.environ.get("REPS", "5000"))
rng = np.random.default_rng(20261016)
b = pd.read_parquet(os.path.join(RES, "base.parquet")).sort_values("ent").reset_index(drop=True)
fam = json.load(open(os.path.join(RES, "family.json")))
names = fam["family"]
X = b[[f"fam::{k}" for k in names]].to_numpy().astype(float)          # n × K
R = b.R.to_numpy(); yr = b.year.to_numpy(); n1 = X.sum(0); n0 = len(R) - n1
L: list[str] = []
def say(s=""):
    L.append(str(s)); print(s)

def dstat(Rm: np.ndarray) -> np.ndarray:
    """Rm: (reps, n) → (reps, K) ortR(bayrak) − ortR(¬bayrak)."""
    s1 = Rm @ X; tot = Rm.sum(1, keepdims=True)
    return s1 / n1 - (tot - s1) / n0

perms = np.stack([circ_shift(yr, rng) for _ in range(REPS)])
Rnull = R[perms]; Tnull = (R >= 3).astype(float)[perms]
def family_test(y: np.ndarray, ynull: np.ndarray, tag: str) -> pd.DataFrame:
    obs = dstat(y[None, :])[0]; nul = dstat(ynull)
    mu, sd = nul.mean(0), nul.std(0)
    z = (obs - mu) / sd; zn = (nul - mu) / sd
    mx2 = np.abs(zn).max(1); mxneg = (-zn).max(1); mxpos = zn.max(1)
    p_raw2 = (np.abs(zn) >= np.abs(z)).mean(0)
    df = pd.DataFrame({"flag": names, "source": [fam["source"][k] for k in names], "n_on": n1.astype(int),
                       "d": obs, "null_mean": mu, "null_sd": sd, "z": z, "p_raw_2s": p_raw2,
                       "p_sel_2s": [(mx2 >= abs(v)).mean() for v in z],
                       "p_sel_neg": [(mxneg >= -v).mean() for v in z], "p_sel_pos": [(mxpos >= v).mean() for v in z]})
    o = np.argsort(df.p_raw_2s.to_numpy()); m = len(df); run = 0.0; holm = np.empty(m)
    for r_, i in enumerate(o):
        run = max(run, min(1.0, (m - r_) * max(df.p_raw_2s.iloc[i], 1 / REPS))); holm[i] = run
    df["p_holm"] = holm
    df = df.sort_values("z", key=np.abs, ascending=False)
    say(f"\n=== C1 aile testi [{tag}] K={len(names)} bayrak, {REPS} yıl-içi dairesel kaydırma ===")
    say(f"boş max|z| %50/%90/%95/%99 = {np.percentile(mx2, [50, 90, 95, 99]).round(2).tolist()}")
    say(df.head(15).round(4).to_string(index=False))
    return df

c1 = family_test(R, Rnull, "ortR"); c1.to_csv(os.path.join(RES, "c1_family.csv"), index=False)
c1t = family_test((R >= 3).astype(float), Tnull, "P(R≥3)"); c1t.to_csv(os.path.join(RES, "c1_tail_family.csv"), index=False)
for k in ("S1_seri_kirilim(≥2)", "S2_onceki_gun>%1", "S3_FOMC_penceresi"):
    for nm, df in (("ortR", c1), ("P3", c1t)):
        r = df[df.flag == k].iloc[0]
        rank = int((df.z.abs() >= abs(r.z)).sum())
        say(f"  {k:<22} [{nm}] d={r.d:+.4f} z={r.z:+.2f} sıra {rank}/{len(df)}  p_raw={r.p_raw_2s:.4f} p_sel(2s)={r.p_sel_2s:.3f}"
            f" p_sel(neg)={r.p_sel_neg:.3f} p_sel(pos)={r.p_sel_pos:.3f} Holm={r.p_holm:.3f}")

# ── alt-aileler: yalnız aramanın kendi parçası (anatomi / makro) içinde düzeltme — bilgi amaçlı ──
for srcname, flag in (("anatomi", "S1_seri_kirilim(≥2)"), ("makro", "S2_onceki_gun>%1")):
    idx = [i for i, k in enumerate(names) if fam["source"][k] == srcname]
    obs = dstat(R[None, :])[0][idx]; nul = dstat(Rnull)[:, idx]
    mu, sd = nul.mean(0), nul.std(0); z = (obs - mu) / sd; mx = np.abs((nul - mu) / sd).max(1)
    j = [names[i] for i in idx].index(flag)
    say(f"  alt-aile {srcname} (K={len(idx)}): {flag} z={z[j]:+.2f} p_sel(2s)={(mx >= abs(z[j])).mean():.3f}")

# ── C2: P1-F (aynı yıl × UTC saati × bayrak durumu) DiD ──
P = pd.read_parquet(os.path.join(RES, "allbars.parquet"))
def p1f(flag: str, draws: int = 40, seed: int = 5, tail: bool = False):
    r = np.random.default_rng(seed)
    yv = (P.R >= 3).astype(float).to_numpy() if tail else P.R.to_numpy()
    yb = (b.R >= 3).astype(float).to_numpy() if tail else b.R.to_numpy()
    key_all = (P.year.to_numpy() * 100 + P.utc_h.to_numpy()) * 2 + P[flag].to_numpy().astype(int)
    pools = pd.Series(np.arange(len(P))).groupby(key_all).apply(np.array).to_dict()
    Fb = b[flag].to_numpy().astype(bool)
    key_ev = (b.year.to_numpy() * 100 + b.utc_h.to_numpy()) * 2 + Fb.astype(int)
    pm = np.full(len(b), np.nan)
    for k, idx in pd.Series(np.arange(len(b))).groupby(key_ev).indices.items():
        p = pools.get(k)
        if p is not None and len(p):
            pm[idx] = yv[p[r.integers(0, len(p), (len(idx), draws))]].mean(1)
    x = yb - pm; ok = np.isfinite(x)
    xs, F, days = x[ok], Fb[ok], b.ent_day.to_numpy()[ok]
    u, inv = np.unique(days, return_inverse=True)
    sF = np.bincount(inv, xs * F, len(u)); nF = np.bincount(inv, F.astype(float), len(u))
    sN = np.bincount(inv, xs * ~F, len(u)); nN = np.bincount(inv, (~F).astype(float), len(u))
    obs = sF.sum() / nF.sum() - sN.sum() / nN.sum()
    bi = np.random.default_rng(7).integers(0, len(u), (4000, len(u)))
    bs = sF[bi].sum(1) / nF[bi].sum(1) - sN[bi].sum(1) / nN[bi].sum(1)
    # tüm-bar ham bayrak farkı (eşleşmesiz, bilgi)
    Fp = P[flag].to_numpy().astype(bool)
    return dict(flag=flag, stat="P3" if tail else "ortR", n_on=int(Fb.sum()), rule_in=float(yb[Fb].mean()), rule_out=float(yb[~Fb].mean()),
                rule_diff=float(yb[Fb].mean() - yb[~Fb].mean()), rand_in=float(np.nanmean(pm[Fb])), rand_out=float(np.nanmean(pm[~Fb])),
                rand_diff=float(np.nanmean(pm[Fb]) - np.nanmean(pm[~Fb])), DiD=float(obs), P_DiD_lt0=float((bs < 0).mean()),
                ci_lo=float(np.percentile(bs, 2.5)), ci_hi=float(np.percentile(bs, 97.5)), cover=float(ok.mean()),
                allbars_in=float(yv[Fp].mean()), allbars_out=float(yv[~Fp].mean()), allbars_on_rate=float(Fp.mean()))
rows = [p1f(f) for f in ("S1_ge1", "S1_ge2", "S1_ge3", "S2_gt075", "S2_gt100", "S2_gt125", "S12", "S3_fomcwin")]
rows.append(p1f("S3_fomcwin", tail=True))
c2 = pd.DataFrame(rows); c2.to_csv(os.path.join(RES, "c2_p1f.csv"), index=False)
say("\n=== C2 P1-F (aynı yıl×UTC saati×bayrak durumu, 40 çekim) — DiD = (kural−plasebo | bayrak) − (… | ¬bayrak) ===")
say(c2.round(4).to_string(index=False))

# ── C3: çağlar + bir çağ hariç ──
rows = []
for flag in ("S1_ge1", "S1_ge2", "S1_ge3", "S2_gt075", "S2_gt100", "S2_gt125", "S12", "S3_fomcwin"):
    F = b[flag].to_numpy().astype(bool)
    for nm, y0, y1 in ERAS:
        s = (yr >= y0) & (yr <= y1); x = ~s
        rows.append(dict(flag=flag, era=nm, n=int(s.sum()), n_on=int((F & s).sum()), on_rate=float(F[s].mean()),
                         d=float(R[F & s].mean() - R[~F & s].mean()),
                         d_P3=float((R[F & s] >= 3).mean() - (R[~F & s] >= 3).mean()),
                         d_excl=float(R[F & x].mean() - R[~F & x].mean()),
                         d_P3_excl=float((R[F & x] >= 3).mean() - (R[~F & x] >= 3).mean()),
                         R_in=float(R[F & s].mean()), R_out=float(R[~F & s].mean())))
c3 = pd.DataFrame(rows); c3.to_csv(os.path.join(RES, "c3_eras.csv"), index=False)
say("\n=== C3 çağlar (d = ortR bayrak − ¬bayrak; d_excl = o çağ HARİÇ) ===")
say(c3.round(3).to_string(index=False))
# yıl bazında işaret
yy = []
for flag in ("S1", "S2"):
    F = b[flag].to_numpy().astype(bool)
    g = pd.DataFrame({"y": yr, "F": F, "R": R}).groupby(["y", "F"]).R.mean().unstack()
    dd = (g[True] - g[False]).dropna()
    say(f"  {flag} yıl bazında fark<0 oranı: {(dd < 0).mean():.2f} ({(dd < 0).sum()}/{len(dd)}) — " +
        ", ".join(f"{int(k)}:{v:+.2f}" for k, v in dd.items()))
open(os.path.join(RES, "02_log.txt"), "w").write("\n".join(L) + "\n")
