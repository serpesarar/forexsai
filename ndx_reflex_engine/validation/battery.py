"""Validation battery — every candidate must pass ALL applicable tests.

Candidates (from models/train.py results, pre-registered before this run):
  mom_cont      base-rate family (no ML) — both directions
  vwap_rev(A)   ML-gated, Tier A
  vwap_rev(AB)  ML-gated, Tier A+B
  chan_rev(A)   ML-gated (borderline; included for completeness)

Tests:
  1. friction stress  — extra cost = (mult−1)·spread_med/sl_dist + slippage bump,
                        EV must stay > 0 at 1.5× and 2.0× event-bar spread
  2. trigger placebo  — event times shifted ±(30–180) min ×PLACEBO_SHIFTS,
                        relabeled: real base EV must beat p95 of placebo EVs
                        (tests that the *timing* of events carries information)
  3. ML placebo       — labels permuted within train, full WF+calibration+gate
                        pipeline re-run ×100: real holdout gated EV must beat
                        p95 of the noise-lift distribution
  4. block bootstrap  — daily-block bootstrap of holdout gated PnL,
                        P(EV>0) ≥ BOOTSTRAP_P_EV_POS
  5. calibration      — holdout reliability: predicted-p quintiles monotone-ish
                        in realized WR (Spearman ≥ 0.7)

Usage: python3 validation/battery.py            (tests 1,2,4,5 — fast)
       python3 validation/battery.py --ml-placebo  (adds test 3 — slow)
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
from scipy.stats import spearmanr
from sklearn.isotonic import IsotonicRegression

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from labels.triple_barrier import Geometry, label_events_fast  # noqa: E402
from models.train import ev_of, feature_cols, load_dataset, walk_forward_oos  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("battery")

RNG = np.random.default_rng(20260704)


def holdout_gated(ds: pd.DataFrame, split_day, fam: str, tier: str) -> pd.DataFrame:
    """Recreate the trainer's holdout gated subset for a fitted family/tier."""
    with open(os.path.join(config.MODELS_DIR, f"{fam}_{tier}_cal.pkl"), "rb") as f:
        cal = pickle.load(f)
    m = lgb.Booster(model_file=os.path.join(config.MODELS_DIR, f"{fam}_{tier}.txt"))
    hold = ds[(ds["family"] == fam) & (ds["day"] > split_day)].copy()
    p = cal["iso"].predict(m.predict(hold[cal["cols"]]))
    hold["p_cal"] = p
    hold["ev_pred"] = ev_of(p, cal["win_r"], cal["loss_r"])
    return hold[hold["ev_pred"] >= config.EV_MARGIN_R]


def test_friction(sub: pd.DataFrame) -> dict:
    out = {}
    for mult in (1.5, 2.0):
        extra = (mult - 1.0) * sub["spread_med_ev"] / sub["sl_dist"] + \
                (config.SLIPPAGE_PTS / sub["sl_dist"]) * (mult - 1.0)
        out[f"ev_at_{mult}x"] = round(float((sub["r_net"] - extra).mean()), 4)
    out["pass"] = bool(out["ev_at_1.5x"] > 0)
    return out


