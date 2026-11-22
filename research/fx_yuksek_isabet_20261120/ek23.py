"""EK-23: COT-TERS geliştirme G1 (kalabalık ∧ ekliyor) + G2 (kesitsel) — PROTOCOL.md EK-23."""
import json
import numpy as np, pandas as pd
import core, ek18, ek18b, ek19_20 as E

GEO = {"A": (0.5, 3.0, 10), "B": (1.0, 3.0, 10)}
CCY = {"099741": "EUR", "096742": "GBP", "097741": "JPY", "232741": "AUD", "090741": "CAD", "092741": "CHF", "112741": "NZD"}
AV = set(core.PAIRS)


def fix(T):
    pre = pd.to_datetime(T.day) < "2010-01-01"
    T.loc[pre, "cost"] = T.loc[pre, "cost"] / 2
    T["net"] = T.gross - T.cost; T["R"] = T.net / T.sl_bp
    return T


def usd_pair(c):
    for p, s in (("EUR", ("EURUSD", 1)), ("GBP", ("GBPUSD", 1)), ("AUD", ("AUDUSD", 1)), ("NZD", ("NZDUSD", 1)),
                 ("JPY", ("USDJPY", -1)), ("CAD", ("USDCAD", -1)), ("CHF", ("USDCHF", -1))):
        if c == p:
            return s


def g1(Z, codes, geo):
    out = []
    for code, (pair, cs) in codes.items():
        c = Z[Z.code == code]
        m = (c.zP.abs() >= 1.5) & (np.sign(c.zF) == np.sign(c.zP)) & (c.zF.abs() >= 1.0)
        days = [pd.Timestamp(p).normalize() for p in c.pub[m]]
        x = E.fx(pair); idx = x.day.values
        dd = [pd.Timestamp(idx[np.searchsorted(idx, np.datetime64(d), side="right") - 1]) for d in days if np.searchsorted(idx, np.datetime64(d), side="right") > 0]
        t = E.trades_for(pair, dd, (-np.sign(c.zP[m].values) * cs).astype(int)[:len(dd)], geo)
        if len(t): out.append(t)
    return fix(pd.concat(out, ignore_index=True)) if out else pd.DataFrame()


def g2(Z, geo):
    W = Z[Z.code.isin(CCY)].pivot_table(index="pub", columns="code", values="zP")
    W.columns = [CCY[c] for c in W.columns]
    W["USD"] = 0.0
    sig = {}
    for pub, r in W.dropna(thresh=6).iterrows():
        r = r.dropna()
        hi, lo = r.idxmax(), r.idxmin()
        if r[hi] - r[lo] < 2.0:
            continue
        # en uzun-kalabalık (hi) SAT, en kısa-kalabalık (lo) AL
        if hi + lo in AV:
            pair, side = hi + lo, -1
        elif lo + hi in AV:
            pair, side = lo + hi, 1
        else:
            k = hi if abs(r[hi]) >= abs(r[lo]) else lo
            pair, s = usd_pair(k)
            side = -s if k == hi else s
        sig.setdefault(pair, []).append((pd.Timestamp(pub).normalize(), side))
    out = []
    for pair, lst in sig.items():
        x = E.fx(pair); idx = x.day.values
        dd, ss = [], []
        for d, s in lst:
            j = np.searchsorted(idx, np.datetime64(d), side="right") - 1
            if j > 0:
                dd.append(pd.Timestamp(idx[j])); ss.append(s)
        t = E.trades_for(pair, dd, np.array(ss), geo)
        if len(t): out.append(t)
    return fix(pd.concat(out, ignore_index=True)) if out else pd.DataFrame()


def summ3(T, name):
    if len(T) == 0:
        return {"n": 0}
    y = pd.to_datetime(T.day).dt.year
    r = {}
    for nm, m in (("1993_2009", y <= 2009), ("2010_2017", (y >= 2010) & (y <= 2017)), ("2018_2026", y >= 2018)):
        g = T[m.values]
        if len(g) == 0:
            continue
        s = core.summ(g, boot=True)
        mo = max(1.0, (pd.to_datetime(g.day).max() - pd.to_datetime(g.day).min()).days / 30.44)
        r[nm] = {k: s[k] for k in ("n", "wr", "ort", "P", "yari", "stres15")} | {"frq": round(g.day.nunique() / mo, 2), "en_kotu": round(float(g.net.min()), 1)}
    return r


def main():
    Zt, Zl = ek18b.tff(), ek18b.legacy()
    Zl = Zl[Zl.rep < "2010-01-01"]
    LEG7 = {k: v for k, v in ek18b.LEG.items() if k != "095741"}
    res = {}
    for gn, geo in GEO.items():
        T1 = pd.concat([g1(Zt, ek18.CODES, geo), g1(Zl, ek18b.LEG, geo)], ignore_index=True)
        T2 = pd.concat([g2(Zt, geo), g2(Zl, geo)], ignore_index=True)
        res[f"G1|{gn}"] = summ3(T1, "G1"); res[f"G2|{gn}"] = summ3(T2, "G2")
        T1.to_parquet(core.RES / f"trades_EK23_G1{gn}.parquet"); T2.to_parquet(core.RES / f"trades_EK23_G2{gn}.parquet")
        for k in (f"G1|{gn}", f"G2|{gn}"):
            print(k, json.dumps(res[k], default=str), flush=True)
    (core.RES / "ek23.json").write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
