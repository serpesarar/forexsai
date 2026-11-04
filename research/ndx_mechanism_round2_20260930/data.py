"""Offline inputs and closed-bar context for the mechanism follow-up."""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parent / "ndx_five_gates_20260930"))
import lab
import second_search as old2
from transfer import prepare, duka, fresh


def datasets():
    old = lab.load().copy()
    mask = old.source.eq("cache") & old.ts.lt(pd.Timestamp("2026-03-08", tz="UTC"))
    old.loc[mask, "t"] += 3600
    early = old[old.source.eq("cache")].drop(columns=["ts"]).copy()
    mt = fresh().drop(columns=["ts"]).copy()
    return {"duka": duka(), "mt5": prepare(pd.concat([early, mt], ignore_index=True), "cache_then_mt5")}


def context(d: pd.DataFrame, tf: int = 1):
    f = old2.extra_features(d, tf)
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "t": "count"}
    for k in [5, 15]:
        x = d.set_index("ts").resample(f"{k}min", closed="left", label="left").agg(agg)
        x = x[x.t.eq(k)].dropna().reset_index()
        x["avail"] = x.ts.dt.as_unit("s").astype("int64") + k * 60
        ema = x.close.ewm(span=20, adjust=False, min_periods=20).mean()
        vals = {f"m{k}_dir": np.where((x.close > ema) & (ema > ema.shift(3)), 1,
                                     np.where((x.close < ema) & (ema < ema.shift(3)), -1, 0)),
                f"m{k}_body": (x.close - x.open) / (x.high - x.low).replace(0, np.nan)}
        ix = np.searchsorted(x.avail.to_numpy(), f.decision.to_numpy(), side="right") - 1
        safe = np.maximum(ix, 0)
        ok = (ix >= 0) & ((f.decision.to_numpy() - x.avail.to_numpy()[safe]) < k * 120)
        for col, val in vals.items():
            f[col] = np.where(ok, np.asarray(val)[safe], np.nan)
    # Statistical context retains 120 M1 observations at every trigger timeframe.
    c = d.close
    r = c.diff()
    fixed = pd.DataFrame({
        "vr120": c.diff(5).rolling(120).var() / (5 * r.rolling(120).var().replace(0, np.nan)),
        "er60_m1": c.diff(60).abs() / r.abs().rolling(60).sum(),
        "drift60_m1": c.diff(60) / d.atr70,
        "pos240": (c - d.low.rolling(240).min()) / (d.high.rolling(240).max() - d.low.rolling(240).min()),
        "z15_m1": (c - c.rolling(15).mean()) / c.rolling(15).std().replace(0, np.nan),
        "cont240": d.t.diff().eq(60).rolling(240).sum().eq(240),
    })
    ix = np.searchsorted(d.t.to_numpy() + 60, f.decision.to_numpy(), side="right") - 1
    for col in fixed:
        f[col] = fixed[col].to_numpy()[ix]
    # Only yesterday's completed cash close is visible. Weekend carry is bounded.
    m = pd.read_csv(ROOT / "research/ndx_gate_forge/data/macro_daily_patched.csv", parse_dates=["date"]).set_index("date")
    ndx = m.NDXCASH_close.dropna().sort_index()
    ret = ndx.pct_change()
    macro = pd.DataFrame({"ret1": ret, "ret5": ndx.pct_change(5),
                          "z5": ndx.pct_change(5) / (ret.rolling(20).std() * np.sqrt(5))})
    dates = pd.to_datetime(f.day) - pd.Timedelta(days=1)
    j = np.searchsorted(macro.index.to_numpy(), dates.to_numpy(), side="right") - 1
    safe = np.maximum(j, 0)
    age = (dates.to_numpy() - macro.index.to_numpy()[safe]) / np.timedelta64(1, "D")
    ok = (j >= 0) & (age <= 4)
    for col in macro:
        f[col] = np.where(ok, macro[col].to_numpy()[safe], np.nan)
    return f


def bot_decisions():
    a = pd.read_csv(ROOT / "nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv")
    b = pd.read_csv(ROOT / "research/ndx_gate_forge/data/box_trades_40d.csv")
    d = pd.concat([a, b[b.symbol.eq("NAS100")]], ignore_index=True).drop_duplicates("position_id", keep="last")
    d["ot"] = pd.to_datetime(d.open_time_utc, utc=True)
    d["exit_time"] = pd.to_datetime(d.close_time_utc, utc=True)
    d["net"] = d.profit + d.commission + d.swap
    d["points"] = np.where(d.direction.eq("BUY"), 1, -1) * (d.close_price - d.open_price)
    # Split legs in the same minute are one direction decision, even across magic.
    d["bucket"] = d.ot.dt.floor("min")
    g = d.groupby(["bucket", "direction"], sort=True).agg(
        ot=("ot", "min"), exit_time=("exit_time", "max"), open_price=("open_price", "mean"),
        points=("points", "mean"), usd=("net", "sum"), magic=("magic", "first"), legs=("position_id", "size"))
    g = g.reset_index()
    g["side"] = np.where(g.direction.eq("BUY"), 1, -1)
    g["decision"] = g.ot.dt.as_unit("s").astype("int64")
    return g
