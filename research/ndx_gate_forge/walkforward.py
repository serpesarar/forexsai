"""Gün-düzeyi koşullar: SEÇİM yalnız 2016-2020 (1h, 2 saatlik z), TEST 2021-2026 işlem düzeyi."""
import numpy as np, pandas as pd
from macro10y import build, CONDS
from common import block_boot, OUT
import daylevel_trades as dt

d = build()
tr = d[d.year <= 2020]
sel = []
for name, (fn, sgn) in CONDS.items():
    m = fn(tr).fillna(False).to_numpy(bool)
    x = tr[m]
    if x.nyd.nunique() < 15:
        continue
    bs = block_boot(x.y.to_numpy(), x.nyd.astype(str).to_numpy(), 3000)
    p = float(np.mean(np.sign(bs) == sgn))
    sel.append({"koşul": name, "yön": sgn, "gün_16_20": x.nyd.nunique(), "etki_16_20": x.y.mean() * 100, "P_16_20": p})
S = pd.DataFrame(sel)
S["seçildi"] = S.P_16_20 >= 0.90
# OOS: 2021+ işlem düzeyi (30m) + 1h z2
T30 = dt.long_trades("30m"); T30 = T30[T30.nyd.dt.year >= 2021].reset_index(drop=True)
T1 = dt.m1_trades()
def oos(T, name, sgn):
    x = dt.day_conditions(T.nyd, T.nyh, T.wd)
    x["tom"] = False
    # CONDS fonksiyonları macro10y sütun adlarını kullanır → eşle
    z = pd.DataFrame({"vix": x.vix, "vix_ts": x.vix_ts, "vix_chg1": x.vix_chg1, "ndx_ret1": x.ndx_ret1, "ndx_ret5": x.ndx_ret5,
                      "ndx_d200": x.ndx_d200, "mtd": x.mtd, "month_end2": x.month_end2, "wd": x.wd, "fomc_eve": x.fomc_eve})
    fn = CONDS[name][0]
    try:
        m = fn(z).fillna(False).to_numpy(bool)
    except Exception:
        return np.nan, np.nan, 0
    side = "S" if sgn > 0 else "B"
    y = T[f"R_{side}"] - T.groupby(["grp", "utc_h"])[f"R_{side}"].transform("mean")
    v = y.to_numpy()[m]; ok = ~np.isnan(v)
    if ok.sum() == 0:
        return np.nan, np.nan, 0
    bs = block_boot(v[ok], T.nyd.astype(str).to_numpy()[m][ok], 2000)
    return v[ok].mean(), float(np.mean(bs < 0)), len(np.unique(T.nyd.to_numpy()[m][ok]))
d2 = d[d.year >= 2021]
for i, r in S.iterrows():
    m = CONDS[r["koşul"]][0](d2).fillna(False).to_numpy(bool)
    S.loc[i, "z_2021+"] = d2[m].y.mean() * 100
    for lab, T in [("30m", T30), ("1m", T1)]:
        e, p, n = oos(T, r["koşul"], r["yön"])
        S.loc[i, f"R_{lab}"] = e; S.loc[i, f"P_{lab}"] = p; S.loc[i, f"gün_{lab}"] = n
S["z_doğru"] = np.sign(S["z_2021+"]) == S["yön"]
pd.set_option("display.width", 250)
print(S.round(3).sort_values(["seçildi", "P_16_20"], ascending=False).to_string(index=False))
s = S[S.seçildi]; ns = S[~S.seçildi]
print(f"\nSEÇİLEN (2016-20 P≥.90): {len(s)} koşul → 2021+ z doğru {int(s.z_doğru.sum())}/{len(s)}, 30m R<0 {int((s.R_30m<0).sum())}/{s.R_30m.notna().sum()}, 1m R<0 {int((s.R_1m<0).sum())}/{s.R_1m.notna().sum()}")
print(f"SEÇİLMEYEN: {len(ns)} → 2021+ z doğru {int(ns.z_doğru.sum())}/{len(ns)}, 30m R<0 {int((ns.R_30m<0).sum())}/{ns.R_30m.notna().sum()}")
S.to_csv(OUT / "walkforward_daylevel.csv", index=False)
