import json, sys, numpy as np, pandas as pd
from pathlib import Path
import ox
V, G, KD = ox.V, ox.G, ox.KD
R = ox.ROOT
sys.path.insert(0, str(R / "research/korku_genislik_20261118/src"))
import gn
def pre_days(idx, offs):
    ox_days = ox.opex_days(idx); pos = {d: i for i, d in enumerate(idx)}; w = set()
    for f in ox_days:
        i = pos[f]
        for o in offs:
            if i - o >= 0: w.add(idx[i - o])
    return w
def c3b(c, idx, w):
    r2 = V.rsi2(pd.Series(c, index=idx)).values; rows = []; i = 0
    while i < len(c) - 1:
        if r2[i] < 10:
            j = i + 1
            while j < min(i + 5, len(c) - 1) and not c[j] > c[j - 1]: j += 1
            rows.append({"d": idx[i], "net": (c[j] / c[i] - 1) * 1e4 - 2 - V.FIN * (idx[j] - idx[i]).days, "ic": idx[i] in w}); i = j; continue
        i += 1
    return pd.DataFrame(rows)
def st(t):
    a, b = t[t.ic].net.values, t[~t.ic].net.values
    r = np.random.default_rng(8); bs = r.choice(a, (5000, len(a))).mean(1) - r.choice(b, (5000, len(b))).mean(1)
    return {"n_ic": int(len(a)), "ic": round(float(a.mean()), 1), "dis": round(float(b.mean()), 1), "fark": round(float(a.mean() - b.mean()), 1),
            "P_fark_eksi": round(float((bs < 0).mean()), 4)}
out = {}
q = V.ohlc("QQQ"); nd = V.ndx_frame(); n = nd[(nd.index >= "1985-10-01") & (nd.index <= "1999-02-28")]
out["C3b_QQQ_exante"] = st(c3b(q.c.values, q.index, pre_days(q.index, (1, 2))))
out["C3b_QQQ_exante_son5"] = st(c3b(q.c.values, q.index, pre_days(q.index, (1, 2))).query("d >= '2021-11-01'"))
out["C3b_NDX_1985_1999_exante"] = st(c3b(n.c.values, n.index, pre_days(nd.index, (1, 2))))
feeds = {"DUKA_NDX": (G.ndx_bars(), 60), "MT5_NAS100": (KD.mt5_m30("NAS100"), 1800), "MT5_US500": (KD.mt5_m30("US500", "2018-06-01"), 1800),
         "MT5_US30": (KD.mt5_m30("US30"), 1800), "MT5_US2000": (KD.mt5_m30("US2000"), 1800)}
pool = []
for nm, (b, stp) in feeds.items():
    k = gn.nts(b, stp); k = k[k.K1].reset_index(drop=True)
    idx = pd.DatetimeIndex(pd.to_datetime(sorted(set(G.day_prices(b, "America/New_York", [960], stp).index))))
    w = pre_days(idx, (1, 2))  # giriş günü OPEX Çar/Per → ertesi gün Per/Cum
    k["ic"] = pd.to_datetime(k.d).isin(w)
    out[f"K1_gunici_{nm}"] = st(k)
    pool.append(k.assign(z=(k.net - k.net.mean()) / k.net.std()))
p = pd.concat(pool); a, b = p[p.ic].z.values, p[~p.ic].z.values
r = np.random.default_rng(9); bs = r.choice(a, (5000, len(a))).mean(1) - r.choice(b, (5000, len(b))).mean(1)
out["K1_gunici_havuz_z"] = {"n_ic": int(len(a)), "fark_z": round(float(a.mean() - b.mean()), 3), "P_fark_eksi": round(float((bs < 0).mean()), 4)}
for k_, v in out.items(): print(k_, v)
Path(__file__).resolve().parents[1].joinpath("results/ek3_veto.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
