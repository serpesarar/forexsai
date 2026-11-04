"""ADIM 3: yoğunlaşma, kümelenme, özellik karşılaştırması (etki büyüklüğü), mekanizma, altının en büyük günleriyle örtüşme."""
import os
import numpy as np, pandas as pd
from scipy import stats
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
T = pd.read_parquet(os.path.join(RES, "trades.parquet"))
A = pd.read_parquet(os.path.join(RES, "all_events.parquet"))
day = pd.read_parquet(os.path.join(RES, "days.parquet"))
D = pd.read_parquet(os.path.join(RES, "d1.parquet"))
L = []
def say(s=""):
    L.append(s); print(s)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50)

# ───────── 1. yoğunlaşma + mutabakat ─────────
say("=== 1. YOĞUNLAŞMA ===")
def conc(R, key, label):
    s = pd.Series(R).groupby(key).sum().sort_values(ascending=False)
    tot = R.sum()
    out = [f"{label}: n={len(R)} gün={len(s)} toplamR={tot:.1f} ortR={R.mean():+.4f}"]
    for k in (5, 10, 20, 30, 50):
        drop = set(s.index[:k]); keep = ~np.isin(key, list(drop))
        out.append(f"   en iyi {k:>2} gün: pay %{100*s.iloc[:k].sum()/tot:5.1f} ({s.iloc[:k].sum():.1f}R) | hariç ortR {R[keep].mean():+.4f} (n={keep.sum()})")
    for k in (20, 50):
        drop = set(s.index[-k:]); keep = ~np.isin(key, list(drop))
        out.append(f"   en kötü {k} gün: {s.iloc[-k:].sum():.1f}R | hariç ortR {R[keep].mean():+.4f}")
    return out
for x in conc(A.R.to_numpy(), A.date.to_numpy(), "TÜM OLAY (örtüşmeli, sinyal UTC günü) — eski %72 hesabı"): say(x)
for x in conc(T.R.to_numpy(), T.eday.to_numpy(), "TEK-POZİSYON (giriş UTC günü) — bu çalışmanın tanımı"): say(x)
for x in conc(T.R.to_numpy(), T.eday_ny.to_numpy(), "TEK-POZİSYON (giriş NY-17 işlem günü)"): say(x)
# işlem düzeyi: en büyük 20 işlem
r = np.sort(T.R.to_numpy())[::-1]
say(f"İşlem düzeyi: en iyi 20 işlem {r[:20].sum():.1f}R (%{100*r[:20].sum()/r.sum():.0f}); R≥5 işlem sayısı {(r>=5).sum()} toplam {r[r>=5].sum():.1f}R")
say(f"Gün başına işlem: top20 günlerde {day[day.grp=='top20'].n_tr.mean():.2f}, tüm günler {day.n_tr.mean():.2f}")
# NY-17 sıralamasıyla örtüşme
sny = pd.Series(T.R.to_numpy()).groupby(T.eday_ny.to_numpy()).sum().sort_values(ascending=False)
top_ny = set(sny.index[:20]); top_utc = list(day.index[:20])
ov = sum(1 for dte in top_utc if dte in top_ny or T[T.eday == dte].eday_ny.iloc[0] in top_ny)
say(f"UTC ilk-20 ile NY-17 ilk-20 örtüşmesi (aynı işlem): {ov}/20")
# plasebo: rastgele 20 gün çıkarılınca? (tek-poz, rastgele R dağılımında kuyruk ne kadar 'normal')
# kuyruk kalınlığı: günlük R dağılımı
dr = day.R
say(f"Günlük R: ort {dr.mean():+.3f} medyan {dr.median():+.2f} sd {dr.std():.2f} çarpıklık {stats.skew(dr):.2f}; p99={dr.quantile(.99):.2f} p1={dr.quantile(.01):.2f}")

