"""Validate the new daily-volatility execution path and first-event causality."""
import json
import numpy as np
import pandas as pd
from run import OUT, lab, load_data, features
from caprev import context_extra, detect, replay, RULES


def fixtures():
    t = pd.date_range("2026-09-21 03:00", "2026-09-21 16:00", freq="min", tz="America/New_York").tz_convert("UTC")
    d = pd.DataFrame({"t": t.as_unit("s").asi8, "open": 100., "high": 101., "low": 99., "close": 100., "spread_px": 2.})
    e = pd.DataFrame([{"decision": d.t.iat[1], "side": 1, "dvol": .10, "day": "2026-09-21", "vix": 25.}])
    r = replay(d, e, "CAPREV").iloc[0]
    assert abs(r.entry - 102.2) < 1e-9 and abs(r.exit - 99.8) < 1e-9 and r.reason == "time"
    x = d.copy(); x.loc[2, ["open", "low"]] = 85.
    r = replay(x, e, "CAPREV").iloc[0]
    assert r.reason == "stop" and abs(r.exit - 84.8) < 1e-9 and r.R < -1
    x = d.copy(); x.loc[2, "low"] = 90.
    r = replay(x, e, "CAPREV").iloc[0]
    assert r.reason == "stop" and abs(r.exit - (r.entry - r.risk - .2)) < 1e-9
    x = d.copy().drop(index=3).reset_index(drop=True)
    assert replay(x, e, "CAPREV").iloc[0].reason == "data_gap"
    r = replay(d, e, "CAPREV", delay=1).iloc[0]
    assert r.entry_t == e.decision.iat[0] + 60
    # Actual ask OHLC overrides the spread proxy for short liquidation.
    for col in ["open", "high", "low", "close"]:
        d["ask_" + col] = d[col] + 3.
    e["side"] = -1
    r = replay(d, e, "CAP_SELL").iloc[0]
    assert abs(r.entry - 99.8) < 1e-9 and abs(r.exit - 103.2) < 1e-9
    # Fixed bracket: the opening target precedes a later intrabar stop.
    e["side"] = 1
    x = d.copy(); x.loc[2, ["open", "high", "low"]] = [190., 195., -20.]
    r = replay(x, e, "CAP_FIXED").iloc[0]
    assert r.reason == "target" and not r.ambiguous
    x.loc[2, "open"] = 100.
    r = replay(x, e, "CAP_FIXED").iloc[0]
    assert r.reason == "stop" and r.ambiguous
    return 8


def main():
    n = fixtures()
    ds = load_data(); d = ds["mt5"]
    cols = ["dvol", "vix", "channel5", "chase_sell"]
    checks = []
    for tf in [1, 5, 15]:
        full = context_extra(d, features(d, tf, "mt5"))
        t = int(pd.Timestamp("2026-03-23T15:17Z").timestamp())
        partial = d[d.t < t].copy()
        f = context_extra(partial, features(partial, tf, "mt5"))
        pd.testing.assert_frame_equal(full[full.decision <= t][cols].reset_index(drop=True), f[cols].reset_index(drop=True))
        for rule in RULES:
            a, b = detect(full, tf, rule), detect(f, tf, rule)
            a = a[a.decision <= t]
            pd.testing.assert_frame_equal(a[["decision", "side"]].reset_index(drop=True), b[["decision", "side"]].reset_index(drop=True))
        checks.append(tf)
    (OUT / "verification_caprev.json").write_text(json.dumps({"status": "PASS", "execution_fixtures": n, "prefix_tf": checks, "rules": RULES}, indent=2))
    print("PASS", n, "fixtures", checks, flush=True)

if __name__ == "__main__":
    main()
