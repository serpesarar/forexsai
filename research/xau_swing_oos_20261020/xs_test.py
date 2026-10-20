"""XS-01 — XAU Golden Donchian, bağımsız dönem. Ön-kayıt: PROTOCOL.md."""
import json
import numpy as np
import pandas as pd

H1 = pd.read_parquet("../decider_xau_tpsl_20261015/mekanik/data/duka_h1.parquet").rename(columns={"o": "open", "h": "high", "l": "low", "c": "close"})
H1 = H1.sort_values("ts").reset_index(drop=True)
END_OOS = pd.Timestamp("2021-05-01", tz="UTC"); MID = pd.Timestamp("2015-01-01", tz="UTC")
FR = 0.40; N = 55; SL, TP, HOLD = 2.0, 4.0, 20 * 24
rng = np.random.default_rng(2010)


def daily(h):
    ny = h.ts.dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)
    g = h.groupby(ny.dt.floor("1D"))
    d = pd.DataFrame({"ts": g.ts.first(), "open": g.open.first(), "high": g.high.max(), "low": g.low.min(),
                      "close": g.close.last(), "ao": g.ao.first(), "n": g.size()})
    d = d[d.n >= 10].reset_index(drop=True)
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(1)
    d["atr"] = tr.rolling(14).mean(); d["ema200"] = d.close.ewm(span=200, adjust=False).mean()
    d["hh"] = d.high.rolling(N).max().shift(1)
    d["sig"] = (d.close >= d.hh) & (d.close > d.ema200) & (d.index >= 200)
    return d


def sim(entry, sl, tp, j0):
    hi, lo, cl = H1.high.values, H1.low.values, H1.close.values
    end = min(j0 + HOLD, len(H1))
    for j in range(j0, end):
        if lo[j] <= sl:
            return sl, j
        if hi[j] >= tp:
            return tp, j
    return cl[end - 1], end - 1


def run(d, mask, one_pos=True, real=False):
    rows = []; busy = -1; h1ts = H1.ts.values
    for i in np.flatnonzero(mask):
        if i + 1 >= len(d) or not np.isfinite(d.atr[i]):
            continue
        j0 = int(np.searchsorted(h1ts, d.ts.values[i + 1]))
        if one_pos and j0 <= busy:
            continue
        e = d.ao[i + 1] if real else d.open[i + 1]
        risk = SL * d.atr[i]
        x, jx = sim(e, e - risk, e + TP * d.atr[i], j0)
        busy = jx
        net = x - e - (0 if real else FR)
        rows.append({"ts": d.ts[i + 1], "R": net / risk})
    return pd.DataFrame(rows)


def boot(r):
    r = r.to_numpy(); i = rng.integers(0, len(r), (10000, len(r))); return float((r[i].mean(1) > 0).mean())


d = daily(H1)
out = {}
for per, m in (("bagimsiz_2008_2021", d.ts < END_OOS), ("orijinal_2021_2026", d.ts >= END_OOS), ("tum", d.ts.notna())):
    t = run(d, d.sig & m); tr = run(d, d.sig & m, real=True)
    base = run(d, m & (d.index >= 200), one_pos=False)
    o = {"islem": len(t), "WR": float((t.R > 0).mean()), "ortR": float(t.R.mean()), "P_EV": boot(t.R),
         "toplamR": float(t.R.sum()), "ortR_gercek_spread": float(tr.R.mean()), "taban_hergun_BUY_ortR": float(base.R.mean())}
    if per.startswith("bag"):
        o["yari1_ortR"] = float(t[t.ts < MID].R.mean()); o["yari2_ortR"] = float(t[t.ts >= MID].R.mean())
        o["yillar"] = t.assign(y=t.ts.dt.year).groupby("y").R.agg(["size", "sum"]).round(2).to_dict("index")
    out[per] = o
print(json.dumps(out, indent=1, default=str))
json.dump(out, open("sonuc.json", "w"), indent=1, default=str)
