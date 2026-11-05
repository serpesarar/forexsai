import numpy as np, pandas as pd
from lab2 import *
pd.set_option("display.width", 200)
def seg(tf, h0m, h1m, a=None, b=None, sp_mult=1.0, sym="XAUUSD"):
    x = mt5_bars(sym, tf); x["d"] = x.ts_et.dt.normalize(); x["m"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute
    x = x[x.ts_et.dt.dayofweek.isin([6, 0, 1, 2, 3])]
    e = x[x.m == h0m].drop_duplicates("d").set_index("d"); 
    z = x[x.m == h1m].drop_duplicates("d").set_index("d")
    if h1m < h0m: z.index = z.index - pd.Timedelta(days=1)
    j = e.join(z, rsuffix="_x", how="inner")
    r = (j.o_x - j.sp_x * 0 ) / (j.o + sp_mult * j.sp) - 1
    r = r * 1e4 - sp_mult * 0
    if a: r = r[r.index >= a]
    if b: r = r[r.index < b]
    return r, j.sp.median(), j.sp.quantile(.9)
def pr(l, r, sp, q):
    u, inv = np.unique(r.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, r.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (2000, len(u)))
    print(f"{l:34s} n={len(r):4d} ort={r.mean():6.2f} isabet={(r>0).mean():.3f} P={((S[ix].sum(1)/N[ix].sum(1))>0).mean():.3f} y1={r.iloc[:len(r)//2].mean():5.2f} y2={r.iloc[len(r)//2:].mean():5.2f} | giriş spread med={sp:.2f} p90={q:.2f}")
print("M5 2025-06→, çıkış 22:00")
for m in (1080, 1085, 1095, 1110, 1140, 1200): pr(f"giriş {m//60}:{m%60:02d}", *seg("M5", m, 1320))
print("M15 2022-08→")
for m in (1080, 1095, 1110, 1140, 1200): pr(f"giriş {m//60}:{m%60:02d}", *seg("M15", m, 1320))
print("M30 2018→ bölü dönem, giriş 19:00")
for a, b in (("2018-05-25", "2020-01-01"), ("2020-01-01", "2022-01-01"), ("2022-01-01", "2024-01-01"), ("2024-01-01", "2025-07-01"), ("2025-07-01", "2027-01-01")): pr(f"{a[:7]}→{b[:7]}", *seg("M30", 1140, 1320, a, b))
print("Spread saat profili XAU M5 son 60 gün (ET)")
x = mt5_bars("XAUUSD", "M5"); x = x[x.ts_et >= x.ts_et.max() - pd.Timedelta(days=60)]; p = x.groupby(x.ts_et.dt.hour).sp.median().round(2); print(p.loc[[15, 16, 17, 18, 19, 20, 21, 22, 23, 2, 8]].to_dict())
print("Saatlik getiri profili XAU M15 (bp, ET, tüm dönem, bar açılış→açılış)")
y = mt5_bars("XAUUSD", "M15"); y["r"] = np.log(y.o.shift(-1) / y.o) * 1e4; y = y[(y.t.diff().shift(-1) < 1800)]
print(y.groupby(y.ts_et.dt.hour).r.sum().div(len(y.ts_et.dt.normalize().unique())).round(2).to_dict())
for s in ("NAS100", "SpotCrude"):
    print(s, "giriş 19:00→22:00 M15"); pr("", *seg("M15", 1140, 1320, sym=s))
