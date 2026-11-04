"""Offline, frozen CAPREV event-time and payoff-path experiments."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parent / "ndx_synthesis_20261002"))
import run as prior
lab = prior.lab
RULES = ["BASE", "FRESH_CROSS", "CASH_ONLY", "FAIL_10", "HALF_RUNNER", "VIX_COOLING",
         "ALREADY_BELOW", "FULL_TP1", "ALWAYS_10", "VIX_RISING"]
PRIMARY = RULES[1:6]
M1_PERIODS = {"D25a": ("2025-01-02", "2025-07-01"), "D25b": ("2025-07-01", "2026-01-01"),
              "C26": ("2026-02-11", "2026-05-16"), "M26": ("2026-05-20", "2026-08-29"),
              "S26": ("2026-09-01", "2026-10-02")}
LONG_PERIODS = {"L16_20": ("2016-01-01", "2021-01-01"), "L21_23": ("2021-01-01", "2024-01-01"),
                "L24_25": ("2024-01-01", "2026-01-01"), "L26": ("2026-01-01", "2026-07-15")}


def native(tf):
    name = {15: "15m", 30: "30m", 60: "1h"}[tf]
    path = ROOT / f"research/ndx_buy_lab/data/long_{name}.csv"
    d = pd.read_csv(path)
    local = pd.to_datetime(d.ts, utc=True).dt.tz_localize(None) - pd.Timedelta(hours=7)
    d["ts"] = local.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")
    d = d.dropna(subset=["ts"])
    d = d[d.ts < pd.Timestamp("2026-07-15", tz="UTC")].sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    d["t"] = d.ts.dt.as_unit("s").astype("int64")
    ny = d.ts.dt.tz_convert("America/New_York")
    d["day"] = ny.dt.tz_localize(None).dt.strftime("%Y-%m-%d")
    d["ny_min"], d["weekday"] = ny.dt.hour * 60 + ny.dt.minute, ny.dt.weekday
    # Historical bars do not contain actual bid/ask. This is an explicit proxy.
    d["native"] = True
    d["spread_px"] = 2 * .00006 * d.open
    return d


def macro():
    return pd.read_csv(prior.OUT / "macro_daily.csv", parse_dates=["date"]).set_index("date").sort_index()


def context(d, trigger_tf, execution_tf):
    if execution_tf == 1:
        f = d.set_index("ts").resample(f"{trigger_tf}min").agg(
            open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("t", "size"))
        f = f[f.n.eq(trigger_tf)].reset_index()
    else:
        assert trigger_tf == execution_tf
        f = d[["ts", "open", "high", "low", "close"]].copy()
    f["decision"] = f.ts.dt.as_unit("s").astype("int64") + trigger_tf * 60
    ny = pd.to_datetime(f.decision, unit="s", utc=True).dt.tz_convert("America/New_York")
    f["day"] = ny.dt.tz_localize(None).dt.strftime("%Y-%m-%d")
    f["minute"], f["weekday"] = ny.dt.hour * 60 + ny.dt.minute, ny.dt.weekday
    if execution_tf == 1:
        ix = np.searchsorted(d.t.to_numpy() + 60, f.decision.to_numpy(), side="right") - 1
        warm = d.valid60.to_numpy()[ix]
    else:
        warm = d.t.diff().eq(execution_tf * 60).rolling(max(1, 60 // execution_tf)).sum().eq(max(1, 60 // execution_tf)).to_numpy()
    f["valid"] = warm & f.weekday.lt(4) & f.minute.between(180 + trigger_tf, 900)
    m = macro()
    ndx = m.NDXCASH_close.dropna()
    date = pd.to_datetime(f.day).to_numpy()
    j = np.searchsorted(ndx.index.to_numpy(), date, side="left") - 1
    safe = np.maximum(j, 0)
    ok = (j >= 0) & ((date - ndx.index.to_numpy()[safe]) / np.timedelta64(1, "D") <= 5)
    for col, value in {"ret1": ndx.pct_change(), "ret5": ndx.pct_change(5), "dvol": ndx.pct_change().rolling(20).std()}.items():
        f[col] = np.where(ok, value.to_numpy()[safe], np.nan)
    cash_prev_day = pd.Series(ndx.index.strftime("%Y-%m-%d").to_numpy()[safe], index=f.index)
    start = 540 if execution_tf == 60 else 570
    rth = d[d.ny_min.between(start, 960 - execution_tf)].groupby("day").agg(low=("low", "min"), n=("t", "size"))
    rth = rth[rth.n.eq((960 - start) // execution_tf)]
    f["level"] = cash_prev_day.map(rth.low).where(ok)
    v = m.VIX_close.dropna()
    k = np.searchsorted(v.index.to_numpy(), date, side="left") - 1
    good = (k >= 1) & ((date - v.index.to_numpy()[np.maximum(k, 0)]) / np.timedelta64(1, "D") <= 5)
    for col, val in {"vix": v, "vix_change": v.diff()}.items():
        f[col] = np.where(good, val.to_numpy()[np.maximum(k, 0)], np.nan)
    f["stress"] = (f.ret1 <= -.015) | (f.ret5 <= -.04)
    f["eligible"] = f.valid & f.stress & f.vix.ge(18.4) & f.dvol.gt(0) & f.level.notna()
    f["fresh"] = f.day.eq(f.day.shift()) & f.decision.diff().eq(trigger_tf * 60)
    f["fresh"] &= f.minute.shift().ge(180 + trigger_tf) & (f.close.shift() >= f.level) & (f.close < f.level)
    return f


def detect(f, rule):
    mask = f.eligible & (f.close < f.level)
    if rule == "FRESH_CROSS":
        mask &= f.fresh
    elif rule == "CASH_ONLY":
        step = int((f.decision.iloc[0] - f.ts.iloc[0].timestamp()) / 60)
        mask &= f.minute >= 570 + step
    elif rule == "VIX_COOLING":
        mask &= f.vix_change < 0
    elif rule == "VIX_RISING":
        mask &= f.vix_change >= 0
    elif rule == "ALREADY_BELOW":
        first = f[f.valid].groupby("day", sort=False).head(1).index
        mask &= f.index.isin(first)
    return f[mask].groupby("day", sort=False).head(1).copy()


def replay(d, ev, rule, step=1, spread_mult=1., slip=.2, delay=0):
    """One net position, optional half liquidation, fixed initial risk denominator."""
    t = d.t.to_numpy()
    op, hi, lo, close = [d[c].to_numpy() for c in ["open", "high", "low", "close"]]
    native_proxy = "native" in d
    if native_proxy:
        ask_open = op + .00006 * op * spread_mult
        bid_open, bid_high, bid_low, bid_close = [d[c].to_numpy() * (1 - .00006 * spread_mult) for c in ["open", "high", "low", "close"]]
    else:
        sp = d.spread_px.to_numpy()
        ask_open = (d.ask_open.to_numpy() if "ask_open" in d else op + sp) + (spread_mult - 1) * sp
        bid_open, bid_high, bid_low, bid_close = op, hi, lo, close
    rows = []
    for e in ev.itertuples():
        entry_t = e.decision + delay * step * 60
        i = np.searchsorted(t, entry_t)
        if i >= len(t) or t[i] != entry_t:
            continue
        entry = ask_open[i] + slip
        risk = entry * e.dvol
        stop, target = entry - risk, entry + risk
        cutoff = int(pd.Timestamp(e.day + " 16:00", tz="America/New_York").timestamp())
        ten = int(pd.Timestamp(e.day + " 10:00", tz="America/New_York").timestamp())
        fraction, realized, target_done = 1., 0., False
        reason, exitpx, ambiguous, k = None, None, False, i
        partial_t = None
        while k < len(t) and t[k] <= cutoff:
            if t[k] != entry_t + (k - i) * step * 60:
                k -= 1
                exitpx, reason = bid_close[k] - slip, "data_gap"
                break
            o, h, low = bid_open[k], bid_high[k], bid_low[k]
            # Opening price is observed before any within-bar excursion.
            if o <= stop:
                exitpx, reason = o - slip, "stop"
                break
            has_target = rule in ["HALF_RUNNER", "FULL_TP1"] and not target_done
            if has_target and o >= target:
                qty = .5 if rule == "HALF_RUNNER" else 1.
                realized += qty * (target - slip - entry) / risk
                fraction -= qty; target_done = True; partial_t = int(t[k])
                if fraction == 0:
                    exitpx, reason = target - slip, "target"
                    break
            at_ten = t[k] == ten and entry_t < ten
            fail = rule == "FAIL_10" and at_ten and close[k - 1] <= e.level
            early = rule == "ALWAYS_10" and at_ten
            if t[k] == cutoff or fail or early:
                exitpx, reason = o - slip, "fail10" if fail else "time"
                break
            hit_stop = low <= stop
            hit_target = has_target and not target_done and h >= target
            if hit_stop:
                ambiguous = bool(hit_target)
                exitpx, reason = stop - slip, "stop"
                break
            if hit_target:
                qty = .5 if rule == "HALF_RUNNER" else 1.
                realized += qty * (target - slip - entry) / risk
                fraction -= qty; target_done = True; partial_t = int(t[k])
                if fraction == 0:
                    exitpx, reason = target - slip, "target"
                    break
            k += 1
        if reason is None:
            k = min(k - 1, len(t) - 1)
            exitpx, reason = bid_close[k] - slip, "data_gap"
        realized += fraction * (exitpx - entry) / risk
        rows.append({"decision": e.decision, "entry_t": entry_t, "exit_t": int(t[k]) + step * 60,
                     "entry": entry, "exit": exitpx, "risk": risk, "R": realized, "points": realized * risk,
                     "reason": reason, "ambiguous": ambiguous, "day": e.day, "side": 1, "candidate": rule,
                     "vix": e.vix, "vix_change": e.vix_change, "level": e.level, "entry_minute": e.minute,
                     "target_done": target_done, "partial_t": partial_t})
    return pd.DataFrame(rows, columns=["decision", "entry_t", "exit_t", "entry", "exit", "risk", "R", "points", "reason", "ambiguous", "day", "side", "candidate", "vix", "vix_change", "level", "entry_minute", "target_done", "partial_t"])


def metrics(a, b):
    info = lab.stats(a)
    paired = prior.summary(a, b)["paired"]
    return {**info, "delta_R": float(a.R.sum() - b.R.sum()), "paired": paired, "bootstrap": lab.bootstrap(a),
            "halves": [lab.stats(a.iloc[:len(a)//2]), lab.stats(a.iloc[len(a)//2:])],
            "drop_best": {str(n): lab.stats(a.sort_values("R").iloc[:-n].sort_values("decision")) for n in [1,3,5] if len(a) > n},
            "yearly": {str(y): lab.stats(z) for y,z in a.groupby(a.day.str[:4])},
            "risk_median": float(a.risk.median()) if len(a) else None}


def audit_clock(d, minute_data, step):
    x = minute_data.set_index("ts").resample(f"{step}min").agg(close=("close", "last"), n=("t", "size"))
    x = x[x.n.eq(step)].reset_index()
    x["t"] = x.ts.dt.as_unit("s").astype("int64")
    scans = []
    for lag in [-60, 0, 60]:
        shifted = d[["t", "close"]].copy(); shifted.t += lag * 60
        z = shifted.merge(x[["t", "close"]], on="t", suffixes=("_native", "_m1"))
        err = (z.close_native - z.close_m1).abs()
        scans.append({"shift_minutes": lag, "n": len(z), "median_error": float(err.median())})
    best = min(scans, key=lambda q: q["median_error"])
    assert best["shift_minutes"] == 0 and best["median_error"] < 10, "Native clock does not match corrected M1"
    peak = d.assign(year=d.day.str[:4], span=d.high-d.low).groupby(["year", "ny_min"]).span.median().reset_index()
    peak = peak.loc[peak.groupby("year").span.idxmax()]
    return {"offset_scans": scans, "annual_range_peak_NY": {r.year: int(r.ny_min) for r in peak.itertuples()}}


def main():
    ds = prior.load_data()
    sources = [(s, d, 1, [1,5,15]) for s,d in ds.items()]
    clock = {}
    for tf in [15,30,60]:
        d = native(tf)
        clock[str(tf)] = audit_clock(d, ds["mt5"], tf)
        sources.append((f"native{tf}",d,tf,[tf]))
    lab.save_json(OUT / "clock_audit.json", clock)
    result = {"protocol_sha256": hashlib.sha256((HERE/"PROTOCOL.md").read_bytes()).hexdigest(),
              "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "configurations": RULES,
              "sources": {}, "results": {}}
    allframes = []
    for source,d,step,tfs in sources:
        result["sources"][source] = {"rows":len(d), "first":str(d.ts.min()), "last":str(d.ts.max()),
                                     "execution_tf":step, "RTH_proxy":step==60}
        periods = LONG_PERIODS if step>1 else {k:v for k,v in M1_PERIODS.items() if (k.startswith("D25") if source=="duka" else not k.startswith("D25"))}
        for tf in tfs:
            f = context(d,tf,step)
            f.to_pickle(OUT/f"features_{source}_{tf}.pkl")
            ev = {rule:detect(f,rule) for rule in RULES}
            cases = {"base":{},"spread3":{"spread_mult":3},"slip1":{"slip":1.},"delay1":{"delay":1}}
            if step==1 and tf!=1:cases={"base":{}}
            for case,kw in cases.items():
                executed = {rule:replay(d,x,rule,step,**kw) for rule,x in ev.items()}
                for rule,a in executed.items():
                    a["source"],a["trigger_tf"],a["case"] = source,tf,case
                    # Events outside frozen analysis epochs are retained separately, not silently counted.
                    a.to_csv(OUT/f"trades_{source}_{tf}_{case}_{rule}.csv",index=False)
                    allframes.append(a)
                    for period,(start,end) in periods.items():
                        lo,hi=lab.stamp(start),lab.stamp(end)
                        z=a[(a.decision>=lo)&(a.exit_t<hi)].copy()
                        b=executed["BASE"];b=b[(b.decision>=lo)&(b.exit_t<hi)]
                        result["results"][f"{source}_{tf}_{case}_{period}_{rule}"]=metrics(z,b)
                print("RESULT",source,tf,case,[(r,len(a),round(a.R.sum(),3))for r,a in executed.items()],flush=True)
        lab.save_json(OUT/"evaluation.json",result)
    allrows=pd.concat(allframes,ignore_index=True)
    allrows.to_csv(OUT/"all_trades.csv",index=False)
    result["evaluation_cells"]=len(result["results"])
    lab.save_json(OUT/"evaluation.json",result)
    print("DONE",result["evaluation_cells"],flush=True)


if __name__=="__main__":main()
