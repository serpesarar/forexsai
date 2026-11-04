#!/usr/bin/env python3
"""Offline, causal NDX strategy search and frozen out-of-sample validation.

See PROTOCOL.md. No MT5, remote, database or order API is used.
All OHLC timestamps denote bar START; feature timestamps denote availability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
CACHE = ROOT / "nasdaq_1m_candle_cache_2026-02-10_2026-08-29/nasdaq_1m_candle_cache_TAM_2026-02-10_2026-08-29.csv"
MT5 = ROOT / "nasdaq_tam_veri_2026-08-29/1m_veri/NAS100_1m_2026-05-19_2026-08-28.csv"
PERIODS = {
    "discovery": ("2026-02-11", "2026-05-16"),
    "discovery_a": ("2026-02-11", "2026-04-01"),
    "discovery_b": ("2026-04-01", "2026-05-16"),
    "validation": ("2026-05-20", "2026-07-01"),
    "validation_a": ("2026-05-20", "2026-06-10"),
    "validation_b": ("2026-06-10", "2026-07-01"),
    "final": ("2026-07-02", "2026-08-29"),
    "final_a": ("2026-07-02", "2026-08-01"),
    "final_b": ("2026-08-01", "2026-08-29"),
}
FAMILIES = ["pullback", "sweep", "compression", "absorption", "exhaustion",
            "failed_break", "efficient_pullback", "vwap_reclaim", "opening_break",
            "opening_failure", "two_shock", "midpoint_reclaim"]


def stamp(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").timestamp())


def save_json(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def read_bars(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d["ts"] = pd.to_datetime(d.time_utc, format="ISO8601", utc=True)
    d["volume"] = d.get("tick_volume", d.get("volume"))
    d["spread_px"] = d["spread"] * .1 if "spread" in d else 1.3
    d["source"] = "mt5" if "spread" in d else "cache"
    return d[["ts", "open", "high", "low", "close", "volume", "spread_px", "source"]].sort_values("ts").reset_index(drop=True)


def atr(d: pd.DataFrame, n: int) -> pd.Series:
    c = d.close.shift()
    tr = pd.concat([d.high-d.low, (d.high-c).abs(), (d.low-c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False, min_periods=n).mean()


def load() -> pd.DataFrame:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "bars.pkl"
    if p.exists():
        return pd.read_pickle(p)
    a, b = read_bars(CACHE), read_bars(MT5)
    audit = {"source_hashes": {}, "sources": {}, "offset_scan": []}
    for path, d in [(CACHE, a), (MT5, b)]:
        bad = (d.high < d[["open", "close"]].max(axis=1)) | (d.low > d[["open", "close"]].min(axis=1)) | (d.high < d.low)
        if bad.any() or d.ts.duplicated().any():
            raise ValueError(f"Bad OHLC/duplicate timestamps: {path}")
        audit["source_hashes"][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        audit["sources"][d.source.iloc[0]] = {"rows": len(d), "start": str(d.ts.iloc[0]), "end": str(d.ts.iloc[-1]), "bad_ohlc": int(bad.sum())}
    ta = a.ts.dt.as_unit("s").astype("int64").to_numpy()
    tb = b.ts.dt.as_unit("s").astype("int64").to_numpy()
    for lag in [-180, -120, 0, 120, 180]:
        _, ia, ib = np.intersect1d(ta+lag*60, tb, return_indices=True)
        err = np.abs(a.close.to_numpy()[ia]-b.close.to_numpy()[ib])
        audit["offset_scan"].append({"shift_minutes": lag, "overlap": len(err), "median_error_points": float(np.median(err)), "within_5_points": float(np.mean(err <= 5))})
    # Already repaired export. Never apply the historical repair a second time.
    d = pd.concat([a[a.ts < b.ts.iloc[0]], b], ignore_index=True).sort_values("ts").reset_index(drop=True)
    d["t"] = d.ts.dt.as_unit("s").astype("int64")
    d["atr70"] = atr(d, 70)
    d["atr14"] = atr(d, 14)
    ny = d.ts.dt.tz_convert("America/New_York")
    d["ny_min"] = ny.dt.hour*60+ny.dt.minute
    d["day"] = ny.dt.strftime("%Y-%m-%d")
    d["weekday"] = ny.dt.weekday
    d["valid60"] = d.t.diff().eq(60).rolling(60, min_periods=60).sum().eq(60)
    gaps = d.t.diff().fillna(60)
    audit["merged_rows"] = len(d)
    audit["gap_sizes_minutes"] = {str(k): int(v) for k, v in (gaps/60).value_counts().head(12).items()}
    audit["mt5_spread_points"] = {str(k): float(v) for k, v in b.spread_px.describe(percentiles=[.5,.9,.99]).items()}
    # Intraday volatility anchor is a diagnostic, not a strategy-selection feature.
    for name, x in [("cache", a), ("mt5", b)]:
        local = x.ts.dt.tz_convert("America/New_York")
        temp = pd.DataFrame({"month": x.ts.dt.strftime("%Y-%m"), "minute": local.dt.hour*60+local.dt.minute, "range": x.high-x.low})
        g = temp.groupby(["month", "minute"]).range.mean().reset_index()
        peaks = g.loc[g.groupby("month").range.idxmax()]
        audit[f"{name}_monthly_range_peak_ny"] = peaks.to_dict("records")
    d.to_pickle(p)
    save_json(OUT / "data_audit.json", audit)
    return d


def features(d: pd.DataFrame, tf: int = 1) -> pd.DataFrame:
    """A feature row exists only at the close of a complete aggregation bin."""
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "t": "count"}
    f = d.set_index("ts").resample(f"{tf}min", label="left", closed="left").agg(agg)
    f = f[f.t.eq(tf)].dropna().reset_index()
    f["decision"] = f.ts.dt.as_unit("s").astype("int64") + tf*60
    f["t"] = f.decision
    # Complete M1 context as of the decision; actual next open remains execution-only.
    idx = np.searchsorted(d.t.to_numpy()+60, f.decision.to_numpy(), side="right")-1
    for col in ["atr70", "atr14", "valid60"]:
        f[col] = d[col].to_numpy()[idx]
    ny = pd.to_datetime(f.decision, unit="s", utc=True).dt.tz_convert("America/New_York")
    # Formatting local wall dates without a timezone avoids a slow pandas path.
    f["day"] = ny.dt.tz_localize(None).dt.strftime("%Y-%m-%d")
    f["minute"] = ny.dt.hour*60+ny.dt.minute
    f["weekday"] = ny.dt.weekday
    f["valid"] = f.valid60.astype(bool) & f.atr70.gt(0) & f.weekday.lt(4) & f.minute.between(180, 930)
    # H1 values become available at start+3600, never at the start of that hour.
    h = d.set_index("ts").resample("60min", label="left", closed="left").agg(agg)
    h = h[h.t.eq(60)].dropna().reset_index()
    h["available"] = h.ts.dt.as_unit("s").astype("int64")+3600
    h["ema50"] = h.close.ewm(span=50, adjust=False, min_periods=50).mean()
    hi = np.searchsorted(h.available.to_numpy(), f.decision.to_numpy(), side="right")-1
    f["h1_dir"] = np.where(hi >= 0, np.sign((h.close-h.ema50).to_numpy()[np.maximum(hi, 0)]), np.nan)
    f["h1_fresh"] = (hi >= 0) & ((f.decision.to_numpy()-h.available.to_numpy()[np.maximum(hi, 0)]) < 7200)
    f["range"] = (f.high-f.low).replace(0, np.nan)
    f["body"] = (f.close-f.open)/f.range
    f["clv"] = (2*f.close-f.high-f.low)/f.range
    f["ema20"] = f.close.ewm(span=max(2, round(20/tf)), adjust=False).mean()
    f["ema60"] = f.close.ewm(span=max(2, round(60/tf)), adjust=False).mean()
    steps = max(2, round(60/tf))
    f["eff"] = f.close.diff(steps).abs()/f.close.diff().abs().rolling(steps).sum()
    f["path_dir"] = np.sign(f.close.diff(steps))
    f["trend_dir"] = np.sign(f.ema20-f.ema60)
    # Proxy VWAP anchored at 03:00 NY using tick volume, not exchange volume.
    active = f.minute.ge(180)
    v = f.volume.where(active, 0)
    pv = ((f.high+f.low+f.close)/3*v).where(active, 0)
    f["vwap"] = pv.groupby(f.day).cumsum()/v.groupby(f.day).cumsum().replace(0, np.nan)
    # A complete 09:30–09:45 opening range is known only from 09:45 onward.
    od = d[d.ny_min.between(570, 584)].groupby("day").agg(or_high=("high", "max"), or_low=("low", "min"), or_count=("close", "size"))
    f["or_high"] = f.day.map(od.or_high).where(f.minute.ge(585) & f.day.map(od.or_count).eq(15))
    f["or_low"] = f.day.map(od.or_low).where(f.minute.ge(585) & f.day.map(od.or_count).eq(15))
    for look in [15, 30, 60]:
        n = max(3, round(look/tf))
        f[f"hi{look}"] = f.high.shift().rolling(n).max()
        f[f"lo{look}"] = f.low.shift().rolling(n).min()
        f[f"z{look}"] = (f.close-f.close.rolling(n).mean()) / f.close.rolling(n).std().replace(0, np.nan)
        f[f"ret{look}"] = f.close.diff(n)/f.atr70
        # Known previous-window efficiency, used to distinguish shock from drift.
        f[f"eff{look}"] = f.close.diff(n).abs()/f.close.diff().abs().rolling(n).sum()
    return f


def events(f: pd.DataFrame, spec: dict, tf: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Return decision timestamps and side, without any future bars or labels."""
    name, look = spec["family"], spec["lookback"]
    c, o, h, l, a = f.close, f.open, f.high, f.low, f.atr70
    hi, lo = f[f"hi{look}"], f[f"lo{look}"]
    prev = c.shift()
    crossup = (c > f.ema20) & (prev <= f.ema20.shift())
    crossdn = (c < f.ema20) & (prev >= f.ema20.shift())
    lastup = c > f.high.shift()
    lastdn = c < f.low.shift()
    nshort = max(1, round(5/tf))
    priorret = (c.shift()-c.shift(1+nshort))/a
    if name == "pullback":
        bu = (f.trend_dir > 0) & crossup & (priorret < -.5)
        se = (f.trend_dir < 0) & crossdn & (priorret > .5)
        # Lookback controls depth, not the context EMA.
        bu &= c.shift().rolling(max(2, round(look/tf))).min() < f.ema20.shift()-.5*a
        se &= c.shift().rolling(max(2, round(look/tf))).max() > f.ema20.shift()+.5*a
    elif name == "sweep":
        bu = (l < lo) & (c > lo) & (f.clv > .4) & ((np.minimum(c,o)-l)/f.range > .35)
        se = (h > hi) & (c < hi) & (f.clv < -.4) & ((h-np.maximum(c,o))/f.range > .35)
    elif name == "compression":
        tight = ((hi-lo)/a < {15: 5, 30: 7, 60: 10}[look]) & (f.atr14.shift()/a < 1.0)
        bu = tight & (c > hi) & (f.body > .5)
        se = tight & (c < lo) & (f.body < -.5)
    elif name == "absorption":
        shock = (f["range"].shift()/a > {15: 1.8, 30: 2.2, 60: 2.6}[look])
        bu = shock & (f.body.shift() < -.6) & (c > (f.open.shift()+prev)/2) & (c > o)
        se = shock & (f.body.shift() > .6) & (c < (f.open.shift()+prev)/2) & (c < o)
    elif name == "exhaustion":
        z = f[f"z{look}"].shift()
        bu = (z < -2) & lastup & (f.clv > .2)
        se = (z > 2) & lastdn & (f.clv < -.2)
    elif name == "failed_break":
        bu = (prev < lo.shift()) & (c > lo.shift()) & (f.clv > .2)
        se = (prev > hi.shift()) & (c < hi.shift()) & (f.clv < -.2)
    elif name == "efficient_pullback":
        eff = f[f"eff{look}"].shift()
        drift = f[f"ret{look}"].shift()
        bu = (eff > .25) & (drift > 1) & (priorret < -.3) & lastup
        se = (eff > .25) & (drift < -1) & (priorret > .3) & lastdn
    elif name == "vwap_reclaim":
        bu = (prev < f.vwap.shift()-.3*a) & (c > f.vwap) & (f[f"ret{look}"] > 0)
        se = (prev > f.vwap.shift()+.3*a) & (c < f.vwap) & (f[f"ret{look}"] < 0)
    elif name == "opening_break":
        window = f.minute.between(585, 585+look*3)
        bu = window & (prev <= f.or_high.shift()) & (c > f.or_high) & (f.body > .3)
        se = window & (prev >= f.or_low.shift()) & (c < f.or_low) & (f.body < -.3)
    elif name == "opening_failure":
        window = f.minute.between(585, 585+look*3)
        bu = window & (l < f.or_low) & (c > f.or_low) & (f.clv > .3)
        se = window & (h > f.or_high) & (c < f.or_high) & (f.clv < -.3)
    elif name == "two_shock":
        k = max(3, round(look/tf))
        pastlow = l.shift(2).rolling(k).min()
        pasthi = h.shift(2).rolling(k).max()
        # New extreme with weaker directional path, followed by a local reclaim.
        bu = (l.shift() < pastlow) & (f[f"ret{look}"].shift() < -1) & lastup & (f.body > .2)
        se = (h.shift() > pasthi) & (f[f"ret{look}"].shift() > 1) & lastdn & (f.body < -.2)
    else:
        mid = (hi+lo)/2
        bu = (prev < mid.shift()) & (c > mid) & (f[f"ret{look}"] > 1) & (f.body > .3)
        se = (prev > mid.shift()) & (c < mid) & (f[f"ret{look}"] < -1) & (f.body < -.3)
    gate = spec["context"]
    if gate == "h1":
        bu &= f.h1_fresh & (f.h1_dir > 0)
        se &= f.h1_fresh & (f.h1_dir < 0)
    elif gate == "efficiency":
        bu &= (f.eff > .2) & (f.path_dir > 0)
        se &= (f.eff > .2) & (f.path_dir < 0)
    elif gate == "quiet":
        bu &= (f.atr14/f.atr70 < 1)
        se &= (f.atr14/f.atr70 < 1)
    if spec["side"] == "buy":
        se &= False
    elif spec["side"] == "sell":
        bu &= False
    bu &= f.valid
    se &= f.valid
    both = bu & se
    bu &= ~both
    se &= ~both
    mask = (bu | se).to_numpy()
    return f.decision.to_numpy()[mask], np.where(bu.to_numpy()[mask], 1, -1)


