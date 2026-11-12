"""QS-03 R2 tatil öncesi + R4 Fed net likiditesi (PROTOCOL.md)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import binomtest

H = Path(__file__).resolve().parent
D = H / "data"
FD = H.parent / "geri_cekilme_20261106/data"
FOREIGN = ["AEX", "AXJO", "BSESN", "BVSP", "FCHI", "GSPTSE", "IBEX", "JKSE", "KS11", "MXX", "SSMI", "TWII"]
RNG = np.random.default_rng(43)
UNUSUAL = pd.to_datetime(["2001-09-11", "2001-09-12", "2001-09-13", "2001-09-14", "2012-10-29", "2012-10-30",
                          "2018-12-05", "2025-01-09", "2004-06-11", "2007-01-02"])


def st(a) -> dict:
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    if len(a) < 3:
        return {"n": int(len(a))}
    p = float((a[RNG.integers(0, len(a), (5000, len(a)))].mean(1) > 0).mean())
    return {"n": int(len(a)), "ort": round(float(a.mean()), 2), "P": round(p, 3), "isabet": round(float((a > 0).mean()), 3)}


def preholiday(idx: pd.DatetimeIndex, unusual=UNUSUAL) -> pd.Series:
    """d tatil öncesi mi: d ile sonraki işlem günü arasında ≥1 hafta içi işlemsiz gün (olağandışılar hariç)."""
    flag = np.zeros(len(idx), bool)
    for k in range(len(idx) - 1):
        gap = pd.bdate_range(idx[k] + pd.Timedelta(days=1), idx[k + 1] - pd.Timedelta(days=1))
        gap = [g for g in gap if g not in set(unusual)]
        if len(gap) >= 1 and (idx[k + 1] - idx[k]).days <= 6:
            flag[k] = True
    return pd.Series(flag, index=idx)


def r2_series(close: pd.Series, cost: float, unusual=UNUSUAL):
    close = close.dropna(); r = (close / close.shift(1) - 1) * 1e4
    ph = preholiday(close.index, unusual)
    return (r - cost)[ph], (r - cost)


def r2() -> dict:
    out = {"ABD": {}, "yabanci": {}}
    for nm in ("SPY", "QQQ", "DIA", "IWM"):
        c = pd.read_parquet(D / f"{nm}.parquet")["Adj Close"]
        for per, a, b in (("KESIF", "1999-01-01", "2012-12-31"), ("TEST", "2013-01-01", "2026-11-10")):
            cc = c[(c.index >= a) & (c.index <= b)]
            rule, base = r2_series(cc, 2.0)
            out["ABD"][f"{nm}_{per}"] = st(rule) | {"taban": round(float(base.mean()), 2), "fark": round(float(rule.mean() - base.mean()), 2)}
    g = pd.read_parquet(D / "GSPC.parquet").Close; g = g[(g.index >= "1985-01-01") & (g.index < "1999-01-01")]
    rule, base = r2_series(g, 2.0)
    out["GSPC_1985_98"] = st(rule) | {"taban": round(float(base.mean()), 2), "fark": round(float(rule.mean() - base.mean()), 2)}
    for nm in FOREIGN:
        x = pd.read_csv(FD / f"{nm}.csv"); x.index = pd.to_datetime(x.Date.str[:10])
        c = x.Close[x.Close > 0]
        rule, base = r2_series(c, 3.0, unusual=pd.DatetimeIndex([]))
        out["yabanci"][nm] = st(rule) | {"taban": round(float(base.mean()), 2), "fark": round(float(rule.mean() - base.mean()), 2)}
    # ölçüt
    def pool(per):
        f = [out["ABD"][f"{n}_{per}"] for n in ("SPY", "QQQ", "DIA", "IWM")]
        diffs = [v["fark"] for v in f]
        return float(np.mean(diffs)), min(v.get("P", 0) for v in f)
    kf, kp = pool("KESIF"); tf, tp = pool("TEST")
    # havuz P: ABD 4 fonun kural günleri birleşik bootstrap (fark tabana göre)
    fd = [v["fark"] for v in out["yabanci"].values() if v.get("n", 0) >= 20]
    pos = sum(1 for x in fd if x > 0); sp = binomtest(pos, len(fd), 0.5, alternative="greater").pvalue
    c1 = kf > 0 and all(out["ABD"][f"{n}_KESIF"]["fark"] > 0 for n in ("SPY", "QQQ"))
    c2 = tf > 0 and all(out["ABD"][f"{n}_TEST"]["fark"] > 0 for n in ("SPY", "QQQ"))
    c3 = pos >= 0.6 * len(fd) and sp <= 0.10
    c4 = out["GSPC_1985_98"]["fark"] > 0
    cls = "B" if all([c1, c2, c3, c4]) else ("C+" if c2 and c3 else ("C" if any([c1, c2, c3, c4]) else "X"))
    out["olcut"] = {"KESIF_ABD_fark": round(kf, 2), "TEST_ABD_fark": round(tf, 2), "yabanci_arti": f"{pos}/{len(fd)}",
                    "isaret_p": round(float(sp), 3), "1": c1, "2": c2, "3": c3, "4": c4, "sinif": cls}
    return out


def r4() -> dict:
    w = pd.read_csv(D / "WALCL.csv"); t = pd.read_csv(D / "WTREGEN.csv"); r = pd.read_csv(D / "RRPONTSYD.csv")
    for x in (w, t, r):
        x.columns = ["d", "v"]; x["d"] = pd.to_datetime(x.d); x["v"] = pd.to_numeric(x.v, errors="coerce")
    nl = w.set_index("d").v - t.set_index("d").v.reindex(w.d).values
    rr = r.set_index("d").v.reindex(w.d, method="ffill").fillna(0).values * 1000  # milyar → milyon
    nl = (nl - rr).dropna()
    ch = nl.pct_change(4)
    q = pd.read_parquet(D / "QQQ.parquet"); f = q["Adj Close"] / q.Close; o = q.Open * f
    rows = []
    for wed, c in ch.dropna().items():
        fri = wed + pd.Timedelta(days=2)
        i = o.index.searchsorted(fri)
        j = o.index.searchsorted(fri + pd.Timedelta(days=7))
        if j >= len(o):
            break
        rows.append(dict(d=o.index[i], up=c > 0, ret=(o.iloc[j] / o.iloc[i] - 1) * 1e4))
    W = pd.DataFrame(rows).set_index("d")
    out = {}
    for per, a, b in (("KESIF", "2003-01-01", "2014-12-31"), ("TEST", "2015-01-01", "2026-10-31"), ("TEST_2015_19", "2015-01-01", "2019-12-31")):
        x = W[(W.index >= a) & (W.index <= b)]
        up, dn = x.ret[x.up].to_numpy(), x.ret[~x.up].to_numpy()
        B = 5000; bu = up[RNG.integers(0, len(up), (B, len(up)))].mean(1); bd = dn[RNG.integers(0, len(dn), (B, len(dn)))].mean(1)
        out[per] = {"NL_artis": st(up), "NL_azalis": st(dn), "fark": round(float(up.mean() - dn.mean()), 2),
                    "P_fark": round(float((bu > bd).mean()), 3), "her_zaman_uzun": round(float(x.ret.mean()), 2)}
    ok = all(out[p]["fark"] > 0 and out[p]["P_fark"] >= 0.9 for p in ("KESIF", "TEST")) and out["TEST_2015_19"]["fark"] > 0
    out["sinif"] = "C+" if ok else "X"
    return out


if __name__ == "__main__":
    res = {"R2": r2(), "R4": r4()}
    (H / "results/r2_r4.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
