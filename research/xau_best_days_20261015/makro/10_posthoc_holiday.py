"""POST-HOC (en iyi gün listesinde tatil-sonrası günler göze çarptıktan sonra tanımlandı):
F_posthol = giriş UTC günü, bir hafta-içi ABD borsa tatilinden (S&P500 kapanışı olmayan hafta içi gün) sonraki İLK
ABD işlem günü VEYA tatilin kendisi. Tatil takvimi önceden bilinir (NYSE) → ex-ante. Mekanizma adayı: tatil saatlerinde
ATR_H1 (14 bar) sıkışır → SL dar → normal bir günlük hareket çok büyük R olur."""
import os, numpy as np, pandas as pd
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
M = pd.read_csv(os.path.join(OUT, "macro_daily.csv"), index_col=0, parse_dates=True)
spx_days = set(M.index[M.spx.notna()])
bd = pd.bdate_range("2007-06-01", "2026-10-15")
hol = [d for d in bd if d not in spx_days]
post = set()
for h in hol:
    nx = h + pd.offsets.BDay(1)
    while nx not in spx_days and nx < pd.Timestamp("2026-10-15"): nx += pd.offsets.BDay(1)
    post.add(nx); post.add(h)
print("hafta içi ABD tatili sayısı", len(hol), "örnek", [str(x.date()) for x in hol[-6:]])
rng = np.random.default_rng(5)
def test(df, nm):
    m = pd.to_datetime(df.ent_day).isin(post).values; h1 = (df.year <= 2016).values
    r = df.R.values
    out = dict(set=nm, n_on=int(m.sum()), pct_on=m.mean(), R_on=r[m].mean(), R_off=r[~m].mean(), P3_on=(r[m] >= 3).mean(), P3_off=(r[~m] >= 3).mean(),
               dR_0816=r[m & h1].mean() - r[~m & h1].mean(), dR_1726=r[m & ~h1].mean() - r[~m & ~h1].mean(),
               dP3_0816=(r[m & h1] >= 3).mean() - (r[~m & h1] >= 3).mean(), dP3_1726=(r[m & ~h1] >= 3).mean() - (r[~m & ~h1] >= 3).mean())
    g = df.assign(m=m).groupby(["m", "ent_day"]).R.agg(["sum", "size"])
    a, b = g.loc[True], g.loc[False]
    ia = rng.integers(0, len(a), (2000, len(a))); ib = rng.integers(0, len(b), (2000, len(b)))
    dd = a["sum"].values[ia].sum(1) / a["size"].values[ia].sum(1) - b["sum"].values[ib].sum(1) / b["size"].values[ib].sum(1)
    out["dR_ci"] = np.percentile(dd, [2.5, 97.5]).round(3).tolist()
    if "gvol" in df: out["gvol_on_med"] = np.nanmedian(df.gvol.values[m]); out["gvol_off_med"] = np.nanmedian(df.gvol.values[~m])
    return out
tr = pd.read_csv(os.path.join(OUT, "trades_feat.csv")); rb = pd.read_csv(os.path.join(OUT, "random_feat.csv"))
days = pd.read_csv(os.path.join(OUT, "days.csv"))
res = pd.DataFrame([test(tr, "kural"), test(rb, "rastgele BUY")]); pd.set_option("display.width", 250)
print(res.round(3).to_string(index=False))
for k in (20, 50):
    top = pd.to_datetime(days.head(k).ent_day); print(f"en iyi {k} içinde tatil/tatil-sonrası gün:", int(top.isin(post).sum()), [str(x.date()) for x in top[top.isin(post)]])
alld = pd.to_datetime(tr.ent_day.unique()); print("tüm işlem günlerinde oran", round(alld.isin(post).mean(), 3))
print("en kötü 20 içinde:", int(pd.to_datetime(days.tail(20).ent_day).isin(post).sum()))
