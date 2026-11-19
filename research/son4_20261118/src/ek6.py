import json, numpy as np, pandas as pd
from pathlib import Path
import ox, ek3_veto as E3, ek5 as E5
V = ox.V
R = ox.ROOT
out = {"a_kitap": {}, "b_haftalik": {}}
t = pd.read_parquet(R / "research/ndx_10y_1m_20261116/results/a_trades.parquet")
t["d"] = pd.to_datetime(t.d)
idx = pd.DatetimeIndex(sorted(set(V.ndx_frame().index)))
win = E3.pre_days(idx, (0, 1, 2))
unit = {"C3B": "net_bp", "C3": "net_bp", "CAPREV": "R", "ORBVIX": "R", "ORBVIX_LO": "R", "CEKIC": "R", "KSG": "net_bp",
        "AYSONU_SON": "net_bp", "AYSONU_E2": "net_bp", "FOMC_GECE": "net_bp"}
r = np.random.default_rng(41)
def cmp(a, b):
    if len(a) < 5 or len(b) < 5: return {"n": int(len(a))}
    bs = r.choice(a, (5000, len(a))).mean(1) - r.choice(b, (5000, len(b))).mean(1)
    return {"n_a": int(len(a)), "n_b": int(len(b)), "a": round(float(a.mean()), 3), "b": round(float(b.mean()), 3), "fark": round(float(a.mean() - b.mean()), 3),
            "P_fark_eksi": round(float((bs < 0).mean()), 4)}
for rule, g in t.groupby("rule"):
    col = unit[rule]; wd = g.d.dt.dayofweek.isin([2, 3, 4]).values; ic = g.d.isin(win).values
    rec = {"tum": cmp(g[ic][col].values, g[wd & ~ic][col].values)}
    for e, a_, b_ in (("ESKI", "2018-01-01", "2021-10-31"), ("YENI", "2021-11-01", "2026-12-31")):
        m = ((g.d >= a_) & (g.d <= b_)).values
        rec[e] = cmp(g[ic & m][col].values, g[wd & ~ic & m][col].values)
    rec["birim"] = col
    out["a_kitap"][rule] = rec
    print("KITAP", rule, rec)
for nm in ("QQQ", "SPY"):
    x = V.ohlc(nm); veto = E3.pre_days(x.index, (0, 1, 2))
    tr = {"K1": E5.k1_daily(x), "C3b": E3.c3b(x.c.values, x.index, veto)}
    for rn, z in tr.items():
        z = z[~z.d.isin(veto)]
        dw = z.d.dt.dayofweek
        rec = {}
        for e, a_, b_ in (("1993_2004", "1993-01-01", "2004-12-31"), ("2005_2022", "2005-01-01", "2022-10-31"), ("2022_sonrasi", "2022-11-01", "2026-12-31")):
            m = ((z.d >= a_) & (z.d <= b_)).values
            rec[e] = cmp(z[m & (dw == 3).values].net.values, z[m & dw.isin([0, 1, 2]).values].net.values)
        out["b_haftalik"][f"{nm}_{rn}"] = rec
        print("HAFTALIK", nm, rn, rec)
Path(__file__).resolve().parents[1].joinpath("results/ek6.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
