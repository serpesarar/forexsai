"""V6 — pure DIRECTIONAL prediction: will price be above or below the decision
level after 5 minutes and after 60 minutes? Maximize honest OOS accuracy.

This drops TP/SL entirely. At each decision point (event bar close) we predict
P(up) over horizon H, and measure directional accuracy out-of-sample vs the base
rate. The whole point: how far above coin-flip can we honestly get, and on how
many calls, when we only act on the most-confident predictions.

Decision points  : all detected trigger events (2025 dataset + fresh 2026), 13-20 UTC.
Label            : y = 1 if mid[t+H] > mid[t] (H ∈ {5, 60} min); dropped if the future
                   bar is missing / crosses a data gap / passes session flat time.
Model            : LightGBM P(up), Tier-A causal features, calibrated (isotonic).
Selection        : train split only; evaluate on 2025 holdout + 2026 broker candles.
Report           : base rate, overall accuracy, and accuracy on the top-confidence
                   quantiles (this is the tradeable directional edge).
"""
from __future__ import annotations

import glob
import json
import logging
import os
import sys
from datetime import date

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from features.pack import TIER_A_COLS, compute_feature_frame, event_features  # noqa: E402
from research.transfer_test_2026 import fetch_candles, to_bar_frame  # noqa: E402
from triggers.detect import detect_day  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("v6_dir")

HORIZONS = (5, 60)
COLS = TIER_A_COLS + ["is_buy"]  # is_buy = the event's own directional hint
GAP_MIN = config.GAP_MAX_SILENT_MIN


def add_dir_labels(events: pd.DataFrame, bars_by_day: dict) -> pd.DataFrame:
    """Attach y5/y60 = 1 if mid is higher H minutes later (same day, no gap crossing)."""
    ev = events.copy()
    for H in HORIZONS:
        ev[f"y{H}"] = np.nan
    for day, grp in ev.groupby(ev["ts"].dt.date.astype(str)):
        bars = bars_by_day.get(day)
        if bars is None:
            continue
        b = bars.sort_values("ts").reset_index(drop=True)
        tmap = pd.Series(b["mid_c"].to_numpy(), index=b["ts"].to_numpy().astype("datetime64[ns]"))
        ts_ns = b["ts"].to_numpy().astype("datetime64[ns]").astype("int64")
        for idx in grp.index:
            t = pd.Timestamp(ev.at[idx, "ts"]).to_datetime64().astype("datetime64[ns]")
            t_ns = t.astype("int64")
            cur = tmap.get(t)
            if cur is None:
                continue
            for H in HORIZONS:
                tgt = t + np.timedelta64(H, "m")
                fut = tmap.get(tgt)
                if fut is None:
                    # nearest bar within 1 min after target, else drop (gap/end)
                    pos = np.searchsorted(ts_ns, tgt.astype("int64"))
                    if pos >= len(ts_ns):
                        continue
                    if (ts_ns[pos] - tgt.astype("int64")) > 60_000_000_000:
                        continue
                    # ensure no gap between t and that bar
                    seg = np.diff(ts_ns[np.searchsorted(ts_ns, t_ns):pos + 1])
                    if len(seg) and seg.max() > GAP_MIN * 60_000_000_000:
                        continue
                    fut = b["mid_c"].to_numpy()[pos]
                ev.at[idx, f"y{H}"] = 1.0 if fut > cur else 0.0
    return ev


def build_features(bars_by_day: dict) -> pd.DataFrame:
    """Detect events + compute (now-causal) features for every day. Used for BOTH years
    so the leak-fixed feature pack is applied consistently (not the cached dataset)."""
    days = sorted(bars_by_day.keys())
    frames = []
    for i, d in enumerate(days):
        prev = None if i == 0 else bars_by_day[days[i - 1]]
        try:
            dd = date.fromisoformat(d)
        except ValueError:
            continue
        ev = detect_day(bars_by_day[d], prev, dd)
        if ev.empty:
            continue
        ctx = pd.concat([prev, bars_by_day[d]]).reset_index(drop=True) if prev is not None else bars_by_day[d]
        fe = event_features(compute_feature_frame(ctx), ev)
        if not fe.empty:
            frames.append(fe)
    return pd.concat(frames, ignore_index=True)


