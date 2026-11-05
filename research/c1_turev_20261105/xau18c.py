import numpy as np, pandas as pd
from xau18_core import seg
def show(l, tf, a, b, sym="XAUUSD"):
    r, sp, q = seg(tf, a, b, sym=sym)
    u, inv = np.unique(r.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, r.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (2000, len(u)))
    print(f"{l:22s} {sym:9s} n={len(r)} ort={r.mean():5.2f} med={r.median():5.2f} isabet={(r>0).mean():.3f} P={((S[ix].sum(1)/N[ix].sum(1))>0).mean():.3f} sp={sp:.2f}/{q:.2f}", r.groupby(r.index.year).mean().round(1).to_dict())
show("18:00→18:30", "M30", 1080, 1110); show("18:00→19:00", "M30", 1080, 1140); show("18:30→19:00", "M30", 1110, 1140); show("19:00→22:00", "M30", 1140, 1320); show("18:00→18:15", "M15", 1080, 1095); show("18:15→18:30", "M15", 1095, 1110); show("18:00→18:05", "M5", 1080, 1085); show("18:05→18:30", "M5", 1085, 1110)
for sym in ("NAS100", "SpotCrude"): show("18:00→18:30", "M30", 1080, 1110, sym)