# ───────── 2. zaman kümelenmesi ─────────
say("\n=== 2. KÜMELENME ===")
def episodes(dates, gap=14):
    ds = sorted(pd.to_datetime(dates)); ep = [[ds[0]]]
    for x in ds[1:]:
        (ep[-1].append(x) if (x - ep[-1][-1]).days <= gap else ep.append([x]))
    return ep
for grp, k in (("top20", 20), ("top50", 50)):
    dates = day.index[:k]
    ep = episodes(dates)
    yrs = pd.Series(pd.to_datetime(dates).year).value_counts().sort_index()
    say(f"{grp}: {len(ep)} ayrık epizod (≤14 gün aralık), {pd.to_datetime(dates).to_period('M').nunique()} ayrı ay; yıllar: " + " ".join(f"{y}:{c}" for y, c in yrs.items()))
    multi = [e for e in ep if len(e) > 1]
    say("   çok-günlü epizodlar: " + "; ".join(",".join(x.strftime('%Y-%m-%d') for x in e) for e in multi))
    rng = np.random.default_rng(1); sims = []
    alld = day.index.to_numpy()
    for _ in range(2000):
        sims.append(len(episodes(rng.choice(alld, k, replace=False))))
    sims = np.array(sims)
    say(f"   rastgele {k} işlem günü → epizod sayısı medyan {np.median(sims):.0f} (%5 {np.percentile(sims,5):.0f}); gözlenen {len(ep)}; P(sim ≤ gözlenen)={np.mean(sims<=len(ep)):.3f}")
# yıl dağılımı vs işlem günü dağılımı (yıllara normalize)
yd = pd.DataFrame({"y": pd.to_datetime(day.index).year, "top50": day["rank"] <= 50})
tab = yd.groupby("y").agg(gun=("top50", "size"), top50=("top50", "sum"))
tab["beklenen"] = tab.gun / tab.gun.sum() * 50
say("yıl | işlem günü | top50 | beklenen:\n" + tab.round(1).to_string())
chi = stats.chisquare(tab.top50, tab.beklenen)
say(f"   top50 yıl dağılımı ki-kare p={chi.pvalue:.3f}")
# otokorelasyon (işlem günü sırası)
x = day.sort_index().R.to_numpy()
for lag in (1, 2, 3, 5):
    rho, p = stats.spearmanr(x[:-lag], x[lag:]); say(f"   günlük R Spearman otokor lag{lag}: {rho:+.3f} (p={p:.3f})")
# takvim günleri (işlem yok = 0)
cal = day.sort_index().R.copy(); cal.index = pd.to_datetime(cal.index)
cal = cal.reindex(pd.bdate_range(cal.index.min(), cal.index.max()), fill_value=0.0)
for lag in (1, 5):
    rho, p = stats.spearmanr(cal.values[:-lag], cal.values[lag:]); say(f"   iş-günü takvimi (0 dolgulu) Spearman lag{lag}: {rho:+.3f} (p={p:.3f})")
thr = day.R.quantile(0.9); s = day.sort_index().R; big = (s >= thr).to_numpy()
nxt = np.array([big[i+1:i+6].any() for i in range(len(big)-5)])
say(f"   P(sonraki 5 işlem gününde top-%10 gün | bugün top-%10) = {nxt[big[:len(nxt)]].mean():.3f} vs koşulsuz {nxt.mean():.3f}")
# haftalık R otokor
w = T.groupby(pd.to_datetime(T.eday).dt.to_period("W")).R.sum()
w = w.reindex(pd.period_range(w.index.min(), w.index.max(), freq="W"), fill_value=0)
say(f"   haftalık R otokor lag1 {stats.spearmanr(w.values[:-1], w.values[1:])[0]:+.3f}; aylık lag1 " +
    f"{(lambda m: stats.spearmanr(m.values[:-1], m.values[1:])[0])(T.groupby(pd.to_datetime(T.eday).dt.to_period('M')).R.sum()):+.3f}")
