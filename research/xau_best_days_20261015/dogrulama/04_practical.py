"""ADIM 4 (PROTOCOL §7, C5): bayraklı olayları ATLA + tek-pozisyonu yeniden yürüt. Ölçüler + boş (R, süre yıl-içi
dairesel kaydırma, aynı filtre, yeniden yürütme). İleri kümelerde d için etiket permütasyonu (bilgi).
Çıktı: results/c5_practical.csv, results/c5_yearly.csv, results/c4_perm.csv, results/04_log.txt"""
from __future__ import annotations
import os
import numpy as np, pandas as pd
from common import RES, one_position, circ_shift

REPS = int(os.environ.get("REPS", "2000"))
e = pd.read_parquet(os.path.join(RES, "allev.parquet")).sort_values("ent").reset_index(drop=True)
VARS = ["S1_ge1", "S1_ge2", "S1_ge3", "S2_gt075", "S2_gt100", "S2_gt125", "S12"]
WEEKS = pd.period_range("2008-01-01", "2026-06-16", freq="W").astype(str)
L: list[str] = []
def say(s=""):
    L.append(str(s)); print(s)

def metrics(sub: pd.DataFrame) -> dict:
    r = sub.R.to_numpy()
    wk = pd.Series(r).groupby(sub.week.to_numpy()).sum()
    wall = wk.reindex(WEEKS, fill_value=0.0)
    cum = np.cumsum(r); dd = float((cum - np.maximum.accumulate(np.r_[0.0, cum])[1:]).min())
    day = pd.Series(r).groupby(sub.ent_day.to_numpy()).sum().sort_values(ascending=False)
    top20 = set(day.index[:20]); keep = ~np.isin(sub.ent_day.to_numpy(), list(top20))
    yr = pd.Series(r).groupby(sub.year.to_numpy()).sum()
    return dict(n=len(r), per_week=len(r) / len(WEEKS), ortR=float(r.mean()), totR=float(r.sum()), maxdd=dd,
                pos_weeks_active=float((wk > 0).mean()), pos_weeks_all=float((wall > 0).mean()),
                R_week=float(wall.mean()), sharpe_w=float(wall.mean() / wall.std()),
                top20_share=float(day.iloc[:20].sum() / r.sum()), top50_share=float(day.iloc[:50].sum() / r.sum()),
                ex_top20_ortR=float(r[keep].mean()), ex_top20_totR=float(r[keep].sum()),
                pos_years=f"{int((yr > 0).sum())}/{len(yr)}", wr=float((r > 0).mean()))

ent = e.ent.to_numpy(); dur = e.dur.to_numpy(); R = e.R.to_numpy(); yr = e.year.to_numpy()
kb = one_position(ent, ent + dur)
rows = [dict(variant="TABAN (filtresiz)", **metrics(e[kb]))]
for v in VARS:
    F = e[v].to_numpy().astype(bool); idx = np.where(~F)[0]
    kf = one_position(ent[idx], ent[idx] + dur[idx])
    rows.append(dict(variant=f"ATLA {v}", **metrics(e.iloc[idx][kf])))
P = pd.DataFrame(rows)
# boş: (R, süre) yıl-içi dairesel kaydırma → aynı filtre + yeniden yürütme; istatistik = ortR(filtre) − ortR(taban)
rng = np.random.default_rng(424242)
nullv = {v: np.empty(REPS) for v in VARS}; nullt = {v: np.empty(REPS) for v in VARS}
Fm = {v: e[v].to_numpy().astype(bool) for v in VARS}
for i in range(REPS):
    p = circ_shift(yr, rng); Rp, dp = R[p], dur[p]
    kb0 = one_position(ent, ent + dp); b0 = Rp[kb0].mean(); t0 = Rp[kb0].sum()
    for v in VARS:
        idx = np.where(~Fm[v])[0]; kf = one_position(ent[idx], ent[idx] + dp[idx])
        nullv[v][i] = Rp[idx][kf].mean() - b0; nullt[v][i] = Rp[idx][kf].sum() - t0
