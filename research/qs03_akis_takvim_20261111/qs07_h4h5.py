"""QS-07 EK-1: H4 haftalık dengeleme (Cuma seansı / hafta sonu gecesi), H5 Avrupa yerel akışı (DAX − Euro tahvil). PROTOCOL_QS07.md."""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from r1_dengeleme import px, synth_bond, st, H
from qs04 import monthly, side, TH
from qs06_harita import adj_oc

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, SWAP_BP  # noqa: E402
COST = 2.0
WTH = 0.01


# ---------------- H4 ----------------
def month_end_excl(cal: pd.DatetimeIndex) -> set:
    pos = pd.Series(np.arange(len(cal)), index=cal); last = pos.groupby(cal.to_period("M")).max().to_numpy(); ex = set()
    for D in last:
        for q in range(-3, 4):
            if 0 <= D + q < len(cal):
                ex.add(cal[D + q])
    return ex


def weekly_events(eq: pd.Series, bond: pd.Series) -> pd.DataFrame:
    cal = eq.dropna().index.intersection(bond.dropna().index); e, b = eq.reindex(cal), bond.reindex(cal)
    ex = month_end_excl(cal)
    wk = pd.Series(cal, index=cal).groupby([cal.isocalendar().year.values, cal.isocalendar().week.values])
    groups = [g.values for _, g in wk]
    rows = []
    for k in range(1, len(groups)):
        days = groups[k]
        if len(days) < 3 or any(pd.Timestamp(d) in ex for d in days):
            continue
        F, F1, W0 = pd.Timestamp(days[-1]), pd.Timestamp(days[-2]), pd.Timestamp(groups[k - 1][-1])
        dw = (e[F1] / e[W0] - 1) - (b[F1] / b[W0] - 1)
        sw = -1 if dw >= WTH else (1 if dw <= -WTH else 0)
        if sw:
            rows.append(dict(F=F, sw=sw, dw=dw))
    return pd.DataFrame(rows)


def h4_etf(Ev: pd.DataFrame, names, a, b) -> dict:
    OC = {n: adj_oc(n, "Adj Close" if n != "GSPC" else "Close") for n in names}
    A, Bn = [], []
    for _, r in Ev[(Ev.F >= a) & (Ev.F < b)].iterrows():
        ga, gb = [], []
        for n in names:
            O, C = OC[n]; idx = C.index
            if r.F not in idx:
                continue
            i = idx.get_loc(r.F)
            if i + 1 >= len(idx):
                continue
            ga.append(r.sw * (C.iloc[i] / O.iloc[i] - 1) * 1e4); gb.append(-r.sw * (O.iloc[i + 1] / C.iloc[i] - 1) * 1e4)
        if ga:
            A.append(np.mean(ga) - COST); Bn.append(np.mean(gb) - COST)
    return {"H4a_cuma_seansi": st(np.array(A)), "H4b_hafta_sonu_gecesi_ters": st(np.array(Bn))}


def h4_broker(Ev: pd.DataFrame) -> dict:
    out = {}
    for sym in ("NAS100", "US500"):
        mk = Mkt(sym); A, Bn = [], []
        cal = px("SPY").dropna().index
        for _, r in Ev[Ev.F >= "2018-06-01"].iterrows():
            p = cal.get_loc(r.F)
            if p + 1 >= len(cal):
                continue
            i0, i1, i2 = mk.at(r.F + pd.Timedelta(minutes=570)), mk.at(r.F + pd.Timedelta(minutes=960)), mk.at(cal[p + 1] + pd.Timedelta(minutes=570))
            if min(i0, i1, i2) < 0:
                continue
            A.append(r.sw * (mk.o[i1] - mk.o[i0]) / mk.o[i0] * 1e4 - mk.cost(i0) / mk.o[i0] * 1e4)
            Bn.append(-r.sw * (mk.o[i2] - mk.o[i1]) / mk.o[i1] * 1e4 - mk.cost(i1) / mk.o[i1] * 1e4 - SWAP_BP * mk.swaps(mk.et[i1], mk.et[i2]))
        out[sym] = {"H4a": st(np.array(A)), "H4b": st(np.array(Bn))}
    return out


