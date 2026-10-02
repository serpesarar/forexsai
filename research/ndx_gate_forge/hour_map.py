"""10 yıl saatlik: NY saati × yıl × VIX rejimi sürüklenme haritası (2 saatlik ileri getiri, vol-normalize)."""
import numpy as np, pandas as pd
from long_data import load_long, macro

d = load_long("1h")
ny = d.ts.dt.tz_convert("America/New_York")
d["nyh"] = ny.dt.hour.values
d["nyd"] = ny.dt.date.values
d["wd"] = ny.dt.weekday.values
d["year"] = ny.dt.year.values
# 2 saatlik ileri: bu saatin açılışından (h) h+1 kapanışına — ardışık saatler şartı
t = d.ts.astype("int64") // 10**9
nxt_ok = (t.shift(-1) - t) == 3600
d["r2"] = np.where(nxt_ok, d.close.shift(-1) / d.open - 1, np.nan)
d["r1"] = d.close / d.open - 1
# vol normalizasyonu: önceki 20 günün günlük getiri std'si (nedensel)
m = macro()
ndx = m.NDXCASH_close.dropna()
vol = ndx.pct_change().rolling(20).std().shift(1)
vix = m.VIX_close.dropna()
vd = pd.Series(pd.to_datetime(d.nyd))
prev = vd - pd.Timedelta(days=1)
full = pd.date_range("2014-01-01", "2026-12-31")
vol_f = vol.reindex(full).ffill(); vix_f = vix.reindex(full).ffill()
# NY 17:00 sonrası saatler ertesi işlem gününe ait ama makro yine "en son kapanış" → önceki takvim günü kapanışı güvenli
d["dvol"] = vol_f.reindex(prev).to_numpy()
d["vixp"] = vix_f.reindex(prev).to_numpy()
d["z2"] = d.r2 / d.dvol
d = d[(d.wd <= 3)]
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
piv = d.pivot_table(index="nyh", columns="year", values="z2", aggfunc="mean") * 100
piv["all"] = d.groupby("nyh").z2.mean() * 100
piv["t"] = d.groupby("nyh").z2.mean() / (d.groupby("nyh").z2.std() / np.sqrt(d.groupby("nyh").z2.count()))
piv["pos_yrs"] = (piv[[c for c in piv.columns if isinstance(c, (int, np.integer))]] > 0).sum(1)
print("2h ileri getiri / günlük vol ×100 (Pzt-Per), NY saati:")
print(piv.round(1).to_string())
for lab, cond in [("VIX<18.4", d.vixp < 18.4), ("VIX>=18.4", d.vixp >= 18.4)]:
    x = d[cond]
    g = x.groupby("nyh").z2
    out = pd.DataFrame({"mean": g.mean() * 100, "t": g.mean() / (g.std() / np.sqrt(g.count())), "n": g.count(),
                        "pos_yrs": x.pivot_table(index="nyh", columns="year", values="z2", aggfunc="mean").gt(0).sum(1),
                        "yrs": x.pivot_table(index="nyh", columns="year", values="z2", aggfunc="mean").notna().sum(1)})
    print(lab); print(out.round(2).T.to_string())
