"""QS-05: T1 ay ortası trend, T2 diğer ABD endeksleri (broker), T3 VIX korku katmanı (PROTOCOL_QS05.md)."""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from scipy.stats import binomtest
from r1_dengeleme import px, synth_bond, st, H
from qs04 import monthly, side, TH, COST
from qs04_e4 import load, CSV, PQ

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, SWAP_BP  # noqa: E402
RNG = np.random.default_rng(61)


def sharpe(v):
    v = np.asarray(v, float); s = v.std(ddof=1)
    return round(float(v.mean() / s * np.sqrt(12)), 2) if s > 0 else None


# ---------- T1 ----------
def t1_series(c: pd.Series, cost: float, a=None, b=None) -> dict:
    c = c.dropna(); c = c[c > 0]; idx = c.index; v = c.to_numpy()
    L = pd.Series(np.arange(len(idx)), index=idx).groupby(idx.to_period("M")).max().to_numpy()
    out = []
    for k in range(1, len(L)):
        s = L[k] - 10; e = s + 3
        if s <= L[k - 1] or e >= L[k]:
            continue
        if a is not None and not (pd.Timestamp(a) <= idx[s] < pd.Timestamp(b)):
            continue
        m = v[s] / v[L[k - 1]] - 1
        sd = 1 if m >= TH else (-1 if m <= -TH else 0)
        if sd:
            out.append((sd, sd * (v[e] / v[s] - 1) * 1e4 - cost))
    arr = np.array(out) if out else np.zeros((0, 2))
    return {"hepsi": st(arr[:, 1]) if len(arr) else {"n": 0}, "uzun": st(arr[arr[:, 0] == 1, 1]) if len(arr) else {"n": 0},
            "kisa": st(arr[arr[:, 0] == -1, 1]) if len(arr) else {"n": 0}}


def t1_broker() -> dict:
    q = px("QQQ"); mk = Mkt("NAS100"); idx = q.index; v = q.to_numpy()
    L = pd.Series(np.arange(len(idx)), index=idx).groupby(idx.to_period("M")).max().to_numpy()
    out = []
    for k in range(1, len(L)):
        s = L[k] - 10; e = s + 3
        if s <= L[k - 1] or e >= L[k] or idx[s] < pd.Timestamp("2018-06-01"):
            continue
        m = v[s] / v[L[k - 1]] - 1; sd = 1 if m >= TH else (-1 if m <= -TH else 0)
        if not sd:
            continue
        off = pd.Timedelta(hours=16, minutes=30); i, j = mk.at(idx[s] + off), mk.at(idx[e] + off)
        if i < 0 or j < 0:
            continue
        out.append(sd * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - mk.cost(i) / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j]))
    return st(np.array(out))


def t1() -> dict:
    res = {"yabanci_tum": {nm: t1_series(load(nm), 3.0) for nm in CSV + PQ}}
    res["GSPC_1990_2002"] = t1_series(px("GSPC", "Close"), 2.0, "1990-01-01", "2002-08-01")
    res["QQQ_2002_26_(goruldu)"] = t1_series(px("QQQ"), 2.0, "2002-08-01", "2026-11-01")
    res["broker_NAS100_2018_26"] = t1_broker()
    means = [r["hepsi"]["ort"] for r in res["yabanci_tum"].values() if r["hepsi"].get("n", 0) >= 30]
    pos = sum(m > 0 for m in means); sp = binomtest(pos, len(means), .5, alternative="greater").pvalue
    c1 = pos >= .6 * len(means) and sp <= .10 and np.mean(means) > 0
    c2 = res["GSPC_1990_2002"]["hepsi"].get("ort", -1) > 0; c3 = res["broker_NAS100_2018_26"].get("ort", -1) > 0
    lu = [r["uzun"]["ort"] for r in res["yabanci_tum"].values() if r["uzun"].get("n", 0) >= 20]
    lk = [r["kisa"]["ort"] for r in res["yabanci_tum"].values() if r["kisa"].get("n", 0) >= 20]
    res["ozet"] = {"piyasa": len(means), "arti": int(pos), "havuz": round(float(np.mean(means)), 1), "isaret_p": round(float(sp), 4),
                   "uzun_havuz": round(float(np.mean(lu)), 1), "uzun_arti": f"{sum(x > 0 for x in lu)}/{len(lu)}",
                   "kisa_havuz": round(float(np.mean(lk)), 1), "kisa_arti": f"{sum(x > 0 for x in lk)}/{len(lk)}",
                   "sinif": "B-" if c1 and c2 and c3 else ("C+" if c1 else "X")}
    return res


