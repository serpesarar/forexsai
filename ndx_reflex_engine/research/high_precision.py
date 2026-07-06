"""High-precision mode — select (family, geometry, tau) on TRAIN ONLY to target
a ≥70% win-rate signal stream, then freeze for the 10-group proof.

Phase S (this script):
  * candidate families: chan_rev, vwap_rev, sr_react, sweep, mom_cont
  * WR-oriented geometry grid: tp ∈ {0.5, 0.75} × sl ∈ {1.25, 1.5} × ts ∈ {30, 60}
  * for each (family, geometry): relabel TRAIN events, purged walk-forward
    (models/train.py machinery, Tier A features only — must transfer to broker
    candles), isotonic calibration, then sweep tau on pooled train-OOS
    predictions for the smallest tau with WR ≥ TARGET_WR and n ≥ MIN_N
  * freeze the per-family best (geometry, tau) → data/models/hp_frozen.json
    + final models trained on the full train split

Nothing outside the first-60%-of-days train split is read here.
"""
from __future__ import annotations

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
from features.pack import META_COLS, TIER_A_COLS  # noqa: E402
from labels.triple_barrier import Geometry, label_events_fast  # noqa: E402
from models.train import walk_forward_oos  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("hp_select")

TARGET_WR = 0.85          # selection target (buffer above the 70% goal; also the
                          # +EV breakeven for tp0.5/sl2.0 is 80% — aim above it)
MIN_N_OOS = 80            # minimum pooled train-OOS events at tau
GEO_GRID = [Geometry(tp, sl, ts) for tp in (0.4, 0.5, 0.75) for sl in (1.5, 2.0, 2.5) for ts in (30, 60)]
FAMILIES = ["chan_rev", "vwap_rev", "sr_react", "sweep", "mom_cont"]
COLS = TIER_A_COLS + META_COLS + ["is_buy"]


def load_features() -> tuple[pd.DataFrame, object]:
    ds = pd.read_parquet(os.path.join(config.EVENTS_DIR, "dataset.parquet"))
    feat_cols = ["ts", "direction", "family"] + COLS
    feats = ds[feat_cols].drop_duplicates(subset=["ts", "direction", "family"])
    days = sorted(ds["ts"].dt.date.unique())
    split_day = days[int(len(days) * 0.6)]
    return feats, split_day


def relabel(feats: pd.DataFrame, geo: Geometry) -> pd.DataFrame:
    out = []
    for day, grp in feats.groupby(feats["ts"].dt.date.astype(str)):
        bp = os.path.join(config.BARS_DIR, f"{day}.parquet")
        if not os.path.exists(bp):
            continue
        out.append(label_events_fast(pd.read_parquet(bp), grp.reset_index(drop=True), geo))
    lab = pd.concat(out, ignore_index=True)
    lab = lab[lab["outcome"].isin(["win", "loss"])].copy()
    lab["y"] = (lab["outcome"] == "win").astype(int)
    lab["r_net"] = lab["r_multiple"] - config.SLIPPAGE_PTS / lab["sl_dist"]
    lab["day"] = lab["ts"].dt.date
    return lab


