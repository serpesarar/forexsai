import json, sys, numpy as np, pandas as pd
from pathlib import Path
import ox, ek3_veto as E3
V, G, KD, gn = ox.V, ox.G, ox.KD, E3.gn
NY = "America/New_York"
def lab(idx):
    w = E3.pre_days(idx, (1, 2)); f = E3.pre_days(idx, (0,))
    return w, f
def cmp(t, a_mask, b_mask):
    a, b = t[a_mask].net.values, t[b_mask].net.values
    if len(a) < 5 or len(b) < 5: return {"n": int(len(a))}
    r = np.random.default_rng(12); bs = r.choice(a, (5000, len(a))).mean(1) - r.choice(b, (5000, len(b))).mean(1)
    return {"n_a": int(len(a)), "n_b": int(len(b)), "a": round(float(a.mean()), 1), "b": round(float(b.mean()), 1), "fark": round(float(a.mean() - b.mean()), 1),
            "P_fark_eksi": round(float((bs < 0).mean()), 4)}
out = {}
q, s = V.ohlc("QQQ"), V.ohlc("SPY")
for nm, x in (("QQQ", q), ("SPY", s)):
    w, f = lab(x.index)
    dow = lambda d: pd.to_datetime(d).dt.dayofweek
    if nm == "QQQ":
        t = E3.c3b(x.c.values, x.index, w); wd = dow(t.d).isin([2, 3]).values
        out["a_C3b_QQQ"] = cmp(t, t.ic.values, wd & ~t.ic.values)
        tf = t.assign(f=t.d.isin(f)); out["b_C3b_QQQ_OPEX_cuma"] = cmp(tf, tf.f.values, ~tf.f.values & ~tf.ic.values)
    c, o, h, l, idx = x.c.values, x.o.values, x.h.values, x.l.values, x.index
    k1 = (c <= (h + l) / 2 * 0.995) & (c < o); ii = np.flatnonzero(k1[:-1])
    t = pd.DataFrame({"d": idx[ii], "net": (c[ii + 1] / c[ii] - 1) * 1e4 - 2 - V.FIN * (idx[ii + 1] - idx[ii]).days.values})
    t["ic"] = t.d.isin(w); wd = dow(t.d).isin([2, 3]).values
    out[f"a_K1_{nm}"] = cmp(t, t.ic.values, wd & ~t.ic.values)
    tf = t.assign(f=t.d.isin(f)); out[f"b_K1_{nm}_OPEX_cuma"] = cmp(tf, tf.f.values, ~tf.f.values & ~tf.ic.values)
    # KSG vekili: her gece kapanış -> ertesi açılış
    g = pd.DataFrame({"d": idx[:-1], "net": (o[1:] / c[:-1] - 1) * 1e4 - 2 - V.FIN * (idx[1:] - idx[:-1]).days.values})
    g["ic"] = g.d.isin(w); wd = dow(g.d).isin([2, 3]).values
    out[f"c_KSG_vekil_{nm}"] = cmp(g, g.ic.values, wd & ~g.ic.values)
feeds = {"DUKA_NDX": (G.ndx_bars(), 60), "MT5_NAS100": (KD.mt5_m30("NAS100"), 1800), "MT5_US500": (KD.mt5_m30("US500", "2018-06-01"), 1800),
         "MT5_US30": (KD.mt5_m30("US30"), 1800), "MT5_US2000": (KD.mt5_m30("US2000"), 1800)}
for nm, (b, stp) in feeds.items():
    k = gn.nts(b, stp)
    idx = pd.DatetimeIndex(pd.to_datetime(sorted(set(G.day_prices(b, NY, [960], stp).index))))
    w, f = lab(idx)
    k["ic"] = pd.to_datetime(k.d).isin(w); wd = pd.to_datetime(k.d).dt.dayofweek.isin([2, 3]).values
    kk = k[k.K1]; wdk = pd.to_datetime(kk.d).dt.dayofweek.isin([2, 3]).values
    out[f"a_K1_gunici_{nm}"] = cmp(kk, kk.ic.values, wdk & ~kk.ic.values)
    if nm in ("DUKA_NDX", "MT5_NAS100"):
        dp = G.day_prices(b, NY, [570, 960], stp); dd = sorted(dp.index); rows = []
        for i in range(len(dd) - 1):
            a, c_ = dd[i], dd[i + 1]
            p0, s0, p1 = dp.loc[a, "o960"], dp.loc[a, "s960"], dp.loc[c_, "o570"]
            if np.isfinite(p0) and np.isfinite(p1): rows.append({"d": pd.Timestamp(a), "net": (p1 / (p0 + s0) - 1) * 1e4 - V.FIN * (c_ - a).days})
        n_ = pd.DataFrame(rows); n_["ic"] = n_.d.isin(w); wdn = n_.d.dt.dayofweek.isin([2, 3]).values
        out[f"c_KSG_gercek_{nm}"] = cmp(n_, n_.ic.values, wdn & ~n_.ic.values)
for k_, v in out.items(): print(k_, v)
Path(__file__).resolve().parents[1].joinpath("results/ek4_veto.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
