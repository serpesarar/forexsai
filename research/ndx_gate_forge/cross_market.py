"""CAPREV bağımsız piyasa testi — kural NDX'ten DEĞİŞTİRİLMEDEN taşındı.

(1) DAX (GDAXI, candle_cache UTC): stres = DAX'ın kendi önceki Xetra kapanışı getirisi ≤ −%1,5 veya 5g ≤ −%4;
    VIX(önceki ABD günü) ≥ 18,4; Pzt–Per Berlin 08:00–16:30 arasında önceki Xetra (09:00–17:30) dibinin altındaki
    İLK bar kapanışı → sonraki bar açılışında BUY; 1×günlük-vol stop; çıkış aynı gün 17:30 / ertesi gün 17:30.
(2) Günlük OHLC (macro_daily: SPX, QQQ, NDXCASH, 2015+): stres günü & gün içi dip < önceki gün dibi →
    önceki gün dibinden limit BUY (açılış altındaysa açılıştan), kapanışta çık. Kaba ama bağımsız endeks.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, DATA, block_boot
from long_data import macro

SPR = 0.00006


def build_dax(tf: str) -> pd.DataFrame:
    step = {"1h": 60, "30m": 30, "15m": 15}[tf]
    d = pd.read_parquet(DATA / f"dax_{tf}.parquet")
    d = d[d.ts >= "2019-01-01"].reset_index(drop=True)
    be = d.ts.dt.tz_convert("Europe/Berlin")
    d["nyd"] = pd.to_datetime(be.dt.date.values)
    d["m"] = (be.dt.hour * 60 + be.dt.minute).values
    d["end"] = d.m + step
    d["wd"] = be.dt.weekday.values
    close_end = 1050 if step <= 30 else 1080          # 17:30 (1h'te 18:00 yaklaşımı)
    rth = d[(d.m >= 540) & (d.end <= close_end)]
    cnt = rth.groupby("nyd").size()
    lo = rth.groupby("nyd").low.min()[cnt >= (close_end - 540) / step * 0.8]
    cl = d[d.end == close_end].groupby("nyd").close.last()
    days = lo.index.to_numpy()
    k = np.searchsorted(days, d.nyd.to_numpy(), side="left") - 1
    gap = (d.nyd.to_numpy() - np.where(k >= 0, days[np.maximum(k, 0)], np.datetime64("NaT"))).astype("timedelta64[D]").astype(float)
    d["pdl"] = np.where((k >= 0) & (gap <= 4), lo.to_numpy()[np.maximum(k, 0)], np.nan)
    ret = cl.pct_change()
    full = pd.date_range("2018-01-01", "2026-12-31")
    prev = d.nyd - pd.Timedelta(days=1)
    f = lambda s: s.reindex(full).ffill().reindex(prev).to_numpy()
    d["r1"], d["r5"], d["dvol"] = f(ret), f(cl.pct_change(5)), f(ret.rolling(20).std())
    d["vix"] = f(macro().VIX_close.dropna())
    d["year"] = d.nyd.dt.year
    d["close_end"] = close_end
    return d


def events(d: pd.DataFrame, stress: str, vix: str) -> pd.DataFrame:
    w = (d.m >= 480) & (d.end <= 990) & (d.wd <= 3) & d.pdl.notna()
    st = (d.r1 <= -.015) | (d.r5 <= -.04)
    sm = {"stress": st, "nonstress": ~st}[stress]
    vm = {"hi": d.vix >= 18.4, "lo": d.vix < 18.4, "all": d.vix.notna()}[vix]
    ev = d[w & sm & vm & (d.close < d.pdl)].groupby("nyd").head(1).copy()
    ev["ei"] = ev.index + 1
    ev = ev[(ev.ei < len(d))]
    return ev[d.nyd.to_numpy()[ev.ei] == ev.nyd.to_numpy()]


def exits(d: pd.DataFrame, E: pd.DataFrame, side: int = 1) -> pd.DataFrame:
    ce = d.close_end.iat[0]
    idx = pd.Series(d.index[d.end == ce], index=d.nyd[d.end == ce]).groupby(level=0).last()
    tdays = idx.index.to_numpy()
    lo, hi, op, cl = (d[c].to_numpy() for c in ["low", "high", "open", "close"])
    rows = []
    for r in E.itertuples():
        k = np.searchsorted(tdays, np.datetime64(r.nyd))
        if k >= len(tdays) or tdays[k] != np.datetime64(r.nyd):
            continue
        entry = op[r.ei]
        stop = entry * (1 - side * r.dvol)
        out = {"nyd": r.nyd, "year": r.year, "vix": r.vix}
        tg = {"d0": int(idx.iloc[k])}
        if k + 1 < len(tdays):
            tg["d1"] = int(idx.iloc[k + 1])
        sp = None
        for j in range(r.ei, max(tg.values()) + 1):
            if (side == 1 and lo[j] <= stop) or (side == -1 and hi[j] >= stop):
                sp = (j, (min(op[j], stop) if side == 1 else max(op[j], stop)) if j > r.ei else stop)
                break
        for n_, j in tg.items():
            px = sp[1] if sp and sp[0] <= j else cl[j]
            out[n_] = (side * (px / entry - 1) - 2 * SPR) / r.dvol
        rows.append(out)
    return pd.DataFrame(rows)


def stat(x: pd.DataFrame, col: str) -> dict:
    v = x[col].dropna() if len(x) else pd.Series(dtype=float)
    if len(v) < 3:
        return {"n": int(len(v))}
    bs = block_boot(v.to_numpy(), x.loc[v.index, "nyd"].astype(str).to_numpy(), 2000)
    py = x.loc[v.index].groupby("year")[col].mean()
    q = v.quantile([.05, .95])
    return {"n": int(len(v)), "ort": round(float(v.mean()), 3), "kırpılmış": round(float(v[(v >= q.iloc[0]) & (v <= q.iloc[1])].mean()), 3),
            "medyan": round(float(v.median()), 3), "isabet": round(float((v > 0).mean()), 2),
            "P(>0)": round(float(np.mean(bs > 0)), 3), "yıl+": f"{int((py > 0).sum())}/{len(py)}"}


def hour_placebo(d: pd.DataFrame, E: pd.DataFrame, reps: int = 200) -> dict:
    rng = np.random.default_rng(9)
    win = d[(d.m >= 480) & (d.end <= 990)]
    pools = pd.Series(win.index, index=win.nyd).groupby(level=0).apply(lambda x: x.to_numpy())
    real = exits(d, E).d0.mean()
    ms = []
    for _ in range(reps):
        R = E.copy()
        R["ei"] = [int(rng.choice(pools[r.nyd])) + 1 if r.nyd in pools.index else r.ei for r in E.itertuples()]
        ms.append(exits(d, R[R.ei < len(d)]).d0.mean())
    ms = np.array(ms)
    return {"gerçek": round(float(real), 3), "plasebo_ort": round(float(np.nanmean(ms)), 3),
            "plasebo_%95": round(float(np.nanpercentile(ms, 95)), 3), "yüzdelik": round(float(np.mean(ms < real)), 3)}


def daily_indices() -> dict:
    m = macro()
    out = {}
    for name, p in [("SPX", "SPX"), ("QQQ", "QQQ"), ("NDXCASH", "NDXCASH")]:
        x = m[[f"{p}_open", f"{p}_high", f"{p}_low", f"{p}_close", "VIX_close"]].dropna().copy()
        x.columns = ["o", "h", "l", "c", "vix"]
        x["pl"] = x.l.shift(1)
        x["r1"] = x.c.pct_change().shift(1)
        x["r5"] = x.c.pct_change(5).shift(1)
        x["dvol"] = x.c.pct_change().rolling(20).std().shift(1)
        x["vixp"] = x.vix.shift(1)
        x["wd"] = x.index.weekday
        x["year"] = x.index.year
        st = (x.r1 <= -.015) | (x.r5 <= -.04)
        touch = x.l < x.pl
        entry = np.minimum(x.o, x.pl)
        x["ret"] = (x.c / entry - 1 - 2 * SPR) / x.dvol
        x["nyd"] = x.index
        for lab, msk in {"stres∧VIX≥18,4": st & (x.vixp >= 18.4), "stres∧VIX<18,4": st & (x.vixp < 18.4),
                         "stressiz∧VIX≥18,4": ~st & (x.vixp >= 18.4)}.items():
            e = x[msk & touch & (x.wd <= 3)]
            out[f"{name} {lab}"] = stat(e, "ret")
        # kontrol: aynı stres günlerinde açılıştan BUY → kapanış (dip kırılımı şartı yok)
        e = x[st & (x.vixp >= 18.4) & (x.wd <= 3)].copy()
        e["ret_open"] = (e.c / e.o - 1 - 2 * SPR) / e.dvol
        out[f"{name} kontrol: stres∧VIX≥18,4 açılıştan BUY"] = stat(e, "ret_open")
    return out


def main() -> dict:
    res = {}
    for tf in ["1h", "30m", "15m"]:
        d = build_dax(tf)
        r = {}
        for st in ["stress", "nonstress"]:
            for vx in ["hi", "lo"]:
                x = exits(d, events(d, st, vx))
                r[f"{st}×VIX{vx} aynı gün"] = stat(x, "d0")
                if st == "stress" and vx == "hi":
                    r["stress×VIXhi ertesi gün"] = stat(x, "d1")
                    r["ayna SELL aynı gün"] = stat(exits(d, events(d, st, vx), side=-1), "d0")
                    r["saat plasebosu"] = hour_placebo(d, events(d, st, vx))
        res[f"DAX {tf}"] = r
        print(tf, "tamam", flush=True)
    res["Günlük endeksler (2015+)"] = daily_indices()
    return res


if __name__ == "__main__":
    res = main()
    (OUT / "cross_market.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for k, r in res.items():
        print(f"\n===== {k} =====")
        for kk, v in r.items():
            print(f"  {kk}: {v}")
