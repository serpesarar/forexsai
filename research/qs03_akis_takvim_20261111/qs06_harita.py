"""QS-06 A1 (gün × seans akış haritası, ileri yürüme) + A2 (F1 kardeş yarım saatleri). PROTOCOL_QS06.md."""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from r1_dengeleme import px, synth_bond, st, H
from qs04 import monthly, side, TH, COST

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, SWAP_BP  # noqa: E402
KS = [-2, -1, 0, 1, 2, 3]


def adj_oc(nm: str, col_close="Adj Close"):
    x = pd.read_parquet(H / "data" / f"{nm}.parquet")
    f = x[col_close] / x.Close
    return (x.Open * f), x[col_close]


def cell_table(eq: pd.Series, bond: pd.Series, names: list[str], a: str, b: str) -> pd.DataFrame:
    M = monthly(eq, bond, {"_": eq}); M = M[(M.d_s >= a) & (M.d_s < b)].reset_index(drop=True)
    s = side(M.dm.to_numpy())
    oc = {n: adj_oc(n, "Adj Close" if n != "GSPC" else "Close") for n in names}
    rows = []
    for k_, r in M.iterrows():
        if s[k_] == 0:
            continue
        row = {"m": r.m, "s": s[k_], "dD": r.dD}
        for k in KS:
            gn, gd = [], []
            for n in names:
                O, C = oc[n]; idx = C.index
                if r.d_D not in idx:
                    continue
                p = idx.get_loc(r.d_D) + k
                if p - 1 < 0 or p >= len(idx):
                    continue
                gn.append((O.iloc[p] / C.iloc[p - 1] - 1) * 1e4); gd.append((C.iloc[p] / O.iloc[p] - 1) * 1e4)
            if gn:
                row[f"GECE{k:+d}"] = s[k_] * np.mean(gn); row[f"GUN{k:+d}"] = s[k_] * np.mean(gd)
        rows.append(row)
    return pd.DataFrame(rows)


def tstat(v):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    return round(float(v.mean() / v.std(ddof=1) * np.sqrt(len(v))), 2) if len(v) > 2 else 0.0


def broker_cell(sym: str, M: pd.DataFrame, cal: pd.DatetimeIndex, seg: str, k: int, sign_dir: np.ndarray) -> dict:
    mk = Mkt(sym); out = []
    for i_, r in M.iterrows():
        if sign_dir[i_] == 0 or r.d_s < pd.Timestamp("2018-06-01"):
            continue
        p = cal.get_loc(r.d_D) + k
        if p >= len(cal):
            continue
        if seg == "GECE":
            t0, t1 = cal[p - 1] + pd.Timedelta(minutes=960), cal[p] + pd.Timedelta(minutes=570)
        else:
            t0, t1 = cal[p] + pd.Timedelta(minutes=570), cal[p] + pd.Timedelta(minutes=960)
        i, j = mk.at(t0), mk.at(t1)
        if i < 0 or j < 0 or j <= i:
            continue
        out.append(sign_dir[i_] * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - mk.cost(i) / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j]))
    return st(np.array(out))


def a1() -> dict:
    spy, tlt = px("SPY"), px("TLT")
    K = cell_table(spy, tlt, ["QQQ", "SPY"], "2002-08-01", "2014-01-01")
    T = cell_table(spy, tlt, ["QQQ", "SPY"], "2014-01-01", "2026-11-01")
    E = cell_table(px("SPY", "Close"), synth_bond(px("TNX", "Close")), ["SPY"], "1993-03-01", "2002-08-01")
    cells = [f"{seg}{k:+d}" for k in KS for seg in ("GECE", "GUN")]
    harita = {c: {"KESIF_ort": round(float(K[c].mean()), 1), "KESIF_t": tstat(K[c]), "TEST_ort": round(float(T[c].mean()), 1),
                  "TEST_t": tstat(T[c]), "1993_2002_ort": round(float(E[c].mean()), 1)} for c in cells}
    secilen = [c for c in cells if abs(harita[c]["KESIF_t"]) >= 2.0]
    M = monthly(spy, tlt, {"_": spy}); M = M[M.d_s >= "2002-08-01"].reset_index(drop=True)
    cal = spy.dropna().index.intersection(tlt.dropna().index)
    s_all = side(M.dm.to_numpy())
    karar = {}
    for c in secilen:
        d = 1 if harita[c]["KESIF_t"] > 0 else -1
        seg, k = ("GECE" if c.startswith("GECE") else "GUN"), int(c.replace("GECE", "").replace("GUN", ""))
        tv = d * T[c].to_numpy() - COST; ev = d * E[c].to_numpy() - COST
        tst, est = st(tv), st(ev)
        br = {sym: broker_cell(sym, M, cal, seg, k, d * s_all) for sym in ("NAS100", "US500")}
        c1 = tst.get("ort", -1) > 0 and tst.get("P", 0) >= .9; c2 = est.get("ort", -1) > 0
        c3 = all(br[x].get("ort", -1) > 0 for x in br)
        karar[c] = {"yon": "s ile aynı" if d == 1 else "s'nin tersi", "TEST": tst, "1993_2002": est, "broker": br,
                    "sinif": "B-" if c1 and c2 and c3 else ("C+" if c1 and (c2 or c3) else "X")}
    return {"harita": harita, "secilen": secilen, "karar": karar}


