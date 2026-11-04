"""Prefix and mutation checks for newly introduced decision features and gates."""
import json
import numpy as np
import pandas as pd
from run import OUT, lab, load_data, features, events, apply_overlay, reclaim, OVERLAYS, RECLAIMS

def main():
    ds = load_data()
    d = ds["mt5"]
    checked = []
    cols = ["ret1", "ret5", "extension", "prev_rth_low", "raw_ratio", "season_ratio", "low15_m1", "stress", "shock"]
    # Cut during RTH, not just at a session boundary, exposing accidental full-day reads.
    for tf in [1, 3, 5]:
        full = features(d, tf, "mt5")
        full_events = events(full, tf)
        for cutoff in ["2026-03-24T15:17:00Z", "2026-06-22T15:17:00Z", "2026-09-17T15:17:00Z"]:
            t = int(pd.Timestamp(cutoff).timestamp())
            partial = d[d.t < t].copy()
            f = features(partial, tf, "mt5")
            a = full[full.decision <= t].reset_index(drop=True)
            pd.testing.assert_frame_equal(a[cols], f[cols].reset_index(drop=True))
            x = events(f, tf)
            for rule in OVERLAYS:
                af = apply_overlay(d, full_events, rule)
                ap = apply_overlay(partial, x, rule)
                # A delayed intention exists only once all waiting bars have closed.
                af = af[af.decision <= t][["origin", "decision", "side", "candidate"]]
                ap = ap[ap.decision <= t][["origin", "decision", "side", "candidate"]]
                pd.testing.assert_frame_equal(af.reset_index(drop=True), ap.reset_index(drop=True))
            for rule in RECLAIMS:
                af = reclaim(full, tf, rule)
                ap = reclaim(f, tf, rule)
                af = af[af.decision <= t][["origin", "decision", "side"]]
                pd.testing.assert_frame_equal(af.reset_index(drop=True), ap[["origin", "decision", "side"]].reset_index(drop=True))
            checked.append({"tf": tf, "cutoff": cutoff, "rules": len(OVERLAYS) + len(RECLAIMS)})
        print("PREFIX PASS", tf, flush=True)
    # Future OHLC and volume can be arbitrary without changing earlier decisions.
    t = lab.stamp("2026-09-17")
    changed = d.copy()
    future = changed.t >= t
    changed.loc[future, ["open", "high", "low", "close"]] *= 1.2
    changed.loc[future, "volume"] *= 100
    # Recompute causal ATR because the deliberate perturbation changes later ATR.
    changed["atr14"], changed["atr70"] = lab.atr(changed, 14), lab.atr(changed, 70)
    a, b = features(d, 1, "mt5"), features(changed, 1, "mt5")
    pd.testing.assert_frame_equal(a[a.decision <= t][cols], b[b.decision <= t][cols])
    result = {"prefix_checks": checked, "future_mutation": "passed", "rules": 14,
              "new_input_overlap": "passed in load_data", "status": "PASS"}
    (OUT / "verification.json").write_text(json.dumps(result, indent=2))
    print("ALL PASS", flush=True)

if __name__ == "__main__":
    main()
