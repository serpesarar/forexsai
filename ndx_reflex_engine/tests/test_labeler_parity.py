"""Parity check: label_events (reference loop) vs label_events_fast (numpy).

Runs both labelers over several real days of events and asserts identical
outcome / exit_reason / r_multiple. Run: python3 tests/test_labeler_parity.py
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from labels.triple_barrier import Geometry, label_events, label_events_fast  # noqa: E402


def main() -> None:
    events = pd.read_parquet(os.path.join(config.EVENTS_DIR, "events_raw.parquet"))
    events["day"] = events["ts"].dt.date.astype(str)
    days = sorted(events["day"].unique())
    sample_days = days[:: max(1, len(days) // 8)][:8]
    geo = Geometry(tp_atr=1.0, sl_atr=1.0, time_stop_min=60)

    total = mismatches = 0
    for day in sample_days:
        bar_path = os.path.join(config.BARS_DIR, f"{day}.parquet")
        if not os.path.exists(bar_path):
            continue
        bars = pd.read_parquet(bar_path)
        ev = events[events["day"] == day][["ts", "direction", "family"]].reset_index(drop=True)
        ref = label_events(bars, ev, geo)
        fast = label_events_fast(bars, ev, geo)
        cmp_cols = ["outcome", "exit_reason"]
        neq = (ref[cmp_cols] != fast[cmp_cols]).any(axis=1)
        r_neq = ~np.isclose(ref["r_multiple"].fillna(-9), fast["r_multiple"].fillna(-9), atol=1e-9)
        bad = neq | r_neq
        total += len(ev)
        mismatches += int(bad.sum())
        if bad.any():
            print(f"{day}: {int(bad.sum())} mismatches")
            print(pd.concat([ref[bad][["ts", "direction"] + cmp_cols + ["r_multiple"]],
                             fast[bad][cmp_cols + ["r_multiple"]].add_suffix("_fast")], axis=1).head(10))

    print(f"parity: {total - mismatches}/{total} identical")
    assert mismatches == 0, f"{mismatches} mismatches between loop and fast labeler"
    print("PASS")


if __name__ == "__main__":
    main()
