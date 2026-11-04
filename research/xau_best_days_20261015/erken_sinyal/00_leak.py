"""PROTOCOL §6 önek (prefix) sızıntı testi — sonuç hesaplanmaz."""
import numpy as np, pandas as pd
from common import raw_duka, prep_h1, RES
from features import raw_features, load_vix
vix = load_vix()
raw = raw_duka()
full = prep_h1(raw); F = raw_features(full, vix)
cols = ["bw_prev", "bw_q20", "F1", "F2", "d1_hh20", "d1_hh250", "F6", "F7", "clv", "F3", "vol_ratio", "F4", "F5", "F8", "mom6", "vix_prev", "F10"]
rng = np.random.default_rng(1); L = []
for cut in rng.integers(20000, len(raw) - 1000, 3):
    t = prep_h1(raw.iloc[:cut]); Ft = raw_features(t, vix)
    first_day = t.day.iloc[-1]
    keep = (t.day != first_day).to_numpy()
    a = F.iloc[:cut][keep][cols].reset_index(drop=True); b = Ft[keep][cols].reset_index(drop=True)
    bad = {}
    for c_ in cols:
        x, y = a[c_].to_numpy(), b[c_].to_numpy()
        if x.dtype == bool or y.dtype == bool:
            diff = (x.astype(bool) != y.astype(bool)).sum()
        else:
            diff = (~((np.isclose(x.astype(float), y.astype(float), equal_nan=True)))).sum()
        if diff: bad[c_] = int(diff)
    L.append(f"kesim {cut} ({t.ts.iloc[-1]}): karşılaştırılan {keep.sum()} bar, farklı: {bad or 'YOK'}")
print("\n".join(L)); open(f"{RES}/00_leak.txt", "w").write("\n".join(L) + "\n")
