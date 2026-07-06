"""Run all trigger detectors over the full bar archive → events_raw.parquet.

Usage: python3 research/build_events.py
"""
from __future__ import annotations

import glob
import logging
import os
import sys
from datetime import date

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from triggers.detect import detect_day  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("build_events")


def main() -> None:
    paths = sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet")))
    all_events = []
    prev_bars = None
    for p in paths:
        day = date.fromisoformat(os.path.basename(p).replace(".parquet", ""))
        bars = pd.read_parquet(p)
        if day.weekday() >= 5 or day in config.HOLIDAYS_2025:
            prev_bars = bars
            continue
        ev = detect_day(bars, prev_bars, day)
        if not ev.empty:
            all_events.append(ev)
        prev_bars = bars

    events = pd.concat(all_events, ignore_index=True).sort_values("ts").reset_index(drop=True)
    os.makedirs(config.EVENTS_DIR, exist_ok=True)
    out = os.path.join(config.EVENTS_DIR, "events_raw.parquet")
    events.to_parquet(out, index=False)
    log.info("events: %d total → %s", len(events), out)
    log.info("\n%s", events.groupby(["family", "direction"]).size().unstack(fill_value=0).to_string())
    log.info("per-day mean: %.1f", len(events) / events["ts"].dt.date.nunique())


if __name__ == "__main__":
    main()