# ay bazında R yoğunlaşması
mR = T.groupby(pd.to_datetime(T.eday).dt.to_period("M")).R.sum().sort_values(ascending=False)
say(f"   en iyi 10 ay: " + ", ".join(f"{k}:{v:.1f}" for k, v in mR.head(10).items()) + f" | toplamın %{100*mR.head(10).sum()/T.R.sum():.0f}'i ({len(mR)} ay)")

# ───────── 3. özellik karşılaştırması ─────────
say("\n=== 3. ÖZELLİKLER (temsilci işlem / gün) — grup vs 'diğer işlem günleri' ===")
feats = [c for c in day.columns if c.startswith("rep_xa_") and c not in ("rep_xa_session",)] + \
        [c for c in day.columns if c.startswith("rep_xp_")] + ["n_tr"]
day["is_asia"] = (day.rep_xa_session == "Asya").astype(float); day["is_ldn"] = (day.rep_xa_session == "Londra").astype(float)
day["is_ny"] = (day.rep_xa_session == "NY").astype(float)
day["is_fri"] = (day.rep_weekday == 4).astype(float); day["is_mon"] = (day.rep_weekday == 0).astype(float)
feats += ["is_asia", "is_ldn", "is_ny", "is_mon", "is_fri"]
def es(a, b):
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) < 3 or len(b) < 3: return [np.nan] * 6
    sp = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1)) / (len(a)+len(b)-2))
    dd = (a.mean() - b.mean()) / sp if sp > 0 else np.nan
    u = stats.mannwhitneyu(a, b, alternative="two-sided")
    auc = u.statistic / (len(a) * len(b))
    return [np.median(a), np.median(b), a.mean(), dd, auc, u.pvalue]
rows = []
top20 = day["rank"] <= 20; top50 = day["rank"] <= 50; top1 = day["rank"] <= 30; worst = day.rank_worst <= 20
mid = ~(top50 | worst)
for f in feats:
    v = day[f].astype(float).to_numpy()
    r20 = es(v[top20], v[~top20 & ~worst]); r50 = es(v[top50], v[mid]); rw = es(v[worst], v[mid])
    rows.append([f, "EX-ANTE" if "_xa_" in f or f.startswith("is_") else "EX-POST"] + r20[:2] + r20[3:] + r50[3:5] + [r50[5]] + rw[0:1] + rw[3:5] + [rw[5]])
F = pd.DataFrame(rows, columns=["özellik", "tür", "top20_med", "diğer_med", "d_top20", "AUC_top20", "p_top20", "d_top50", "AUC_top50", "p_top50",
                                "worst20_med", "d_worst20", "AUC_worst20", "p_worst20"])
F["|AUC-0.5|_top50"] = (F.AUC_top50 - 0.5).abs()
F = F.sort_values(["tür", "|AUC-0.5|_top50"], ascending=[True, False])
F.round(3).to_csv(os.path.join(RES, "feature_effects.csv"), index=False)
say(F.drop(columns=["|AUC-0.5|_top50"]).round(3).to_string(index=False))
say(f"(özellik sayısı {len(feats)}; Bonferroni α=0.05/{len(feats)}={0.05/len(feats):.4f})")
# kategorik dağılımlar
for c in ("rep_xa_session", "rep_weekday", "rep_ent_hour"):
    ct = pd.crosstab(day[c], np.select([top20, top50, worst], ["top20", "top21_50", "worst20"], "diğer"), normalize="columns").round(3)
    say(f"\n{c} dağılımı (sütun %):\n" + ct.to_string())