def main() -> None:
    feats, split_day = load_features()
    train_feats = feats[feats["ts"].dt.date <= split_day]
    log.info("train events (pre-label): %d, split %s", len(train_feats), split_day)

    frozen: dict[str, dict] = {}
    for fam in FAMILIES:
        fam_feats = train_feats[train_feats["family"] == fam]
        if len(fam_feats) < config.MIN_TRAIN_EVENTS_PER_FAMILY:
            # too small for ML — allow a BASE-RATE stream if some geometry's raw
            # train WR clears the target (tau=None marks no model gate)
            best_base = None
            for geo in GEO_GRID:
                df = relabel(fam_feats, geo)
                if len(df) < MIN_N_OOS:
                    continue
                wr = float(df["y"].mean())
                if wr >= TARGET_WR and (best_base is None or len(df) > best_base["n"]):
                    best_base = {"geo": geo, "n": len(df), "wr": wr,
                                 "ev": float(df["r_net"].mean())}
            if best_base:
                geo = best_base["geo"]
                frozen[fam] = {"tp_atr": geo.tp_atr, "sl_atr": geo.sl_atr,
                               "ts_min": geo.time_stop_min, "tau": None,
                               "train_oos_n": best_base["n"],
                               "train_oos_wr": round(best_base["wr"], 4),
                               "train_oos_ev": round(best_base["ev"], 4)}
                log.info("%s FROZEN (base-rate): tp=%.2f sl=%.2f ts=%d → train n=%d WR=%.1f%% EV=%+.3fR",
                         fam, geo.tp_atr, geo.sl_atr, geo.time_stop_min,
                         best_base["n"], best_base["wr"] * 100, best_base["ev"])
            else:
                log.info("%s: %d train events < %d and no base-rate geometry ≥ %.0f%% — skipped",
                         fam, len(fam_feats), config.MIN_TRAIN_EVENTS_PER_FAMILY, TARGET_WR * 100)
            continue
        best = None
        for geo in GEO_GRID:
            df = relabel(fam_feats, geo).reset_index(drop=True)
            if len(df) < config.MIN_TRAIN_EVENTS_PER_FAMILY:
                continue
            oos = walk_forward_oos(df, COLS)
            ok = oos.notna()
            if ok.sum() < 200:
                continue
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(oos[ok], df.loc[ok, "y"])
            p = pd.Series(iso.predict(oos[ok]), index=df.index[ok])
            sub = df.loc[ok].assign(p=p)
            # smallest tau achieving TARGET_WR with n >= MIN_N_OOS
            for tau in np.arange(0.50, 0.96, 0.01):
                g = sub[sub["p"] >= tau]
                if len(g) < MIN_N_OOS:
                    break
                wr = g["y"].mean()
                if wr >= TARGET_WR:
                    cand = {"geo": geo, "tau": round(float(tau), 2), "oos_n": len(g),
                            "oos_wr": round(float(wr), 4),
                            "oos_ev": round(float(g["r_net"].mean()), 4),
                            "df": df, "iso": iso}
                    if best is None or len(g) > best["oos_n"]:
                        best = cand
                    break
        if best is None:
            log.info("%s: no (geometry, tau) reaches WR %.0f%% with n>=%d — excluded",
                     fam, TARGET_WR * 100, MIN_N_OOS)
            continue

        geo = best["geo"]
        df = best["df"]
        m = lgb.train(config.LGBM_PARAMS, lgb.Dataset(df[COLS], df["y"]), num_boost_round=200)
        m.save_model(os.path.join(config.MODELS_DIR, f"hp_{fam}.txt"))
        with open(os.path.join(config.MODELS_DIR, f"hp_{fam}_cal.pkl"), "wb") as f:
            pickle.dump({"iso": best["iso"], "cols": COLS}, f)
        frozen[fam] = {"tp_atr": geo.tp_atr, "sl_atr": geo.sl_atr, "ts_min": geo.time_stop_min,
                       "tau": best["tau"], "train_oos_n": best["oos_n"],
                       "train_oos_wr": best["oos_wr"], "train_oos_ev": best["oos_ev"]}
        log.info("%s FROZEN: tp=%.2f sl=%.2f ts=%d tau=%.2f → train-OOS n=%d WR=%.1f%% EV=%+.3fR",
                 fam, geo.tp_atr, geo.sl_atr, geo.time_stop_min, best["tau"],
                 best["oos_n"], best["oos_wr"] * 100, best["oos_ev"])

    with open(os.path.join(config.MODELS_DIR, "hp_frozen.json"), "w") as f:
        json.dump({"split_day": str(split_day), "target_wr": TARGET_WR,
                   "families": frozen}, f, indent=2)
    log.info("frozen config → hp_frozen.json (%d families)", len(frozen))


if __name__ == "__main__":
    main()
