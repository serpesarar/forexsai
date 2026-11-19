"""vm.py — MX-01 döngü haritası, MX-02 çeyreklik/devir, MX-03 yerel vade doğal deneyi. python vm.py"""
from __future__ import annotations

import calendar as cal
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/son4_20261118/src"))
sys.path.insert(0, str(ROOT / "research/korku_genislik_20261118/src"))
import ox  # noqa: E402
import gn  # noqa: E402  (ek3_veto kullanılmıyordu; içe aktarılınca kendini koşup results/ek3_veto.json'u yeniden yazıyordu)

V, G, KD = ox.V, ox.G, ox.KD
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
NY = "America/New_York"
FIN = V.FIN


# ---------- takvimler ----------
def nth_weekday(y: int, m: int, wd: int, n: int) -> date:
    d = date(y, m, 1)
    d += timedelta(days=(wd - d.weekday()) % 7)
    return d + timedelta(days=7 * (n - 1))


def last_weekday(y: int, m: int, wd: int) -> date:
    d = date(y, m, cal.monthrange(y, m)[1])
    return d - timedelta(days=(d.weekday() - wd) % 7)


def snap(idx: pd.DatetimeIndex, d: date) -> pd.Timestamp | None:
    t = pd.Timestamp(d)
    td = set(idx)
    for _ in range(5):
        if t in td:
            return t
        t -= pd.Timedelta(days=1)
    return None


def expiries(idx: pd.DatetimeIndex, kind: str) -> list[pd.Timestamp]:
    out = []
    for y in range(idx[0].year, idx[-1].year + 1):
        for m in range(1, 13):
            if kind == "fri3":
                d = nth_weekday(y, m, 4, 3)
            elif kind == "fri2":
                d = nth_weekday(y, m, 4, 2)
            elif kind == "thu2":
                d = nth_weekday(y, m, 3, 2)
            elif kind == "thu3":
                d = nth_weekday(y, m, 3, 3)
            elif kind == "wed3":
                d = nth_weekday(y, m, 2, 3)
            elif kind == "hsi":
                ms = idx[(idx.year == y) & (idx.month == m)]
                if len(ms) >= 2:
                    out.append(ms[-2])
                continue
            elif kind == "nifty":
                d = last_weekday(y, m, 3) if (y, m) < (2025, 9) else last_weekday(y, m, 1)
            s = snap(idx, d)
            if s is not None and idx[0] <= s <= idx[-1]:
                out.append(s)
    return sorted(set(out))


def window(idx: pd.DatetimeIndex, ex: list) -> set:
    pos = {d: i for i, d in enumerate(idx)}
    w = set()
    for e in ex:
        i = pos.get(e)
        if i is None:
            continue
        for o in (1, 2):
            if i - o >= 0:
                w.add(idx[i - o])
    return w


def days_to(idx: pd.DatetimeIndex, ex: list) -> np.ndarray:
    pos = np.array([idx.get_loc(e) for e in ex])
    i = np.arange(len(idx))
    j = np.searchsorted(pos, i)
    k = np.where(j < len(pos), pos[np.minimum(j, len(pos) - 1)] - i, 99)
    return k


