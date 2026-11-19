"""EK-1: OPEX Çar/Per korku günü → SAT, 1 sa / 5 sa / 1 gün / 1,5 gün; kontrol OPEX dışı K1 uzun."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import oz
R = oz.ROOT
sys.path.insert(0, str(R / "research/korku_genislik_20261118/src")); sys.path.insert(0, str(R / "research/son4_20261118/src"))
import gn, ek3_veto as E3
G, KD, V = oz.G, oz.KD, oz.V
NY = oz.NY
def trades(b, st):
    k = gn.nts(b, st); k = k[k.K1].reset_index(drop=True); k["d"] = pd.to_datetime(k.d)
    idx = pd.DatetimeIndex(pd.to_datetime(sorted(set(G.day_prices(b, NY, [960], st).index))))
    w = E3.pre_days(idx, (1, 2)); t, o, sp = b.t.values, b.o.values, b.sp.values
    tol = 300 if st == 60 else st; rows = []
    for d, ic in zip(k.d, k.d.isin(w)):
        u = oz.ts(d, 16, 0); i = int(np.searchsorted(t, u))
        if i >= len(t) or t[i] - u > tol: continue
        for hn, hm in oz.HOLDS.items():
            j = i + max(1, hm * 60 // st)
            if j >= len(t): continue
            rows.append({"d": d, "ic": bool(ic), "hold": hn, "sat": -((o[j] + sp[j]) / o[i] - 1) * 1e4,
                         "al": (o[j] / (o[i] + sp[i]) - 1) * 1e4 - oz.FIN * hm / 1440})
    return pd.DataFrame(rows)
def st_(v):
    if len(v) < 5: return {"n": int(len(v))}
    r = np.random.default_rng(71); P = float((r.choice(v, (5000, len(v))).mean(1) > 0).mean())
    return {"n": int(len(v)), "ort": round(float(v.mean()), 1), "isabet": round(float((v > 0).mean()), 3), "P_arti": round(P, 4),
            "en_kotu": round(float(v.min()), 1), "en_iyi": round(float(v.max()), 1)}
feeds = {"DUKA_NDX": (G.ndx_bars(), 60), "MT5_NAS100": (KD.mt5_m30("NAS100"), 1800), "MT5_US500": (KD.mt5_m30("US500", "2018-06-01"), 1800),
         "MT5_US30": (KD.mt5_m30("US30"), 1800), "MT5_US2000": (KD.mt5_m30("US2000"), 1800)}
out = {"OPEX_SAT": {}, "kontrol_AL_OPEX_disi": {}, "havuz": {}}
allt = []
for nm, (b, stp) in feeds.items():
    t = trades(b, stp); t["feed"] = nm; allt.append(t)
    for hn in oz.HOLDS:
        z = t[t.hold == hn]
        out["OPEX_SAT"][f"{nm}_{hn}"] = st_(z[z.ic].sat.values)
        out["kontrol_AL_OPEX_disi"][f"{nm}_{hn}"] = st_(z[~z.ic].al.values)
A = pd.concat(allt)
for hn in oz.HOLDS:
    z = A[(A.hold == hn) & A.ic].copy()
    sd = A[A.hold == hn].groupby("feed").sat.std()
    z["zs"] = z.sat / z.feed.map(sd)
    r = np.random.default_rng(72)
    out["havuz"][hn] = {"n": int(len(z)), "z_ort": round(float(z.zs.mean()), 3), "P_arti": round(float((r.choice(z.zs.values, (5000, len(z))).mean(1) > 0).mean()), 4),
                        "besleme_arti": int((z.groupby("feed").sat.mean() > 0).sum()), "yarilar_bp": [round(float(z.sort_values("d").sat.values[:len(z)//2].mean()), 1), round(float(z.sort_values("d").sat.values[len(z)//2:].mean()), 1)]}
# uzun geçmiş: günlük C3b OPEX Çar/Per girişi SAT, sabit 1/2 gün
for nm, x in (("NDX_1985_1999", V.ndx_frame()), ("QQQ", V.ohlc("QQQ"))):
    c, idx = x.c.values, x.index; w = E3.pre_days(idx, (1, 2)); r2 = V.rsi2(pd.Series(c, index=idx)).values
    for h in (1, 2):
        v = np.array([-(c[i + h] / c[i] - 1) * 1e4 - 2 for i in range(len(c) - h) if r2[i] < 10 and idx[i] in w and
                      (nm != "NDX_1985_1999" or idx[i] <= pd.Timestamp("1999-02-28"))])
        u = np.array([(c[i + h] / c[i] - 1) * 1e4 - 2 for i in range(len(c) - h) if r2[i] < 10 and idx[i] not in w and
                      (nm != "NDX_1985_1999" or idx[i] <= pd.Timestamp("1999-02-28"))])
        out["havuz"][f"gunluk_C3b_{nm}_SAT_{h}g"] = {**st_(v), "kontrol_AL_ort": round(float(u.mean()), 1)}
for sec, d in out.items():
    for k_, v_ in d.items(): print(sec, k_, v_)
Path(__file__).resolve().parents[1].joinpath("results/ek1_sat.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
