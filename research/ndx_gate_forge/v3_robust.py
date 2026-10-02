"""V3 kapitülasyon alımı — sağlamlık bataryası (10y 1h + 5y 30m + 3.4y 15m).

Olay: stres günü (önceki ABD günü NDX ≤ −%1,5 veya 5g ≤ −%4), NY 03:00–15:00 arası ilk bar
kapanışı < önceki RTH dibi → sonraki bar açılışında BUY.
Çıkışlar: (a) 16:00 NY kapanış, (b) yüzde braket TP %0,35 / SL %0,48 (≈80/110), (c) ertesi gün 16:00.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, block_boot
from long_data import load_long, macro
from daylevel_trades import walk_pct

SPR = 0.00006


def prep(tf: str) -> pd.DataFrame:
    d = load_long(tf).copy()
    step = {"15m": 15, "30m": 30, "1h": 60}[tf]
    ny = d.ts.dt.tz_convert("America/New_York")
    d["nyd"] = pd.to_datetime(ny.dt.date.values)
    d["m"] = (ny.dt.hour * 60 + ny.dt.minute).values
    d["end"] = d.m + step
    d["wd"] = ny.dt.weekday.values
    rth = d[(d.m >= 9 * 60 + (30 if step < 60 else 0)) & (d.end <= 16 * 60)]
    lo = rth.groupby("nyd").low.min()
    days = lo.index.to_numpy()
    k = np.searchsorted(days, d.nyd.to_numpy(), side="left") - 1
    d["pdl"] = np.where(k >= 0, lo.to_numpy()[np.maximum(k, 0)], np.nan)
    m = macro()
    full = pd.date_range("2014-01-01", "2026-12-31")
    ndx = m.NDXCASH_close.dropna()
    prev = d.nyd - pd.Timedelta(days=1)
    f = lambda s: s.reindex(full).ffill().reindex(prev).to_numpy()
    d["r1"], d["r5"] = f(ndx.pct_change()), f(ndx.pct_change(5))
    d["dvol"] = f(ndx.pct_change().rolling(20).std())
    d["vix"] = f(m.VIX_close.dropna())
    d["t"] = d.ts.astype("int64") // 10**9
    d["step"] = step
    return d.reset_index(drop=True)


def events(d: pd.DataFrame, r1=-.015, r5=-.04, depth=0.0, stress_mode="stress", delay=1) -> pd.DataFrame:
    step = d.step.iat[0]
    w = (d.m >= 180) & (d.end <= 15 * 60) & (d.wd <= 3)
    stress = (d.r1 <= r1) | (d.r5 <= r5)
    cond = {"stress": stress, "nonstress": ~stress, "all": stress | ~stress}[stress_mode]
    ev = w & cond & (d.close < d.pdl * (1 - depth))
    first = d[ev].groupby("nyd").head(1).copy()
    first["ei"] = first.index + delay            # giriş barı
    first = first[first.ei < len(d)]
    first = first[(d.nyd.to_numpy()[first.ei] == first.nyd.to_numpy())]
    return first


def outcomes(d: pd.DataFrame, E: pd.DataFrame, spr_mult: float = 1.0, side: int = 1) -> pd.DataFrame:
    close16 = d[d.end == 16 * 60].groupby("nyd").close.last()
    close16_next = close16.shift(-1)
    entry = d.open.to_numpy()[E.ei]
    s = SPR * spr_mult
    x = E[["nyd"]].copy()
    x["year"] = x.nyd.dt.year
    x["dvol"] = E.dvol.to_numpy()
    x["vix"] = E.vix.to_numpy()
    ex = close16.reindex(E.nyd).to_numpy()
    x["r_close"] = (side * (ex / entry - 1) - 2 * s) / x.dvol          # günlük-vol birimi
    x["pct_close"] = side * (ex / entry - 1) - 2 * s
    exn = close16_next.reindex(E.nyd).to_numpy()
    x["r_next"] = (side * (exn / entry - 1) - 2 * s) / x.dvol
    R = walk_pct(d.t.to_numpy(), d.open.to_numpy(float), d.high.to_numpy(float), d.low.to_numpy(float),
                 d.close.to_numpy(float), (E.ei - 1).to_numpy(), np.full(len(E), side), .00348, .00478, s, 12 * 3600, 3 * 3600)
    x["R_80_110"] = R
    return x.dropna(subset=["r_close"])


def summ(x: pd.DataFrame, col: str) -> dict:
    if len(x) == 0:
        return {"n": 0}
    v = x[col].dropna()
    bs = block_boot(v.to_numpy(), x.loc[v.index, "nyd"].astype(str).to_numpy(), 3000)
    py = x.groupby("year")[col].mean()
    return {"n": int(len(v)), "ort": round(float(v.mean()), 3), "medyan": round(float(v.median()), 3),
            "isabet": round(float((v > 0).mean()), 3), "P(>0)": round(float(np.mean(bs > 0)), 3),
            "yıl+": f"{int((py > 0).sum())}/{len(py)}"}


def main() -> dict:
    res = {}
    for tf in ["1h", "30m", "15m"]:
        d = prep(tf)
        base = outcomes(d, events(d))
        r = {"temel (16:00 çıkış, gvol)": summ(base, "r_close"), "temel % getiri": summ(base, "pct_close"),
             "80/110 braket (R)": summ(base, "R_80_110"), "ertesi gün 16:00 (gvol)": summ(base, "r_next"),
             "spread ×3": summ(outcomes(d, events(d), 3.0), "r_close"),
             "giriş +1 bar gecikme": summ(outcomes(d, events(d, delay=2)), "r_close"),
             "kontrol: stressiz gün aynı olay": summ(outcomes(d, events(d, stress_mode="nonstress")), "r_close"),
             "ayna: aynı olayda SELL": summ(outcomes(d, events(d), side=-1), "r_close")}
        # yıl çıkarma & uç günler
        if len(base):
            r["en iyi 5 gün çıkarılınca"] = summ(base.sort_values("r_close").iloc[:-5], "r_close")
            r["2020+2022 çıkarılınca"] = summ(base[~base.year.isin([2020, 2022])], "r_close")
            r["VIX<18.4 günleri"] = summ(base[base.vix < 18.4], "r_close")
            r["VIX≥18.4 günleri"] = summ(base[base.vix >= 18.4], "r_close")
            r["yıl yıl ort"] = base.groupby("year").r_close.agg(["size", "mean"]).round(3).to_dict("index")
        # eşik duyarlılığı (seçim değil, bıçak-sırtı kontrolü)
        grid = {}
        for r1 in (-.01, -.015, -.02):
            for r5 in (-.03, -.04, -.05):
                x = outcomes(d, events(d, r1=r1, r5=r5))
                grid[f"r1≤{r1:.1%}|r5≤{r5:.0%}"] = (len(x), round(float(x.r_close.mean()), 3) if len(x) else None)
        r["eşik ızgarası (n, ort)"] = grid
        dep = {}
        for dp in (0.0, 0.0025, 0.005):
            x = outcomes(d, events(d, depth=dp))
            dep[f"dip altı ≥%{dp*100:.2f}"] = (len(x), round(float(x.r_close.mean()), 3) if len(x) else None)
        r["derinlik"] = dep
        res[tf] = r
    return res


if __name__ == "__main__":
    res = main()
    (OUT / "v3_robust.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for tf, r in res.items():
        print(f"\n===== {tf} =====")
        for k, v in r.items():
            print(f"  {k}: {v}")
