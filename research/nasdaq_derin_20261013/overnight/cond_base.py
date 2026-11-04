"""Taban A — koşullu stratejiler için 'aynı günlerde, aynı uzunlukta, her başlangıç saati' (PROTOCOL §4)."""
import json, numpy as np, pandas as pd
from engine import *  # noqa
from long_data import macro as load_macro
MAC = load_macro(); ET = "America/New_York"
b = load_bars("ndx1h"); b = b[b.ts < pd.Timestamp(DISC_END, tz="UTC")].reset_index(drop=True)
px = Px(b, True)
base = build_events(b, Win("U", ET, (0, 1, 0), (0, 4, 0)), (16, 0), True, MAC, ARR_USD)  # tüm D + r_prev/vix
conds = {"hepsi": "", "dn0.5": "dn0.5", "dn1.0": "dn1.0", "vix": "vix", "dn0.5vix": "dn0.5vix"}
out = {}
for L, tgt in [(3, 1), (15, -6)]:
    for cn, c in conds.items():
        D = pd.DatetimeIndex(apply_cond(base, c).index)
        res = {}
        for k in range(-6, 14):
            naive = D + pd.Timedelta(hours=k)
            te = pd.DatetimeIndex(naive).tz_localize(ET, ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None).values
            tx = (pd.to_datetime(te) + pd.Timedelta(hours=L)).values
            r = pd.Series(px.get(tx) / px.get(te) - 1, index=D).dropna()
            res[k] = dict(n=len(r), bp=r.mean() * 1e4, t=r.mean() / r.std() * np.sqrt(len(r)),
                          bp1620=r[r.index.year <= 2020].mean() * 1e4, bp2126=r[r.index.year >= 2021].mean() * 1e4)
        t = pd.DataFrame(res).T
        t.index = [f"{(k % 24):02d}:00" for k in t.index]
        tg = f"{tgt % 24:02d}:00"
        rank = int((t.bp > t.loc[tg, "bp"]).sum()) + 1
        hold = base.loc[D].ret_gross.mean() * 1e4 if False else np.nan
        print(f"\n=== L={L}s koşul={cn} (n gün={len(D)}): hedef {tg} {t.loc[tg,'bp']:.2f} bp, sıra {rank}/{len(t)}, diğerleri ort {t.drop(tg).bp.mean():.2f} bp"
              f" | çağ1 hedef {t.loc[tg,'bp1620']:.2f} vs diğer {t.drop(tg).bp1620.mean():.2f} | çağ2 hedef {t.loc[tg,'bp2126']:.2f} vs diğer {t.drop(tg).bp2126.mean():.2f}")
        print(t[["n", "bp", "t", "bp1620", "bp2126"]].round(2).T.to_string())
        out[f"L{L}_{cn}"] = dict(rank=rank, of=len(t), target=t.loc[tg, "bp"], others=t.drop(tg).bp.mean(),
                                 tgt1620=t.loc[tg, "bp1620"], oth1620=t.drop(tg).bp1620.mean(),
                                 tgt2126=t.loc[tg, "bp2126"], oth2126=t.drop(tg).bp2126.mean())
json.dump(out, open("results/cond_baseA.json", "w"), indent=1, default=float)
