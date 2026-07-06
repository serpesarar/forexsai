"""Meta-model trainer — per-family LightGBM P(win) with purged walk-forward,
isotonic calibration and EV-gated decisions.

Protocol (DESIGN.md §7–8):
  * chronological day split: first 60% = TRAIN (all model work), last 40% = HOLDOUT
    (touched exactly once, at the end, by the frozen pipeline)
  * inside TRAIN: expanding-window walk-forward over WF_FOLDS chronological day
    folds with WF_EMBARGO_DAYS purge; fold predictions pooled = honest train-OOS
  * isotonic calibration fitted on pooled train-OOS predictions
  * decision: trade iff EV(p_cal) ≥ EV_MARGIN_R, with EV from the family's
    empirical win/loss R (train-OOS estimates, slippage included in r_net)
  * families with < MIN_TRAIN_EVENTS_PER_FAMILY resolved train events are
    base-rate-only (no ML) — reported but never fitted
  * Tier A-only and Tier A+B variants trained; A is the deployment floor

Usage: python3 models/train.py [--tier A|AB]
Writes: data/models/<family>_<tier>.txt (lgbm), _cal.pkl, summary JSON + stdout report.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import pickle
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from features.pack import META_COLS, TIER_A_COLS, TIER_B_COLS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("train")

FAMILIES_ML = ["chan_rev", "vwap_rev", "sr_react", "sweep"]
FAMILIES_BASE = ["orb", "mom_cont"]


def load_dataset() -> tuple[pd.DataFrame, pd.Timestamp]:
    ds = pd.read_parquet(os.path.join(config.EVENTS_DIR, "dataset.parquet"))
    ds = ds[ds["outcome"].isin(["win", "loss"])].copy()
    ds["y"] = (ds["outcome"] == "win").astype(int)
    ds["r_net"] = ds["r_multiple"] - config.SLIPPAGE_PTS / ds["sl_dist"]
    ds["day"] = ds["ts"].dt.date
    days = sorted(ds["day"].unique())
    split_day = days[int(len(days) * 0.6)]
    return ds, split_day


def feature_cols(tier: str) -> list[str]:
    cols = TIER_A_COLS + META_COLS + ["is_buy"]
    if tier == "AB":
        cols += TIER_B_COLS
    return cols


def walk_forward_oos(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """Expanding-window purged walk-forward; returns OOS raw probabilities
    for every event in folds 2..K (fold 1 is bootstrap-train only)."""
    days = np.array(sorted(df["day"].unique()))
    folds = np.array_split(days, config.WF_FOLDS)
    oos = pd.Series(np.nan, index=df.index)
    for k in range(1, len(folds)):
        test_days = set(folds[k])
        train_max = pd.Timestamp(folds[k][0]) - pd.Timedelta(days=config.WF_EMBARGO_DAYS)
        tr = df[df["day"] < train_max.date()]
        te = df[df["day"].isin(test_days)]
        if len(tr) < 100 or te.empty:
            continue
        m = lgb.train(config.LGBM_PARAMS, lgb.Dataset(tr[cols], tr["y"]),
                      num_boost_round=300,
                      valid_sets=[lgb.Dataset(te[cols], te["y"])],
                      callbacks=[lgb.early_stopping(30, verbose=False)])
        oos.loc[te.index] = m.predict(te[cols], num_iteration=m.best_iteration)
    return oos


def ev_of(p: np.ndarray, win_r: float, loss_r: float) -> np.ndarray:
    return p * win_r + (1 - p) * loss_r  # loss_r is negative (includes slippage)


def evaluate_family(fam: str, ds: pd.DataFrame, split_day, tier: str, outdir: str) -> dict:
    df = ds[ds["family"] == fam].reset_index(drop=True)
    train, hold = df[df["day"] <= split_day], df[df["day"] > split_day]
    res: dict = {"family": fam, "tier": tier,
                 "train_n": len(train), "hold_n": len(hold),
                 "train_base_wr": round(float(train["y"].mean()), 4),
                 "train_base_ev": round(float(train["r_net"].mean()), 4),
                 "hold_base_wr": round(float(hold["y"].mean()), 4) if len(hold) else None,
                 "hold_base_ev": round(float(hold["r_net"].mean()), 4) if len(hold) else None}

    if len(train) < config.MIN_TRAIN_EVENTS_PER_FAMILY:
        res["mode"] = "base_rate_only"
        return res

    cols = feature_cols(tier)
    train = train.copy()
    oos_p = walk_forward_oos(train, cols)
    ok = oos_p.notna()
    if ok.sum() < 200:
        res["mode"] = "insufficient_oos"
        return res

    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(oos_p[ok], train.loc[ok, "y"])
    p_cal = pd.Series(iso.predict(oos_p[ok]), index=train.index[ok])

    # empirical win/loss R from train-OOS events only (slippage inside r_net)
    win_r = float(train.loc[ok][train.loc[ok, "y"] == 1]["r_net"].mean())
    loss_r = float(train.loc[ok][train.loc[ok, "y"] == 0]["r_net"].mean())
    ev = ev_of(p_cal.to_numpy(), win_r, loss_r)
    gate = ev >= config.EV_MARGIN_R
    res["train_oos_gated_n"] = int(gate.sum())
    res["train_oos_gated_wr"] = round(float(train.loc[ok].loc[gate, "y"].mean()), 4) if gate.any() else None
    res["train_oos_gated_ev"] = round(float(train.loc[ok].loc[gate, "r_net"].mean()), 4) if gate.any() else None
    res["train_oos_base_ev"] = round(float(train.loc[ok, "r_net"].mean()), 4)
    res["win_r"], res["loss_r"] = round(win_r, 4), round(loss_r, 4)

    # final model on full train, then ONE holdout pass
    m = lgb.train(config.LGBM_PARAMS, lgb.Dataset(train[cols], train["y"]), num_boost_round=200)
    if len(hold):
        p_hold = iso.predict(m.predict(hold[cols]))
        ev_h = ev_of(p_hold, win_r, loss_r)
        g = ev_h >= config.EV_MARGIN_R
        res["hold_gated_n"] = int(g.sum())
        res["hold_gated_wr"] = round(float(hold.loc[g, "y"].mean()), 4) if g.any() else None
        res["hold_gated_ev"] = round(float(hold.loc[g, "r_net"].mean()), 4) if g.any() else None

    m.save_model(os.path.join(outdir, f"{fam}_{tier}.txt"))
    with open(os.path.join(outdir, f"{fam}_{tier}_cal.pkl"), "wb") as f:
        pickle.dump({"iso": iso, "win_r": win_r, "loss_r": loss_r, "cols": cols}, f)
    res["mode"] = "ml"
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="A", choices=["A", "AB"])
    args = ap.parse_args()

    ds, split_day = load_dataset()
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    log.info("dataset: %d resolved events, split day %s, tier %s", len(ds), split_day, args.tier)

    results = []
    for fam in FAMILIES_ML + FAMILIES_BASE:
        r = evaluate_family(fam, ds, split_day, args.tier, config.MODELS_DIR)
        results.append(r)
        log.info(json.dumps(r, default=str))

    with open(os.path.join(config.MODELS_DIR, f"summary_{args.tier}.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)

    log.info("\n=== SUMMARY (tier %s) ===", args.tier)
    log.info("%-10s %-14s %6s %6s | %-22s | %-22s", "family", "mode", "trainN", "holdN",
             "train-OOS gated (n/wr/ev)", "HOLDOUT gated (n/wr/ev)")
    for r in results:
        t = f"{r.get('train_oos_gated_n','-')}/{r.get('train_oos_gated_wr','-')}/{r.get('train_oos_gated_ev','-')}"
        h = f"{r.get('hold_gated_n','-')}/{r.get('hold_gated_wr','-')}/{r.get('hold_gated_ev','-')}"
        log.info("%-10s %-14s %6d %6d | %-22s | %-22s",
                 r["family"], r.get("mode", "?"), r["train_n"], r["hold_n"], t, h)


if __name__ == "__main__":
    main()
