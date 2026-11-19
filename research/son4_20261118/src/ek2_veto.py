import json, sys, numpy as np, pandas as pd
from pathlib import Path
import ox, vs
V = ox.V
def opex_window_days(idx):
    ox_days = ox.opex_days(idx); pos = {d: i for i, d in enumerate(idx)}; w = set()
    for f in ox_days:
        i = pos[f]; w.add(f)
        if i >= 1: w.add(idx[i - 1])
    return w
def c3b_trades(c, idx, w):
    r2 = V.rsi2(pd.Series(c, index=idx)).values; rows = []; i = 0
    while i < len(c) - 1:
        if r2[i] < 10:
            j = i + 1
            while j < min(i + 5, len(c) - 1) and not c[j] > c[j - 1]: j += 1
            held = set(idx[i + 1:j + 1])
            rows.append({"d": idx[i], "net": (c[j] / c[i] - 1) * 1e4 - 2 - V.FIN * (idx[j] - idx[i]).days, "ic": bool(held & w)}); i = j; continue
        i += 1
    return pd.DataFrame(rows)
def k1_trades(x, w, es=False):
    c, o, h, l, idx = x.c.values, x.o.values, x.h.values, x.l.values, x.index
    k1 = (c <= (h + l) / 2 * 0.995) & (c < o); ii = np.flatnonzero(k1[:-1])
    if es: net = (c[ii + 1] / o[ii + 1] - 1) * 1e4 - 2
    else: net = (c[ii + 1] / c[ii] - 1) * 1e4 - 2 - V.FIN * (idx[ii + 1] - idx[ii]).days.values
    return pd.DataFrame({"d": idx[ii], "net": net, "ic": [idx[i + 1] in w for i in ii]})
out = {}; sets = {}
q = V.ohlc("QQQ"); s = V.ohlc("SPY"); nd = V.ndx_frame()
wq, ws, wn = opex_window_days(q.index), opex_window_days(s.index), opex_window_days(nd.index)
sets["C3b_QQQ"] = c3b_trades(q.c.values, q.index, wq)
n = nd[(nd.index >= "1985-10-01") & (nd.index <= "1999-02-28")]
sets["C3b_NDX_1985_1999"] = c3b_trades(n.c.values, n.index, wn)
sets["K1_QQQ"] = k1_trades(q, wq); sets["K1_SPY"] = k1_trades(s, ws); sets["ES_QQQ"] = k1_trades(q, wq, es=True)
pool = []
for k, t in sets.items():
    a, b = t[t.ic].net.values, t[~t.ic].net.values
    r = np.random.default_rng(3); bs = r.choice(a, (5000, len(a))).mean(1) - r.choice(b, (5000, len(b))).mean(1)
    yr = t[t.ic].groupby(t[t.ic].d.dt.year).net.mean()
    son5 = t[t.d >= "2021-11-01"]
    out[k] = {"n_ic": int(len(a)), "n_dis": int(len(b)), "ic": round(float(a.mean()), 1), "dis": round(float(b.mean()), 1),
              "fark": round(float(a.mean() - b.mean()), 1), "P_fark_eksi": round(float((bs < 0).mean()), 4),
              "son5_ic_dis": [round(float(son5[son5.ic].net.mean()), 1), round(float(son5[~son5.ic].net.mean()), 1), int(son5.ic.sum())]}
    pool.append(t.assign(set=k, z=(t.net - t.net.mean()) / t.net.std()))
p = pd.concat(pool); a, b = p[p.ic].z.values, p[~p.ic].z.values
r = np.random.default_rng(4); bs = r.choice(a, (5000, len(a))).mean(1) - r.choice(b, (5000, len(b))).mean(1)
out["havuz_z"] = {"n_ic": int(len(a)), "fark_z": round(float(a.mean() - b.mean()), 3), "P_fark_eksi": round(float((bs < 0).mean()), 4)}
for k, v in out.items(): print(k, v)
Path(__file__).resolve().parents[1].joinpath("results/ek2_veto.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
