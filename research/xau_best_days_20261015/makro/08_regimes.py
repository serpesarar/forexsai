"""Kriz/rejim pencereleri (EX-POST etiket, tarihler literatürden) — işlem günü payı vs en iyi gün payı vs R payı."""
import os, numpy as np, pandas as pd
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
W = {"GFC 2008-09→2009-06": ("2008-09-01", "2009-06-30"), "Avro/ABD not indirimi 2011-07→12": ("2011-07-01", "2011-12-31"),
     "Taper/altın çöküşü 2013-04→12": ("2013-04-01", "2013-12-31"), "COVID 2020-02-15→08": ("2020-02-15", "2020-08-31"),
     "Ukrayna 2022-02-15→04": ("2022-02-15", "2022-04-30"), "SVB 2023-03-08→05": ("2023-03-08", "2023-05-31"),
     "İsrail-Hamas 2023-10-07→11": ("2023-10-07", "2023-11-30"), "MB alımı/tarife 2024-03→2025-12": ("2024-03-01", "2025-12-31")}
tr = pd.read_csv(os.path.join(OUT, "trades_feat.csv")); days = pd.read_csv(os.path.join(OUT, "days.csv"))
t20 = set(days.head(20).ent_day); t50 = set(days.head(50).ent_day); tot = tr.R.sum(); ndays = tr.ent_day.nunique()
anyw = np.zeros(len(tr), bool); rows = []
for k, (a, b) in W.items():
    m = (tr.ent_day >= a) & (tr.ent_day <= b); anyw |= m.values; dd = set(tr[m].ent_day)
    rows.append(dict(rejim=k, islem=int(m.sum()), gun_payi=len(dd) / ndays, ortR=tr[m].R.mean(), P3=(tr[m].R >= 3).mean(),
                     R_payi=tr[m].R.sum() / tot, top20=len(dd & t20), top50=len(dd & t50)))
m = anyw; dd = set(tr[m].ent_day)
rows.append(dict(rejim="HERHANGİ kriz penceresi", islem=int(m.sum()), gun_payi=len(dd) / ndays, ortR=tr[m].R.mean(), P3=(tr[m].R >= 3).mean(),
                 R_payi=tr[m].R.sum() / tot, top20=len(dd & t20), top50=len(dd & t50)))
rows.append(dict(rejim="pencere DIŞI", islem=int((~m).sum()), gun_payi=1 - len(dd) / ndays, ortR=tr[~m].R.mean(), P3=(tr[~m].R >= 3).mean(),
                 R_payi=tr[~m].R.sum() / tot, top20=20 - len(dd & t20), top50=50 - len(dd & t50)))
R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "regimes.csv"), index=False); print(R.round(3).to_string(index=False))
# yıl bazında en iyi 50 dağılımı
print(pd.Series([d[:4] for d in t50]).value_counts().sort_index().to_dict())