# ───────── 3b. ex-ante özelliklerin işlem düzeyinde dürüst sınaması ─────────
say("\n=== 3b. EX-ANTE özellikler: işlem düzeyi (tek-poz n=3664), beşli dilim ortR + iki-yarı işaret tutarlılığı ===")
xa = [c for c in T.columns if c.startswith("xa_") and c not in ("xa_session",)]
T["half"] = np.where(pd.to_datetime(T.eday) < "2017-01-01", "H1_08-16", "H2_17-26")
T["big"] = (T.R >= 5).astype(int)
rows = []
for f in xa:
    v = T[f].astype(float)
    if v.nunique() < 3:
        q = v
    else:
        q = pd.qcut(v.rank(method="first"), 5, labels=False)
    mR = T.groupby(q).R.mean(); tail = T.groupby(q).big.mean()
    h = T.groupby(["half", q]).R.mean().unstack(0)
    top_minus_bot = (mR.iloc[-1] - mR.iloc[0])
    hs = (h.iloc[-1] - h.iloc[0])
    ok = np.isfinite(v)
    auc = stats.mannwhitneyu(v[ok & (T.big == 1)], v[ok & (T.big == 0)]).statistic / ((ok & (T.big == 1)).sum() * (ok & (T.big == 0)).sum())
    rho = stats.spearmanr(v[ok], T.R[ok])[0]
    rows.append([f, len(mR), *(mR.round(3).tolist() + [np.nan] * (5 - len(mR))), round(top_minus_bot, 3),
                 round(hs.iloc[0], 3), round(hs.iloc[1], 3), round(auc, 3), round(rho, 3), *(tail.round(3).tolist()[:1] + tail.round(3).tolist()[-1:])])
Q = pd.DataFrame(rows, columns=["özellik", "k", "Q1", "Q2", "Q3", "Q4", "Q5", "Q5-Q1", "Q5-Q1_08-16", "Q5-Q1_17-26", "AUC(R≥5)", "rho(R)", "P(R≥5)_Q1", "P(R≥5)_Q5"])
Q["tutarlı"] = np.sign(Q["Q5-Q1_08-16"]) == np.sign(Q["Q5-Q1_17-26"])
Q = Q.reindex(Q["AUC(R≥5)"].sub(0.5).abs().sort_values(ascending=False).index)
Q.to_csv(os.path.join(RES, "exante_quintiles.csv"), index=False)
say(Q.to_string(index=False))
say(f"R≥5 işlem: {T.big.sum()} (%{100*T.big.mean():.1f}), toplam {T.R[T.big==1].sum():.1f}R")

# ───────── 4. mekanizma ─────────
say("\n=== 4. MEKANİZMA ===")
day["R_after_day0"] = day.rep_R - day.rep_xp_R_day0
for nm, msk in (("top20", top20), ("top50", top50), ("diğer", mid), ("worst20", worst)):
    sub = day[msk]
    say(f"{nm}: temsilci işlem R ort {sub.rep_R.mean():.2f}; giriş günü sonuna kadar biriken {sub.rep_xp_R_day0.mean():.2f}R, "
        f"sonrası {sub.R_after_day0.mean():.2f}R; R'nin giriş günü SONRASI payı (toplam) %{100*sub.R_after_day0.sum()/sub.rep_R.sum():.0f}; "
        f"TIME çıkış %{100*(sub.rep_code=='TIME').mean():.0f}; tutma medyan {sub.rep_xp_held.median():.0f} bar; "
        f"MFE ort {sub.rep_xp_mfe_R.mean():.2f}, geri-verme ort {sub.rep_xp_giveback_R.mean():.2f}; çıkış=max kapanış %{100*sub.rep_xp_exit_at_maxclose.mean():.0f}; "
        f"çıkış sonrası 20 bar ort {sub.rep_xp_post20_R.mean():+.2f}R (>0: %{100*(sub.rep_xp_post20_R>0).mean():.0f}); "
        f"vol genişleme (işlem içi TR / giriş ATR) medyan {sub.rep_xp_vol_expand.median():.2f}")
