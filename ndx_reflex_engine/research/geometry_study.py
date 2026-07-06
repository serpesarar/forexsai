"""Geometry study — per-family honest base rates over the TP/SL/time-stop grid.

For each (family, geometry) cell: label all events with the fast triple-barrier
replayer, dedup 60-min per (family, direction), report n / WR / mean R / EV net
of slippage. EV is in R units; slippage enters as SLIPPAGE_PTS / sl_dist per trade.

The winning geometry per family is chosen on the TRAIN SPLIT ONLY (first 60%
of days, chronological) — the last 40% never touches geometry selection.

Output:
  data/events/geometry_grid.parquet   full grid results (train split)
  data/events/geometry_choice.json    frozen per-family geometry
  stdout summary
"""
from __future__ import annotations

import glob
import itertools
import json
import logging
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from labels.triple_barrier import Geometry, label_events_fast  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("geometry_study")


def dedup(ev: pd.DataFrame) -> pd.DataFrame:
    """60-min dedup per (family, direction) — the statistic-hygiene standard."""
    keep = []
    last: dict[tuple, pd.Timestamp] = {}
    for _, r in ev.sort_values("ts").iterrows():
        key = (r["family"], r["direction"])
        prev = last.get(key)
        if prev is None or (r["ts"] - prev) >= pd.Timedelta(minutes=config.DEDUP_MIN):
            keep.append(r)
            last[key] = r["ts"]
    return pd.DataFrame(keep)


def label_all(events: pd.DataFrame, geo: Geometry) -> pd.DataFrame:
    """Label events day-by-day against that day's bars."""
    out = []
    for day, ev_day in events.groupby(events["ts"].dt.date.astype(str)):
        bar_path = os.path.join(config.BARS_DIR, f"{day}.parquet")
        if not os.path.exists(bar_path):
            continue
        bars = pd.read_parquet(bar_path)
        out.append(label_events_fast(bars, ev_day.reset_index(drop=True), geo))
    return pd.concat(out, ignore_index=True)


def summarize(lab: pd.DataFrame) -> pd.DataFrame:
    res = lab[lab["outcome"].isin(["win", "loss"])].copy()
    if res.empty:
        return pd.DataFrame()
    res["r_net"] = res["r_multiple"] - config.SLIPPAGE_PTS / res["sl_dist"]
    g = res.groupby(["family", "direction"])
    return pd.DataFrame({
        "n": g.size(),
        "wr": g.apply(lambda x: (x["outcome"] == "win").mean(), include_groups=False),
        "ev_r": g["r_net"].mean(),
        "dropped_pct": lab.groupby(["family", "direction"]).apply(
            lambda x: (x["outcome"] == "dropped").mean(), include_groups=False),
    }).reset_index()


def main() -> None:
    events = pd.read_parquet(os.path.join(config.EVENTS_DIR, "events_raw.parquet"))
    days = sorted(events["ts"].dt.date.unique())
    split = days[int(len(days) * 0.6)]
    train_ev = events[events["ts"].dt.date <= split]
    log.info("train split: %s..%s (%d events), holdout untouched after %s",
             days[0], split, len(train_ev), split)

    rows = []
    grid = list(itertools.product(config.TB_TP_ATR_GRID, config.TB_SL_ATR_GRID,
                                  config.TB_TIME_STOP_MIN_GRID))
    for tp, sl, ts_min in grid:
        geo = Geometry(tp, sl, ts_min)
        lab = label_all(train_ev, geo)
        lab_d = dedup(lab)
        s = summarize(lab_d)
        if s.empty:
            continue
        s["tp_atr"], s["sl_atr"], s["ts_min"] = tp, sl, ts_min
        rows.append(s)
        log.info("geo tp=%.2f sl=%.2f ts=%d done (%d resolved)", tp, sl, ts_min, int(s["n"].sum()))

    full = pd.concat(rows, ignore_index=True)
    full.to_parquet(os.path.join(config.EVENTS_DIR, "geometry_grid.parquet"), index=False)

    # choose per (family, direction): max EV with n >= 30; require ev > 0 to be viable
    choice: dict[str, dict] = {}
    for (fam, d), sub in full[full["n"] >= 30].groupby(["family", "direction"]):
        best = sub.loc[sub["ev_r"].idxmax()]
        choice[f"{fam}|{d}"] = {
            "tp_atr": float(best["tp_atr"]), "sl_atr": float(best["sl_atr"]),
            "ts_min": int(best["ts_min"]), "train_n": int(best["n"]),
            "train_wr": round(float(best["wr"]), 4), "train_ev_r": round(float(best["ev_r"]), 4),
            "viable": bool(best["ev_r"] > 0),
        }
    with open(os.path.join(config.EVENTS_DIR, "geometry_choice.json"), "w") as f:
        json.dump(choice, f, indent=2)

    log.info("\n=== BEST GEOMETRY PER FAMILY (train split, deduped, net slippage) ===")
    for k, v in sorted(choice.items()):
        log.info("%-16s tp=%.2f sl=%.2f ts=%3d  n=%4d  WR=%.1f%%  EV=%+.3fR  %s",
                 k, v["tp_atr"], v["sl_atr"], v["ts_min"], v["train_n"],
                 v["train_wr"] * 100, v["train_ev_r"], "VIABLE" if v["viable"] else "dead")


if __name__ == "__main__":
    main()