# ---------- kurallar ----------
def load(name: str) -> pd.DataFrame:
    d = pd.read_parquet(HERE / f"data/{name}.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    x = pd.DataFrame({"o": d.Open, "h": d.High, "l": d.Low, "c": d.Close}).astype(float).dropna()
    return x[(x.c > 0) & (x.h >= x.l)]


def c3b(x: pd.DataFrame) -> pd.DataFrame:
    c, idx = x.c.values, x.index
    r2 = V.rsi2(x.c).values
    rows, i = [], 0
    while i < len(c) - 1:
        if r2[i] < 10:
            j = i + 1
            while j < min(i + 5, len(c) - 1) and not c[j] > c[j - 1]:
                j += 1
            rows.append({"d": idx[i], "net": (c[j] / c[i] - 1) * 1e4 - 2 - FIN * (idx[j] - idx[i]).days})
            i = j
            continue
        i += 1
    return pd.DataFrame(rows)


def k1(x: pd.DataFrame) -> pd.DataFrame:
    c, o, h, l, idx = x.c.values, x.o.values, x.h.values, x.l.values, x.index
    ok = (o != c) & (h != l)  # açılışı kapanışa eşit (eski veri) günleri dışarıda
    m = (c <= (h + l) / 2 * 0.995) & (c < o) & ok
    ii = np.flatnonzero(m[:-1])
    return pd.DataFrame({"d": idx[ii], "net": (c[ii + 1] / c[ii] - 1) * 1e4 - 2 - FIN * (idx[ii + 1] - idx[ii]).days.values})


def diff(t: pd.DataFrame, m: np.ndarray, base: np.ndarray | None = None, seed: int = 0) -> dict:
    b = ~m if base is None else base
    a, bb = t.net.values[m], t.net.values[b]
    if len(a) < 5 or len(bb) < 5:
        return {"n": int(len(a))}
    r = np.random.default_rng(seed)
    bs = r.choice(a, (5000, len(a))).mean(1) - r.choice(bb, (5000, len(bb))).mean(1)
    return {"n": int(len(a)), "n_diger": int(len(bb)), "ic": round(float(a.mean()), 1), "diger": round(float(bb.mean()), 1),
            "fark": round(float(a.mean() - bb.mean()), 1), "P_eksi": round(float((bs < 0).mean()), 4)}


def zpool(sets: list[tuple[pd.DataFrame, np.ndarray]]) -> dict:
    za, zb = [], []
    for t, m in sets:
        s = t.net.std()
        z = (t.net.values - t.net.mean()) / s
        za.append(z[m])
        zb.append(z[~m])
    a, b = np.concatenate(za), np.concatenate(zb)
    r = np.random.default_rng(9)
    bs = r.choice(a, (5000, len(a))).mean(1) - r.choice(b, (5000, len(b))).mean(1)
    return {"n": int(len(a)), "fark_z": round(float(a.mean() - b.mean()), 3), "P_eksi": round(float((bs < 0).mean()), 4)}


# ---------- MX-01 / MX-02 ----------
BUCKETS = (("k0", [0]), ("k1_2_veto", [1, 2]), ("k3_7", list(range(3, 8))), ("k8_12", list(range(8, 13))), ("k13_17", list(range(13, 18))),
           ("k18p", list(range(18, 99))))


def nasdaq_sets() -> dict:
    out = {}
    q, s, nd = V.ohlc("QQQ"), V.ohlc("SPY"), V.ndx_frame()
    for nm, x, rule in (("C3b_QQQ", q, c3b), ("K1_QQQ", q, k1), ("K1_SPY", s, k1)):
        t = rule(x)
        ex = expiries(x.index, "fri3")
        k = days_to(x.index, ex)
        t["k"] = pd.Series(k, index=x.index).reindex(t.d).values
        t["q"] = [((pd.Timestamp(d).month in (3, 6, 9, 12))) for d in t.d]
        out[nm] = t
    n = nd[(nd.index >= "1985-10-01") & (nd.index <= "1999-02-28")]
    t = c3b(n)
    ex = expiries(nd.index, "fri3")
    k = pd.Series(days_to(nd.index, ex), index=nd.index)
    t["k"] = k.reindex(t.d).values
    t["q"] = [pd.Timestamp(d).month in (3, 6, 9, 12) for d in t.d]
    out["C3b_NDX_1985_1999"] = t
    feeds = {"DUKA_NDX": (G.ndx_bars(), 60), "MT5_NAS100": (KD.mt5_m30("NAS100"), 1800), "MT5_US500": (KD.mt5_m30("US500", "2018-06-01"), 1800),
             "MT5_US30": (KD.mt5_m30("US30"), 1800), "MT5_US2000": (KD.mt5_m30("US2000"), 1800)}
    for nm, (b, st) in feeds.items():
        kk = gn.nts(b, st)
        kk = kk[kk.K1].reset_index(drop=True)
        idx = pd.DatetimeIndex(pd.to_datetime(sorted(set(G.day_prices(b, NY, [960], st).index))))
        ex = expiries(idx, "fri3")
        kser = pd.Series(days_to(idx, ex), index=idx)
        kk["d"] = pd.to_datetime(kk.d)
        kk["k"] = kser.reindex(kk.d).values
        kk["q"] = kk.d.dt.month.isin([3, 6, 9, 12]).values
        out[f"K1gi_{nm}"] = kk[["d", "net", "k", "q"]]
    return out


def mx01(S: dict) -> dict:
    res = {}
    for bn, ks in BUCKETS:
        rec = {nm: diff(t, np.isin(t.k.values, ks), seed=3) for nm, t in S.items()}
        rec["havuz_z"] = zpool([(t, np.isin(t.k.values, ks)) for t in S.values()])
        res[bn] = rec
    return res


def mx02(S: dict) -> dict:
    res = {}
    veto = lambda t: np.isin(t.k.values, [1, 2])  # noqa: E731
    res["veto_ceyreklik"] = zpool([(t, veto(t) & t.q.values) for t in S.values()])
    res["veto_aylik"] = zpool([(t, veto(t) & ~t.q.values) for t in S.values()])
    res["devir_haftasi"] = zpool([(t, np.isin(t.k.values, range(5, 10)) & t.q.values) for t in S.values()])
    res["devir_haftasi_set"] = {nm: diff(t, np.isin(t.k.values, range(5, 10)) & t.q.values, seed=5) for nm, t in S.items()}
    return res


# ---------- MX-03 ----------
MARKETS = {"N225": "fri2", "KS11": "thu2", "HSI": "hsi", "AXJO": "thu3", "NSEI": "nifty", "TWII": "wed3",
           "GDAXI": "fri3", "STOXX50E": "fri3", "FCHI": "fri3", "FTSE": "fri3"}


def mx03() -> dict:
    res = {}
    loc_sets, us_sets = [], []
    for mk, kind in MARKETS.items():
        x = load(mk)
        if mk == "N225":
            x = x[x.index >= "1989-06-01"]
        if mk == "KS11":
            x = x[x.index >= "1997-07-01"]
        loc = window(x.index, expiries(x.index, kind))
        us = window(x.index, expiries(x.index, "fri3"))
        rec = {}
        for rn, rule in (("C3b", c3b), ("K1", k1)):
            t = rule(x)
            if len(t) < 30:
                continue
            ml = t.d.isin(loc).values
            mu = t.d.isin(us).values
            rec[f"{rn}_taban_ort"] = round(float(t.net.mean()), 1)
            rec[f"{rn}_yerel"] = diff(t, ml, seed=11)
            if kind != "fri3":
                rec[f"{rn}_ABD"] = diff(t, mu & ~ml, base=~mu & ~ml, seed=12)
                loc_sets.append((t, ml))
                us_sets.append((t, mu & ~ml))
        res[mk] = {"takvim": kind, **rec}
    res["havuz_farkli_takvim_yerel"] = zpool(loc_sets)
    res["havuz_farkli_takvim_ABD"] = zpool(us_sets)
    return res


def main() -> None:
    RES.mkdir(exist_ok=True)
    S = nasdaq_sets()
    out = {"MX01": mx01(S), "MX02": mx02(S), "MX03": mx03()}
    (RES / "vm.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for bn, rec in out["MX01"].items():
        print("MX01", bn, "havuz", rec["havuz_z"], {k: (v.get("n"), v.get("fark")) for k, v in rec.items() if k != "havuz_z"})
    for k, v in out["MX02"].items():
        print("MX02", k, v)
    for k, v in out["MX03"].items():
        print("MX03", k, v)


if __name__ == "__main__":
    main()