# R'nin parçalanması: R = hareket$/(1.5×ATR_H1). Büyük R: hareket mi büyük, ATR mi küçük?
T["move_atrD1"] = T.R * 1.5 * T.atr / T.xa_atrD1
T["atrH1_over_D1"] = T.xa_atrH1_over_D1
for nm, msk in (("R≥5", T.R >= 5), ("0<R<5", (T.R > 0) & (T.R < 5)), ("R≤0", T.R <= 0)):
    sub = T[msk]
    say(f"{nm} (n={len(sub)}): çıkış hareketi / ATR_D1 medyan {sub.move_atrD1.median():.2f}; ATR_H1/ATR_D1 medyan {sub.atrH1_over_D1.median():.3f}; "
        f"vol genişleme medyan {sub.xp_vol_expand.median():.2f}")
# Bayraklar (örtüşebilir)
b = pd.DataFrame(index=day.index)
b["sıkışma→genişleme"] = (day.rep_xa_bbw_pct120 <= 0.2) & (day.rep_xp_vol_expand >= 1.5)
b["sıkışma (ex-ante bbw≤%20)"] = day.rep_xa_bbw_pct120 <= 0.2
b["vol genişleme ≥1.5 (ex-post)"] = day.rep_xp_vol_expand >= 1.5
b["güçlü trend devamı (c>EMA50>EMA200, 52wH'ye ≤1 ATR_D1)"] = (day.rep_xa_d1_above_ema50 == 1) & (day.rep_xa_ema50_gt_200 == 1) & (day.rep_xa_dist_52wh_atr >= -1)
b["ATH'de/yakın (≤1 ATR_D1)"] = day.rep_xa_dist_ath_atr >= -1
b["boşluk/şok (|gap|≥0.5 ATR_D1 veya 24s içinde ≥3 ATR_H1 gövde)"] = (day.rep_xa_gap_atr.abs() >= 0.5) | (day.rep_xa_shock24_atr >= 3)
b["çok-günlü bacak (R'nin >%50'si giriş günü sonrası)"] = (day.R_after_day0 > 0.5 * day.rep_R) & (day.rep_R > 0)
b["ilk kırılım (önceki 20-tepeden ≥20 bar sonra)"] = day.rep_xa_bars_since_prev_brk >= 20
b["yüksek vol rejimi (ATR_D1 % ≥ 252g p80)"] = day.rep_xa_atrD1p_pct252 >= 0.8
b["giriş günü altın ≥ +2 ATR_D1 (ex-post)"] = day.rep_xp_day_ret_atr >= 2
rows = []
for c in b.columns:
    rows.append([c, b[c][top20].mean(), b[c][top50].mean(), b[c][mid].mean(), b[c][worst].mean(),
                 day.loc[b[c] & top20, "R"].sum() / day.loc[top20, "R"].sum()])
M = pd.DataFrame(rows, columns=["bayrak", "top20 %", "top50 %", "diğer %", "worst20 %", "top20 R payı"])
say(M.round(3).to_string(index=False))
M.to_csv(os.path.join(RES, "mechanism_flags.csv"), index=False)
# R ağırlıklı hazır cevap: top50 R'nin kaçı 'sadece sürüklenme' — bayrak kombinasyonu
day["mech"] = np.select([b.iloc[:, 0], b.iloc[:, 5], b.iloc[:, 3]], ["sıkışma→genişleme", "şok/gap", "trend devamı"], "diğer")
say("Öncelikli tekil sınıflama (sıkışma→genişleme > şok > trend devamı > diğer) top50:\n" + day[top50].groupby("mech").R.agg(["size", "sum"]).round(1).to_string())
say("aynı sınıflama diğer günler:\n" + day[mid].groupby("mech").R.agg(["size", "mean"]).round(3).to_string())

