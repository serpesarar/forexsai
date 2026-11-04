"""ADIM 6: kuralın R'si altının en büyük yükseliş günlerine ne kadar bağlı? + top-30 (%1) AUC."""
import os, numpy as np, pandas as pd
from scipy import stats
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
T = pd.read_parquet(os.path.join(RES, "trades.parquet")); D = pd.read_parquet(os.path.join(RES, "d1.parquet")); day = pd.read_parquet(os.path.join(RES, "days.parquet"))
D.index = pd.to_datetime(D.index); D = D[(D.index >= "2008-02-01") & (D.index < "2026-06-17")]
T["tday"] = pd.to_datetime(T.tday)
L = []
def say(x): L.append(x); print(x)
tot = T.R.sum()
for metric in ("ret1", "ret_atr"):
    for k in (20, 50, 100, int(len(D) * 0.01)):
        top = set(D[metric].nlargest(k).index)
        m = T.tday.isin(top)
        say(f"altının en iyi {k:>3} günü ({metric}): o günlerde giriş R {T.R[m].sum():6.1f} (toplamın %{100*T.R[m].sum()/tot:.0f}, n={m.sum()}, ortR {T.R[m].mean():+.2f}); bu günler hariç ortR {T.R[~m].mean():+.4f}")
    bot = set(D[metric].nsmallest(50).index); m = T.tday.isin(bot)
    say(f"altının en kötü 50 günü ({metric}): giriş R {T.R[m].sum():.1f} (n={m.sum()}, ortR {T.R[m].mean():+.2f})")
# yükseliş günü dilimleri: altın gün getirisi (ATR) dilimine göre kural günlük R
dd = day.copy(); dd["q"] = pd.cut(dd.rep_xp_day_ret_atr, [-99, -1, -0.5, 0, 0.5, 1, 2, 99])
say("Giriş günü altın getirisi (ATR_D1) dilimine göre gün R: \n" + dd.groupby("q", observed=True).R.agg(["size", "mean", "sum"]).round(2).to_string())
top30 = day["rank"] <= 30
for f in ["rep_xa_atrH1_over_D1", "rep_xa_atrH1_pct500", "rep_xa_bbw_pct120", "rep_xa_dist_52wh_atr", "rep_xa_brk_density24", "rep_xa_dist_ath_pct", "rep_xa_hour_sig", "rep_xa_ema50_slope10"]:
    a = day[f][top30].dropna(); b = day[f][~top30 & (day.rank_worst > 20)].dropna()
    u = stats.mannwhitneyu(a, b); say(f"top30 {f}: med {a.median():.3f} vs {b.median():.3f} AUC {u.statistic/(len(a)*len(b)):.3f} p {u.pvalue:.4f}")
open(os.path.join(RES, "gold_days.txt"), "w").write("\n".join(L) + "\n")