def a2() -> dict:
    spy, tlt = px("SPY"), px("TLT")
    M = monthly(spy, tlt, {"_": spy}); M = M[M.d_s >= "2018-06-01"].reset_index(drop=True)
    cal = spy.dropna().index.intersection(tlt.dropna().index)
    sR1 = side(M.dm.to_numpy()); sE2 = np.where(M.dD.to_numpy() >= TH, 1, 0)
    defs = {"A2a_D-1_1530_1600": (sR1, -1, 930, 960), "A2b_D-2_1530_1600": (sR1, -2, 930, 960),
            "A2c_D+1_0930_1000_E2uzun": (sE2, 1, 570, 600)}
    out = {}
    for name, (sg, k, m0, m1) in defs.items():
        res = {}
        for sym in ("NAS100", "US500", "US30", "US2000"):
            mk = Mkt(sym); v, ctrl = [], []
            for i_, r in M.iterrows():
                p = cal.get_loc(r.d_D) + k
                if p >= len(cal):
                    continue
                i, j = mk.at(cal[p] + pd.Timedelta(minutes=m0)), mk.at(cal[p] + pd.Timedelta(minutes=m1))
                if i < 0 or j < 0:
                    continue
                g = (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4
                if sg[i_] != 0:
                    v.append(sg[i_] * g - mk.cost(i) / mk.o[i] * 1e4)
            d = pd.DataFrame({"m": mk.m, "d": mk.d, "o": mk.o}); A = d[d.m == m0].set_index("d").o; B = d[d.m == m1].set_index("d").o
            jx = A.index.intersection(B.index); jx = jx[jx >= "2018-06-01"]
            res[sym] = st(np.array(v)) | {"tum_gunler_uzun_brut": round(float(((B[jx] - A[jx]) / A[jx] * 1e4).mean()), 2)}
        # Dukascopy
        p_ = pd.read_parquet(H.parent / "geri_cekilme_limit_20261109/data/path.parquet")
        et = pd.to_datetime(p_.t, unit="s", utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
        s_ = pd.Series(p_.open.values, index=et); sp = pd.Series(p_.spr.values, index=et); dv = []
        for i_, r in M.iterrows():
            if sg[i_] == 0:
                continue
            p = cal.get_loc(r.d_D) + k
            if p >= len(cal):
                continue
            t0, t1 = cal[p] + pd.Timedelta(minutes=m0), cal[p] + pd.Timedelta(minutes=m1)
            if t0 in s_.index and t1 in s_.index:
                dv.append(sg[i_] * (s_[t1] - s_[t0]) / s_[t0] * 1e4 - sp[t0] / s_[t0] * 1e4)
        res["Dukascopy_NDX"] = st(np.array(dv))
        br = [res[x] for x in ("NAS100", "US500", "US30", "US2000")]
        pos = sum(x.get("ort", -1) > 0 for x in br); p90 = sum(x.get("P", 0) >= .9 for x in br)
        res["sinif"] = "B-" if pos >= 3 and p90 >= 2 and res["Dukascopy_NDX"].get("ort", -1) > 0 else ("C" if pos >= 3 else "X")
        out[name] = res
    return out


if __name__ == "__main__":
    res = {"A1": a1(), "A2": a2()}
    (H / "results/qs06_harita.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    h = res["A1"]["harita"]
    print(f"{'hucre':8s} {'KES_ort':>8s} {'KES_t':>6s} {'TEST_ort':>9s} {'TEST_t':>7s} {'93-02':>7s}")
    for c, v in h.items():
        print(f"{c:8s} {v['KESIF_ort']:8.1f} {v['KESIF_t']:6.2f} {v['TEST_ort']:9.1f} {v['TEST_t']:7.2f} {v['1993_2002_ort']:7.1f}")
    print("secilen:", res["A1"]["secilen"])
    for c, v in res["A1"]["karar"].items():
        print(c, v["yon"], "TEST", v["TEST"], "93-02", v["1993_2002"], {k: (x.get("n"), x.get("ort"), x.get("P")) for k, x in v["broker"].items()}, v["sinif"])
    for n, v in res["A2"].items():
        print(n, v["sinif"])
        for k, x in v.items():
            if k != "sinif":
                print("   ", k, x)
