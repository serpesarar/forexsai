"""ADIM 2: gün tablosu (giriş UTC günü), sıralama, best_days.csv. Temsilci işlem = günün |R| en büyük işlemi."""
import os, sys
import numpy as np, pandas as pd
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
NOTES = "/Users/melihcanodacioglu/Desktop/panel/research_notes/XAU kırılım kuralının en iyi günleri"
T = pd.read_parquet(os.path.join(RES, "trades.parquet"))
T["absR"] = T.R.abs()
g = T.groupby("eday")
day = g.agg(R=("R", "sum"), n_tr=("R", "size"), hours=("ent_hour", lambda s: ",".join(map(str, s))),
            codes=("code", lambda s: ",".join(s)))
rep = T.loc[g.absR.idxmax()].set_index("eday")
day = day.join(rep.add_prefix("rep_"))
day = day.sort_values("R", ascending=False)
day["rank"] = np.arange(1, len(day) + 1)
day["rank_worst"] = day.R.rank(method="first").astype(int)
N = len(day); top1 = max(1, int(round(0.01 * N)))
day["grp"] = np.select([day["rank"] <= 20, day["rank"] <= 50, day["rank"] <= top1, day.rank_worst <= 20],
                       ["top20", "top21_50", "top21_50", "worst20"], "other")
day.to_parquet(os.path.join(RES, "days.parquet"))
print("gün sayısı", N, "top1% =", top1, "gün; işlem", len(T))
cols = {"rank": "rank", "R": "R_day", "n_tr": "n_trades", "hours": "entry_hours_utc", "codes": "exit_codes",
        "rep_weekday": "weekday", "rep_xa_session": "session", "rep_R": "R_main_trade", "rep_code": "exit_main",
        "rep_xp_held": "held_bars", "rep_xp_mfe_R": "mfe_R", "rep_xp_R_day0": "R_by_end_of_entry_day",
        "rep_xp_day_ret1": "gold_day_ret", "rep_xp_day_ret_atr": "gold_day_ret_atrD1", "rep_xp_day_range_atr": "day_range_atrD1",
        "rep_xp_day_fwd1": "fwd1d", "rep_xp_day_fwd3": "fwd3d", "rep_xp_day_fwd5": "fwd5d",
        "rep_xa_atrD1p_pct252": "atrD1_pct252_exante", "rep_xa_dist_ath_atr": "dist_ATH_atrD1", "rep_xa_dist_52wh_atr": "dist_52wH_atrD1",
        "rep_xa_d1_above_ema50": "d1_gt_ema50", "rep_xa_d1_above_ema200": "d1_gt_ema200", "rep_xa_ema50_slope10": "ema50_slope10_atr",
        "rep_xa_w1_above_ema20": "w1_gt_ema20", "rep_xa_ret5": "ret5d_prior", "rep_xa_ret20": "ret20d_prior", "rep_xa_gap_atr": "gap_atrD1",
        "rep_xa_bbw_pct120": "bbw_pct120", "rep_xa_rng20_atr": "range20_atrH1", "rep_xa_bars_since_prev_brk": "bars_since_prev_20hi",
        "rep_xa_pen_high_atr": "break_beyond_atrH1", "rep_xa_pen_close_atr": "close_vs_level_atrH1", "rep_xa_body_atr": "brk_body_atrH1",
        "rep_xa_vol_ratio_hour": "brk_tickvol_vs_hour_med", "rep_xa_atrH1_over_D1": "atrH1_over_atrD1", "grp": "group"}
day["in_top20"] = day["rank"] <= 20; day["in_top1pct"] = day["rank"] <= top1; day["in_top50"] = day["rank"] <= 50
cols.update({"in_top20": "in_top20", "in_top1pct": "in_top1pct_(top30)", "in_top50": "in_top50", "rank_worst": "rank_worst"})
out = day[list(cols)].rename(columns=cols)
out.insert(0, "date_utc", out.index)
sel = out[out.group.isin(["top20", "top21_50", "top1pct_rest", "worst20"])].copy()
sel = sel.sort_values(["group", "rank"], key=lambda s: s.map({"top20": 0, "top21_50": 1, "top1pct_rest": 2, "worst20": 3}) if s.name == "group" else s)
os.makedirs(NOTES, exist_ok=True)
sel.round(4).to_csv(os.path.join(NOTES, "best_days.csv"), index=False)
out.round(4).to_csv(os.path.join(RES, "all_days.csv"), index=False)
print(sel.groupby("group").size())
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(out.head(20)[["date_utc", "R_day", "n_trades", "entry_hours_utc", "exit_codes", "weekday", "R_main_trade", "mfe_R", "held_bars",
                    "gold_day_ret", "fwd1d", "fwd3d", "fwd5d", "day_range_atrD1"]].round(3).to_string())
