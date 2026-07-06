"""Tick parquet → 1-minute bid/ask bars with microstructure columns.

Output: ndx_reflex_engine/data/bars_1m/<YYYY-MM-DD>.parquet, one row per minute
that contains at least one tick. Columns:

  ts               minute start (UTC, tz-aware)
  bid_o/h/l/c      bid OHLC
  ask_o/h/l/c      ask OHLC
  mid_o/h/l/c      mid OHLC
  spread_mean/med/p95
  n_ticks          tick count (activity proxy — Dukascopy index feed has no volume)
  up_ticks/down_ticks    tick-rule counts on mid changes
  sign_flip_ratio  fraction of consecutive mid moves that reversed sign
  max_run          longest same-direction mid-move run
  path_len         sum |Δmid| inside the minute (choppiness vs range)
  range_mid        mid high − low

Labels replay against bid/ask columns directly, so the spread lives inside the
replay rather than as a constant haircut.
"""
from __future__ import annotations

import glob
import logging
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("build_bars")


def _run_stats(sign: np.ndarray) -> tuple[int, int, float, int]:
    """(up_ticks, down_ticks, sign_flip_ratio, max_run) from signed mid changes."""
    nz = sign[sign != 0]
    if len(nz) < 2:
        return int((nz > 0).sum()), int((nz < 0).sum()), 0.0, len(nz)
    flips = int((nz[1:] != nz[:-1]).sum())
    # max same-sign run length
    change = np.flatnonzero(nz[1:] != nz[:-1])
    edges = np.concatenate(([0], change + 1, [len(nz)]))
    max_run = int(np.diff(edges).max())
    return int((nz > 0).sum()), int((nz < 0).sum()), flips / (len(nz) - 1), max_run


def build_day(tick_path: str, out_dir: str) -> str | None:
    day = os.path.basename(tick_path).replace(".parquet", "")
    dst = os.path.join(out_dir, f"{day}.parquet")
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(tick_path):
        return dst

    t = pd.read_parquet(tick_path)
    if t.empty:
        return None
    t["ts"] = pd.to_datetime(t["ts_ms"], unit="ms", utc=True)
    t["minute"] = t["ts"].dt.floor("1min")

    agg = t.groupby("minute").agg(
        bid_o=("bid", "first"), bid_h=("bid", "max"), bid_l=("bid", "min"), bid_c=("bid", "last"),
        ask_o=("ask", "first"), ask_h=("ask", "max"), ask_l=("ask", "min"), ask_c=("ask", "last"),
        mid_o=("mid", "first"), mid_h=("mid", "max"), mid_l=("mid", "min"), mid_c=("mid", "last"),
        spread_mean=("spread", "mean"), spread_med=("spread", "median"),
        spread_p95=("spread", lambda s: s.quantile(0.95)),
        n_ticks=("mid", "size"),
    )

    # microstructure per minute (vectorized inner loop per group)
    micro = {}
    for minute, g in t.groupby("minute"):
        dm = np.diff(g["mid"].to_numpy())
        sign = np.sign(dm)
        up, dn, flip, run = _run_stats(sign)
        micro[minute] = (up, dn, flip, run, float(np.abs(dm).sum()))
    md = pd.DataFrame.from_dict(
        micro, orient="index",
        columns=["up_ticks", "down_ticks", "sign_flip_ratio", "max_run", "path_len"],
    )
    bars = agg.join(md)
    bars["range_mid"] = bars["mid_h"] - bars["mid_l"]
    bars = bars.reset_index().rename(columns={"minute": "ts"})
    bars.to_parquet(dst, index=False)
    return dst


def main() -> None:
    os.makedirs(config.BARS_DIR, exist_ok=True)
    paths = sorted(glob.glob(os.path.join(config.TICKS_PARQUET_DIR, "*.parquet")))
    n = 0
    for p in paths:
        if build_day(p, config.BARS_DIR):
            n += 1
    log.info("bars complete: %d day files", n)


if __name__ == "__main__":
    main()
