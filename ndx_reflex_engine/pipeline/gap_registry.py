"""Gap registry — the honesty layer under triggers and labels.

Scans the 1m bar files and produces gap_registry.parquet with one row per
(day, gap_start, gap_end) for every silent period > GAP_MAX_SILENT_MIN inside
the instrument's expected trading coverage. Holidays and weekends are excluded
by the static 2025 calendar; the CFD daily break (~21:00→23:00 UTC) is treated
as expected closure, not a gap.

Downstream rules (enforced in triggers/ and labels/):
  * a trigger whose lookback window crosses a gap is dropped
  * a label whose barrier window crosses a gap is dropped
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

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("gap_registry")

# Expected daily closure of the CFD (UTC hours, observed in the feed).
DAILY_BREAK_START_H = 21
DAILY_BREAK_END_H = 23


def _is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in config.HOLIDAYS_2025


def day_gaps(bar_path: str) -> list[dict]:
    day_str = os.path.basename(bar_path).replace(".parquet", "")
    d = date.fromisoformat(day_str)
    if not _is_trading_day(d):
        return []
    bars = pd.read_parquet(bar_path, columns=["ts"])
    if bars.empty:
        return [{"day": day_str, "gap_start": None, "gap_end": None, "minutes": 24 * 60, "whole_day": True}]
    ts = bars["ts"].sort_values().reset_index(drop=True)
    gaps = []
    diffs = ts.diff().dt.total_seconds().div(60).fillna(0)
    for i in diffs[diffs > config.GAP_MAX_SILENT_MIN].index:
        start, end = ts[i - 1], ts[i]
        # ignore the expected daily break window entirely contained in 21:00–23:00
        if start.hour >= DAILY_BREAK_START_H and (end.hour >= DAILY_BREAK_END_H or end.hour < 1):
            continue
        gaps.append({
            "day": day_str, "gap_start": start, "gap_end": end,
            "minutes": round((end - start).total_seconds() / 60, 1), "whole_day": False,
        })
    return gaps


def main() -> None:
    rows: list[dict] = []
    for p in sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet"))):
        rows.extend(day_gaps(p))
    reg = pd.DataFrame(rows)
    os.makedirs(config.DATA_DIR, exist_ok=True)
    reg.to_parquet(config.GAPS_PATH, index=False)
    in_session = reg[~reg["whole_day"].fillna(False)] if not reg.empty else reg
    log.info("gap registry: %d gaps recorded (%s days affected) → %s",
             len(reg), reg["day"].nunique() if not reg.empty else 0, config.GAPS_PATH)
    if not in_session.empty:
        worst = in_session.nlargest(5, "minutes")[["day", "gap_start", "gap_end", "minutes"]]
        log.info("worst in-session gaps:\n%s", worst.to_string(index=False))


if __name__ == "__main__":
    main()
