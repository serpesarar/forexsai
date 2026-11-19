import json, numpy as np, pandas as pd
from pathlib import Path
import ox, ek3_veto as E3
V, G, KD, gn = ox.V, ox.G, ox.KD, E3.gn
NY = "America/New_York"
def wins(idx):
    veto = E3.pre_days(idx, (0, 1, 2))
    ox_days = sorted(ox.opex_days(idx)); pos = {d: i for i, d in enumerate(idx)}; post = set()
    for f in ox_days:
        i = pos[f]
        for o in (1, 2):
            if i + o < len(idx): post.add(idx[i + o])
    return veto, post
def k1_daily(x):
    c, o, h, l, idx = x.c.values, x.o.values, x.h.values, x.l.values, x.index
    k1 = (c <= (h + l) / 2 * 0.995) & (c < o); ii = np.flatnonzero(k1[:-1])
    return pd.DataFrame({"d": idx[ii], "net": (c[ii + 1] / c[ii] - 1) * 1e4 - 2 - V.FIN * (idx[ii + 1] - idx[ii]).days.values,
                         "sp15": np.full(len(ii), 1.0)})
sets = {}
q, s = V.ohlc("QQQ"), V.ohlc("SPY")
for nm, x in (("QQQ", q), ("SPY", s)):
    veto, post = wins(x.index)
    if nm == "QQQ":
        t = E3.c3b(x.c.values, x.index, veto); sets["C3b_QQQ"] = (t.assign(veto=t.d.isin(veto), post=t.d.isin(post)), 1.0)
    t = k1_daily(x); sets[f"K1_{nm}"] = (t.assign(veto=t.d.isin(veto), post=t.d.isin(post)), 1.0)
nd = V.ndx_frame(); n = nd[(nd.index >= "1985-10-01") & (nd.index <= "1999-02-28")]
veto, post = wins(nd.index); t = E3.c3b(n.c.values, n.index, veto); sets["C3b_NDX_1985_1999"] = (t.assign(veto=t.d.isin(veto), post=t.d.isin(post)), 1.0)
feeds = {"DUKA_NDX": (G.ndx_bars(), 60), "MT5_NAS100": (KD.mt5_m30("NAS100"), 1800), "MT5_US500": (KD.mt5_m30("US500", "2018-06-01"), 1800),
         "MT5_US30": (KD.mt5_m30("US30"), 1800), "MT5_US2000": (KD.mt5_m30("US2000"), 1800)}
for nm, (b, stp) in feeds.items():
    k = gn.nts(b, stp); k = k[k.K1].reset_index(drop=True)
    idx = pd.DatetimeIndex(pd.to_datetime(sorted(set(G.day_prices(b, NY, [960], stp).index))))
    veto, post = wins(idx); d = pd.to_datetime(k.d)
    sets[f"K1gi_{nm}"] = (k.assign(d=d, veto=d.isin(veto), post=d.isin(post)), 1.0)
out = {"veto": {}, "doz_vade_sonrasi": {}}
r = np.random.default_rng(31)
allv = []
for nm, (t, _) in sets.items():
    v = t[t.veto].sort_values("d").net.values; h = len(v) // 2
    out["veto"][nm] = {"n_veto": int(len(v)), "veto_ort": round(float(v.mean()), 1), "kalan_ort": round(float(t[~t.veto].net.mean()), 1),
                       "yarilar": [round(float(v[:h].mean()), 1), round(float(v[h:].mean()), 1)], "P_EV_eksi": round(float((r.choice(v, (5000, len(v))).mean(1) < 0).mean()), 4)}
    wd = t.d.dt.dayofweek.isin([0, 1]).values
    a, b = t[t.post.values].net.values, t[wd & ~t.post.values].net.values
    bs = r.choice(a, (5000, len(a))).mean(1) - r.choice(b, (5000, len(b))).mean(1)
    out["doz_vade_sonrasi"][nm] = {"n": int(len(a)), "vade_sonrasi": round(float(a.mean()), 1), "diger_pzt_sali": round(float(b.mean()), 1),
                                   "fark": round(float(a.mean() - b.mean()), 1), "P_fark_arti": round(float((bs > 0).mean()), 4)}
    allv.append(t.assign(z=(t.net - t.net.mean()) / t.net.std(), set=nm))
p = pd.concat(allv)
vz = p[p.veto].sort_values("d"); h = len(vz) // 2
out["veto_havuz"] = {"n_veto": int(len(vz)), "z_ort": round(float(vz.z.mean()), 3), "yarilar_z": [round(float(vz.z.values[:h].mean()), 3), round(float(vz.z.values[h:].mean()), 3)],
                     "P_EV_eksi_z": round(float((r.choice(vz.z.values, (5000, len(vz))).mean(1) < 0).mean()), 4)}
# sürtünme ×1,5: vetolanan gün içi K1'de spread 1,5 kat → net daha da eksi; gerçek-spread gün içi ile günlük vekil aynı yön (ölçüt 5)
pa, pb = p[p.post.values].z.values, p[p.d.dt.dayofweek.isin([0, 1]).values & ~p.post.values].z.values
bs = r.choice(pa, (5000, len(pa))).mean(1) - r.choice(pb, (5000, len(pb))).mean(1)
out["doz_havuz_z"] = {"n": int(len(pa)), "fark_z": round(float(pa.mean() - pb.mean()), 3), "P_fark_arti": round(float((bs > 0).mean()), 4)}
for k_, v_ in out.items(): print(k_, json.dumps(v_, ensure_ascii=False))
Path(__file__).resolve().parents[1].joinpath("results/ek5.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
