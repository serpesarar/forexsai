"""THE PROOF — frozen high-precision stream evaluated on 10 disjoint date groups.

Groups (never used for any selection):
  G1–G5 : 2025 HOLDOUT (days after the 60% split) in 5 contiguous chunks,
          Dukascopy proxy feed, real bid/ask replay + slippage
  G6–G10: 2026 real USTEC broker candles, monthly (Feb..Jun),
          synthetic 2.0-pt spread + slippage (transfer conditions)

For every group: pooled events from all frozen families, gated at each family's
frozen tau, labeled at its frozen geometry. PASS = WR ≥ 0.70 in ALL 10 groups.
EV is reported alongside — a WR pass with negative EV will be flagged, not hidden.

Usage: python3 research/prove_70.py
"""
from __future__ import annotations

import json
import logging
import os
import pickle
import sys
from datetime import date

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from features.pack import compute_feature_frame, event_features  # noqa: E402
from labels.triple_barrier import Geometry, label_events_fast  # noqa: E402
from triggers.detect import detect_day  # noqa: E402
from research.transfer_test_2026 import fetch_candles, to_bar_frame  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("prove_70")


def load_frozen() -> dict:
    with open(os.path.join(config.MODELS_DIR, "hp_frozen.json")) as f:
        return json.load(f)


def score_and_label(fam: str, cfg: dict, feats: pd.DataFrame,
                    bars_by_day: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Gate family events at frozen tau and label at frozen geometry."""
    id_cols = ["ts", "direction", "family"]
    if cfg["tau"] is None:  # base-rate family: every event trades, no model gate
        gated = (feats.loc[feats["family"] == fam, id_cols]
                 .drop_duplicates(subset=id_cols).reset_index(drop=True))
    else:
        m = lgb.Booster(model_file=os.path.join(config.MODELS_DIR, f"hp_{fam}.txt"))
        with open(os.path.join(config.MODELS_DIR, f"hp_{fam}_cal.pkl"), "rb") as f:
            cal = pickle.load(f)
        keep = id_cols + [c for c in cal["cols"] if c not in id_cols]
        sub = (feats.loc[feats["family"] == fam, keep]
               .drop_duplicates(subset=id_cols)
               .reset_index(drop=True))
        if sub.empty:
            return pd.DataFrame()
        sub["p"] = cal["iso"].predict(m.predict(sub[cal["cols"]]))
        gated = sub[sub["p"] >= cfg["tau"]].reset_index(drop=True)
    if gated.empty:
        return pd.DataFrame()
    geo = Geometry(cfg["tp_atr"], cfg["sl_atr"], cfg["ts_min"])
    labs = []
    for d, grp in gated.groupby(gated["ts"].dt.date.astype(str)):
        if d not in bars_by_day:
            continue
        labs.append(label_events_fast(bars_by_day[d], grp.reset_index(drop=True), geo))
    if not labs:
        return pd.DataFrame()
    lab = pd.concat(labs, ignore_index=True)
    lab = lab[lab["outcome"].isin(["win", "loss"])].copy()
    lab["y"] = (lab["outcome"] == "win").astype(int)
    lab["r_net"] = lab["r_multiple"] - config.SLIPPAGE_PTS / lab["sl_dist"]
    return lab


def eval_2025_groups(frozen: dict) -> list[dict]:
    ds = pd.read_parquet(os.path.join(config.EVENTS_DIR, "dataset.parquet"))
    split_day = date.fromisoformat(frozen["split_day"])
    hold = ds[ds["ts"].dt.date > split_day]
    days = sorted(hold["ts"].dt.date.astype(str).unique())
    bars_by_day = {d: pd.read_parquet(os.path.join(config.BARS_DIR, f"{d}.parquet"))
                   for d in days if os.path.exists(os.path.join(config.BARS_DIR, f"{d}.parquet"))}
    chunks = np.array_split(np.array(days), 5)
    groups = []
    for gi, chunk in enumerate(chunks, start=1):
        feats = hold[hold["ts"].dt.date.astype(str).isin(set(chunk))]
        labs = [score_and_label(f, c, feats, bars_by_day) for f, c in frozen["families"].items()]
        lab = pd.concat([l for l in labs if not l.empty], ignore_index=True) if any(
            not l.empty for l in labs) else pd.DataFrame()
        groups.append(_group_row(f"G{gi} 2025 {chunk[0]}..{chunk[-1]}", lab))
    return groups


def eval_2026_groups(frozen: dict) -> list[dict]:
    candles = fetch_candles()
    bars = to_bar_frame(candles)
    days = sorted(bars["ts"].dt.date.unique())
    # detect + features day by day with prev-day context
    ev_frames, feat_frames = [], []
    bars_by_day: dict[str, pd.DataFrame] = {}
    for i, d in enumerate(days):
        day_bars = bars[bars["ts"].dt.date == d].reset_index(drop=True)
        bars_by_day[str(d)] = day_bars
        ctx = bars[bars["ts"].dt.date.isin(days[max(0, i - 1):i + 1])].reset_index(drop=True)
        ev = detect_day(day_bars, None if i == 0 else bars[bars["ts"].dt.date == days[i - 1]].reset_index(drop=True), d)
        if ev.empty:
            continue
        feat = compute_feature_frame(ctx)
        fe = event_features(feat, ev)
        if not fe.empty:
            feat_frames.append(fe)
    feats = pd.concat(feat_frames, ignore_index=True)
    log.info("2026: %d gated-candidate events across %d days", len(feats), len(days))

    groups = []
    for gi, month in enumerate([2, 3, 4, 5, 6], start=6):
        mf = feats[(feats["ts"].dt.year == 2026) & (feats["ts"].dt.month == month)]
        labs = [score_and_label(f, c, mf, bars_by_day) for f, c in frozen["families"].items()]
        lab = pd.concat([l for l in labs if not l.empty], ignore_index=True) if any(
            not l.empty for l in labs) else pd.DataFrame()
        groups.append(_group_row(f"G{gi} 2026-{month:02d} (broker)", lab))
    return groups


def _group_row(name: str, lab: pd.DataFrame) -> dict:
    if lab.empty:
        return {"group": name, "n": 0, "wr": None, "ev": None, "pass": False}
    return {"group": name, "n": len(lab), "wr": round(float(lab["y"].mean()), 4),
            "ev": round(float(lab["r_net"].mean()), 4),
            "pass": bool(lab["y"].mean() >= 0.70)}


def main() -> None:
    frozen = load_frozen()
    log.info("frozen families: %s", json.dumps(frozen["families"], indent=2))
    groups = eval_2025_groups(frozen) + eval_2026_groups(frozen)
    log.info("\n=== 10-GROUP PROOF (target: WR ≥ 70%% in every group) ===")
    all_pass = True
    for g in groups:
        flag = "PASS" if g["pass"] else "FAIL"
        all_pass &= g["pass"]
        log.info("%-28s n=%4s  WR=%s  EV=%s  %s", g["group"], g["n"],
                 f"{g['wr']*100:.1f}%" if g["wr"] is not None else "-",
                 f"{g['ev']:+.3f}R" if g["ev"] is not None else "-", flag)
    pooled_n = sum(g["n"] for g in groups)
    log.info("VERDICT: %s (pooled n=%d)", "ALL 10 GROUPS PASS" if all_pass else "NOT PROVEN", pooled_n)
    with open(os.path.join(config.MODELS_DIR, "prove70_report.json"), "w") as f:
        json.dump({"groups": groups, "all_pass": all_pass}, f, indent=2)


if __name__ == "__main__":
    main()
