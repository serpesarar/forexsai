import json
from pathlib import Path
import numpy as np, pandas as pd
import vm
S = vm.nasdaq_sets()
def tom_set(dates):
    d = pd.DatetimeIndex(sorted(set(pd.to_datetime(dates))))
    return d
# işlem günü takvimi: QQQ ∪ ^NDX ∪ gün içi gün listeleri
cal = pd.DatetimeIndex(sorted(set(vm.V.ohlc("QQQ").index) | set(vm.V.ndx_frame().index)))
ym = cal.to_period("M")
tom = set()
for p in ym.unique():
    days = cal[ym == p]
    tom.add(days[-1])
    nxt = cal[ym == p + 1]
    for d in nxt[:3]: tom.add(d)
out = {}
k13 = lambda t: np.isin(t.k.values, range(13, 18))
T = lambda t: t.d.isin(tom).values
out["a_TOM"] = vm.zpool([(t, T(t)) for t in S.values()])
out["a_TOM_set"] = {nm: vm.diff(t, T(t), seed=21) for nm, t in S.items()}
# (b) TOM dışında k13-17
sets_b = []
for nm, t in S.items():
    m = ~T(t); tt = t[m].reset_index(drop=True); sets_b.append((tt, k13(tt)))
out["b_k13_17_TOM_disi"] = vm.zpool(sets_b)
out["b_set"] = {nm: vm.diff(tt, mm, seed=22) for (tt, mm), nm in zip(sets_b, S)}
sets_c = []
for nm, t in S.items():
    m = ~k13(t); tt = t[m].reset_index(drop=True); sets_c.append((tt, T(tt)))
out["c_TOM_k13_17_disi"] = vm.zpool(sets_c)
out["c_set"] = {nm: vm.diff(tt, mm, seed=23) for (tt, mm), nm in zip(sets_c, S)}
out["k13_17_icinde_TOM_payi"] = round(float(np.mean(np.concatenate([T(t)[k13(t)] for t in S.values()]))), 3)
for k, v in out.items(): print(k, v)
Path(__file__).resolve().parents[1].joinpath("results/ek1_tom.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
