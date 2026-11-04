"""Her ex-ante özellik için: ortR açık/kapalı, P(R≥3), R payı, fark + gün-blok bootstrap %95 CI, iki kronolojik yarı
(2008-16 / 2017-26), rastgele-BUY'da aynı fark (fark-içinde-fark), en iyi 20/50 günde görülme oranı vs taban."""
import os, numpy as np, pandas as pd
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
tr = pd.read_csv(os.path.join(OUT, "trades_feat.csv")); rb = pd.read_csv(os.path.join(OUT, "random_feat.csv"))
days = pd.read_csv(os.path.join(OUT, "days.csv")); top20 = set(days.head(20).ent_day); top50 = set(days.head(50).ent_day)
F = [c for c in tr.columns if c.startswith("F_")]
rng = np.random.default_rng(7); B = 2000

def boot_diff(df, f):
    a = df[df[f] == True]; b = df[df[f] == False]
    def sums(x):
        g = x.groupby("ent_day").R.agg(["sum", "size"]); return g["sum"].values, g["size"].values
    sa, ka = sums(a); sb, kb = sums(b)
    if len(sa) < 5 or len(sb) < 5: return np.nan, np.nan, np.nan
    ia = rng.integers(0, len(sa), (B, len(sa))); ib = rng.integers(0, len(sb), (B, len(sb)))
    dd = sa[ia].sum(1) / ka[ia].sum(1) - sb[ib].sum(1) / kb[ib].sum(1)
    return float(dd.mean()), float(np.percentile(dd, 2.5)), float(np.percentile(dd, 97.5))

rows = []
tot = tr.R.sum(); h1 = tr.year <= 2016
for f in F:
    on = tr[f] == True
    if on.sum() < 20: continue
    dfm, lo, hi = boot_diff(tr, f)
    dh1 = tr[h1 & on].R.mean() - tr[h1 & ~on].R.mean(); dh2 = tr[~h1 & on].R.mean() - tr[~h1 & ~on].R.mean()
    ron = rb[f] == True
    rdiff = rb[ron].R.mean() - rb[~ron].R.mean()
    tdays = tr[on].ent_day.unique()
    rows.append(dict(feat=f, n_on=int(on.sum()), pct_on=on.mean(), R_on=tr[on].R.mean(), R_off=tr[~on].R.mean(),
                     diff=tr[on].R.mean() - tr[~on].R.mean(), ci_lo=lo, ci_hi=hi,
                     P3_on=(tr[on].R >= 3).mean(), P3_off=(tr[~on].R >= 3).mean(),
                     Rshare_on=tr[on].R.sum() / tot, d_0816=dh1, d_1726=dh2,
                     rnd_on=rb[ron].R.mean(), rnd_diff=rdiff, did=(tr[on].R.mean() - tr[~on].R.mean()) - rdiff,
                     top20_hit=len(set(tdays) & top20) / 20, top50_hit=len(set(tdays) & top50) / 50,
                     base_dayrate=len(tdays) / tr.ent_day.nunique()))
res = pd.DataFrame(rows); res.to_csv(os.path.join(OUT, "feature_tests.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(res.round(3).to_string(index=False))
# genel referanslar
print("tüm işlemler ortR", round(tr.R.mean(), 4), "P(R>=3)", round((tr.R >= 3).mean(), 4), "rastgele BUY ortR", round(rb.R.mean(), 4), "P3", round((rb.R >= 3).mean(), 4))
for nm, s in [("2008-16", tr[h1]), ("2017-26", tr[~h1])]:
    print(nm, len(s), round(s.R.mean(), 4), round((s.R >= 3).mean(), 4))
