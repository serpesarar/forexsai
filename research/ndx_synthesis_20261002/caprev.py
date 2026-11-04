"""Independent M1 execution audit of the newly discovered TUR3 addendum."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from run import (HERE, OUT, PERIODS, load_data, features, macro_series, events, execute,
                 summary, lab, old2)

RULES = ["CAPREV", "CAP_ALLVIX", "CAP_LOWVIX", "CAP_CALM", "CAP_SELL", "CAP_FIXED", "CAP_RECLAIM"]


def context_extra(d, f):
    m = macro_series()
    dates = pd.to_datetime(f.day).to_numpy()
    j = np.searchsorted(m.index.to_numpy(), dates, side="left") - 1
    ok = (j >= 0) & ((dates - m.index.to_numpy()[np.maximum(j, 0)]) / np.timedelta64(1, "D") <= 5)
    f = f.copy()
    f["dvol"] = np.where(ok, m.pct_change().rolling(20).std().to_numpy()[np.maximum(j, 0)], np.nan)
    macro = pd.read_csv(OUT / "macro_daily.csv", parse_dates=["date"]).set_index("date")
    vix = macro.VIX_close.dropna().sort_index()
    k = np.searchsorted(vix.index.to_numpy(), dates, side="left") - 1
    good = (k >= 0) & ((dates - vix.index.to_numpy()[np.maximum(k, 0)]) / np.timedelta64(1, "D") <= 5)
    f["vix"] = np.where(good, vix.to_numpy()[np.maximum(k, 0)], np.nan)
    # Reproduce the other report's regression residual scale with closed M5s.
    v = d.set_index("ts").resample("5min").agg(close=("close", "last"), n=("t", "size"))
    v = v[v.n.eq(5)].reset_index()
    n = 50
    y = v.close.to_numpy(float)
    sx = np.arange(n, dtype=float)
    sy = np.convolve(y, np.ones(n), "valid")
    sxy = np.convolve(y, sx[::-1], "valid")
    sy2 = np.convolve(y * y, np.ones(n), "valid")
    mean = sy / n
    slope = (sxy / n - sx.mean() * mean) / sx.var()
    variance = np.maximum(sy2 / n - mean * mean - slope * slope * sx.var(), 0)
    z = np.full(len(y), np.nan)
    z[n - 1:] = np.divide(y[n - 1:] - (mean + slope * (n - 1 - sx.mean())), np.sqrt(variance),
                         out=np.full(len(variance), np.nan), where=variance > 1e-12)
    avail = v.ts.dt.as_unit("s").astype("int64").to_numpy() + 300
    j = np.searchsorted(avail, f.decision, side="right") - 1
    good = (j >= 0) & ((f.decision.to_numpy() - avail[np.maximum(j, 0)]) < 300)
    f["channel5"] = np.where(good, z[np.maximum(j, 0)], np.nan)
    f["chase_sell"] = np.sum(np.vstack([(f.channel5 <= -1), (f.m15_dir < 0),
                                         (f.close < f.prev_rth_low), f.stress]), axis=0)
    return f


def detect(f, tf, rule):
    eligible = f.valid & f.minute.between(180 + tf, 900) & f.dvol.gt(0)
    cond = (f.close < f.prev_rth_low)
    if rule == "CAP_RECLAIM":
        cond = f.prev_rth_low.eq(f.prev_rth_low.shift()) & f.decision.diff().eq(tf * 60)
        cond &= (f.close.shift() <= f.prev_rth_low) & (f.close > f.prev_rth_low)
        cond &= (f.prev_rth_low - f.low15_m1 >= .5 * f.atr70) & (f.clv > .2)
    if rule == "CAP_CALM":
        eligible &= ~f.stress & f.ret1.notna() & (f.vix >= 18.4)
    else:
        eligible &= f.stress
        if rule == "CAP_LOWVIX":
            eligible &= f.vix < 18.4
        elif rule != "CAP_ALLVIX":
            eligible &= f.vix >= 18.4
    x = f[eligible & cond].groupby("day", sort=False).head(1).copy()
    x["side"] = -1 if rule == "CAP_SELL" else 1
    return x


def replay(d, ev, rule, spread_mult=1., slip=.2, delay=0):
    t = d.t.to_numpy()
    oo, hh, ll, cc = [d[c].to_numpy() for c in ["open", "high", "low", "close"]]
    sp = d.spread_px.to_numpy()
    exact_ask = "ask_open" in d
    ask = {x: d["ask_" + x].to_numpy() if exact_ask else d[x].to_numpy() + sp for x in ["open", "high", "low", "close"]}
    rows = []
    for e in ev.itertuples():
        entry_time = e.decision + delay * 60
        i = np.searchsorted(t, entry_time)
        if i >= len(t) or t[i] != entry_time:
            continue
        side = e.side
        entry = oo[i] - slip if side < 0 else ask["open"][i] + (spread_mult - 1) * sp[i] + slip
        risk = 110. if rule == "CAP_FIXED" else entry * e.dvol
        stop = entry - side * risk
        target = entry + 80 if rule == "CAP_FIXED" else np.inf
        reason, exitpx, k, ambiguous = None, None, i, False
        deadline = int(pd.Timestamp(e.day + " 16:00", tz="America/New_York").timestamp())
        while k < len(t) and t[k] <= deadline:
            if t[k] != entry_time + 60 * (k - i):
                k -= 1
                exitpx = cc[k] - slip if side > 0 else ask["close"][k] + (spread_mult - 1) * sp[k] + slip
                reason = "data_gap"
                break
            o, h, lo = oo[k], hh[k], ll[k]
            if side < 0:
                o, h, lo = [ask[c][k] + (spread_mult - 1) * sp[k] for c in ["open", "high", "low"]]
            if t[k] == deadline:
                exitpx = o - side * slip
                reason = "stop" if (o <= stop if side > 0 else o >= stop) else "time"
                if rule == "CAP_FIXED" and o >= target:
                    exitpx, reason = target - slip, "target"
                break
            hit_stop = lo <= stop if side > 0 else h >= stop
            hit_target = rule == "CAP_FIXED" and h >= target
            if hit_target and o >= target:
                hit_stop = False
            if hit_stop:
                exitpx = (min(o, stop) if side > 0 else max(o, stop)) - side * slip
                reason = "stop"
                ambiguous = bool(hit_target)
                break
            if hit_target:
                exitpx, reason = target - slip, "target"
                break
            k += 1
        if reason is None:
            k = min(k - 1, len(t) - 1)
            exitpx = cc[k] - slip if side > 0 else ask["close"][k] + (spread_mult - 1) * sp[k] + slip
            reason = "data_gap"
        points = side * (exitpx - entry)
        rows.append({"decision": e.decision, "entry_t": entry_time, "exit_t": int(t[k]) + 60,
                     "side": side, "entry": entry, "exit": exitpx, "risk": risk, "R": points / risk,
                     "points": points, "reason": reason, "ambiguous": ambiguous, "day": e.day,
                     "candidate": rule, "priority": 0, "vix": e.vix, "dvol": e.dvol})
    return pd.DataFrame(rows, columns=["decision", "entry_t", "exit_t", "side", "entry", "exit", "risk", "R",
                                       "points", "reason", "ambiguous", "day", "candidate", "priority", "vix", "dvol"])


def main():
    result = {"protocol_sha256": hashlib.sha256((HERE / "PROTOCOL_ADDENDUM.md").read_bytes()).hexdigest(),
              "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "results": {}}
    for source, d in load_data().items():
        periods = ["D25a", "D25b"] if source == "duka" else ["C26", "M26", "S26", "Sep30", "Oct01"]
        cases = {"base": {}, "spread3": {"spread_mult": 3}, "slip1": {"slip": 1.}, "delay1": {"delay": 1}}
        for tf in [1, 5, 15]:
            f = context_extra(d, features(d, tf, source))
            for case, kw in cases.items():
                if tf != 1 and case != "base":
                    continue
                for rule in RULES:
                    a = replay(d, detect(f, tf, rule), rule, **kw)
                    for p in periods:
                        lo, hi = map(lab.stamp, PERIODS[p])
                        r = a[(a.decision >= lo) & (a.decision < hi) & (a.exit_t < hi)].reset_index(drop=True)
                        info = lab.stats(r)
                        info.update({"bootstrap": lab.bootstrap(r), "risk_median": float(r.risk.median()) if len(r) else None,
                                     "halves": [lab.stats(r.iloc[:len(r)//2]), lab.stats(r.iloc[len(r)//2:])],
                                     "drop_best5": lab.stats(r.sort_values("R").iloc[:-5].sort_values("decision")) if len(r) > 5 else None})
                        result["results"][f"{p}_{tf}_{case}_{rule}"] = info
                        r.to_csv(OUT / f"trades_{p}_{tf}_{case}_{rule}.csv", index=False)
            print("CAP", source, tf, {r: (len(detect(f, tf, r))) for r in RULES}, flush=True)
        # Chase is tested on exactly the original strategy opportunities and execution.
        fs = {tf: context_extra(d, pd.read_pickle(OUT / f"features_{source}_{tf}.pkl")) for tf in [1, 3, 5]}
        for case, kw in cases.items():
            grids = {g: lab.simulate_grid(d, **{**params, **kw}) for g, params in {**old2.GEOMETRIES, "fixed": {"geometry": "fixed"}}.items()}
            for tf in ([1, 3, 5] if case == "base" else [1]):
                x = events(fs[tf], tf)
                z = x[~((x.side < 0) & (x.chase_sell >= 3))]
                for p in periods:
                    a, b = execute(z, grids, p), execute(x, grids, p)
                    result["results"][f"{p}_{tf}_{case}_CHASE"] = summary(a, b)
                    a.to_csv(OUT / f"trades_{p}_{tf}_{case}_CHASE.csv", index=False)
        lab.save_json(OUT / "addendum.json", result)
    print("DONE", len(result["results"]), flush=True)


if __name__ == "__main__":
    main()
