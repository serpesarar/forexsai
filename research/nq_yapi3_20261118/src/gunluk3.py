"""gunluk3.py — MC (iç korelasyon), YC (yen carry), FD (FOMC döngüsü). python gunluk3.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/nq_kombi_20261118/src"))
import vk as V  # noqa: E402

N, U, FIN = V.N, V.U, V.FIN
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
KES, TEST0 = V.KES, V.TEST0
STOCKS = ["AAPL", "MSFT", "AMZN", "INTC", "CSCO", "QCOM", "ADBE", "AMGN", "COST", "PEP", "CMCSA", "NVDA"]


def mega() -> pd.DataFrame:
    d = pd.read_parquet(HERE / "data/megacap_jpy.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return d


def fwd(x: pd.DataFrame, i: int, h: int, side: int) -> float:
    c, idx = x.c.values, x.index
    cal = (idx[i + h] - idx[i]).days
    return side * (c[i + h] / c[i] - 1) * 1e4 - 2 - (FIN * cal if side > 0 else 0)


def episodes(x: pd.DataFrame, trig: np.ndarray, h: int, side: int, need_off: bool = True) -> pd.DataFrame:
    rows, busy = [], -1
    for i in range(5, len(x) - h):
        if trig[i] and i > busy and (not need_off or not trig[i - 5:i].any()):
            rows.append({"d": x.index[i], "net": fwd(x, i, h, side)})
            busy = i + h
    return pd.DataFrame(rows)


def placebo(x: pd.DataFrame, ep: pd.DataFrame, h: int, side: int, n: int = 2000) -> dict:
    if len(ep) < 5:
        return {"n": int(len(ep))}
    rng = np.random.default_rng(13)
    yrs = x.index.year.values
    ok = np.arange(len(x)) < len(x) - h
    pools = {y: np.flatnonzero((yrs == y) & ok) for y in set(ep.d.dt.year)}
    ys = ep.d.dt.year.values
    sims = np.array([np.mean([fwd(x, int(rng.choice(pools[y])), h, side) for y in ys]) for _ in range(n)])
    r = float(ep.net.mean())
    return {"n": int(len(ep)), "ort": round(r, 1), "plasebo": round(float(sims.mean()), 1), "fark": round(r - float(sims.mean()), 1),
            "yuzdelik": round(float((sims < r).mean()), 4), "isabet": round(float((ep.net > 0).mean()), 3), "en_kotu": round(float(ep.net.min()), 1)}


def by_era(x: pd.DataFrame, trig: np.ndarray, h: int, side: int, need_off: bool = True) -> dict:
    ep = episodes(x, trig, h, side, need_off)
    if ep.empty:
        return {"KESIF": {"n": 0}, "TEST": {"n": 0}}
    return {"KESIF": placebo(x, ep[ep.d <= KES], h, side), "TEST": placebo(x, ep[ep.d >= TEST0], h, side)}


def pick(x: pd.DataFrame, trig: np.ndarray, h: int, need_off: bool = True) -> dict:
    k = by_era(x, trig, h, 1, need_off)["KESIF"]
    side = 1 if k.get("fark", 0) >= 0 else -1
    return {"yon": side, **by_era(x, trig, h, side, need_off)}


def mc() -> dict:
    m = mega()[STOCKS].dropna(how="all")
    r = np.log(m).diff()
    out = {}
    for t in ("QQQ", "SPY"):
        x = N.frame(t)
        rr = r.reindex(x.index)
        cors = []
        for i in range(len(rr)):
            w = rr.iloc[max(0, i - 19):i + 1].dropna(axis=1, how="any")
            if i < 19 or w.shape[1] < 8:
                cors.append(np.nan)
                continue
            cm = np.corrcoef(w.values.T)
            cors.append(cm[np.triu_indices_from(cm, 1)].mean())
        rho = pd.Series(cors, index=x.index)
        p = N.pct(rho)
        hi = (p >= 0.8).fillna(False).values
        lo = (p <= 0.2).fillna(False).values
        for h in (5, 20):
            out[f"{t}_MC1_yuksek_rho_h{h}"] = pick(x, hi, h)
            out[f"{t}_MC2_dusuk_rho_h{h}"] = pick(x, lo, h)
        mm = m.reindex(x.index)
        near = (mm >= mm.rolling(20).max() * 0.98).sum(axis=1)
        newhi = (x.c >= x.c.rolling(20).max()).values
        trig = newhi & (near <= 4).values
        for h in (5, 20):
            out[f"{t}_MC3_dar_tepe_SAT_h{h}"] = by_era(x, trig, h, -1, need_off=False)
    return out


def yc() -> dict:
    j = mega()["JPY=X"].dropna()
    out = {}
    for t in ("QQQ", "SPY"):
        x = N.frame(t)
        jj = j.reindex(x.index).ffill()
        r5 = (jj / jj.shift(5) - 1).values
        q5 = (x.c / x.c.shift(5) - 1).values
        trig = np.nan_to_num(r5) <= -0.025
        for h in (5, 20):
            out[f"{t}_YC_h{h}"] = pick(x, trig, h)
            out[f"{t}_YC_hisse_dusuk_h{h}"] = pick(x, trig & (np.nan_to_num(q5) <= -0.03), h)
    return out


def fd() -> dict:
    cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    fomc = sorted(set(pd.to_datetime(cal[cal.event.str.upper().str.contains("FOMC")].date)))
    out = {}
    for t in ("QQQ", "SPY"):
        x = N.frame(t)
        idx = x.index
        r = (x.c / x.c.shift(1) - 1).values * 1e4
        pos = np.searchsorted(idx, pd.DatetimeIndex(fomc))
        k = np.full(len(idx), -1)
        last = None
        fset = set(int(p) for p, f in zip(pos, fomc) if p < len(idx) and idx[p] == f)
        for i in range(len(idx)):
            if i in fset:
                last = i
            if last is not None:
                k[i] = i - last
        # hafta t: k ∈ [5t−1, 5t+3]; k=−1 (FOMC'den önceki gün) bir sonraki döngünün haftası 0
        nxt = np.full(len(idx), 10 ** 6)
        nf = None
        for i in range(len(idx) - 1, -1, -1):
            if i in fset:
                nf = i
            if nf is not None:
                nxt[i] = nf - i
        kk = np.where(nxt == 1, -1, k)
        week = np.floor((kk + 1) / 5).astype(int)
        valid = (kk >= -1) & (kk <= 33) & (idx >= pd.Timestamp(fomc[0]))
        even = valid & (week % 2 == 0)
        odd = valid & (week % 2 == 1)
        rec = {}
        for e, a, b in (("ICORNEK_2008_2016", "2008-01-01", "2016-12-31"), ("YAYIN_SONRASI_2017_2021", "2017-01-01", "2021-10-31"),
                        ("TEST", "2021-11-01", "2026-12-31")):
            sel = (idx >= a) & (idx <= b) & np.isfinite(r)
            ev, od = r[even & sel], r[odd & sel]
            rec[e] = {"n_cift": int(len(ev)), "n_tek": int(len(od)), "cift": round(float(ev.mean()), 2), "tek": round(float(od.mean()), 2),
                      "fark": round(float(ev.mean() - od.mean()), 2), "P": round(V.ath.bboot(ev, od, 5), 4),
                      "hafta0": round(float(r[valid & (week == 0) & sel].mean()), 2)}
        out[t] = rec
    return out


def main() -> None:
    RES.mkdir(exist_ok=True)
    out = {"MC": mc(), "YC": yc(), "FD": fd()}
    (RES / "gunluk3.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for fam, cs in out.items():
        for k, v in cs.items():
            print(fam, k, json.dumps(v, ensure_ascii=False))


if __name__ == "__main__":
    main()
