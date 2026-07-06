"""Dukascopy tick CSVs → canonical per-day parquet.

Input : ~/dukascopy_us100/data/<YYYY-MM-DD>/usatechidxusd-tick-*.csv
        columns: timestamp(epoch ms UTC), askPrice, bidPrice
Output: ndx_reflex_engine/data/ticks/<YYYY-MM-DD>.parquet
        columns: ts_ms(int64), ask(f64), bid(f64), mid(f64), spread(f64)

Idempotent: skips days whose parquet already exists and is newer than the CSV.
Empty/weekend/holiday CSVs produce no output file.
"""
from __future__ import annotations

import glob
import logging
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("ingest_ticks")


def ingest_day(day_dir: str, out_dir: str) -> str | None:
    """Convert one day's CSV to parquet. Returns output path or None if skipped."""
    day = os.path.basename(day_dir)
    csvs = glob.glob(os.path.join(day_dir, "*.csv"))
    if not csvs or os.path.getsize(csvs[0]) == 0:
        return None
    src = csvs[0]
    dst = os.path.join(out_dir, f"{day}.parquet")
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return dst

    df = pd.read_csv(src, dtype={"timestamp": "int64", "askPrice": "float64", "bidPrice": "float64"})
    if df.empty:
        return None
    df = df.rename(columns={"timestamp": "ts_ms", "askPrice": "ask", "bidPrice": "bid"})
    df = df.sort_values("ts_ms", kind="stable").drop_duplicates(subset=["ts_ms", "ask", "bid"])
    # sanity: drop crossed quotes (audit found none, but never trust future downloads)
    crossed = df["ask"] < df["bid"]
    if crossed.any():
        log.warning("%s: dropping %d crossed quotes", day, int(crossed.sum()))
        df = df[~crossed]
    df["mid"] = (df["ask"] + df["bid"]) / 2.0
    df["spread"] = df["ask"] - df["bid"]
    df.to_parquet(dst, index=False)
    return dst


def main() -> None:
    os.makedirs(config.TICKS_PARQUET_DIR, exist_ok=True)
    day_dirs = sorted(glob.glob(os.path.join(config.TICKS_RAW_DIR, "20*")))
    done = skipped = 0
    for d in day_dirs:
        out = ingest_day(d, config.TICKS_PARQUET_DIR)
        if out:
            done += 1
        else:
            skipped += 1
    log.info("ingest complete: %d days written/current, %d empty/skipped", done, skipped)


if __name__ == "__main__":
    main()
