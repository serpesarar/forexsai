"""Taban A istatistiği: hedef pencere − aynı gün diğer başlangıç saatlerinin ortalaması (brüt), ay-blok bootstrap."""
import json, numpy as np, pandas as pd
from engine import *  # noqa
from long_data import macro as load_macro
MAC = load_macro(); ET = "America/New_York"
b = load_bars("ndx1h"); b = b[b.ts < pd.Timestamp(DISC_END, tz="UTC")].reset_index(drop=True)
px = Px(b, True)
base = build_events(b, Win("U", ET, (0, 1, 0), (0, 4, 0)), (16, 0), True, MAC, ARR_USD)
BAD = {2, 16, 17}   # 15s pencere 02:00 başlangıcı 17:00'de biter (bar yok/kopya) — dışarıda
out = {}
for L, tgt in [(3, 1), (1, 2), (15, -6)]:
    D = pd.DatetimeIndex(base.index)
    R = {}
    for k in range(-6, 14):
        if L == 15 and (k % 24) == 2:
            continue
        naive = D + pd.Timedelta(hours=k)
        te = pd.DatetimeIndex(naive).tz_localize(ET, ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None).values
        tx = (pd.to_datetime(te) + pd.Timedelta(hours=L)).values
        R[k] = pd.Series(px.get(tx) / px.get(te) - 1, index=D)
    M = pd.DataFrame(R)
    oth = M.drop(columns=[tgt]).mean(axis=1, skipna=True)
    diff = (M[tgt] - oth).dropna() * 1e4
    for cn, c in [("hepsi", ""), ("dn0.5", "dn0.5"), ("dn1.0", "dn1.0"), ("vix", "vix"), ("dn0.5vix", "dn0.5vix")]:
        idx = apply_cond(base, c).index
        x = diff.reindex(idx).dropna().to_frame("R")
        P = month_boot(x)
        e1 = x[x.index.year <= 2020].R.mean(); e2 = x[x.index.year >= 2021].R.mean()
        print(f"L={L:2d} hedef {tgt%24:02d}:00 koşul={cn:9s} n={len(x):4d} fark={x.R.mean():+6.2f} bp  P(>0)={P:.3f}  çağ1 {e1:+.2f} çağ2 {e2:+.2f}")
        out[f"L{L}_{cn}"] = dict(n=len(x), diff_bp=x.R.mean(), P=P, e1=e1, e2=e2)
json.dump(out, open("results/base_diff.json", "w"), indent=1, default=float)
