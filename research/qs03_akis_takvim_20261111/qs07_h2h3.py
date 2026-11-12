"""QS-07 H2 (itme → sönüm, ay sonu vs sıradan gün eğimi) + H3 (çeyrek penceresi, görülmemiş 1985-2003). PROTOCOL_QS07.md."""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from scipy.stats import binomtest
from r1_dengeleme import px, synth_bond, st, H
from qs04 import monthly, side
from qs06_harita import adj_oc
from qs06_geri_alim import groups, diff_stats
from qs04_e4 import load, CSV

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt  # noqa: E402
RNG = np.random.default_rng(73)


def ols_slope(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float); ok = np.isfinite(x) & np.isfinite(y); x, y = x[ok], y[ok]
    return float(np.polyfit(x, y, 1)[0]) if len(x) > 3 else np.nan


def etf_events(names, eq, bond, a, b):
    """Ay sonu olayları (P, Y) ve sıradan günler (P_t, Y_t); her fon kendi tarih dizisinde."""
    cal = eq.dropna().index.intersection(bond.dropna().index)
    M = monthly(eq, bond, {"_": eq}); M = M[(M.d_s >= a) & (M.d_s < b)].reset_index(drop=True); s = side(M.dm.to_numpy())
    OC = {n: adj_oc(n, "Adj Close" if n != "GSPC" else "Close") for n in names}
    ev = []
    excl = set()
    for k, r in M.iterrows():
        p = cal.get_loc(r.d_D)
        for q in range(-3, 4):
            if 0 <= p + q < len(cal):
                excl.add(cal[p + q])
        if s[k] == 0:
            continue
        P, Y = [], []
        for n in names:
            O, C = OC[n]; idx = C.index
            if r.d_D not in idx:
                continue
            i = idx.get_loc(r.d_D)
            if i + 1 >= len(idx):
                continue
            P.append(s[k] * (C.iloc[i] / O.iloc[i] - 1) * 1e4); Y.append(-s[k] * (O.iloc[i + 1] / C.iloc[i] - 1) * 1e4)
        if P:
            ev.append((r.d_D, np.mean(P), np.mean(Y)))
    E = pd.DataFrame(ev, columns=["d", "P", "Y"])
    # sıradan günler
    od = []
    for n in names:
        O, C = OC[n]; idx = C.index
        intr = (C / O - 1) * 1e4; night = (O.shift(-1) / C - 1) * 1e4
        sel = (idx >= a) & (idx < b) & ~idx.isin(list(excl))
        sg = np.sign(intr[sel]); od.append(pd.DataFrame({"d": idx[sel], "P": intr[sel].abs().values, "Y": (-sg * night[sel]).values, "n": n}))
    Od = pd.concat(od).dropna()
    return E, Od


def h2_block(E, Od):
    bE = ols_slope(E.P, E.Y); bO = ols_slope(Od.P, Od.Y)
    bs = []
    em = E.reset_index(drop=True); om = Od.reset_index(drop=True)
    for _ in range(2000):
        e = em.iloc[RNG.integers(0, len(em), len(em))]; o = om.iloc[RNG.integers(0, len(om), min(len(om), 4000))]
        bs.append(ols_slope(e.P, e.Y) - ols_slope(o.P, o.Y))
    bs = np.array(bs)
    hiP = E[E.P >= E.P.median()]; loP = E[E.P < E.P.median()]
    return {"n_ay_sonu": int(len(E)), "egim_ay_sonu": round(bE, 3), "egim_siradan": round(bO, 3), "fark": round(bE - bO, 3),
            "P_fark>0": round(float((bs > 0).mean()), 3), "Y_buyuk_itme": st(hiP.Y.to_numpy()), "Y_kucuk_itme": st(loP.Y.to_numpy()),
            "ort_itme_P": round(float(E.P.mean()), 1)}


