"""ADIM 4: aday ex-ante özellikler için Welch t + gün-kümeli kontrol, karışıklık (saat×ATR), R paydası ayrıştırması, top-20 ayrıntı."""
import os, sys
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik"); sys.dont_write_bytecode = True
from mech import day_t
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
T = pd.read_parquet(os.path.join(RES, "trades.parquet")); day = pd.read_parquet(os.path.join(RES, "days.parquet"))
L = []
def say(s=""):
    L.append(str(s)); print(s)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50)
T["half"] = np.where(pd.to_datetime(T.eday) < "2017-01-01", "08-16", "17-26")
T["yr"] = pd.to_datetime(T.eday).dt.year
say("=== A. Aday ex-ante dilimleri: ortR, n, gün-kümeli t (dilim içi ortR>0), fark Welch t; yarılar ===")
cands = {
    "Asya saat (sinyal 23-06 UTC)": (T.xa_hour_sig >= 23) | (T.xa_hour_sig <= 6),
    "ATR_H1 500-bar yüzdeliği ≤0.2": T.xa_atrH1_pct500 <= 0.2,
    "son 24 barda ≥2 önceki kırılım (seri kırılım)": T.xa_brk_density24 >= 2,
    "son 24 barda 0 önceki kırılım": T.xa_brk_density24 == 0,
    "ATH'ye ≤%2": T.xa_dist_ath_pct >= -0.02,
    "BB genişliği 120-bar yüzdeliği ≤0.2": T.xa_bbw_pct120 <= 0.2,
    "seviye yaşı ≥15 bar": T.xa_level_age >= 15,
    "D1 > EMA50": T.xa_d1_above_ema50 == 1,
}
rows = []
for k, msk in cands.items():
    a, b = T.R[msk], T.R[~msk]
    w = stats.ttest_ind(a, b, equal_var=False)
    hs = [T.R[msk & (T.half == h)].mean() - T.R[~msk & (T.half == h)].mean() for h in ("08-16", "17-26")]
    yrs = T.groupby(["yr", msk]).R.mean().unstack()
    ypos = ((yrs[True] - yrs[False]) > 0).mean() if True in yrs else np.nan
    rows.append([k, msk.sum(), a.mean(), b.mean(), w.statistic, w.pvalue, hs[0], hs[1], ypos, (a >= 5).mean(), (b >= 5).mean(),
                 day_t(a.to_numpy(), T.eday[msk].to_numpy())])
C = pd.DataFrame(rows, columns=["dilim", "n", "ortR_in", "ortR_out", "Welch_t", "p", "fark_08-16", "fark_17-26", "fark>0 yıl oranı", "P(R≥5)_in", "P(R≥5)_out", "gün-kümeli t (in>0)"])
say(C.round(3).to_string(index=False)); C.round(4).to_csv(os.path.join(RES, "candidate_slices.csv"), index=False)
say("\n=== B. Saat × ATR_H1 yüzdeliği (karışıklık): ortR (n) ===")
T["asia"] = np.where((T.xa_hour_sig >= 23) | (T.xa_hour_sig <= 6), "Asya", "Asya-dışı")
T["atrq"] = pd.qcut(T.xa_atrH1_pct500, 3, labels=["ATR düşük", "orta", "yüksek"])
say(T.pivot_table(index="asia", columns="atrq", values="R", aggfunc=["mean", "size"], observed=True).round(3).to_string())
say("\nSeri kırılım × ATH yakınlığı: ortR (n)")
T["near_ath"] = np.where(T.xa_dist_ath_pct >= -0.02, "ATH≤%2", "ATH>%2")
T["dens"] = np.where(T.xa_brk_density24 >= 2, "seri(≥2)", "tekil(≤1)")
say(T.pivot_table(index="dens", columns="near_ath", values="R", aggfunc=["mean", "size"]).round(3).to_string())
# OLS: R ~ birkaç aday (standartlaştırılmış) — çoklu kontrol
X = pd.DataFrame({"asia": (T.asia == "Asya").astype(float), "atr_pct": T.xa_atrH1_pct500, "dens": T.xa_brk_density24.clip(0, 6),
                  "near_ath": (T.near_ath == "ATH≤%2").astype(float), "bbw": T.xa_bbw_pct120, "age": T.xa_level_age, "yr": T.yr}).dropna()
