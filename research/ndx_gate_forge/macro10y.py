"""10 yıl (2016-05→2026-07) gün-düzeyi koşulların gün-içi yön etkisi.

Birim: Pzt–Per, bot saatleri (07–21 UTC) içindeki her saat başı giriş; çıktı = 2 saat
ileri getiri / önceki 20 günün günlük vol'ü ("z2"). Koşullar ÖNCEKİ ABD işlem gününün
kapanışından (nedensel). Fark = koşul içi ortalama − aynı yıl × aynı NY saati ortalaması.
BUY'ı bloklayan kapı iyi ise fark < 0, SELL'i bloklayan kapı iyi ise fark > 0.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, block_boot
from long_data import load_long, macro

FOMC = """2016-01-27 2016-03-16 2016-04-27 2016-06-15 2016-07-27 2016-09-21 2016-11-02 2016-12-14
2017-02-01 2017-03-15 2017-05-03 2017-06-14 2017-07-26 2017-09-20 2017-11-01 2017-12-13
2018-01-31 2018-03-21 2018-05-02 2018-06-13 2018-08-01 2018-09-26 2018-11-08 2018-12-19
2019-01-30 2019-03-20 2019-05-01 2019-06-19 2019-07-31 2019-09-18 2019-10-30 2019-12-11
2020-01-29 2020-04-29 2020-06-10 2020-07-29 2020-09-16 2020-11-05 2020-12-16
2021-01-27 2021-03-17 2021-04-28 2021-06-16 2021-07-28 2021-09-22 2021-11-03 2021-12-15
2022-01-26 2022-03-16 2022-05-04 2022-06-15 2022-07-27 2022-09-21 2022-11-02 2022-12-14
2023-02-01 2023-03-22 2023-05-03 2023-06-14 2023-07-26 2023-09-20 2023-11-01 2023-12-13
2024-01-31 2024-03-20 2024-05-01 2024-06-12 2024-07-31 2024-09-18 2024-11-07 2024-12-18
2025-01-29 2025-03-19 2025-05-07 2025-06-18 2025-07-30 2025-09-17 2025-10-29 2025-12-10
2026-01-28 2026-03-18 2026-04-29 2026-06-17""".split()


def build() -> pd.DataFrame:
    d = load_long("1h")
    ny = d.ts.dt.tz_convert("America/New_York")
    d["nyh"] = ny.dt.hour.values
    d["nyd"] = pd.to_datetime(ny.dt.date.values)
    d["wd"] = ny.dt.weekday.values
    d["year"] = ny.dt.year.values
    d["utc_h"] = d.ts.dt.hour.values
    t = d.ts.astype("int64") // 10**9
    ok = (t.shift(-1) - t) == 3600
    d["r2"] = np.where(ok, d.close.shift(-1) / d.open - 1, np.nan)
    m = macro()
    full = pd.date_range("2014-01-01", "2026-12-31")
    last = lambda s: s.dropna().reindex(full).ffill()
    prev = d.nyd - pd.Timedelta(days=1)
    ndx = m.NDXCASH_close.dropna()
    vol = ndx.pct_change().rolling(20).std()
    feats = {
        "dvol": vol, "vix": m.VIX_close, "vix_ts": m.VIX_close / m.VIX3M_close,
        "vix_chg1": m.VIX_close.dropna().pct_change(), "vix_chg5": m.VIX_close.dropna().pct_change(5),
        "ndx_ret1": ndx.pct_change(), "ndx_ret5": ndx.pct_change(5),
        "ndx_d200": ndx / ndx.rolling(200).mean() - 1, "ndx_d50": ndx / ndx.rolling(50).mean() - 1,
        "hyg_ret1": m.HYG_close.dropna().pct_change(), "tlt_ret1": m.TLT_close.dropna().pct_change(),
        "dxy_ret1": m.DXY_close.dropna().pct_change(), "us10_chg1": m.US10Y_close.dropna().diff(),
        "ndx_range1": (m.NDXCASH_high - m.NDXCASH_low) / m.NDXCASH_close,
    }
    for k, s in feats.items():
        d[k] = last(s).reindex(prev).to_numpy()
    d["z2"] = d.r2 / d.dvol
    # takvim
    days = pd.Series(sorted(d.nyd.unique()))
    mon = days.dt.to_period("M")
    pos = days.groupby(mon).cumcount()
    rev = days.groupby(mon).cumcount(ascending=False)
    d["tom"] = d.nyd.isin(set(days[(pos < 3) | (rev == 0)]))
    d["month_end2"] = d.nyd.isin(set(days[rev <= 1]))
    tf = []
    for y, mth in zip(d.nyd.dt.year, d.nyd.dt.month):
        fr = pd.date_range(f"{y}-{mth:02d}-01", periods=31, freq="D")
        tf.append(fr[(fr.month == mth) & (fr.weekday == 4)][2])
    delta = (pd.to_datetime(tf) - d.nyd).dt.days.to_numpy()
    d["opex_wk"] = (delta >= 0) & (delta <= 4)
    d["post_opex"] = (delta >= -7) & (delta <= -3)
    fomc = pd.to_datetime(FOMC)
    d["fomc_day_pre"] = d.nyd.isin(fomc) & (d.nyh < 14)
    d["fomc_eve"] = d.nyd.isin(fomc - pd.Timedelta(days=1)) & (d.nyh >= 14)
    # ay-içi getiri (emeklilik fonu yeniden dengelemesi) — bir önceki gün itibarıyla MTD
    mtd = ndx / ndx.groupby(ndx.index.to_period("M")).transform("first") - 1
    d["mtd"] = last(mtd).reindex(prev).to_numpy()
    # bot evreni
    d = d[(d.wd <= 3) & d.utc_h.between(7, 20) & d.z2.notna() & d.dvol.notna()].reset_index(drop=True)
    d["y"] = d.z2 - d.groupby(["year", "nyh"]).z2.transform("mean")
    return d


CONDS = {
    # ad: (koşul fonksiyonu, beklenen yön: +1 → yukarı sürüklenme (SELL blokla), −1 → aşağı (BUY blokla))
    "vix>=18.4 (VIXREG BUY)": (lambda d: d.vix >= 18.4, +1),
    "vix<18.4 (VIXREG SELL)": (lambda d: d.vix < 18.4, -1),
    "vix>=25": (lambda d: d.vix >= 25, +1),
    "vix<14": (lambda d: d.vix < 14, -1),
    "vix_ts>=1 (ters eğri)": (lambda d: d.vix_ts >= 1.0, +1),
    "vix_ts<=0.85 (derin contango)": (lambda d: d.vix_ts <= .85, -1),
    "vix spike +15% (dün)": (lambda d: d.vix_chg1 >= .15, +1),
    "vix düşüş −10% (dün)": (lambda d: d.vix_chg1 <= -.10, -1),
    "vix 5g +30%": (lambda d: d.vix_chg5 >= .30, +1),
    "ndx dün ≤ −1.5%": (lambda d: d.ndx_ret1 <= -.015, +1),
    "ndx dün ≥ +1.5%": (lambda d: d.ndx_ret1 >= .015, -1),
    "ndx 5g ≤ −4%": (lambda d: d.ndx_ret5 <= -.04, +1),
    "ndx 5g ≥ +4%": (lambda d: d.ndx_ret5 >= .04, -1),
    "ndx 200g altı": (lambda d: d.ndx_d200 < 0, -1),
    "ndx 200g +%10 üstü": (lambda d: d.ndx_d200 > .10, -1),
    "ndx 50g altı": (lambda d: d.ndx_d50 < 0, -1),
    "hyg dün ≤ −0.5%": (lambda d: d.hyg_ret1 <= -.005, -1),
    "hyg dün ≥ +0.5%": (lambda d: d.hyg_ret1 >= .005, +1),
    "tlt dün ≥ +1%": (lambda d: d.tlt_ret1 >= .01, -1),
    "tlt dün ≤ −1%": (lambda d: d.tlt_ret1 <= -.01, -1),
    "us10y dün +10bp": (lambda d: d.us10_chg1 >= .10, -1),
    "dxy dün ≥ +0.5%": (lambda d: d.dxy_ret1 >= .005, -1),
    "dün aralık ≥ %2.5": (lambda d: d.ndx_range1 >= .025, +1),
    "Pazartesi": (lambda d: d.wd == 0, +1),
    "Salı": (lambda d: d.wd == 1, +1),
    "Çarşamba": (lambda d: d.wd == 2, +1),
    "Perşembe": (lambda d: d.wd == 3, -1),
    "ay dönümü (son+ilk3)": (lambda d: d.tom, +1),
    "ay sonu son 2 gün & MTD ≥ +4%": (lambda d: d.month_end2 & (d.mtd >= .04), -1),
    "ay sonu son 2 gün & MTD ≤ −4%": (lambda d: d.month_end2 & (d.mtd <= -.04), +1),
    "OPEX haftası": (lambda d: d.opex_wk, +1),
    "OPEX sonrası hafta": (lambda d: d.post_opex, -1),
    "FOMC günü 14:00 öncesi": (lambda d: d.fomc_day_pre, +1),
    "FOMC arifesi 14:00 sonrası": (lambda d: d.fomc_eve, +1),
}


def evaluate(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    years = sorted(d.year.unique())
    for name, (fn, sgn) in CONDS.items():
        m = fn(d).fillna(False).to_numpy(bool)
        x = d[m]
        if x.nyd.nunique() < 20:
            continue
        per_year = x.groupby("year").y.mean()
        ny_ = x.groupby("year").nyd.nunique()
        per_year = per_year[ny_ >= 3]
        bs = block_boot(x.y.to_numpy(), x.nyd.astype(str).to_numpy(), 3000)
        rows.append({"koşul": name, "beklenen": sgn, "gün": x.nyd.nunique(), "fark×100": x.y.mean() * 100,
                     "P(beklenen yön)": float(np.mean(np.sign(bs) == sgn)),
                     "yıl doğru": int((np.sign(per_year) == sgn).sum()), "yıl": int(len(per_year)),
                     "2023+": x[x.year >= 2023].y.mean() * 100, "2016-22": x[x.year < 2023].y.mean() * 100})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    d = build()
    d.to_parquet(OUT.parent / "data" / "macro10y.parquet")
    r = evaluate(d)
    pd.set_option("display.width", 250)
    print(r.round(3).to_string())
    r.to_csv(OUT / "macro10y.csv", index=False)
