"""Frozen, offline comparison of five cross-report mechanisms. No live mutations."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "ndx_mechanism_round2_20260930"))
from data import datasets, context, prepare, lab, old2, bot_decisions
from experiment import delayed, sequential, delta_boot

PERIODS = {"D25a": ("2025-01-02", "2025-07-01"), "D25b": ("2025-07-01", "2025-12-31"),
           "C26": ("2026-02-11", "2026-05-16"), "M26": ("2026-05-20", "2026-08-29"),
           "S26": ("2026-09-01", "2026-09-30"), "Sep30": ("2026-09-30", "2026-10-01"),
           "Oct01": ("2026-10-01", "2026-10-02")}
lab.PERIODS.update(PERIODS)
SPECS = json.loads((HERE.parent / "ndx_five_gates_20260930/results/frozen_second_five.json").read_text())["candidates"]
OVERLAYS = ["BASE", "H1", "K5", "H2", "RAWVOL", "H3", "WAITALL", "H4", "K6", "COMBINED"]
RECLAIMS = ["H5", "RECLAIM_ALL", "RECLAIM_CALM", "RECLAIM_SELL"]
PRIMARY = ["H1", "H2", "H3", "H4", "H5"]


def load_data():
    ds = datasets()
    for path in [HERE.parent / "ndx_mechanism_round2_20260930/results/fresh_day.json", OUT / "fresh_oct01.json"]:
        if not path.exists():
            continue
        x = json.loads(path.read_text())
        z = pd.DataFrame(x["rows"], columns=["t", "open", "high", "low", "close", "volume", "spread"])
        z["spread_px"] = z.spread * x["point"]
        # Frozen existing observations take precedence over refreshed warmup.
        old = ds["mt5"].drop(columns=["ts"])
        overlap = old[["t", "close"]].merge(z[["t", "close"]], on="t", suffixes=("_old", "_new"))
        if len(overlap):
            error = (overlap.close_old - overlap.close_new).abs()
            assert error.median() < 1 and error.max() < 10, "Fresh export clock/price mismatch"
        assert not z.t.duplicated().any()
        assert (z.high >= z[["open", "close"]].max(axis=1)).all()
        assert (z.low <= z[["open", "close"]].min(axis=1)).all()
        z = z[~z.t.isin(old.t)]
        ds["mt5"] = prepare(pd.concat([old, z], ignore_index=True), "mt5_extended")
    return ds


def macro_series():
    path = OUT / "macro_daily.csv"
    if not path.exists():
        path = ROOT / "research/ndx_gate_forge/data/macro_daily_patched.csv"
    m = pd.read_csv(path, parse_dates=["date"]).set_index("date").NDXCASH_close.dropna().sort_index()
    return m


def features(d, tf, source):
    f = context(d, tf)
    m = macro_series()
    # All macro inputs are complete previous cash sessions, never today's close.
    dates = pd.to_datetime(f.day).to_numpy()
    j = np.searchsorted(m.index.to_numpy(), dates, side="left") - 1
    safe = np.maximum(j, 0)
    age = (dates - m.index.to_numpy()[safe]) / np.timedelta64(1, "D")
    ok = (j >= 0) & (age <= 5)
    for name, value in {"ret1": m.pct_change(), "ret5": m.pct_change(5),
                        "extension": m / m.rolling(200).mean() - 1}.items():
        f[name] = np.where(ok, value.to_numpy()[safe], np.nan)
    prev_dates = pd.Series(m.index.strftime("%Y-%m-%d").to_numpy()[safe], index=f.index)
    rth = d[d.ny_min.between(570, 959)].groupby("day").agg(lo=("low", "min"), n=("t", "size"))
    rth = rth[rth.n.eq(390)]
    f["prev_rth_low"] = prev_dates.map(rth.lo).where(ok)
    # Complete M5 tick volume, separated by feed; same local-clock slot past days only.
    v = d.set_index("ts").resample("5min", closed="left", label="left").agg(
        volume=("volume", "sum"), n=("t", "size"))
    v = v[v.n.eq(5)].reset_index()
    v["avail"] = v.ts.dt.as_unit("s").astype("int64") + 300
    if source == "mt5":
        orig = lab.load()
        boundary = int(orig.loc[orig.source.eq("mt5"), "t"].min())
        v["feed"] = np.where(v.avail <= boundary, "cache", "mt5")
    else:
        v["feed"] = "duka"
    ny = v.ts.dt.tz_convert("America/New_York")
    v["slot"] = ny.dt.hour * 60 + ny.dt.minute
    v["raw_ratio"] = v.volume / v.groupby("feed").volume.transform(lambda s: s.shift().rolling(20, min_periods=20).mean())
    v["season_ratio"] = v.volume / v.groupby(["feed", "slot"]).volume.transform(lambda s: s.shift().rolling(20, min_periods=10).median())
    ix = np.searchsorted(v.avail.to_numpy(), f.decision.to_numpy(), side="right") - 1
    safe = np.maximum(ix, 0)
    available = (ix >= 0) & ((f.decision.to_numpy() - v.avail.to_numpy()[safe]) < 300)
    for name in ["raw_ratio", "season_ratio"]:
        f[name] = np.where(available, v[name].to_numpy()[safe], np.nan)
    fixed_low = d.low.rolling(15).min()
    ix = np.searchsorted(d.t.to_numpy() + 60, f.decision.to_numpy(), side="right") - 1
    f["low15_m1"] = fixed_low.to_numpy()[ix]
    f["stress"] = (f.ret1 <= -.015) | (f.ret5 <= -.04)
    f["shock"] = (f.raw_ratio >= 1.5) & (f.season_ratio >= 1.5)
    return f


def events(f, tf):
    rows = []
    for priority, spec in enumerate(SPECS):
        ts, side = old2.detect(f, spec, tf)
        ix = np.searchsorted(f.decision.to_numpy(), ts)
        x = f.iloc[ix].copy()
        x["origin"], x["side"] = ts, side
        x["priority"], x["candidate"], x["geometry"] = priority, spec["id"], spec["geometry"]
        rows.append(x)
    return pd.concat(rows, ignore_index=True).sort_values(["decision", "priority"]).reset_index(drop=True)


def apply_overlay(d, x, rule):
    if rule == "BASE":
        return x.copy()
    veto = pd.Series(False, index=x.index)
    if rule in ["H1", "COMBINED"]:
        veto |= (x.side < 0) & x.stress & (x.close < x.prev_rth_low)
    if rule == "K5":
        veto |= (x.side < 0) & x.stress
    if rule in ["H2", "COMBINED"]:
        veto |= x.shock
    if rule == "RAWVOL":
        veto |= x.raw_ratio >= 1.5
    if rule in ["H4", "COMBINED"]:
        veto |= (x.side > 0) & (x.extension > .10) & x.cont240 & (x.pos240 > .8)
    if rule == "K6":
        veto |= (x.side > 0) & (x.extension > .10)
    z = x[~veto].copy()
    if rule in ["H3", "WAITALL", "COMBINED"]:
        mask = z.shock if rule != "WAITALL" else pd.Series(True, index=z.index)
        later = delayed(d, z[mask], 3)
        later = later[later.band_alive & later.fair_price]
        z = pd.concat([z[~mask], later], ignore_index=True)
    return z.sort_values(["decision", "priority"]).reset_index(drop=True)


def reclaim(f, tf, rule):
    level = f.prev_rth_low
    previous_close = f.close.shift()
    same_level = level.eq(level.shift())
    adjacent = f.decision.diff().eq(tf * 60)
    mask = f.valid & same_level & adjacent & (previous_close <= level) & (f.close > level)
    mask &= ((level - f.low15_m1) >= .5 * f.atr70) & (f.clv > .2)
    if rule in ["H5", "RECLAIM_SELL"]:
        mask &= f.stress
    elif rule == "RECLAIM_CALM":
        mask &= ~f.stress & f.ret1.notna() & f.ret5.notna()
    x = f[mask].copy()
    x["origin"], x["side"] = x.decision, -1 if rule == "RECLAIM_SELL" else 1
    x["priority"], x["candidate"], x["geometry"] = 0, rule, "fixed"
    return x


def execute(x, grids, period):
    rows = []
    lo = lab.stamp(PERIODS[period][0])
    for (priority, name, geom), z in x.groupby(["priority", "candidate", "geometry"]):
        z = z[z.origin >= lo]
        r = lab.replay(z.decision.to_numpy(), z.side.to_numpy(), grids[geom], period, False)
        r["priority"], r["candidate"] = priority, name
        rows.append(r)
    if not rows:
        r = grids["fixed"][1].iloc[:0].copy().reset_index(drop=True)
        r["priority"], r["candidate"] = 0, ""
        return r
    return sequential(pd.concat(rows, ignore_index=True))


def summary(a, base):
    sa, sb = lab.stats(a), lab.stats(base)
    paired = delta_boot(a, base)
    v = pd.concat([a.groupby("day").R.sum().rename("a"), base.groupby("day").R.sum().rename("b")], axis=1).fillna(0)
    paired["affected_days"] = int(((v.a - v.b).abs() > 1e-10).sum())
    # This adjustment is only within this round, not a correction for prior mining.
    paired["bonferroni_p5"] = min(1., 5 * paired["one_sided_p"])
    worst_a = sa.get("worst_gap_ev", sa["ev"]) * sa["n"]
    worst_b = sb.get("worst_gap_ev", sb["ev"]) * sb["n"]
    return {**sa, "base_total_R": sb["total_R"], "delta_R": sa["total_R"] - sb["total_R"],
            "worst_gap_total_R": worst_a, "worst_gap_delta_R": worst_a - worst_b,
            "paired": paired, "bootstrap": lab.bootstrap(a),
            "contributions": {name: lab.stats(z) for name, z in a.groupby("candidate")}}


def run():
    ds = load_data()
    result = {"protocol_sha256": hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest(),
              "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "configurations": OVERLAYS + RECLAIMS, "datasets": {}, "results": {}}
    for source, d in ds.items():
        periods = ["D25a", "D25b"] if source == "duka" else ["C26", "M26", "S26", "Sep30"]
        if source == "mt5" and d.t.max() >= lab.stamp("2026-10-02") - 3600:
            periods.append("Oct01")
        result["datasets"][source] = {"n": len(d), "first": str(d.ts.min()), "last": str(d.ts.max())}
        fs = {}
        xs = {}
        for tf in [1, 3, 5]:
            f = features(d, tf, source)
            fs[tf] = f
            f.to_pickle(OUT / f"features_{source}_{tf}.pkl")
            parent = events(f, tf)
            xs[tf] = {r: apply_overlay(d, parent, r) for r in OVERLAYS}
            xs[tf].update({r: reclaim(f, tf, r) for r in RECLAIMS})
            print("FEATURES", source, tf, len(f), "events", len(parent), flush=True)
        cases = {"base": {}, "spread3": {"spread_mult": 3}, "slip1": {"slip": 1.}, "delay1": {"delay": 1}}
        for case, kw in cases.items():
            geoms = {**old2.GEOMETRIES, "fixed": {"geometry": "fixed"}}
            grids = {name: lab.simulate_grid(d, **{**g, **kw}) for name, g in geoms.items()}
            for tf in ([1, 3, 5] if case == "base" else [1]):
                for period in periods:
                    trades = {rule: execute(x, grids, period) for rule, x in xs[tf].items()}
                    for rule, a in trades.items():
                        parent_rule = "RECLAIM_ALL" if rule in RECLAIMS else "BASE"
                        rec = summary(a, trades[parent_rule])
                        result["results"][f"{period}_{tf}_{case}_{rule}"] = rec
                        a.to_csv(OUT / f"trades_{period}_{tf}_{case}_{rule}.csv", index=False)
                    print("RESULT", source, period, tf, case,
                          [(r, len(trades[r]), round(trades[r].R.sum(), 3)) for r in ["BASE"] + PRIMARY], flush=True)
            lab.save_json(OUT / "evaluation.json", result)
    # Descriptive actual-bot features at exact decision times; no hypothetical USD claims.
    f = fs[1]
    actual = bot_decisions()
    ix = np.searchsorted(f.decision.to_numpy(), actual.decision.to_numpy(), side="right") - 1
    safe = np.maximum(ix, 0)
    ok = (ix >= 0) & ((actual.decision.to_numpy() - f.decision.to_numpy()[safe]) < 60)
    actual = actual[ok].copy().reset_index(drop=True)
    ctx = f.iloc[ix[ok]].reset_index(drop=True)
    # Exact entry price is observable when deciding whether to enter, but candle context is closed.
    flags = {"H1": (actual.side < 0) & ctx.stress & (actual.open_price < ctx.prev_rth_low),
             "K5": (actual.side < 0) & ctx.stress, "H2": ctx.shock, "RAWVOL": ctx.raw_ratio >= 1.5,
             "H4": (actual.side > 0) & (ctx.extension > .10) & ctx.cont240 & (ctx.pos240 > .8),
             "K6": (actual.side > 0) & (ctx.extension > .10)}
    desc = {}
    for rule, flag in flags.items():
        actual[rule] = flag.to_numpy()
        desc[rule] = {}
        for label, z in [("blocked", actual[flag]), ("kept", actual[~flag])]:
            desc[rule][label] = {"n": len(z), "days": int(z.bucket.dt.date.nunique()),
                                 "mean_points": float(z.points.mean()) if len(z) else None,
                                 "sum_actual_usd": float(z.usd.sum())}
    actual.to_csv(OUT / "actual_decisions.csv", index=False)
    lab.save_json(OUT / "actual_cohorts.json", desc)
    lab.save_json(OUT / "evaluation.json", result)
    print("DONE", len(result["results"]), "evaluation cells", flush=True)


if __name__ == "__main__":
    run()