# ───────── 5. altının en büyük yükseliş günleri ─────────
say("\n=== 5. ALTININ EN BÜYÜK GÜNLERİ ===")
DD = D.copy(); DD.index = pd.to_datetime(DD.index)
DD = DD[(DD.index >= "2008-02-01") & (DD.index < "2026-06-17")]
ent_ts = pd.to_datetime(T.ent_ts).dt.tz_convert(None)
xi_ts = ent_ts + pd.to_timedelta(T.xp_held, unit="h")  # yaklaşık (seg içi ardışık)
T["tday"] = pd.to_datetime(T.tday)
dayR = T.groupby("tday").R.sum()
for metric in ("ret1", "ret_atr"):
    top = DD[metric].nlargest(50)
    rec = []
    for dt in top.index:
        entered = dt in dayR.index
        st, en = dt, dt + pd.Timedelta(days=1)
        openmask = (ent_ts < en) & (xi_ts >= st)
        rec.append([dt.date(), DD.loc[dt, metric], entered, dayR.get(dt, np.nan), openmask.any(), T.R[openmask].sum()])
    G = pd.DataFrame(rec, columns=["gün", metric, "o gün giriş", "giriş R", "açık poz. var", "o gün açık işlemlerin R"])
    say(f"Altının en iyi 50 günü ({metric}): o gün giriş {G['o gün giriş'].mean():.0%}, o gün açık pozisyon {G['açık poz. var'].mean():.0%}; "
        f"giriş olan günlerde giriş R ort {G['giriş R'].mean():.2f} (medyan {G['giriş R'].median():.2f}); toplam giriş R {G['giriş R'].sum():.1f}; "
        f"açık işlemlerin toplam R {G['o gün açık işlemlerin R'].sum():.1f}")
    G.to_csv(os.path.join(RES, f"gold_top50_{metric}.csv"), index=False)
    say(G.head(15).round(3).to_string(index=False))
# ters yön: top20 kural günlerinin altın-gün sırası
DD["rk_ret"] = DD.ret1.rank(ascending=False); DD["rk_atr"] = DD.ret_atr.rank(ascending=False)
n_days = len(DD)
tdays = T.groupby("eday").tday.first()
rk = []
for i, dte in enumerate(day.index[:50]):
    td = tdays[dte]
    rk.append([dte, day.R.iloc[i], DD.rk_ret.get(td, np.nan), DD.rk_atr.get(td, np.nan),
               DD.rk_ret.get(td + pd.offsets.BDay(1), np.nan)])
RK = pd.DataFrame(rk, columns=["gün", "R", "altın %getiri sırası", "altın ATR-getiri sırası", "ertesi gün % sırası"])
say(f"top20 kural günlerinden altının en iyi 50 (%getiri) gününe giren: {(RK['altın %getiri sırası'][:20] <= 50).sum()}/20; en iyi 1% ({int(n_days*0.01)}) : {(RK['altın %getiri sırası'][:20] <= n_days*0.01).sum()}/20; "
    f"ATR-getiri top50: {(RK['altın ATR-getiri sırası'][:20] <= 50).sum()}/20; ilk %10: {(RK['altın %getiri sırası'][:20] <= n_days*0.1).sum()}/20; medyan sıra {RK['altın %getiri sırası'][:20].median():.0f}/{n_days}")
say(f"top50 kural günleri: altın top50'de {(RK['altın %getiri sırası'] <= 50).sum()}/50, ilk %10'da {(RK['altın %getiri sırası'] <= n_days*0.1).sum()}/50")
say(RK.head(20).to_string(index=False))
# korelasyon: işlem günlerinde gün R ↔ altın gün getirisi / sonraki gün
j = day[["R", "rep_xp_day_ret_atr", "rep_xp_day_fwd1"]].dropna()
say(f"Spearman(gün R, altın giriş-günü ATR-getirisi) = {stats.spearmanr(j.R, j.rep_xp_day_ret_atr)[0]:.3f}; (gün R, ertesi gün getirisi) = {stats.spearmanr(j.R, j.rep_xp_day_fwd1)[0]:.3f}")
open(os.path.join(RES, "analysis.txt"), "w").write("\n".join(L) + "\n")