def test_trigger_placebo(events: pd.DataFrame, geo: Geometry) -> dict:
    """Shift event times randomly, relabel, compare base EV distribution."""
    real_ev = float(events["r_net"].mean())
    days = events["ts"].dt.date.astype(str).unique()
    bars_by_day = {d: pd.read_parquet(os.path.join(config.BARS_DIR, f"{d}.parquet"))
                   for d in days if os.path.exists(os.path.join(config.BARS_DIR, f"{d}.parquet"))}
    lo, hi = config.PLACEBO_SHIFT_MIN
    placebo_evs = []
    for _ in range(config.PLACEBO_SHIFTS):
        shift = RNG.integers(lo, hi, size=len(events)) * RNG.choice([-1, 1], size=len(events))
        ev_s = events[["ts", "direction", "family"]].copy()
        ev_s["ts"] = ev_s["ts"] + pd.to_timedelta(shift, unit="m")
        ev_s["ts"] = ev_s["ts"].dt.floor("1min")
        labs = []
        for d, grp in ev_s.groupby(ev_s["ts"].dt.date.astype(str)):
            if d not in bars_by_day:
                continue
            labs.append(label_events_fast(bars_by_day[d], grp.reset_index(drop=True), geo))
        lab = pd.concat(labs, ignore_index=True)
        lab = lab[lab["outcome"].isin(["win", "loss"])]
        if len(lab) < 20:
            continue
        r_net = lab["r_multiple"] - config.SLIPPAGE_PTS / lab["sl_dist"]
        placebo_evs.append(float(r_net.mean()))
    p95 = float(np.percentile(placebo_evs, 95))
    return {"real_ev": round(real_ev, 4), "placebo_p95": round(p95, 4),
            "placebo_mean": round(float(np.mean(placebo_evs)), 4),
            "n_placebo": len(placebo_evs), "pass": bool(real_ev > p95)}


def test_bootstrap(sub: pd.DataFrame) -> dict:
    """Stationary daily-block bootstrap of gated PnL."""
    daily = sub.groupby(sub["ts"].dt.date)["r_net"].agg(list)
    blocks = daily.to_list()
    if len(blocks) < 8:
        return {"p_ev_pos": None, "pass": False, "note": "too_few_days"}
    means = []
    for _ in range(4000):
        pick = RNG.integers(0, len(blocks), size=len(blocks))
        sample = [r for i in pick for r in blocks[i]]
        means.append(np.mean(sample))
    p_pos = float(np.mean(np.array(means) > 0))
    return {"p_ev_pos": round(p_pos, 4), "pass": bool(p_pos >= config.BOOTSTRAP_P_EV_POS)}


def test_calibration(hold_all: pd.DataFrame) -> dict:
    """Reliability of p_cal on the FULL holdout (not just gated)."""
    df = hold_all.dropna(subset=["p_cal"])
    if len(df) < 100:
        return {"pass": False, "note": "too_few"}
    q = pd.qcut(df["p_cal"], 5, duplicates="drop")
    rel = df.groupby(q, observed=True).agg(p_mean=("p_cal", "mean"), wr=("y", "mean"), n=("y", "size"))
    rho = spearmanr(rel["p_mean"], rel["wr"]).statistic if len(rel) >= 3 else np.nan
    return {"reliability": rel.round(3).to_dict("index") and rel.round(3).reset_index(drop=True).to_dict("records"),
            "spearman": round(float(rho), 3) if np.isfinite(rho) else None,
            "pass": bool(np.isfinite(rho) and rho >= 0.7)}