def acc_at_quantiles(p: np.ndarray, y: np.ndarray) -> dict:
    """Directional accuracy on the most-confident calls. Confidence = |p-0.5|.
    Prediction = up if p>=0.5 else down. Report over top {100,50,30,15,5}%."""
    conf = np.abs(p - 0.5)
    order = np.argsort(-conf)
    pred = (p >= 0.5).astype(int)
    correct = (pred == y).astype(int)
    out = {}
    for q in (1.0, 0.5, 0.3, 0.15, 0.05):
        k = max(20, int(len(p) * q))
        sel = order[:k]
        out[f"top{int(q*100)}pct"] = {"n": int(k), "acc": round(float(correct[sel].mean()), 4)}
    return out


def main() -> None:
    raw = {os.path.basename(p).replace(".parquet", ""): pd.read_parquet(p)
           for p in sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet")))}
    grp = {str(x): g.reset_index(drop=True)
           for x, g in to_bar_frame(fetch_candles()).groupby(to_bar_frame(fetch_candles())["ts"].dt.date)}

    e25 = build_features(raw)          # fresh, leak-fixed features (not cached dataset)
    e25 = add_dir_labels(e25, raw)
    e26 = build_features(grp)
    e26 = add_dir_labels(e26, grp)

    split = date.fromisoformat("2025-04-11")
    e25["split"] = np.where(e25["ts"].dt.date <= split, "train", "hold")

    report = {}
    for H in HORIZONS:
        yc = f"y{H}"
        tr = e25[(e25["split"] == "train") & e25[yc].notna()]
        ho = e25[(e25["split"] == "hold") & e25[yc].notna()]
        h26 = e26[e26[yc].notna()]
        log.info("\n══ HORIZON %d min ══  (train n=%d, holdout n=%d, 2026 n=%d)",
                 H, len(tr), len(ho), len(h26))
        log.info("  base rate P(up): train %.1f%% | holdout %.1f%% | 2026 %.1f%%",
                 tr[yc].mean() * 100, ho[yc].mean() * 100, h26[yc].mean() * 100)
        # always-majority baseline accuracy (predict the train-majority class)
        maj = int(tr[yc].mean() >= 0.5)
        log.info("  always-'%s' baseline acc: holdout %.1f%% | 2026 %.1f%%",
                 "up" if maj else "down",
                 (ho[yc] == maj).mean() * 100, (h26[yc] == maj).mean() * 100)

        m = lgb.train({**config.LGBM_PARAMS, "objective": "binary"},
                      lgb.Dataset(tr[COLS], tr[yc]), num_boost_round=250)
        iso = IsotonicRegression(out_of_bounds="clip")
        # calibrate on a tail of train via simple split (last 20% of train days)
        tdays = sorted(tr["ts"].dt.date.unique())
        cal_cut = tdays[int(len(tdays) * 0.8)]
        cal = tr[tr["ts"].dt.date > cal_cut]
        iso.fit(m.predict(cal[COLS]), cal[yc])

        for label, sub in (("holdout", ho), ("2026", h26)):
            p = iso.predict(m.predict(sub[COLS]))
            y = sub[yc].to_numpy()
            overall = float(((p >= 0.5).astype(int) == y).mean())
            q = acc_at_quantiles(p, y)
            log.info("  ML dir acc %-8s overall %.1f%% | top50%% %.1f%%(n%d) | top30%% %.1f%%(n%d) | "
                     "top15%% %.1f%%(n%d) | top5%% %.1f%%(n%d)",
                     label, overall * 100,
                     q["top50pct"]["acc"] * 100, q["top50pct"]["n"],
                     q["top30pct"]["acc"] * 100, q["top30pct"]["n"],
                     q["top15pct"]["acc"] * 100, q["top15pct"]["n"],
                     q["top5pct"]["acc"] * 100, q["top5pct"]["n"])
            report[f"H{H}_{label}"] = {"overall_acc": round(overall, 4), "quantiles": q,
                                       "base_rate_up": round(float(sub[yc].mean()), 4)}

    with open(os.path.join(config.MODELS_DIR, "v6_direction.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)
    log.info("\nsaved → v6_direction.json")


if __name__ == "__main__":
    main()
