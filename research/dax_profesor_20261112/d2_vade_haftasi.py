"""D2 — Eurex vade haftası (PROTOCOL.md §D2). ^GDAXI günlük + broker GER40 17:30 fiyatı."""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
sys.path.insert(0, "research/dax_profesor_20261112")
from data_load import load
RNG = np.random.default_rng(7)
OUT = Path("research/dax_profesor_20261112/results")
SWAP_BP_NIGHT = 4.94 / 365 * 100

def third_friday(y: int, m: int) -> pd.Timestamp:
    d = pd.Timestamp(y, m, 15)
    return d + pd.Timedelta(days=(4 - d.weekday()) % 7)

def weekly(close: pd.Series) -> pd.DataFrame:
    close = close.dropna(); idx = close.index
    wk = idx.to_period("W-SUN")
    last = close.groupby(wk).tail(1)
    w = pd.DataFrame({"end": last.index, "c": last.values}); w["ret"] = (w.c / w.c.shift() - 1) * 1e4
    days = set(idx.normalize())
    exp = []
    for y in range(idx[0].year, idx[-1].year + 1):
        for m in range(1, 13):
            f = third_friday(y, m)
            while f not in days and f > pd.Timestamp(y, m, 10): f -= pd.Timedelta(days=1)
            if f in days: exp.append((f, m))
    e = pd.DataFrame(exp, columns=["exp", "m"]); e["wk"] = e.exp.dt.to_period("W-SUN")
    w["wk"] = pd.to_datetime(w.end).dt.to_period("W-SUN")
    w["opx"] = w.wk.isin(set(e.wk)); w["q"] = w.wk.isin(set(e[e.m.isin([3, 6, 9, 12])].wk))
    w["post"] = w.opx.shift(1, fill_value=False); w["postq"] = w.q.shift(1, fill_value=False)
    for k in (-2, -1, 1): w[f"shift{k}"] = w.opx.shift(-k, fill_value=False)   # sahte vadeler (plasebo)
    return w.dropna(subset=["ret"])

def diff_stats(w: pd.DataFrame, flag: str) -> dict:
    a, b = w[w[flag]].ret, w[~w[flag]].ret
    yrs = pd.to_datetime(w.end).dt.year.values; uy = np.unique(yrs); g = {y: w[yrs == y] for y in uy}; ds = []
    for _ in range(3000):
        s = pd.concat([g[y] for y in RNG.choice(uy, len(uy))]); ds.append(s[s[flag]].ret.mean() - s[~s[flag]].ret.mean())
    return dict(n=int(len(a)), mean=a.mean(), other=b.mean(), diff=a.mean() - b.mean(), P_pos=float((np.array(ds) > 0).mean()),
                hit=(a > 0).mean())

def run(w: pd.DataFrame) -> dict:
    out = {f: diff_stats(w, f) for f in ("opx", "q", "post", "postq", "shift-2", "shift-1", "shift1")}
    return out

if __name__ == "__main__":
    g = yf.download("^GDAXI", start="1989-12-01", progress=False, auto_adjust=False)["Close"].squeeze()
    g.index = pd.to_datetime(g.index)
    w = weekly(g)
    res = {"KESIF_1990_2007": run(w[(w.end >= "1990-01-01") & (w.end < "2008-01-01")]),
           "TEST_2008_2026": run(w[w.end >= "2008-01-01"])}
    d = load(); d = d[d.ber.dt.strftime("%H:%M") == "17:30"]
    b = pd.Series(d.o.values, index=pd.DatetimeIndex(d.ber.dt.tz_localize(None).dt.normalize()))
    res["BROKER_2019_2026"] = run(weekly(b))
    # mutlak işlenebilirlik: TEST vade haftası uzun, 7 gece swap + 0,5 bp spread
    t = w[(w.end >= "2008-01-01") & w.opx]
    res["TEST_opx_net_bp"] = float(t.ret.mean() - 7 * SWAP_BP_NIGHT - 0.5)
    yrs = t.groupby(pd.to_datetime(t.end).dt.year).ret.mean(); res["TEST_opx_years_pos"] = f"{(yrs>0).sum()}/{len(yrs)}"
    w.to_csv(OUT / "d2_weeks.csv", index=False)
    print(json.dumps(res, indent=1, default=lambda x: round(float(x), 3)))
    json.dump(res, open(OUT / "d2_ozet.json", "w"), indent=1, default=lambda x: round(float(x), 3))