# ---------- döngü yardımcıları ----------
def cycle_frame():
    inst = {n: px(n) for n in ("QQQ", "SPY", "DIA", "IWM")}
    M = monthly(px("SPY"), px("TLT"), inst); M = M[M.d_s >= "2002-08-01"].reset_index(drop=True)
    cal = px("SPY").dropna().index.intersection(px("TLT").dropna().index)
    M["d_D3"] = [cal[cal.get_loc(d) + 3] for d in M.d_D]
    return M, cal


def broker_cycle(sym: str, M: pd.DataFrame) -> pd.Series:
    """Ay başına döngü P&L (bp): R1 iki bacak D−3→D + E2 uzun D→D+3, 16:30 ET."""
    mk = Mkt(sym); sR1 = side(M.dm.to_numpy()); sE2 = np.where(M.dD.to_numpy() >= TH, 1, 0)
    off = pd.Timedelta(hours=16, minutes=30); out = {}
    first = mk.et[0]
    for k, r in M.iterrows():
        if r.d_s < max(pd.Timestamp("2018-06-01"), first + pd.Timedelta(days=60)):
            continue
        tot, ok = 0.0, True
        for sd, t0, t1_ in ((sR1[k], r.d_s, r.d_D), (sE2[k], r.d_D, r.d_D3)):
            if sd == 0:
                continue
            i, j = mk.at(t0 + off), mk.at(t1_ + off)
            if i < 0 or j < 0:
                ok = False; continue
            tot += sd * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - mk.cost(i) / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j])
        if ok:
            out[r.m] = tot
    return pd.Series(out, dtype=float)


def t2() -> dict:
    M, cal = cycle_frame()
    sR1 = side(M.dm.to_numpy()); sE2 = np.where(M.dD.to_numpy() >= TH, 1, 0)
    res = {"ETF_2002_26": {}}
    for nm in ("QQQ", "SPY", "DIA", "IWM"):
        v = np.where(sR1 != 0, sR1 * M[f"w_{nm}"] - COST, 0) + np.where(sE2 == 1, M[f"n_{nm}"] - COST, 0)
        act = v[(sR1 != 0) | (sE2 == 1)]
        res["ETF_2002_26"][nm] = st(act) | {"SR_aylik": sharpe(v)}
    br = {s: broker_cycle(s, M) for s in ("NAS100", "US500", "US30", "US2000")}
    res["broker"] = {s: st(v.to_numpy()) | {"SR_aylik": sharpe(v.to_numpy()), "ilk_ay": str(v.index.min())} for s, v in br.items()}
    P = pd.concat(br, axis=1)
    common = P.dropna(subset=["NAS100"])
    port = common.mean(axis=1, skipna=True)
    res["portfoy_2018_26"] = {"NAS100_SR": sharpe(common.NAS100.to_numpy()), "esit_agirlik_SR": sharpe(port.to_numpy()),
                              "NAS100_ort": round(float(common.NAS100.mean()), 1), "port_ort": round(float(port.mean()), 1),
                              "korelasyon": {s: round(float(common.NAS100.corr(common[s])), 2) for s in ("US500", "US30", "US2000")}}
    c1 = all(res["ETF_2002_26"][n].get("ort", -1) > 0 and res["ETF_2002_26"][n].get("P", 0) >= .9 for n in ("DIA", "IWM"))
    c2 = all(res["broker"][s].get("ort", -1) > 0 for s in ("US500", "US30", "US2000"))
    c3 = (res["portfoy_2018_26"]["esit_agirlik_SR"] or 0) > (res["portfoy_2018_26"]["NAS100_SR"] or 0)
    res["sinif"] = "genisleme kabul" if c1 and c2 and c3 else ("C+" if c1 and c2 else "X")
    return res


