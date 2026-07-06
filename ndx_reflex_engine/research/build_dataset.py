"""Build the training dataset: event features + frozen-geometry labels.

Per day: feature frame over (prev day + day) context, features extracted at
event confirm bars, labels from the per-family geometry frozen by
geometry_study.py (train split only — holdout never influenced geometry).

Output: data/events/dataset.parquet
"""
from __future__ import annotations

import glob
import json
import logging
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from features.pack import compute_feature_frame, event_features  # noqa: E402
from labels.triple_barrier import Geometry, label_events_fast  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("build_dataset")


def main() -> None:
    events = pd.read_parquet(os.path.join(config.EVENTS_DIR, "events_raw.parquet"))
    with open(os.path.join(config.EVENTS_DIR, "geometry_choice.json")) as f:
        geo_choice = json.load(f)

    bar_paths = sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet")))
    day_of = {os.path.basename(p).replace(".parquet", ""): p for p in bar_paths}
    days = sorted(events["ts"].dt.date.astype(str).unique())

    out = []
    prev_day: str | None = None
    for day in days:
        if day not in day_of:
            prev_day = day if day in day_of else prev_day
            continue
        bars_day = pd.read_parquet(day_of[day])
        ctx = bars_day
        if prev_day and prev_day in day_of:
            ctx = pd.concat([pd.read_parquet(day_of[prev_day]), bars_day], ignore_index=True)
        feat = compute_feature_frame(ctx)

        ev_day = events[events["ts"].dt.date.astype(str) == day].reset_index(drop=True)
        fe = event_features(feat, ev_day)
        if fe.empty:
            prev_day = day
            continue

        # label per family at its frozen geometry
        labeled = []
        for key, g in geo_choice.items():
            fam, d = key.split("|")
            sub = fe[(fe["family"] == fam) & (fe["direction"] == d)]
            if sub.empty:
                continue
            geo = Geometry(g["tp_atr"], g["sl_atr"], g["ts_min"])
            labeled.append(label_events_fast(bars_day, sub.reset_index(drop=True), geo))
        if labeled:
            out.append(pd.concat(labeled, ignore_index=True))
        prev_day = day

    ds = pd.concat(out, ignore_index=True).sort_values("ts").reset_index(drop=True)
    dst = os.path.join(config.EVENTS_DIR, "dataset.parquet")
    ds.to_parquet(dst, index=False)
    resolved = ds[ds["outcome"].isin(["win", "loss"])]
    log.info("dataset: %d events, %d resolved (%.0f%%) → %s",
             len(ds), len(resolved), 100 * len(resolved) / max(len(ds), 1), dst)
    log.info("\n%s", resolved.groupby(["family", "direction"])["outcome"]
             .agg(n="size", wr=lambda s: (s == "win").mean()).round(3).to_string())


if __name__ == "__main__":
    main()