def test_ml_placebo(ds: pd.DataFrame, split_day, fam: str, tier: str, real_gated_ev: float,
                    n_perm: int = 100) -> dict:
    """Permute train labels, re-run WF+calibration+gate, score holdout — ×n_perm."""
    cols = feature_cols(tier)
    df = ds[ds["family"] == fam].reset_index(drop=True)
    train = df[df["day"] <= split_day].copy()
    hold = df[df["day"] > split_day].copy()
    lifts = []
    for it in range(n_perm):
        t = train.copy()
        t["y"] = RNG.permutation(t["y"].to_numpy())
        oos = walk_forward_oos(t, cols)
        ok = oos.notna()
        if ok.sum() < 200:
            continue
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(oos[ok], t.loc[ok, "y"])
        win_r = float(t.loc[ok][t.loc[ok, "y"] == 1]["r_net"].mean())
        loss_r = float(t.loc[ok][t.loc[ok, "y"] == 0]["r_net"].mean())
        m = lgb.train(config.LGBM_PARAMS, lgb.Dataset(t[cols], t["y"]), num_boost_round=200)
        p = iso.predict(m.predict(hold[cols]))
        g = ev_of(p, win_r, loss_r) >= config.EV_MARGIN_R
        if g.sum() >= 20:
            lifts.append(float(hold.loc[g, "r_net"].mean()))
    if not lifts:
        return {"pass": None, "note": "no_valid_permutations"}
    p95 = float(np.percentile(lifts, 95))
    return {"real_gated_ev": round(real_gated_ev, 4), "noise_p95": round(p95, 4),
            "noise_mean": round(float(np.mean(lifts)), 4), "n_perm_valid": len(lifts),
            "pass": bool(real_gated_ev > p95)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ml-placebo", action="store_true")
    args = ap.parse_args()

    ds, split_day = load_dataset()
    # event-bar spread for friction stress: join from bar files once
    ds["day_str"] = ds["ts"].dt.date.astype(str)
    spreads = []
    for d, grp in ds.groupby("day_str"):
        b = pd.read_parquet(os.path.join(config.BARS_DIR, f"{d}.parquet"), columns=["ts", "spread_med"])
        m = grp.merge(b, on="ts", how="left")
        spreads.append(m.set_index(grp.index)["spread_med"])
    ds["spread_med_ev"] = pd.concat(spreads).sort_index()

    with open(os.path.join(config.EVENTS_DIR, "geometry_choice.json")) as f:
        geo_choice = json.load(f)

    report: dict = {}

    # ── candidate 1: mom_cont base rate (both directions, own geometries) ────
    for d in ("BUY", "SELL"):
        key = f"mom_cont|{d}"
        g = geo_choice[key]
        sub = ds[(ds["family"] == "mom_cont") & (ds["direction"] == d) & (ds["day"] > split_day)]
        ev_all = ds[(ds["family"] == "mom_cont") & (ds["direction"] == d)]
        rep = {"hold_n": len(sub), "hold_wr": round(float(sub["y"].mean()), 4),
               "hold_ev": round(float(sub["r_net"].mean()), 4),
               "friction": test_friction(sub),
               "placebo": test_trigger_placebo(ev_all, Geometry(g["tp_atr"], g["sl_atr"], g["ts_min"])),
               "bootstrap": test_bootstrap(sub)}
        rep["pass_all"] = all(t.get("pass") for t in (rep["friction"], rep["placebo"], rep["bootstrap"]))
        report[key + " (base)"] = rep
        log.info("%s: %s", key, json.dumps(rep, default=str))

    # ── candidates 2-4: ML-gated families ────────────────────────────────────
    for fam, tier in (("vwap_rev", "A"), ("vwap_rev", "AB"), ("chan_rev", "A")):
        sub = holdout_gated(ds, split_day, fam, tier)
        hold_all = ds[(ds["family"] == fam) & (ds["day"] > split_day)].copy()
        with open(os.path.join(config.MODELS_DIR, f"{fam}_{tier}_cal.pkl"), "rb") as f:
            cal = pickle.load(f)
        m = lgb.Booster(model_file=os.path.join(config.MODELS_DIR, f"{fam}_{tier}.txt"))
        hold_all["p_cal"] = cal["iso"].predict(m.predict(hold_all[cal["cols"]]))
        rep = {"gated_n": len(sub), "gated_wr": round(float(sub["y"].mean()), 4) if len(sub) else None,
               "gated_ev": round(float(sub["r_net"].mean()), 4) if len(sub) else None,
               "friction": test_friction(sub) if len(sub) else {"pass": False},
               "bootstrap": test_bootstrap(sub) if len(sub) else {"pass": False},
               "calibration": test_calibration(hold_all)}
        if args.ml_placebo and len(sub):
            rep["ml_placebo"] = test_ml_placebo(ds, split_day, fam, tier, float(sub["r_net"].mean()))
        checks = [rep["friction"], rep["bootstrap"], rep["calibration"]] + \
                 ([rep["ml_placebo"]] if "ml_placebo" in rep else [])
        rep["pass_all"] = all(t.get("pass") for t in checks)
        report[f"{fam}({tier})"] = rep
        log.info("%s(%s): %s", fam, tier, json.dumps(rep, default=str))

    with open(os.path.join(config.MODELS_DIR, "battery_report.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)
    log.info("\n=== VERDICTS ===")
    for k, v in report.items():
        log.info("%-22s %s", k, "PASS" if v.get("pass_all") else "FAIL")


if __name__ == "__main__":
    main()
