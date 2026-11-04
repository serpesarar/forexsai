"""En iyi 50 / en kötü 20 gün için makro hareket tablosu: D-1 (ex-ante), D, D+1 (ex-post; işlem 20 saat tutulur).
+ P(R≥3) farkları için gün-blok bootstrap (olay penceresi, FOMC, VIX25)."""
import os, numpy as np, pandas as pd
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
tr = pd.read_csv(os.path.join(OUT, "trades_feat.csv")); M = pd.read_csv(os.path.join(OUT, "macro_daily.csv"), index_col=0, parse_dates=True)
cal = pd.read_csv(os.path.join(OUT, "calendar.csv")); days = pd.read_csv(os.path.join(OUT, "days.csv"))
M = M[M.spx.notna()]                     # yalnız ABD işlem günleri (FRED tatil satırları atılır)
def chg(s, pct):
    s2 = s.dropna(); c = (s2.pct_change() * 100) if pct else s2.diff(); return c.reindex(M.index)
P = pd.DataFrame({"dxy%": chg(M.dxy, 1), "us10y_bp": chg(M.tnx, 0) * 100, "ry10_bp": chg(M.ry10, 0) * 100,
                  "vix_chg": chg(M.vix, 0), "spx%": chg(M.spx, 1), "oil%": chg(M.oil, 1), "gcf%": chg(M.gcf, 1), "vix": M.vix})
def row_at(day, off):
    i = P.index.searchsorted(pd.Timestamp(day))
    if off == -1: i = i - 1
    elif off == +1: i = i + (1 if (i < len(P) and P.index[i] == pd.Timestamp(day)) else 0)
    return P.iloc[i] if 0 <= i < len(P) else None
L = []
for nm, sub in [("best50", days.head(50)), ("worst20", days.tail(20).iloc[::-1])]:
    for _, r in sub.iterrows():
        t = tr[tr.ent_day == r.ent_day]
        evs = cal[(cal.date >= str((pd.Timestamp(r.ent_day) - pd.Timedelta(days=1)).date())) & (cal.date <= str((pd.Timestamp(r.ent_day) + pd.Timedelta(days=1)).date()))]
        rec = dict(set=nm, rank=int(r["rank"]), day=r.ent_day, R=round(r.R, 2), n=int(r.n),
                   ent_h=",".join(pd.to_datetime(t.ent_ts).dt.strftime("%H").tolist()),
                   exit=",".join(pd.to_datetime(t.exit_ts).dt.strftime("%m-%d %H").tolist()), code=",".join(t.code),
                   gold_px=round(r.px, 1), events="; ".join(evs.event + " " + evs.date), vix_prev=round(t.vix_prev.iloc[0], 1),
                   gprev=round(t.gprev.iloc[0] * 100, 2))
        for off, tag in [(-1, "Dm1"), (0, "D"), (1, "Dp1")]:
            x = row_at(r.ent_day, off)
            if x is None: continue
            for k in ["dxy%", "us10y_bp", "ry10_bp", "vix_chg", "spx%", "oil%", "gcf%"]:
                rec[f"{tag}_{k}"] = round(float(x[k]), 2) if pd.notna(x[k]) else np.nan
        L.append(rec)
T = pd.DataFrame(L); T.to_csv(os.path.join(OUT, "topdays_macro.csv"), index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 60)
print(T[["rank", "day", "R", "ent_h", "exit", "events", "vix_prev", "gprev", "D_dxy%", "D_us10y_bp", "D_ry10_bp", "D_vix_chg", "D_spx%", "D_oil%", "D_gcf%", "Dp1_gcf%", "Dp1_spx%", "Dp1_vix_chg"]].to_string(index=False))
# ortalama makro hareket: en iyi 20/50 vs tüm işlem günleri
allr = []
for dd in tr.ent_day.unique():
    x = row_at(dd, 0); y = row_at(dd, 1)
    if x is not None and y is not None: allr.append(dict(day=dd, **{f"D_{k}": x[k] for k in ["dxy%", "us10y_bp", "ry10_bp", "vix_chg", "spx%", "gcf%"]}, **{f"Dp1_{k}": y[k] for k in ["dxy%", "us10y_bp", "ry10_bp", "vix_chg", "spx%", "gcf%"]}))
A = pd.DataFrame(allr).set_index("day")
for nm, s in [("tüm işlem günleri", A), ("en iyi 20", A.loc[A.index.isin(days.head(20).ent_day)]), ("en iyi 50", A.loc[A.index.isin(days.head(50).ent_day)]), ("en kötü 20", A.loc[A.index.isin(days.tail(20).ent_day)])]:
    print(nm, len(s), s.median().round(2).to_dict())
# P(R>=3) farkı bootstrap
rng = np.random.default_rng(3)
def p3(df, f):
    a = df[df[f] == True]; b = df[df[f] == False]
    ga = a.groupby("ent_day").R.agg(lambda r: ((r >= 3).sum(), len(r))); gb = b.groupby("ent_day").R.agg(lambda r: ((r >= 3).sum(), len(r)))
    sa = np.array([v[0] for v in ga]); ka = np.array([v[1] for v in ga]); sb = np.array([v[0] for v in gb]); kb = np.array([v[1] for v in gb])
    ia = rng.integers(0, len(sa), (2000, len(sa))); ib = rng.integers(0, len(sb), (2000, len(sb)))
    dd = sa[ia].sum(1) / ka[ia].sum(1) - sb[ib].sum(1) / kb[ib].sum(1)
    return round(sa.sum() / ka.sum() - sb.sum() / kb.sum(), 4), np.percentile(dd, [2.5, 97.5]).round(4).tolist(), int(sa.sum())
for f in ["F_evwin", "F_fomcday", "F_evday", "F_vix25", "F_vix20", "F_g20up", "F_gprev_up1", "F_ry20dn"]:
    h1 = tr.year <= 2016
    print(f, "P3 farkı", p3(tr, f), "2008-16", p3(tr[h1], f)[0], "2017-26", p3(tr[~h1], f)[0])