def h4() -> dict:
    res = {}
    Ev = weekly_events(px("SPY"), px("TLT"))
    for per, a, b in (("KESIF_2002_13", "2002-08-01", "2014-01-01"), ("TEST_2014_26", "2014-01-01", "2026-11-01")):
        res[per] = h4_etf(Ev, ["QQQ", "SPY"], a, b)
    Ev0 = weekly_events(px("SPY"), synth_bond(px("TNX", "Close")))
    res["SPY_1993_2002"] = h4_etf(Ev0, ["SPY"], "1993-03-01", "2002-08-01")
    res["broker_2018_26"] = h4_broker(Ev)
    for leg, key in (("H4a_cuma_seansi", "H4a"), ("H4b_hafta_sonu_gecesi_ters", "H4b")):
        k_, t_ = res["KESIF_2002_13"][leg], res["TEST_2014_26"][leg]
        c1 = k_.get("ort", -1) > 0 and t_.get("ort", -1) > 0
        c2 = t_.get("P", 0) >= .9 and res["SPY_1993_2002"][leg].get("ort", -1) > 0
        c3 = np.mean([res["broker_2018_26"][s][key].get("ort", -1) for s in ("NAS100", "US500")]) > 0
        res[f"sinif_{key}"] = "B-" if c1 and c2 and c3 else ("C" if c1 else "X")
    return res


# ---------------- H5 ----------------
def eu_bond() -> pd.Series:
    d = pd.read_csv(H / "data/EU_AAA_10Y.csv", parse_dates=["d"]).set_index("d").y / 100
    r = d.shift(1) / 252 - 8 * d.diff()
    return (1 + r.fillna(0)).cumprod()


def h5() -> dict:
    dax = px("GDAXI", "Close"); dax_o = px("GDAXI", "Open"); bond = eu_bond()
    M = monthly(dax, bond, {"GDAXI": dax}); M = M[M.d_s >= "2004-10-01"].reset_index(drop=True)
    Mus = monthly(px("SPY"), px("TLT"), {"_": px("SPY")}).set_index("m").dm
    M["dus"] = M.m.map(Mus)
    s = side(M.dm.to_numpy())
    M["r1"] = np.where(s != 0, s * M.w_GDAXI - 3.0, np.nan)
    M["son"] = [s[k] * (dax.loc[r.d_D] / dax_o.loc[r.d_D] - 1) * 1e4 - 3.0 if s[k] != 0 else np.nan for k, r in M.iterrows()]
    sus = side(M.dus.fillna(0).to_numpy())
    M["r1_us"] = np.where(sus != 0, sus * M.w_GDAXI - 3.0, np.nan)
    res = {}
    for per, a, b in (("KESIF_2004_14", "2004-10-01", "2015-01-01"), ("TEST_2015_26", "2015-01-01", "2026-11-01")):
        m = M[(M.d_s >= a) & (M.d_s < b)]
        X = np.column_stack([np.ones(len(m)), m.dm * 100, m.dus * 100]); y = m.w_GDAXI.to_numpy(); ok = np.isfinite(X).all(1) & np.isfinite(y)
        bta, *_ = np.linalg.lstsq(X[ok], y[ok], rcond=None); rr = y[ok] - X[ok] @ bta
        se = np.sqrt(np.diag(rr.var(ddof=3) * np.linalg.inv(X[ok].T @ X[ok])))
        res[per] = {"R1_EU": st(m.r1.dropna().to_numpy()), "son_seans_EU": st(m.son.dropna().to_numpy()), "R1_US_sinyali_DAX": st(m.r1_us.dropna().to_numpy()),
                    "beta_EU": round(float(bta[1]), 2), "t_EU": round(float(bta[1] / se[1]), 2), "beta_US": round(float(bta[2]), 2), "t_US": round(float(bta[2] / se[2]), 2),
                    "kor_EU_US": round(float(np.corrcoef(m.dm[ok], m.dus[ok])[0, 1]), 2)}
    mk = Mkt("GER40"); g = []
    for k, r in M.iterrows():
        if s[k] == 0 or r.d_s < pd.Timestamp("2018-06-01"):
            continue
        i, j = mk.at(r.d_s + pd.Timedelta(hours=11, minutes=30)), mk.at(r.d_D + pd.Timedelta(hours=11, minutes=30))
        if i < 0 or j < 0 or j <= i:
            continue
        g.append(s[k] * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - mk.cost(i) / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j]))
    res["GER40_broker_2018_26"] = st(np.array(g))
    K, T = res["KESIF_2004_14"], res["TEST_2015_26"]
    c1 = K["R1_EU"].get("ort", -1) > 0 and T["R1_EU"].get("ort", -1) > 0 and \
        st(np.concatenate([M[(M.d_s >= "2004-10-01")].r1.dropna().to_numpy()]))["P"] >= .9
    c2 = all(x["beta_EU"] < 0 and x["t_EU"] <= -1.5 for x in (K, T))
    c3 = res["GER40_broker_2018_26"].get("ort", -1) > 0
    res["sinif"] = "B-" if c1 and c2 and c3 else ("C" if c1 else "X")
    return res


if __name__ == "__main__":
    res = {"H4": h4(), "H5": h5()}
    (H / "results/qs07_h4h5.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
