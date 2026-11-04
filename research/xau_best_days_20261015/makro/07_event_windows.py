"""Olay-türü bazında 'yayın anı tutma penceresinde' (ex-ante): ortR, P(R≥3), rastgele-BUY karşılığı, yarılar."""
import os, numpy as np, pandas as pd
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
cal = pd.read_csv(os.path.join(OUT, "calendar.csv"))
def win(x, ev):
    t = np.sort(pd.to_datetime(cal[cal.event == ev].ts_utc, utc=True).dt.tz_localize(None).values.astype("datetime64[ns]"))
    e = pd.to_datetime(x.ent_ts).values.astype("datetime64[ns]")
    j = np.searchsorted(t, e); nx = t[np.clip(j, 0, len(t) - 1)]
    return (j < len(t)) & ((nx - e) < np.timedelta64(20, "h")) & ((nx - e) >= np.timedelta64(0, "h"))
rng = np.random.default_rng(11)
def bd(df, m):
    g = df.assign(m=m, t3=(df.R >= 3)).groupby(["m", "ent_day"]).agg(s=("R", "sum"), k=("R", "size"), t=("t3", "sum"))
    out = {}
    for v in [True, False]:
        g2 = g.loc[v]; out[v] = (g2.s.values, g2.k.values, g2.t.values)
    (sa, ka, ta), (sb, kb, tb) = out[True], out[False]
    ia = rng.integers(0, len(sa), (2000, len(sa))); ib = rng.integers(0, len(sb), (2000, len(sb)))
    dR = sa[ia].sum(1) / ka[ia].sum(1) - sb[ib].sum(1) / kb[ib].sum(1); dT = ta[ia].sum(1) / ka[ia].sum(1) - tb[ib].sum(1) / kb[ib].sum(1)
    return np.percentile(dR, [2.5, 97.5]).round(3).tolist(), np.percentile(dT, [2.5, 97.5]).round(3).tolist()
tr = pd.read_csv(os.path.join(OUT, "trades_feat.csv")); rb = pd.read_csv(os.path.join(OUT, "random_feat.csv"))
for ev in ["FOMC", "CPI", "NFP", "JH"]:
    m = win(tr, ev); mr = win(rb, ev); h1 = (tr.year <= 2016).values
    ciR, ciT = bd(tr, m)
    print(f"{ev:5} n={m.sum():4} ortR {tr.R[m].mean():+.3f} vs {tr.R[~m].mean():+.3f} CI_fark {ciR} | P3 {(tr.R[m]>=3).mean():.3f} vs {(tr.R[~m]>=3).mean():.3f} CI_fark {ciT}"
          f" | yarı farkı ortR {tr.R[m&h1].mean()-tr.R[~m&h1].mean():+.3f}/{tr.R[m&~h1].mean()-tr.R[~m&~h1].mean():+.3f}"
          f" P3 {(tr.R[m&h1]>=3).mean()-(tr.R[~m&h1]>=3).mean():+.3f}/{(tr.R[m&~h1]>=3).mean()-(tr.R[~m&~h1]>=3).mean():+.3f}"
          f" | rastgele BUY n={mr.sum()} ortR {rb.R[mr].mean():+.3f} vs {rb.R[~mr].mean():+.3f} P3 {(rb.R[mr]>=3).mean():.3f} vs {(rb.R[~mr]>=3).mean():.3f}")