def t3() -> dict:
    vix = px("VIX", "Close")
    M, cal = cycle_frame()
    M["vix_s"] = vix.reindex(M.d_s).values; M["vix_D"] = vix.reindex(M.d_D).values
    res = {}
    def block(m, names, ret_w="w", ret_n="n"):
        sR1 = side(m.dm.to_numpy()); sE2 = m.dD.to_numpy() >= TH
        r1u = np.mean([m[f"{ret_w}_{n}"] for n in names], 0) - COST
        e2u = np.mean([m[f"{ret_n}_{n}"] for n in names], 0) - COST
        hi_r1 = (sR1 == 1) & (m.vix_s >= 18.4); lo_r1 = (sR1 == 1) & (m.vix_s < 18.4)
        hi_e2 = sE2 & (m.vix_D >= 18.4); lo_e2 = sE2 & (m.vix_D < 18.4)
        hi = np.concatenate([r1u[hi_r1], e2u[hi_e2]]); lo = np.concatenate([r1u[lo_r1], e2u[lo_e2]])
        return {"R1u_yuksek": st(r1u[hi_r1]), "R1u_dusuk": st(r1u[lo_r1]), "E2u_yuksek": st(e2u[hi_e2]), "E2u_dusuk": st(e2u[lo_e2]),
                "havuz_yuksek": st(hi), "havuz_dusuk": st(lo), "fark": round(float(hi.mean() - lo.mean()), 1)}
    for per, a, b in (("KESIF", "2002-08-01", "2013-12-31"), ("TEST", "2014-01-01", "2026-10-31")):
        res[per] = block(M[(M.d_s >= a) & (M.d_s <= b)], ["QQQ", "SPY"])
    g = px("GSPC", "Close")
    G = monthly(g, synth_bond(px("TNX", "Close")), {"GSPC": g}); G = G[(G.d_s >= "1990-01-01") & (G.d_s < "2002-08-01")].reset_index(drop=True)
    G["vix_s"] = vix.reindex(G.d_s).values; G["vix_D"] = vix.reindex(G.d_D).values
    res["BAGIMSIZ_1990_2002"] = block(G, ["GSPC"])
    ok = all(res[p]["fark"] > 0 and res[p]["havuz_dusuk"].get("ort", -1) > 0 for p in ("KESIF", "TEST", "BAGIMSIZ_1990_2002"))
    if ok:   # E110: boyut eğimi portföy Sharpe'ını artırıyor mu (QQQ 2002-26)
        sR1 = side(M.dm.to_numpy()); sE2 = M.dD.to_numpy() >= TH
        base = np.where(sR1 != 0, sR1 * M.w_QQQ - COST, 0) + np.where(sE2, M.n_QQQ - COST, 0)
        w1 = np.where((sR1 == 1) & (M.vix_s >= 18.4), 1.5, 1.0); w2 = np.where(sE2 & (M.vix_D >= 18.4), 1.5, 1.0)
        tilt = np.where(sR1 != 0, w1 * (sR1 * M.w_QQQ - COST), 0) + np.where(sE2, w2 * (M.n_QQQ - COST), 0)
        res["E110"] = {"SR_taban": sharpe(base), "SR_egim": sharpe(tilt)}
        ok = res["E110"]["SR_egim"] > res["E110"]["SR_taban"]
    res["sinif"] = "boyut egimi kabul" if ok else "X"
    return res


def betimsel_D() -> dict:
    M, cal = cycle_frame(); mk = Mkt("NAS100"); sR1 = side(M.dm.to_numpy()); a, b = [], []
    for k, r in M.iterrows():
        if sR1[k] == 0 or r.d_s < pd.Timestamp("2018-06-01"):
            continue
        i0, i1, i2 = (mk.at(r.d_D + pd.Timedelta(minutes=m)) for m in (570, 930, 960))
        if min(i0, i1, i2) < 0:
            continue
        a.append(sR1[k] * (mk.o[i1] / mk.o[i0] - 1) * 1e4); b.append(sR1[k] * (mk.o[i2] / mk.o[i1] - 1) * 1e4)
    return {"D_0930_1530": st(np.array(a)), "D_1530_1600": st(np.array(b))}


if __name__ == "__main__":
    import yfinance as yf
    if not (H / "data/VIX.parquet").exists():
        x = yf.Ticker("^VIX").history(start="1990-01-01", end="2026-11-11", auto_adjust=False)
        x.index = pd.DatetimeIndex(x.index).tz_localize(None).normalize(); x.to_parquet(H / "data/VIX.parquet")
    res = {"T1": t1(), "T2": t2(), "T3": t3(), "betimsel_D": betimsel_D()}
    (H / "results/qs05.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
