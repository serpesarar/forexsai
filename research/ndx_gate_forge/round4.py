"""Tur 4 — PROTOCOL_4.md (W1–W6): dip kırılımı alımı ailesinin ayrıştırılması."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, load_1m, block_boot
from long_data import load_long, macro

SPR = 0.00006
EXITS = ["d0_16", "d1_10", "d1_16", "d2_16", "d4_16"]


def build(bars: pd.DataFrame, step: int, rth_start: int) -> pd.DataFrame:
    d = bars[["ts", "open", "high", "low", "close"]].copy().reset_index(drop=True)
    ny = d.ts.dt.tz_convert("America/New_York")
    d["nyd"] = pd.to_datetime(ny.dt.date.values)
    d["m"] = (ny.dt.hour * 60 + ny.dt.minute).values
    d["end"] = d.m + step
    d["wd"] = ny.dt.weekday.values
    rth = d[(d.m >= rth_start) & (d.end <= 960)]
    cnt = rth.groupby("nyd").size()
    full_need = (960 - max(rth_start, 570)) // step * 0.8
    lo = rth.groupby("nyd").low.min()[cnt >= full_need]
    days = lo.index.to_numpy()
    k = np.searchsorted(days, d.nyd.to_numpy(), side="left") - 1
    # yalnız bir önceki TAKVİM işlem gününün dibi (arada boşluk ≤4 gün)
    prevday = np.where(k >= 0, days[np.maximum(k, 0)], np.datetime64("NaT"))
    gap = (d.nyd.to_numpy() - prevday).astype("timedelta64[D]").astype(float)
    d["pdl"] = np.where((k >= 0) & (gap <= 4), lo.to_numpy()[np.maximum(k, 0)], np.nan)
    mm = macro()
    full = pd.date_range("2014-01-01", "2026-12-31")
    ndx = mm.NDXCASH_close.dropna()
    prev = d.nyd - pd.Timedelta(days=1)
    f = lambda s: s.reindex(full).ffill().reindex(prev).to_numpy()
    d["r1"], d["r5"] = f(ndx.pct_change()), f(ndx.pct_change(5))
    d["dvol"] = f(ndx.pct_change().rolling(20).std())
    d["vix"] = f(mm.VIX_close.dropna())
    d["year"] = d.nyd.dt.year
    d["step"] = step
    return d


def events(d: pd.DataFrame, stress: str = "stress", vix: str = "hi", trig: str = "break") -> pd.DataFrame:
    w = (d.m >= 180) & (d.end <= 900) & (d.wd <= 3) & d.pdl.notna()
    st = (d.r1 <= -.015) | (d.r5 <= -.04)
    sm = {"stress": st, "nonstress": ~st, "all": st | ~st}[stress]
    vm = {"hi": d.vix >= 18.4, "lo": d.vix < 18.4, "all": d.vix.notna()}[vix]
    ok = w & sm & vm
    below = d.close < d.pdl
    if trig == "break":
        ev = d[ok & below].groupby("nyd").head(1)
    else:   # geri alım: o gün dip altı görüldükten sonra ilk kapanış > dip
        seen = (ok & below).astype(int).groupby(d.nyd).cummax().astype(bool)
        prev_seen = seen.groupby(d.nyd).shift(1, fill_value=False)
        ev = d[ok & prev_seen & ~below].groupby("nyd").head(1)
    ev = ev.copy()
    ev["ei"] = ev.index + 1
    ev = ev[ev.ei < len(d)]
    ev = ev[d.nyd.to_numpy()[ev.ei] == ev.nyd.to_numpy()]
    return ev


_CACHE: dict = {}


def _maps(d: pd.DataFrame):
    key = id(d)
    if key not in _CACHE:
        tdays = np.array(sorted(d.loc[d.end == 960, "nyd"].unique()))
        idx16 = pd.Series(d.index[d.end == 960], index=d.nyd[d.end == 960]).groupby(level=0).last()
        idx10 = pd.Series(d.index[d.end == 600], index=d.nyd[d.end == 600]).groupby(level=0).last()
        _CACHE[key] = (tdays, idx16, idx10)
    return _CACHE[key]


def exits(d: pd.DataFrame, E: pd.DataFrame, stop_k: float | None = 1.0, side: int = 1, only_d0: bool = False) -> pd.DataFrame:
    tdays, idx16, idx10 = _maps(d)
    lo, op, cl = d.low.to_numpy(), d.open.to_numpy(), d.close.to_numpy()
    hi = d.high.to_numpy()
    rows = []
    for r in E.itertuples():
        ei = r.ei
        entry = op[ei]
        k = np.searchsorted(tdays, np.datetime64(r.nyd), side="left")
        if k >= len(tdays) or tdays[k] != np.datetime64(r.nyd):
            continue
        tgt = {}
        for name, off, src in [("d0_16", 0, idx16), ("d1_10", 1, idx10), ("d1_16", 1, idx16), ("d2_16", 2, idx16), ("d4_16", 4, idx16)]:
            kk = k + off
            if kk < len(tdays) and pd.Timestamp(tdays[kk]) in src.index:
                tgt[name] = int(src[pd.Timestamp(tdays[kk])])
        if "d0_16" not in tgt:
            continue
        stop = entry * (1 - side * stop_k * r.dvol) if stop_k else None
        out = {"nyd": r.nyd, "year": r.year, "vix": r.vix, "dvol": r.dvol}
        if only_d0:
            tgt = {"d0_16": tgt["d0_16"]}
        last = max(tgt.values())
        stopped_at, stop_px = None, None
        if stop is not None:
            for j in range(ei, last + 1):
                if (side == 1 and lo[j] <= stop) or (side == -1 and hi[j] >= stop):
                    stopped_at = j
                    stop_px = (min(op[j], stop) if side == 1 else max(op[j], stop)) if j > ei else stop
                    break
        for name in EXITS:
            if name not in tgt:
                out[name] = np.nan
                continue
            j = tgt[name]
            px = stop_px if (stopped_at is not None and stopped_at <= j) else cl[j]
            out[name] = (side * (px / entry - 1) - 2 * SPR) / r.dvol
        rows.append(out)
    return pd.DataFrame(rows)


def stat(x: pd.Series, days: pd.Series) -> dict:
    x = x.dropna()
    if len(x) < 3:
        return {"n": int(len(x))}
    bs = block_boot(x.to_numpy(), days.loc[x.index].astype(str).to_numpy(), 2000)
    q = x.quantile([.05, .95])
    trim = x[(x >= q.iloc[0]) & (x <= q.iloc[1])]
    top = x.sort_values(ascending=False)
    top10 = top.iloc[:max(1, int(round(len(x) * .1)))].sum()
    return {"n": int(len(x)), "ort": round(float(x.mean()), 3), "kırpılmış": round(float(trim.mean()), 3),
            "medyan": round(float(x.median()), 3), "isabet": round(float((x > 0).mean()), 2),
            "P(>0)": round(float(np.mean(bs > 0)), 3), "üst%10_payı": round(float(top10 / x.sum()), 2) if x.sum() > 0 else None}


def placebo(d: pd.DataFrame, E: pd.DataFrame, reps: int = 200, seed: int = 4) -> dict:
    """Aynı olay günlerinde 03:00–15:00 arası rastgele bar → BUY (aynı stop, aynı gün 16:00 çıkışı)."""
    rng = np.random.default_rng(seed)
    win = d[(d.m >= 180) & (d.end <= 900)]
    pools = pd.Series(win.index, index=win.nyd).groupby(level=0).apply(lambda x: x.to_numpy())
    real = exits(d, E, only_d0=True).d0_16.mean()
    means = []
    for _ in range(reps):
        R = E.copy()
        R["ei"] = [int(rng.choice(pools[r.nyd])) + 1 if r.nyd in pools.index else r.ei for r in E.itertuples()]
        R = R[R.ei < len(d)]
        means.append(exits(d, R, only_d0=True).d0_16.mean())
    means = np.array(means)
    return {"gerçek": round(float(real), 3), "plasebo_ort": round(float(np.nanmean(means)), 3),
            "plasebo_%95": round(float(np.nanpercentile(means, 95)), 3), "yüzdelik": round(float(np.mean(means < real)), 3)}


def sources() -> dict:
    out = {}
    out["1h_0900"] = build(load_long("1h"), 60, 540)
    out["1h_1000"] = build(load_long("1h"), 60, 600)
    out["30m"] = build(load_long("30m"), 30, 570)
    out["15m"] = build(load_long("15m"), 15, 570)
    b = load_1m()
    b = b[b.period != ""]
    out["1m"] = build(b, 1, 570)
    return out


def main() -> dict:
    S = sources()
    res = {}
    for name, d in S.items():
        r = {}
        # W1 + W6: 4 hücre (aynı gün 16:00, 1×gvol stop)
        for st in ["stress", "nonstress"]:
            for vx in ["hi", "lo"]:
                x = exits(d, events(d, st, vx))
                r[f"W1 {st}×VIX{vx}"] = stat(x.d0_16, x.nyd) if len(x) else {"n": 0}
        x = exits(d, events(d, "all", "hi"))
        r["W6 VIX≥18,4 (stres şartsız) — olay sayısı/sonuç"] = stat(x.d0_16, x.nyd) if len(x) else {"n": 0}
        # W2: VIX kovaları (stres∧yüksek VIX)
        base = exits(d, events(d, "stress", "hi"))
        if len(base):
            for lo_, hi_ in [(18.4, 25), (25, 35), (35, 200)]:
                m = (base.vix >= lo_) & (base.vix < hi_)
                r[f"W2 VIX {lo_}-{hi_}"] = stat(base.d0_16[m], base.nyd[m])
            yy = base.groupby("year").d0_16.mean()
            r["W2 yıl+"] = f"{int((yy > 0).sum())}/{len(yy)}"
            # W4: çıkış ufku eğrisi
            r["W4 çıkış eğrisi (stres∧VIX≥18,4)"] = {e: stat(base[e], base.nyd).get("ort") for e in EXITS}
            r["W4 çıkış eğrisi P(>0)"] = {e: stat(base[e], base.nyd).get("P(>0)") for e in EXITS}
            nost = exits(d, events(d, "stress", "hi"), stop_k=None)
            r["W4 stopsuz eğri"] = {e: stat(nost[e], nost.nyd).get("ort") for e in EXITS}
        # W5: geri alım
        rc = exits(d, events(d, "stress", "hi", "reclaim"))
        r["W5 geri alım (stres∧VIX≥18,4)"] = stat(rc.d0_16, rc.nyd) if len(rc) else {"n": 0}
        r["W5 geri alım çıkış eğrisi"] = {e: (stat(rc[e], rc.nyd).get("ort") if len(rc) else None) for e in EXITS}
        # W2 plasebo (yalnız 30m ve 1h_0900 — maliyetli)
        if name in ("30m", "1h_0900", "15m"):
            r["W2 saat plasebosu (aynı günler, 200 tekrar)"] = placebo(d, events(d, "stress", "hi"))
        res[name] = r
        print(name, "tamam", flush=True)
    return res


if __name__ == "__main__":
    res = main()
    (OUT / "round4.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for name, r in res.items():
        print(f"\n===== {name} =====")
        for k, v in r.items():
            print(f"  {k}: {v}")
