"""Meaningful causal-timing and execution checks for the offline simulator."""
from __future__ import annotations

import numpy as np
import pandas as pd

from lab import events, features, load, simulate_grid, specs


def fixture() -> pd.DataFrame:
    ts = pd.date_range("2026-07-06 12:00",periods=160,freq="min",tz="UTC")
    d = pd.DataFrame({"ts":ts,"open":1000.,"high":1001.,"low":999.,"close":1000.,
        "volume":100.,"spread_px":1.3,"source":"fixture","atr70":10.,"atr14":10.,
        "valid60":True,"weekday":0,"ny_min":np.arange(480,640),"day":"2026-07-06"})
    d["t"] = d.ts.dt.as_unit("s").astype("int64")
    return d


def run() -> None:
    d = fixture()
    t = int(d.t.iloc[1])
    # Entry is next bid open + ask spread + adverse entry slippage.
    r = simulate_grid(d)[1].loc[t]
    assert abs(r.entry-1001.5)<1e-8
    assert r.reason == "time" and abs(r.R-(-1.7/50))<1e-8
    # SELL pays spread on exit, including changes during the holding period.
    d.loc[91,"spread_px"] = 2.
    r = simulate_grid(d)[-1].loc[t]
    assert abs(r.entry-999.8)<1e-8 and abs(r.exit-1002.2)<1e-8
    # TP and SL both touched in one minute => conservative stop first.
    d = fixture(); d.loc[1,["high","low"]] = [1100.,900.]
    r = simulate_grid(d)[1].loc[t]
    assert r.reason == "stop" and r.ambiguous and r.R < -1
    # A stop gap is filled at its worse opening price, not at the stop level.
    d = fixture(); d.loc[2,["open","high","low","close"]] = [900.,901.,899.,900.]
    r = simulate_grid(d)[1].loc[t]
    assert r.reason == "stop" and r.R < -2
    # An opening target fill precedes a later low in that same bar.
    d = fixture(); d.loc[2,["open","high","low","close"]] = [1100.,1101.,900.,1000.]
    r = simulate_grid(d)[1].loc[t]
    assert r.reason == "target" and r.R > 1.49
    # No stale next-available entry when the exact entry minute is missing.
    d = fixture().drop(index=1).reset_index(drop=True)
    assert t not in simulate_grid(d)[1].index
    # Unexpected gaps are reported as data_gap rather than removed winners/losers.
    d = fixture().drop(index=4).reset_index(drop=True)
    r = simulate_grid(d)[1].loc[t]
    assert r.reason == "data_gap"
    print("7 bid/ask, gap, ambiguity and deadline execution checks passed",flush=True)
    d = load()
    # An arbitrary partial minute must not change any previously closed feature
    # or trigger. Includes the NY opening-range and closed H1 join.
    cut = int(d[d.ts >= pd.Timestamp("2026-06-03 14:07",tz="UTC")].index[0])
    prefix = d.iloc[:cut].copy()
    cutoff = int(d.t.iloc[cut])
    for tf in [1,3,5]:
        full = features(d,tf)
        pre = features(prefix,tf)
        ff = full[full.decision <= cutoff].reset_index(drop=True)
        pp = pre[pre.decision <= cutoff].reset_index(drop=True)
        pd.testing.assert_frame_equal(ff,pp)
        for spec in specs():
            ta,sa = events(ff,spec,tf)
            tb,sb = events(pp,spec,tf)
            assert np.array_equal(ta,tb) and np.array_equal(sa,sb),spec["id"]
        assert np.all(pp.decision == pp.ts.dt.as_unit("s").astype("int64")+tf*60)
    print("All 432 definitions × 3 timeframes passed prefix-causality checks",flush=True)


if __name__ == "__main__":
    run()