y = T.R.loc[X.index]
Xm = pd.get_dummies(X.drop(columns="yr"), drop_first=True).astype(float)
Xm = (Xm - Xm.mean()) / Xm.std(); Xm = pd.concat([Xm, pd.get_dummies(X.yr, prefix="y", drop_first=True).astype(float)], axis=1)
Xm.insert(0, "c", 1.0)
beta, *_ = np.linalg.lstsq(Xm.to_numpy(), y.to_numpy(), rcond=None)
res = y.to_numpy() - Xm.to_numpy() @ beta
# gün-kümeli SE
G = T.eday.loc[X.index].to_numpy(); XtX_inv = np.linalg.pinv(Xm.T @ Xm)
meat = np.zeros((Xm.shape[1], Xm.shape[1]))
for g in np.unique(G):
    ii = G == g; s = Xm.to_numpy()[ii].T @ res[ii]; meat += np.outer(s, s)
se = np.sqrt(np.diag(XtX_inv @ meat @ XtX_inv))
say("\n=== C. Çoklu regresyon R ~ standart özellikler + yıl sabit etkisi (gün-kümeli SE) ===")
for nm, b_, s_ in zip(Xm.columns[:7], beta[:7], se[:7]):
    say(f"  {nm:>10}: β={b_:+.3f}R/sd  t={b_/s_:+.2f}")
say("\n=== D. R paydası ayrıştırması: R = (hareket/ATR_D1) / (1.5·ATR_H1/ATR_D1) ===")
T["move_d"] = T.R * 1.5 * T.atr / T.xa_atrD1; T["ratio"] = T.atr / T.xa_atrD1
w = T[(T.R > 0)]
for nm, msk in (("R≥5", w.R >= 5), ("0<R<5", w.R < 5)):
    say(f"  {nm}: hareket/ATR_D1 medyan {w.move_d[msk].median():.3f}, ATR_H1/ATR_D1 medyan {w.ratio[msk].median():.3f}")
lm = np.log(w.move_d[w.R >= 5].median() / w.move_d[w.R < 5].median()); lr = np.log(w.ratio[w.R < 5].median() / w.ratio[w.R >= 5].median())
say(f"  log-oran payı: hareket büyüklüğü %{100*lm/(lm+lr):.0f}, küçük payda (dar ATR_H1) %{100*lr/(lm+lr):.0f}")
say("\n=== E. Top-20 ayrıntı ===")
top = day.head(20)
cols = ["R", "rep_ent_hour", "rep_xa_session", "rep_weekday", "rep_xp_held", "rep_xp_mfe_R", "rep_xp_R_day0", "rep_xp_post20_R", "rep_xp_exit_at_maxclose",
        "rep_xp_day_ret1", "rep_xp_day_ret_atr", "rep_xp_day_range_atr", "rep_xp_day_fwd1", "rep_xp_day_fwd3", "rep_xp_day_fwd5"]
say(top[cols].round(3).to_string())
cols2 = ["rep_xa_atrD1p_pct252", "rep_xa_atrH1_pct500", "rep_xa_atrH1_over_D1", "rep_xa_dist_ath_pct", "rep_xa_dist_ath_atr", "rep_xa_dist_52wh_atr",
         "rep_xa_d1_above_ema50", "rep_xa_d1_above_ema200", "rep_xa_ema50_gt_200", "rep_xa_ema50_slope10", "rep_xa_w1_above_ema20", "rep_xa_ret5", "rep_xa_ret20",
         "rep_xa_gap_atr", "rep_xa_bbw_pct120", "rep_xa_rng20_atr", "rep_xa_bars_since_prev_brk", "rep_xa_brk_density24", "rep_xa_level_age",
         "rep_xa_pen_high_atr", "rep_xa_pen_close_atr", "rep_xa_body_atr", "rep_xa_vol_ratio_hour", "rep_xp_vol_expand"]
say(top[cols2].round(3).to_string())
say("\nWorst-20:")
say(day.sort_values("R").head(20)[["R", "n_tr", "hours", "codes", "rep_weekday", "rep_xa_session", "rep_xa_brk_density24", "rep_xa_bbw_pct120", "rep_xa_atrH1_pct500", "rep_xp_day_ret_atr"]].round(3).to_string())
open(os.path.join(RES, "extra.txt"), "w").write("\n".join(L) + "\n")
