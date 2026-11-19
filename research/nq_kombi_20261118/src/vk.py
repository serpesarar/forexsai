"""vk.py — VK-01…05 varyans primi genişletme + KM-01 kombinasyon. python vk.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/nq_yapi2_20261118/src"))
import gunluk2 as N  # noqa: E402

U = N.U
ath = U.ath
FIN = U.lib.FIN_BP_PER_DAY
RES = Path(__file__).resolve().parents[1] / "results"
QS = ROOT / "research/qs03_akis_takvim_20261111/data"
KES, TEST0 = pd.Timestamp("2021-10-31"), pd.Timestamp("2021-11-01")


def vix() -> pd.Series:
    d = pd.read_parquet(QS / "VIX.parquet")
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return d.Close.astype(float)


def vxn() -> pd.Series:
    return U.load("VXN")


def ohlc(t: str) -> pd.DataFrame:
    d = pd.read_parquet(N.DATA / f"{t}.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    f = d["Adj Close"] / d["Close"]
    return pd.DataFrame({"o": d.Open * f, "h": d.High * f, "l": d.Low * f, "c": d["Adj Close"]}).dropna()


def vrp_pct(x: pd.DataFrame, iv: pd.Series) -> pd.Series:
    return N.pct(iv.reindex(x.index) - 100 * x.rv20)


def ndx_frame() -> pd.DataFrame:
    d = pd.read_parquet(ROOT / "research/nq_akis_20261118/data/NDX.parquet")
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return U.frame(d.Close.astype(float).dropna())


def episodes(x: pd.DataFrame, p: pd.Series, h: int = 20) -> pd.DataFrame:
    on = (p >= 0.8).values
    c = x.c.values
    idx = x.index
    rows, busy = [], -1
    for i in range(5, len(x) - h):
        if on[i] and not on[i - 5:i].any() and i > busy:
            cal = (idx[i + h] - idx[i]).days
            rows.append({"d": idx[i], "net": (c[i + h] / c[i] - 1) * 1e4 - 2 - FIN * cal})
            busy = i + h
    return pd.DataFrame(rows)


def placebo(x: pd.DataFrame, ep: pd.DataFrame, h: int = 20, n: int = 2000) -> dict:
    if ep.empty:
        return {}
    rng = np.random.default_rng(9)
    c, idx = x.c.values, x.index
    yrs = idx.year.values
    by = {y: np.flatnonzero((yrs == y) & (np.arange(len(x)) < len(x) - h)) for y in set(ep.d.dt.year)}
    sims = np.zeros(n)
    for k in range(n):
        v = []
        for y in ep.d.dt.year:
            i = int(rng.choice(by[y]))
            v.append((c[i + h] / c[i] - 1) * 1e4 - 2 - FIN * (idx[i + h] - idx[i]).days)
        sims[k] = np.mean(v)
    real = ep.net.mean()
    return {"n": int(len(ep)), "ort": round(float(real), 1), "isabet": round(float((ep.net > 0).mean()), 3), "en_kotu": round(float(ep.net.min()), 1),
            "plasebo_ort": round(float(sims.mean()), 1), "yuzdelik": round(float((sims < real).mean()), 4)}


def vk() -> dict:
    out = {}
    nd = ndx_frame()
    p_ndx_vix = vrp_pct(nd, vix())
    out["VK01_NDX_1990_2000"] = U.cell(nd[(nd.index >= "1990-01-01") & (nd.index <= "2000-12-31")], p_ndx_vix >= 0.8, 20, 1)
    out["VK01_NDX_1990_2000_h5"] = U.cell(nd[(nd.index >= "1990-01-01") & (nd.index <= "2000-12-31")], p_ndx_vix >= 0.8, 5, 1)
    sp = N.frame("SPY")
    p_spy = vrp_pct(sp, vix())
    out["VK02_SPY"] = {h: U.by_era(sp, p_spy >= 0.8, h, 1, [("KESIF", "1990-01-01", "2021-10-31"), ("TEST", "2021-11-01", "2026-12-31")]) for h in (5, 20)}
    q = N.frame("QQQ")
    p_q = vrp_pct(q, vxn())
    ep = episodes(q, p_q)
    out["VK03_QQQ"] = {e: placebo(q, ep[m]) for e, m in (("KESIF", ep.d <= KES), ("TEST", ep.d >= TEST0))}
    ep_n = episodes(nd, p_ndx_vix)
    out["VK03_NDX_VIX_1990_2000"] = placebo(nd, ep_n[(ep_n.d >= "1990-01-01") & (ep_n.d <= "2000-12-31")])
    ep_s = episodes(sp, p_spy)
    out["VK03_SPY"] = {e: placebo(sp, ep_s[m]) for e, m in (("KESIF", ep_s.d <= KES), ("TEST", ep_s.d >= TEST0))}
    hm = {}
    for h in (1, 5, 10, 20, 40, 60):
        days = q.index.to_series()
        f = (q.c.shift(-h) / q.c - 1) * 1e4
        for e, m in (("KESIF", q.index <= KES), ("TEST", q.index >= TEST0)):
            t = (p_q >= 0.8).values & m & f.notna().values
            b = m & f.notna().values
            hm[f"{e}_h{h}"] = round(float(f[t].mean() - f[b].mean()), 1)
    out["VK04_ufuk_fark"] = hm
    out["VK05"] = timing(q, p_q)
    return out


def timing(x: pd.DataFrame, p: pd.Series) -> dict:
    on = (p >= 0.8).astype(float).fillna(0).values
    hold = pd.Series(on).rolling(20, min_periods=1).max().shift(1).fillna(0).values
    r = x.c.pct_change().fillna(0).values
    res = {}
    for e, m in (("TUM_2003", x.index >= "2003-01-01"), ("KESIF_2003", (x.index >= "2003-01-01") & (x.index <= KES)), ("TEST", x.index >= TEST0)):
        for nm, w in (("VP1_zamanlama", hold), ("al_tut", np.ones(len(r)))):
            rr = (w * r)[m]
            eq = np.cumprod(1 + rr)
            res[f"{e}_{nm}"] = {"yillik_%": round(float((eq[-1] ** (252 / len(rr)) - 1) * 100), 1),
                                "sharpe": round(float(rr.mean() / rr.std() * np.sqrt(252)), 2),
                                "maxDD_%": round(float((eq / np.maximum.accumulate(eq) - 1).min() * 100), 1),
                                "maruz_%": round(float(w[m].mean() * 100), 1)}
    return res


# ---------------- KM-01 ----------------
def rsi2(c: pd.Series) -> pd.Series:
    d = c.diff()
    up, dn = d.clip(lower=0), (-d).clip(lower=0)
    rs = up.ewm(alpha=0.5, adjust=False).mean() / dn.ewm(alpha=0.5, adjust=False).mean()
    return 100 - 100 / (1 + rs)


def rule_trades(t: str) -> dict[str, pd.DataFrame]:
    x = ohlc(t)
    c, o, h, l = x.c.values, x.o.values, x.h.values, x.l.values
    idx = x.index
    r2 = rsi2(x.c).values
    out = {}
    rows, i = [], 0
    while i < len(x) - 1:
        if r2[i] < 10:
            j = i + 1
            while j < min(i + 5, len(x) - 1) and not c[j] > c[j - 1]:
                j += 1
            rows.append({"d": idx[i], "net": (c[j] / c[i] - 1) * 1e4 - 2 - FIN * (idx[j] - idx[i]).days})
            i = j
            continue
        i += 1
    out["C3b"] = pd.DataFrame(rows)
    k1 = (c <= (h + l) / 2 * 0.995) & (c < o)
    ii = np.flatnonzero(k1[:-1])
    out["K1"] = pd.DataFrame({"d": idx[ii], "net": (c[ii + 1] / c[ii] - 1) * 1e4 - 2 - FIN * (idx[ii + 1] - idx[ii]).days.values})
    out["ES"] = pd.DataFrame({"d": idx[ii], "net": (c[ii + 1] / (o[ii + 1]) - 1) * 1e4 - 2})
    return out


def dims(t: str, iv: pd.Series) -> dict[str, pd.Series]:
    x = N.frame(t)
    p = vrp_pct(x, iv)
    on = np.log(x.o / x.c.shift(1))
    idr = np.log(x.c / x.o)
    tug = N.pct(on.rolling(20).sum() - idr.rolling(20).sum())
    ew = "QQQE" if t == "QQQ" else "RSP"
    rel = np.log(x.c / N.load(ew).c.reindex(x.index))
    conc = N.pct(rel - rel.shift(20))
    kr = np.log(N.load("HYG").c / N.load("IEF").c).reindex(x.index)
    krp = N.pct(kr - kr.shift(20))
    v = vix().reindex(x.index)
    return {"B1_VP1": p >= 0.8, "B2_VPdusuk": p <= 0.2, "B3_cekisme": tug >= 0.8, "B4_dar": conc >= 0.8, "B5_kredi_zayif": krp <= 0.2,
            "B6_VIX18": v >= 18.4, "_valid": {"B1_VP1": p.notna(), "B2_VPdusuk": p.notna(), "B3_cekisme": tug.notna(), "B4_dar": conc.notna(),
                                             "B5_kredi_zayif": krp.notna(), "B6_VIX18": v.notna()}}


def diff_stat(tr: pd.DataFrame, m: np.ndarray, ok: np.ndarray) -> dict:
    a, b = tr.net.values[m & ok], tr.net.values[~m & ok]
    if len(a) < 5 or len(b) < 5:
        return {"n": int(len(a))}
    rng = np.random.default_rng(4)
    bs = rng.choice(a, (4000, len(a))).mean(1) - rng.choice(b, (4000, len(b))).mean(1)
    return {"n": int(len(a)), "n_degil": int(len(b)), "ile": round(float(a.mean()), 1), "olmadan": round(float(b.mean()), 1),
            "fark": round(float(a.mean() - b.mean()), 1), "P": round(float((bs > 0).mean()), 4)}


def km() -> dict:
    out = {}
    for t, iv in (("QQQ", vxn()), ("SPY", vix())):
        R = rule_trades(t)
        D = dims(t, iv)
        for rn, tr in R.items():
            tr = tr[tr.d >= "2001-01-01"].reset_index(drop=True)
            for bn, ser in D.items():
                if bn.startswith("_"):
                    continue
                m = ser.reindex(tr.d).fillna(False).values.astype(bool)
                ok = D["_valid"][bn].reindex(tr.d).fillna(False).values.astype(bool)
                rec = {}
                for e, em in (("KESIF", (tr.d <= KES).values), ("TEST", (tr.d >= TEST0).values)):
                    rec[e] = diff_stat(tr, m & em, ok & em)
                out[f"{t}_{rn}_{bn}"] = rec
    return out


def main() -> None:
    RES.mkdir(exist_ok=True)
    out = {"VK": vk(), "KM01": km()}
    (RES / "vk_km.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for k, v in out["VK"].items():
        print("VK", k, json.dumps(v, ensure_ascii=False, default=str))
    for k, v in out["KM01"].items():
        print("KM", k, {e: (z.get("n"), z.get("ile"), z.get("olmadan"), z.get("fark"), z.get("P")) for e, z in v.items()})


if __name__ == "__main__":
    main()