def h2_broker():
    spy, tlt = px("SPY"), px("TLT"); cal = spy.dropna().index.intersection(tlt.dropna().index)
    M = monthly(spy, tlt, {"_": spy}); M = M[M.d_s >= "2018-06-01"].reset_index(drop=True); s = side(M.dm.to_numpy()); rows = []
    for sym in ("NAS100", "US500"):
        mk = Mkt(sym)
        for k, r in M.iterrows():
            if s[k] == 0:
                continue
            p = cal.get_loc(r.d_D)
            if p + 1 >= len(cal):
                continue
            i0, i1, i2 = mk.at(cal[p] + pd.Timedelta(minutes=570)), mk.at(cal[p] + pd.Timedelta(minutes=960)), mk.at(cal[p + 1] + pd.Timedelta(minutes=570))
            if min(i0, i1, i2) < 0:
                continue
            rows.append((sym, s[k] * (mk.o[i1] / mk.o[i0] - 1) * 1e4, -s[k] * (mk.o[i2] / mk.o[i1] - 1) * 1e4))
    B = pd.DataFrame(rows, columns=["sym", "P", "Y"])
    return {"n": int(len(B)), "egim": round(ols_slope(B.P, B.Y), 3), "Y_buyuk_itme": st(B.Y[B.P >= B.P.median()].to_numpy()),
            "Y_kucuk_itme": st(B.Y[B.P < B.P.median()].to_numpy())}


def h3():
    out = {"yabanci_1990_2003": {}}
    for nm in CSV + ["GDAXI", "N225", "FTSE"]:
        if nm in ("DJI", "RUT", "IXIC"):
            continue
        r = diff_stats(groups(load(nm)), "1990-01-01", "2004-01-01")
        if "fark" in r:
            out["yabanci_1990_2003"][nm] = {"pencere-disi": round(-r["fark"], 2), "P(pencere>disi)": round(1 - r["P_fark>0"], 3), "n": r["n_acik"] + r["n_yasak"]}
    for nm, ser in (("GSPC", px("GSPC", "Close")), ("IXIC", load("IXIC"))):
        r = diff_stats(groups(ser), "1985-01-01", "1993-01-01")
        out[f"{nm}_1985_93"] = {"pencere-disi": round(-r["fark"], 2), "P(pencere>disi)": round(1 - r["P_fark>0"], 3)}
    v = [x["pencere-disi"] for x in out["yabanci_1990_2003"].values()]
    pos = sum(x > 0 for x in v); sp = binomtest(pos, len(v), .5, alternative="greater").pvalue
    c1 = pos >= .6 * len(v) and sp <= .10 and np.mean(v) > 0
    c2 = out["GSPC_1985_93"]["pencere-disi"] > 0 and out["IXIC_1985_93"]["pencere-disi"] > 0
    out["ozet"] = {"yabanci_arti": f"{pos}/{len(v)}", "havuz": round(float(np.mean(v)), 2), "isaret_p": round(float(sp), 3),
                   "sinif": "B-" if c1 and c2 else ("C" if c1 else "X")}
    return out


def main():
    res = {}
    E, Od = etf_events(["QQQ", "SPY"], px("SPY"), px("TLT"), "2002-08-01", "2026-11-01")
    res["H2_ETF_2002_26"] = h2_block(E, Od)
    E2, Od2 = etf_events(["SPY"], px("SPY"), synth_bond(px("TNX", "Close")), "1993-03-01", "2002-08-01")
    res["H2_SPY_1993_2002"] = h2_block(E2, Od2)
    res["H2_broker_2018_26"] = h2_broker()
    a = res["H2_ETF_2002_26"]; b = res["H2_SPY_1993_2002"]; c = res["H2_broker_2018_26"]
    ca, cb = a["egim_ay_sonu"] > 0, (a["fark"] > 0 and a["P_fark>0"] >= .9)
    cc = c["egim"] > 0; cd = b["egim_ay_sonu"] > 0
    res["H2_sinif"] = "B-" if ca and cb and cc and cd else ("C+" if ca and cb else "X")
    res["H3"] = h3()
    (H / "results/qs07_h2h3.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
