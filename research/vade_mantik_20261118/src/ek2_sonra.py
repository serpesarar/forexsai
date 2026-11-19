import json
from pathlib import Path
import numpy as np, pandas as pd
import vm
S = vm.nasdaq_sets()
def days_since(idx, ex):
    pos = np.array([idx.get_loc(e) for e in ex]); i = np.arange(len(idx))
    j = np.searchsorted(pos, i, side="right") - 1
    return np.where(j >= 0, i - pos[np.maximum(j, 0)], -1)
cal = pd.DatetimeIndex(sorted(set(vm.V.ohlc("QQQ").index) | set(vm.V.ndx_frame().index)))
ex = vm.expiries(cal, "fri3"); A = pd.Series(days_since(cal, ex), index=cal)
ym = cal.to_period("M"); tom = set()
for p in ym.unique():
    days = cal[ym == p]; tom.add(days[-1])
    for d in cal[ym == p + 1][:3]: tom.add(d)
for t in S.values():
    t["a"] = A.reindex(pd.to_datetime(t.d)).values
B = (("a1_2", range(1, 3)), ("a3_7", range(3, 8)), ("a8_12", range(8, 13)), ("a13_17", range(13, 18)), ("a18p", range(18, 40)))
out = {}
for bn, rg in B:
    m = lambda t: np.isin(t.a, list(rg))
    out[bn] = {"havuz": vm.zpool([(t, m(t)) for t in S.values()]), "set": {nm: vm.diff(t, m(t), seed=31) for nm, t in S.items()}}
# birincil a3_7 ek ölçümler
m = lambda t: np.isin(t.a, list(range(3, 8)))
halves = []
for half in (0, 1):
    sets = []
    for t in S.values():
        tt = t.sort_values("d").reset_index(drop=True); cut = tt.d.iloc[len(tt) // 2]
        sel = (tt.d < cut) if half == 0 else (tt.d >= cut); u = tt[sel].reset_index(drop=True); sets.append((u, m(u)))
    halves.append(vm.zpool(sets))
out["a3_7_yarilar"] = halves
sets = []
for t in S.values():
    u = t[~t.d.isin(tom)].reset_index(drop=True); sets.append((u, m(u)))
out["a3_7_TOM_disi"] = vm.zpool(sets)
for k, v in out.items(): print(k, json.dumps(v, ensure_ascii=False) if not isinstance(v, dict) or "havuz" not in v else {"havuz": v["havuz"], **{nm: (x.get("n"), x.get("fark")) for nm, x in v["set"].items()}})
Path(__file__).resolve().parents[1].joinpath("results/ek2_sonra.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
