"""Veri sağlığı: 1h günlük seri ↔ nakit makro; 1h ↔ 30m örtüşme; DAX kapsamı."""
import numpy as np, pandas as pd
from engine import ndx_1h, ndx_30m, dax_1h, macro
a = ndx_1h(); b = ndx_30m(); x = dax_1h(); m = macro()
d = a.day
print("NDX1h gün:", len(d), d.index.min().date(), d.index.max().date(), "MA200 geçerli ilk:", d.ma200.first_valid_index().date())
j = d.join(m[["NDXCASH_close", "NDXCASH_high", "NDXCASH_low"]], how="inner").loc[:"2026-07-28"]
j["ibs_cash"] = (j.NDXCASH_close - j.NDXCASH_low) / (j.NDXCASH_high - j.NDXCASH_low)
print("C/nakit oranı medyan", (j.C / j.NDXCASH_close).median().round(4), "günlük getiri korelasyonu",
      np.corrcoef(j.C.pct_change().iloc[1:], j.NDXCASH_close.pct_change().iloc[1:])[0, 1].round(4))
print("IBS korelasyonu 1h↔nakit", j[["ibs", "ibs_cash"]].corr().iat[0, 1].round(3),
      " IBS<0,2 uyumu:", ((j.ibs < .2) == (j.ibs_cash < .2)).mean().round(3))
cash_rsi = j.NDXCASH_close.diff()
up = cash_rsi.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-cash_rsi).clip(lower=0).ewm(alpha=.5, adjust=False).mean()
j["rsi_cash"] = 100 - 100 / (1 + up / dn)
print("RSI2<10 uyumu 1h↔nakit", ((j.rsi2 < 10) == (j.rsi_cash < 10)).mean().round(3), "korelasyon", j[["rsi2", "rsi_cash"]].corr().iat[0, 1].round(3))
o = a.day[["C", "rsi2", "ibs"]].join(b.day[["C", "rsi2", "ibs"]], rsuffix="_30", how="inner")
print("1h↔30m ortak gün", len(o), "C oran medyan", (o.C / o.C_30).median().round(5), "max sapma %", (100 * (o.C / o.C_30 - 1).abs().max()).round(3),
      "RSI2 korelasyon", o[["rsi2", "rsi2_30"]].corr().iat[0, 1].round(3), "IBS korelasyon", o[["ibs", "ibs_30"]].corr().iat[0, 1].round(3))
print("30m gün:", len(b.day), b.day.index.min().date(), b.day.index.max().date())
print("DAX gün:", len(x.day), x.day.index.min().date(), x.day.index.max().date(), "MA200 ilk", x.day.ma200.first_valid_index().date())
# giriş barı gecikmesi
for mk in (a, b, x):
    dd = mk.day; ei = dd.ci.to_numpy() + 1; ei = ei[ei < len(mk.bars)]
    ts = mk.bars.ts.reset_index(drop=True); gap = ((ts.iloc[ei].reset_index(drop=True) - ts.iloc[ei - 1].reset_index(drop=True)).dt.total_seconds() / 60).to_numpy()
    print(mk.name, "kapanış barı→sonraki bar dk dağılımı", pd.Series(gap).value_counts().head(4).to_dict())