base = P.iloc[0]
P["d_ortR"] = P.ortR - base.ortR; P["d_totR"] = P.totR - base.totR
P["null_mean_d_ortR"] = [np.nan] + [nullv[v].mean() for v in VARS]
P["p_ortR"] = [np.nan] + [float((nullv[v] >= P.d_ortR.iloc[j + 1]).mean()) for j, v in enumerate(VARS)]
P["p_totR"] = [np.nan] + [float((nullt[v] >= P.d_totR.iloc[j + 1]).mean()) for j, v in enumerate(VARS)]
P.to_csv(os.path.join(RES, "c5_practical.csv"), index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
say(f"=== C5 pratik etki (ana küme Duka 2008-01→2026-06-16, {len(WEEKS)} takvim haftası; boş {REPS} tekrar) ===")
say(P.round(4).T.to_string())

# yıllık toplam R: taban vs S1 / S2 / S12 filtre
yy = {}
for nm, F in (("taban", np.zeros(len(e), bool)), ("ATLA_S1", Fm["S1_ge2"]), ("ATLA_S2", Fm["S2_gt100"]), ("ATLA_S12", Fm["S12"])):
    idx = np.where(~F)[0]; kf = one_position(ent[idx], ent[idx] + dur[idx]); s = e.iloc[idx][kf]
    yy[nm] = s.groupby("year").R.sum(); yy[nm + "_n"] = s.groupby("year").R.size()
Y = pd.DataFrame(yy); Y.to_csv(os.path.join(RES, "c5_yearly.csv"))
say("\nYıllık toplam R (n):"); say(Y.round(1).to_string())

# ileri kümeler: d için etiket permütasyonu (tek-poz taban içinde; bilgi amaçlı, tek yönlü d<0)
fw = pd.read_parquet(os.path.join(RES, "fwd_events.parquet"))
rows = []
r2 = np.random.default_rng(9)
for s, X in fw.groupby("set"):
    B = X[X.base]; r = B.R.to_numpy()
    for v in ("S1_ge2", "S2_gt100", "S12"):
        Fb = B[v].to_numpy().astype(bool); obs = r[Fb].mean() - r[~Fb].mean()
        nul = np.empty(20000)
        for i in range(20000):
            q = r2.permutation(Fb); nul[i] = r[q].mean() - r[~q].mean()
        rows.append(dict(set=s, flag=v, n=len(r), n_on=int(Fb.sum()), d=float(obs), p_le=float((nul <= obs).mean()),
                         p_ge=float((nul >= obs).mean()), d_med=float(np.median(r[Fb]) - np.median(r[~Fb]))))
C4 = pd.DataFrame(rows); C4.to_csv(os.path.join(RES, "c4_perm.csv"), index=False)
say("\n=== ileri kümeler: etiket permütasyonu (p_le = P(boş ≤ d), 'atla' yönü) ==="); say(C4.round(3).to_string(index=False))
# ileri: haftalık ölçü
for s, X in fw.groupby("set"):
    X = X.sort_values("t_ent")
    for nm, F in (("taban", np.zeros(len(X), bool)), ("ATLA_S1", X.S1_ge2.to_numpy()), ("ATLA_S2", X.S2_gt100.to_numpy()), ("ATLA_S12", X.S12.to_numpy())):
        Z = X[~F]; k = one_position(Z.t_ent.to_numpy(), Z.t_exit.to_numpy()); r = Z.R.to_numpy()[k]
        cum = np.cumsum(r); dd = (cum - np.maximum.accumulate(np.r_[0.0, cum])[1:]).min()
        wk = (pd.Series(r).groupby(pd.to_datetime(Z.ent_ts.to_numpy()[k], utc=True).tz_convert(None).to_period("W")).sum())
        say(f"  [{s}] {nm:<9} n={len(r):3} ortR {r.mean():+.3f} toplam {r.sum():+.1f} maksDD {dd:+.1f} aktif-hafta+ {(wk > 0).mean():.2f}")
open(os.path.join(RES, "04_log.txt"), "w").write("\n".join(L) + "\n")