def simulate_grid(d: pd.DataFrame, spread_mult: float = 1, slip: float = .2,
                  geometry: str = "primary", delay: int = 0,
                  optimistic: bool = False, risk_mult: float = 5.,
                  hold_minutes: int = 90, reward_ratio: float = 1.5) -> dict[int, pd.DataFrame]:
    """Vectorized bid/ask TP/SL engine, every eligible minute, both directions.

    Risk is frozen at the original decision, even in delayed-entry stress.
    Time exits are fills at next open (or earlier stop/target); 15:55 is a known
    daily deadline. Invalid future gaps are surfaced, never silently discarded.
    """
    t = d.t.to_numpy()
    risk = np.maximum(35., risk_mult*d.atr70.shift().to_numpy())
    rr = reward_ratio
    if geometry == "fixed":
        risk = np.full(len(d), 110.)
        rr = 80/110
    elif geometry == "symmetric":
        rr = 1.
    valid = d.valid60.shift(fill_value=False).to_numpy() & np.isfinite(risk)
    valid &= d.weekday.lt(4).to_numpy() & d.ny_min.between(180, 930).to_numpy()
    valid &= np.r_[False, np.diff(t) == 60]
    ix = np.flatnonzero(valid)
    eix = ix+delay
    keep = eix < len(d)-1
    ix, eix = ix[keep], eix[keep]
    keep = t[eix]-t[ix] == 60*delay
    ix, eix = ix[keep], eix[keep]
    op, hp, lp, cp = [d[x].to_numpy() for x in ["open", "high", "low", "close"]]
    sp = d.spread_px.to_numpy()*spread_mult
    exact_ask = "ask_open" in d and not optimistic
    nymin = d.ny_min.to_numpy()
    out = {}
    for side in [1, -1]:
        unit = risk[ix]
        bid = cp[ix-1] if optimistic else op[eix]
        if side == 1 and exact_ask:
            entry = d.ask_open.to_numpy()[eix]+(spread_mult-1)*d.spread_px.to_numpy()[eix]+slip
        else:
            entry = bid+(sp[eix] if side == 1 else 0.)+side*slip
        target = entry+side*rr*unit
        stop = entry-side*unit
        active = np.ones(len(ix), dtype=bool)
        r = np.full(len(ix), np.nan)
        px = np.full(len(ix), np.nan)
        exitix = np.full(len(ix), -1, dtype=int)
        reason = np.full(len(ix), "", dtype="U12")
        ambiguous = np.zeros(len(ix), dtype=bool)
        for j in range(hold_minutes+1):
            w = np.flatnonzero(active)
            if not len(w):
                break
            k = eix[w]+j
            exists = k < len(d)
            gap = ~exists
            gap[exists] |= t[k[exists]] != t[eix[w[exists]]]+j*60
            if gap.any():
                wg = w[gap]
                kg = np.minimum(eix[wg]+max(j-1,0), len(d)-1)
                if side == -1 and exact_ask:
                    exitpx = d.ask_close.to_numpy()[kg]+(spread_mult-1)*d.spread_px.to_numpy()[kg]+slip
                else:
                    exitpx = cp[kg]+(sp[kg] if side == -1 else 0.)-side*slip
                px[wg], exitix[wg], reason[wg] = exitpx, kg, "data_gap"
                r[wg] = side*(exitpx-entry[wg])/unit[wg]
                active[wg] = False
            w, k = w[~gap], k[~gap]
            if not len(w):
                continue
            ask = sp[k] if side == -1 else 0.
            oo, hh, ll = op[k]+ask, hp[k]+ask, lp[k]+ask
            if side == -1 and exact_ask:
                extra = (spread_mult-1)*d.spread_px.to_numpy()[k]
                oo,hh,ll = [d[col].to_numpy()[k]+extra for col in ["ask_open","ask_high","ask_low"]]
            expired = (j == hold_minutes) | (nymin[k] >= 955)
            hs = ll <= stop[w] if side == 1 else hh >= stop[w]
            ht = hh >= target[w] if side == 1 else ll <= target[w]
            # At the time-stop open, only an opening gap can beat the time exit.
            gapstop = oo <= stop[w] if side == 1 else oo >= stop[w]
            gaptarget = oo >= target[w] if side == 1 else oo <= target[w]
            hs = np.where(expired, gapstop, hs)
            ht = np.where(expired, gaptarget, ht)
            # An already crossed target at the open predates any intrabar stop.
            hs &= ~gaptarget
            ws = w[hs]
            if len(ws):
                val = np.minimum(oo[hs],stop[ws]) if side == 1 else np.maximum(oo[hs],stop[ws])
                val -= side*slip
                px[ws], exitix[ws], reason[ws] = val, k[hs], "stop"
                r[ws] = side*(val-entry[ws])/unit[ws]
                ambiguous[ws] = ht[hs] & ~expired[hs]
                active[ws] = False
            wt = w[ht & ~hs]
            if len(wt):
                val = target[wt]-side*slip  # no optimistic price improvement
                px[wt], exitix[wt], reason[wt] = val, k[ht & ~hs], "target"
                r[wt] = side*(val-entry[wt])/unit[wt]
                active[wt] = False
            we = w[expired & ~hs & ~ht]
            if len(we):
                val = oo[expired & ~hs & ~ht]-side*slip
                px[we], exitix[we], reason[we] = val, k[expired & ~hs & ~ht], "time"
                r[we] = side*(val-entry[we])/unit[we]
                active[we] = False
        good = np.isfinite(r)
        out[side] = pd.DataFrame({"decision": t[ix[good]], "entry_t": t[eix[good]],
            "exit_t": t[exitix[good]]+60, "entry_ix": eix[good], "exit_ix": exitix[good],
            "side": side, "entry": entry[good], "exit": px[good], "risk": unit[good],
            "R": r[good], "points": side*(px[good]-entry[good]), "reason": reason[good],
            "ambiguous": ambiguous[good], "day": d.day.to_numpy()[ix[good]],
            "hour": d.ny_min.to_numpy()[ix[good]]//60}).set_index("decision", drop=False)
    return out


def replay(ts: np.ndarray, sides: np.ndarray, grid: dict, period: str,
           sequential: bool = True) -> pd.DataFrame:
    lo, hi = map(stamp, PERIODS[period])
    rows = []
    for side in [1, -1]:
        x = grid[side]
        keys = ts[(sides == side) & (ts >= lo) & (ts < hi)]
        # Same exact minute only; never use stale next available prices.
        take = x.loc[x.index.intersection(keys)]
        rows.append(take[(take.exit_t < hi) & (take.decision >= lo)])
    allrows = pd.concat(rows, ignore_index=True).sort_values("decision").reset_index(drop=True)
    if not sequential:
        return allrows
    keep, busy, last = [], -1, -1
    for i, row in enumerate(allrows.itertuples()):
        if row.decision < busy or row.decision-last < 600:
            continue
        keep.append(i)
        busy, last = row.exit_t, row.decision
    return allrows.iloc[keep].reset_index(drop=True)


def stats(rows: pd.DataFrame) -> dict:
    if rows.empty:
        return {"n": 0, "ev": 0., "total_R": 0., "wr": 0., "drawdown_R": 0., "points": 0., "days": 0}
    x = rows.R.to_numpy()
    eq = np.r_[0., np.cumsum(x)]
    winners, losers = x[x > 0], x[x < 0]
    avg_win = float(winners.mean()) if len(winners) else 0.
    avg_loss = float(-losers.mean()) if len(losers) else 0.
    return {"n": len(rows), "ev": float(x.mean()), "total_R": float(x.sum()),
            "wr": float((x > 0).mean()), "drawdown_R": float(np.max(np.maximum.accumulate(eq)-eq)),
            "points": float(rows.points.sum()), "days": int(rows.day.nunique()),
            "average_win_R":avg_win,"average_loss_R":avg_loss,
            "empirical_breakeven_wr":avg_loss/(avg_win+avg_loss) if avg_win+avg_loss else 0.,
            "stops": int(rows.reason.eq("stop").sum()), "targets": int(rows.reason.eq("target").sum()),
            "time_exits": int(rows.reason.eq("time").sum()), "data_gaps": int(rows.reason.eq("data_gap").sum()),
            "ambiguous_bars": int(rows.ambiguous.sum()), "worst_gap_ev": float(np.where(rows.reason.eq("data_gap"), np.minimum(-1.,x),x).mean())}


def specs() -> list[dict]:
    return [{"id": f"{fam}_{look}_{ctx}_{side}", "family": fam, "lookback": look,
             "context": ctx, "side": side} for fam in FAMILIES for look in [15,30,60]
            for ctx in ["none","h1","efficiency","quiet"] for side in ["both","buy","sell"]]


def discover() -> None:
    d = load()
    # Selection stage never computes labels after validation end.
    early = d[d.t < stamp("2026-07-01")].copy()
    f = features(early)
    grid = simulate_grid(early)
    results = []
    for i, spec in enumerate(specs()):
        ts, sides = events(f, spec)
        rec = {**spec, "metrics": {p: stats(replay(ts,sides,grid,p)) for p in
               ["discovery","discovery_a","discovery_b","validation","validation_a","validation_b"]}}
        m = rec["metrics"]
        rec["eligible"] = (m["discovery"]["n"] >= 80 and m["validation"]["n"] >= 40 and
            min(m[p]["ev"] for p in ["discovery_a","discovery_b","validation_a","validation_b"]) >= 0 and m["validation"]["ev"] > 0)
        rec["worst_subperiod_ev"] = min(m[p]["ev"] for p in ["discovery_a","discovery_b","validation_a","validation_b"])
        results.append(rec)
        if i % 36 == 35:
            print(f"screened {i+1}/432", flush=True)
    def rank(r):
        return (r["eligible"],r["worst_subperiod_ev"] if r["eligible"] else r["metrics"]["validation"]["ev"],r["metrics"]["validation"]["ev"])
    ordered = sorted(results,key=rank,reverse=True)
    selected, used = [], set()
    for r in ordered:
        if r["family"] in used or r["metrics"]["validation"]["n"] < 30 or r["metrics"]["discovery"]["n"] < 50:
            continue
        selected.append(r)
        used.add(r["family"])
        if len(selected) == 5:
            break
    save_json(OUT/"search_all_432.json",results)
    save_json(OUT/"frozen_five.json",{"protocol_sha256":hashlib.sha256((HERE/"PROTOCOL.md").read_bytes()).hexdigest(),
        "selection_rule":"PROTOCOL.md; final labels not used", "configurations_tried":len(results),
        "eligible_rules":sum(r["eligible"] for r in results), "candidates":selected})
    for r in selected:
        print(r["id"],"eligible",r["eligible"],"worst",round(r["worst_subperiod_ev"],3),
              "D",r["metrics"]["discovery"],"V",r["metrics"]["validation"],flush=True)


def bootstrap(rows: pd.DataFrame, column: str = "R", n: int = 10000) -> dict:
    """Resample whole NY dates, preserving intraday dependence and trade counts."""
    if rows.empty:
        return {"p_positive":0.,"ci95":[0.,0.],"effective_days":0}
    g = rows.groupby("day")[column].agg(["sum","count"])
    rng = np.random.default_rng(930)
    picks = rng.integers(0,len(g),size=(n,len(g)))
    means = g["sum"].to_numpy()[picks].sum(axis=1)/g["count"].to_numpy()[picks].sum(axis=1)
    return {"p_positive":float((means > 0).mean()),"ci95":[float(v) for v in np.quantile(means,[.025,.975])],"effective_days":len(g)}


def matched(rows: pd.DataFrame, grid: dict) -> tuple[dict,pd.DataFrame]:
    """Same day, NY hour, side and geometry; all eligible minute decisions.

    Baseline has overlapping hypothetical opportunities: no claim of executable
    portfolio PnL. The paired lift bootstrap resamples candidate calendar dates.
    """
    full = pd.concat([grid[1],grid[-1]]).reset_index(drop=True)
    full = full[(full.decision >= stamp(PERIODS["final"][0])) & (full.exit_t < stamp(PERIODS["final"][1]))]
    b = full.groupby(["day","hour","side"]).agg(base_R=("R","mean"),base_wr=("R",lambda x:float((x>0).mean())))
    r = rows.merge(b, on=["day","hour","side"],how="left")
    r["lift"] = r.R-r.base_R
    boot = bootstrap(r,"lift")
    # One-sided centered day-block test of zero incremental EV.
    g = r.groupby("day").agg(s=("lift","sum"),n=("lift","size"))
    if len(g):
        observed = float(r.lift.mean())
        sums = g.s.to_numpy()-observed*g.n.to_numpy()
        rng = np.random.default_rng(931)
        ix = rng.integers(0,len(g),size=(10000,len(g)))
        null = sums[ix].sum(axis=1)/g.n.to_numpy()[ix].sum(axis=1)
        p = float((1+(null >= observed).sum())/(len(null)+1))
    else:
        p = 1.
    return {"baseline_ev":float(r.base_R.mean()) if len(r) else 0.,"baseline_wr":float(r.base_wr.mean()) if len(r) else 0.,
            "lift_ev":float(r.lift.mean()) if len(r) else 0.,"lift_bootstrap":boot,"one_sided_p":p},r


def evaluate() -> None:
    frozen = json.loads((OUT/"frozen_five.json").read_text())
    d = load()
    fs = {tf:features(d,tf) for tf in [1,3,5]}
    grids = {"primary": simulate_grid(d)}
    stress_specs = {"spread_1_5":dict(spread_mult=1.5),"spread_3":dict(spread_mult=3),
        "slip_1":dict(slip=1.),"delay_1m":dict(delay=1),
        "fixed_80_110":dict(geometry="fixed"),"symmetric":dict(geometry="symmetric"),
        "optimistic_close":dict(spread_mult=0,slip=0,optimistic=True)}
    for name, kw in stress_specs.items():
        grids[name] = simulate_grid(d,**kw)
        print("execution grid",name,flush=True)
    allresults, portfolio_rows = [], []
    for priority, spec in enumerate(frozen["candidates"]):
        ts,sides = events(fs[1],spec)
        rows = replay(ts,sides,grids["primary"],"final")
        stat = stats(rows)
        boot = bootstrap(rows)
        base, paired = matched(rows,grids["primary"])
        periods = {p:stats(replay(ts,sides,grids["primary"],p)) for p in ["final_a","final_b"]}
        stress = {name:stats(replay(ts,sides,g,"final")) for name,g in grids.items() if name != "primary"}
        transfer = {}
        for tf in [3,5]:
            tt,ss = events(fs[tf],spec,tf)
            tr = replay(tt,ss,grids["primary"],"final")
            transfer[str(tf)] = {**stats(tr),"bootstrap":bootstrap(tr)}
        side_stats = {str(side):stats(rows[rows.side.eq(side)]) for side in [1,-1]}
        monthly = {str(month):stats(r) for month,r in rows.groupby(pd.to_datetime(rows.decision,unit="s",utc=True).dt.strftime("%Y-%m"))}
        n, wr = stat["n"],stat["wr"]
        z = 1.96
        den = 1+z*z/max(n,1)
        ctr = (wr+z*z/(2*max(n,1)))/den
        wid = z*math.sqrt(wr*(1-wr)/max(n,1)+z*z/(4*max(n,1)**2))/den
        checks = {
            "volume_150":n >= 150,
            "positive_ev_day_bootstrap_90":stat["ev"] > 0 and boot["p_positive"] >= .9,
            "both_calendar_halves":all(v["n"] > 0 and v["ev"] >= 0 for v in periods.values()),
            "spread_1_5":stress["spread_1_5"]["ev"] > 0,
            "honest_vs_close_entry":abs(stress["optimistic_close"]["ev"]-stat["ev"]) <= .5*abs(stat["ev"]),
            "one_position":stat["ev"] > 0,
        }
        rec = {"spec":spec,"final":stat,"bootstrap":boot,"wilson95":[max(0.,ctr-wid),min(1.,ctr+wid)],
            "matched_baseline":base,"halves":periods,"monthly":monthly,"sides":side_stats,
            "stress":stress,"timeframe_transfer":transfer,"go_live_checks":checks,
            "bar_card_passes":all(checks.values()),"verdict":"SHADOW" if n >= 150 else "RED",
            "reason":"No future shadow/live fills; replay research only"}
        allresults.append(rec)
        paired.to_csv(OUT/f"trades_{spec['id']}.csv",index=False)
        # Portfolio uses every raw event; an event suppressed by its individual
        # strategy may still be available when that strategy is in a portfolio.
        raw = replay(ts,sides,grids["primary"],"final",False).copy()
        raw["candidate"],raw["priority"] = spec["id"],priority
        portfolio_rows.append(raw)
        print("FINAL",spec["id"],stat,"baseline",base,"3m/5m",{k:round(v['ev'],3) for k,v in transfer.items()},flush=True)
    # Holm family-wise adjustment across the five frozen hypotheses.
    order = sorted(range(len(allresults)),key=lambda i:allresults[i]["matched_baseline"]["one_sided_p"])
    running = 0.
    for j,i in enumerate(order):
        running = max(running,min(1.,(len(order)-j)*allresults[i]["matched_baseline"]["one_sided_p"]))
        allresults[i]["matched_baseline"]["holm_p_five"] = running
    raw = pd.concat(portfolio_rows).sort_values(["decision","priority"]).reset_index(drop=True)
    keep,busy,last = [],-1,-1
    for i,r in enumerate(raw.itertuples()):
        if r.decision < busy or r.decision-last < 600:
            continue
        keep.append(i)
        busy,last = r.exit_t,r.decision
    port = raw.iloc[keep].copy()
    port.to_csv(OUT/"portfolio_trades.csv",index=False)
    portfolio = {**stats(port),"bootstrap":bootstrap(port),"priority":"discovery/validation ranking; no final optimization",
                 "contribution":{name:stats(r) for name,r in port.groupby("candidate")}}
    save_json(OUT/"final_evaluation.json",{"configurations_tried":432,"frozen_sha256":hashlib.sha256((OUT/"frozen_five.json").read_bytes()).hexdigest(),
        "candidates":allresults,"portfolio":portfolio})
    print("PORTFOLIO",portfolio,flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("stage",choices=["audit","discover","evaluate","summary"])
    a = p.parse_args()
    if a.stage == "audit":
        d = load()
        print("Audited",len(d),"bars;",OUT/"data_audit.json",flush=True)
    elif a.stage == "discover":
        discover()
    elif a.stage == "evaluate":
        evaluate()
    else:
        for name in ["final_evaluation.json","second_final.json"]:
            path=OUT/name
            if not path.exists():
                continue
            result=json.loads(path.read_text())
            print(name,flush=True)
            for c in result["candidates"]:
                m=c["final"]
                print(c["spec"]["id"],f"n={m['n']} EV={m['ev']:+.4f}R total={m['total_R']:+.2f}R",
                      f"status={c['verdict']}",flush=True)
        print("Research only; no production trading changes.",flush=True)


if __name__ == "__main__":
    main()
