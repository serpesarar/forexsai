"""FINAL GATE — 2026 broker-candle transfer test.

Runs the mom_cont detector (Tier A, candles only) on real USTEC 1m bars from
candle_cache (2026-02-11 → now) and labels with the SAME frozen geometry and
the SAME honest replay — bid/ask synthesized as mid ∓ spread/2 with a
conservative IC-style spread (SPREAD_PTS_2026), because broker candles are
single-price. Slippage identical to the 2025 study.

A family ships only if its 2026 EV lands inside (or above) the 2025 OOS band.

Usage: python3 research/transfer_test_2026.py
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date

import numpy as np
import pandas as pd
import requests
from dotenv import dotenv_values

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from labels.triple_barrier import Geometry, label_events_fast  # noqa: E402
from triggers.detect import detect_mom_cont, _apply_refractory, _in_window  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("transfer")

SPREAD_PTS_2026 = 2.0   # conservative IC Markets USTEC session spread assumption
CACHE = os.path.join(config.DATA_DIR, "ustec_1m_2026.parquet")


def fetch_candles() -> pd.DataFrame:
    if os.path.exists(CACHE):
        return pd.read_parquet(CACHE)
    env = dotenv_values(os.path.join(os.path.dirname(config.ENGINE_DIR), "backend", ".env"))
    url, key = env["SUPABASE_URL"].rstrip("/"), (env.get("SUPABASE_SERVICE_ROLE_KEY") or env["SUPABASE_KEY"])
    rows, page, page_size = [], 0, 1000  # PostgREST hard-caps at max-rows (1000)
    while True:
        lo = page * page_size
        r = requests.get(
            f"{url}/rest/v1/candle_cache",
            params={"symbol": "eq.NDX.INDX", "timeframe": "eq.1m",
                    "select": "candle_time,open,high,low,close,volume",
                    "order": "candle_time.asc"},
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Range-Unit": "items", "Range": f"{lo}-{lo + page_size - 1}"},
            timeout=60)
        r.raise_for_status()
        chunk = r.json()
        rows.extend(chunk)
        if page % 20 == 0:
            log.info("page %d: %d rows (total %d)", page, len(chunk), len(rows))
        if len(chunk) < page_size:
            break
        page += 1
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["candle_time"], utc=True, format="ISO8601")
    df = df.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    df.to_parquet(CACHE, index=False)
    return df


def to_bar_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Broker OHLC → the engine's bar schema with synthetic bid/ask."""
    h = SPREAD_PTS_2026 / 2.0
    b = pd.DataFrame({"ts": df["ts"]})
    for side, off in (("bid", -h), ("ask", +h), ("mid", 0.0)):
        for k, col in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close")):
            b[f"{side}_{k}"] = df[col] + off
    b["n_ticks"] = df["volume"].fillna(1).clip(lower=1)
    for col in ("spread_mean", "spread_med", "spread_p95"):
        b[col] = SPREAD_PTS_2026
    for col in ("up_ticks", "down_ticks", "sign_flip_ratio", "max_run", "path_len"):
        b[col] = np.nan
    b["range_mid"] = b["mid_h"] - b["mid_l"]
    return b


def main() -> None:
    with open(os.path.join(config.EVENTS_DIR, "geometry_choice.json")) as f:
        geo_choice = json.load(f)

    candles = fetch_candles()
    bars = to_bar_frame(candles)
    log.info("USTEC 1m: %d bars %s → %s", len(bars), bars["ts"].min(), bars["ts"].max())

    # detect mom_cont day by day (with prev-day context), 2026 DST ≈ same 13:00-20:00 window
    events = []
    days = sorted(bars["ts"].dt.date.unique())
    for i, d in enumerate(days):
        ctx = bars[bars["ts"].dt.date.isin(days[max(0, i - 1):i + 1])].reset_index(drop=True)
        ev = detect_mom_cont(ctx)
        if ev.empty:
            continue
        ev = ev[ev["ts"].dt.date == d]
        ev = ev[_in_window(ev["ts"])]
        events.append(ev)
    ev = pd.concat(events, ignore_index=True)
    ev = _apply_refractory(ev)
    log.info("2026 mom_cont events: %d (%.1f/day)", len(ev), len(ev) / max(len(days), 1))

    for dirn in ("SELL", "BUY"):
        g = geo_choice[f"mom_cont|{dirn}"]
        geo = Geometry(g["tp_atr"], g["sl_atr"], g["ts_min"])
        labs = []
        for d, grp in ev[ev["direction"] == dirn].groupby(ev["ts"].dt.date):
            day_bars = bars[bars["ts"].dt.date == d].reset_index(drop=True)
            labs.append(label_events_fast(day_bars, grp.reset_index(drop=True), geo))
        if not labs:
            log.info("mom_cont|%s: no events", dirn)
            continue
        lab = pd.concat(labs, ignore_index=True)
        res = lab[lab["outcome"].isin(["win", "loss"])].copy()
        res["r_net"] = res["r_multiple"] - config.SLIPPAGE_PTS / res["sl_dist"]
        wr = (res["outcome"] == "win").mean()
        log.info("mom_cont|%s 2026 TRANSFER: n=%d resolved (%d dropped) WR=%.1f%% EV=%+.3fR "
                 "(2025: train %+0.3f / holdout battery %+0.3f)",
                 dirn, len(res), (lab["outcome"] == "dropped").sum(), wr * 100,
                 res["r_net"].mean(), g["train_ev_r"],
                 0.495 if dirn == "SELL" else 0.108)
        by_month = res.groupby(res["ts"].dt.to_period("M"))["r_net"].agg(["size", "mean"]).round(3)
        log.info("by month:\n%s", by_month.to_string())


if __name__ == "__main__":
    main()
