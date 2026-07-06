"""V2 — symmetric micro-scalping search (TP≈0.10%, SL≈0.10%, flex to 0.13%).

Phase A: raw base WR landscape over (family × pct-geometry × time-stop), TRAIN split only.
Phase B: ML gate frontier — for each combo, purged-WF LightGBM + isotonic, then the
         maximum train-OOS WR achievable at n ≥ MIN_N (sweep tau). Reports the frontier
         so we can see honestly how close 75%+buffer is.
Phase C: anything reaching TARGET_WR train-OOS at n ≥ MIN_N gets frozen for the
         10-group proof (research/prove_70.py machinery with pct geometry).

All selection on the first-60%-of-days train split. Holdout + 2026 untouched here.
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
from labels.triple_barrier import Geometry  # noqa: E402
from models.train import walk_forward_oos  # noqa: E402
from research.high_precision import COLS, load_features, relabel  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("v2")

TARGET_WR = 0.80          # buffer above the 75% goal
MIN_N_OOS = 80
FAMILIES = ["chan_rev", "vwap_rev", "sr_react", "sweep", "mom_cont", "orb"]
GEOS = [Geometry(tp, sl, ts, mode="pct")
        for tp, sl in ((0.0010, 0.0010), (0.0010, 0.0013), (0.0013, 0.0013), (0.0013, 0.0010))
        for ts in (15, 30, 60)]


def geo_key(g: Geometry) -> str:
    return f"tp{g.tp_atr*100:.2f}%/sl{g.sl_atr*100:.2f}%/ts{g.time_stop_min}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-entry", action="store_true",
                    help="resting limit at event-bar mid (single-bar fill window)")
    ap.add_argument("--tier-b", action="store_true", help="add tick-microstructure features")
    args = ap.parse_args()

    global COLS, GEOS, FAMILIES
    if args.tier_b:
        from features.pack import TIER_B_COLS
        COLS = COLS + TIER_B_COLS
    if args.limit_entry:
        GEOS = [Geometry(g.tp_atr, g.sl_atr, g.time_stop_min, mode="pct",
                         entry_mode="limit_mid") for g in GEOS]
        FAMILIES = ["chan_rev", "vwap_rev", "sr_react"]  # reversion families suit limits
    log.info("options: limit_entry=%s tier_b=%s (%d feature cols)",
             args.limit_entry, args.tier_b, len(COLS))

    ds = pd.read_parquet(os.path.join(config.EVENTS_DIR, "dataset.parquet"))
    feats = ds[["ts", "direction", "family"] + COLS].drop_duplicates(
        subset=["ts", "direction", "family"])
    days = sorted(ds["ts"].dt.date.unique())
    split_day = days[int(len(days) * 0.6)]
    train_feats = feats[feats["ts"].dt.date <= split_day]
    log.info("train events: %d, split %s", len(train_feats), split_day)

    frontier_rows = []
    frozen = {}
    for fam in FAMILIES:
        fam_feats = train_feats[train_feats["family"] == fam]
        if len(fam_feats) < MIN_N_OOS:
            continue
        for geo in GEOS:
            df = relabel(fam_feats, geo).reset_index(drop=True)
            if len(df) < MIN_N_OOS:
                continue
            base_wr = float(df["y"].mean())
            base_ev = float(df["r_net"].mean())
            row = {"family": fam, "geo": geo_key(geo), "n": len(df),
                   "base_wr": round(base_wr, 4), "base_ev": round(base_ev, 4),
                   "oos_best_wr": None, "oos_best_n": None, "oos_best_ev": None, "tau": None}
            # Phase B only if ML-sized and base WR not hopeless (needs +20pp lift max)
            if len(df) >= config.MIN_TRAIN_EVENTS_PER_FAMILY and base_wr >= 0.40:
                oos = walk_forward_oos(df, COLS)
                ok = oos.notna()
                if ok.sum() >= 200:
                    iso = IsotonicRegression(out_of_bounds="clip")
                    iso.fit(oos[ok], df.loc[ok, "y"])
                    sub = df.loc[ok].assign(p=iso.predict(oos[ok]))
                    best = None
                    for tau in np.arange(0.50, 0.96, 0.01):
                        g = sub[sub["p"] >= tau]
                        if len(g) < MIN_N_OOS:
                            break
                        best = {"tau": round(float(tau), 2), "n": len(g),
                                "wr": float(g["y"].mean()), "ev": float(g["r_net"].mean())}
                    if best:
                        row.update(oos_best_wr=round(best["wr"], 4), oos_best_n=best["n"],
                                   oos_best_ev=round(best["ev"], 4), tau=best["tau"])
                        if best["wr"] >= TARGET_WR:
                            m = lgb.train(config.LGBM_PARAMS, lgb.Dataset(df[COLS], df["y"]),
                                          num_boost_round=200)
                            tag = f"v2_{fam}_{geo_key(geo).replace('/','_').replace('%','')}"
                            m.save_model(os.path.join(config.MODELS_DIR, f"{tag}.txt"))
                            with open(os.path.join(config.MODELS_DIR, f"{tag}_cal.pkl"), "wb") as fh:
                                pickle.dump({"iso": iso, "cols": COLS}, fh)
                            frozen[f"{fam}|{geo_key(geo)}"] = {
                                "tag": tag, "tp_pct": geo.tp_atr, "sl_pct": geo.sl_atr,
                                "ts_min": geo.time_stop_min, "tau": best["tau"],
                                "train_oos_n": best["n"], "train_oos_wr": round(best["wr"], 4)}
            frontier_rows.append(row)
            log.info("%-9s %-24s n=%4d baseWR=%.1f%% baseEV=%+.3f | bestOOS: %s",
                     fam, row["geo"], row["n"], base_wr * 100, base_ev,
                     f"WR={row['oos_best_wr']*100:.1f}% n={row['oos_best_n']} tau={row['tau']}"
                     if row["oos_best_wr"] else "-")

    fr = pd.DataFrame(frontier_rows)
    fr.to_csv(os.path.join(config.MODELS_DIR, "v2_frontier.csv"), index=False)
    with open(os.path.join(config.MODELS_DIR, "v2_frozen.json"), "w") as f:
        json.dump({"split_day": str(split_day), "target_wr": TARGET_WR, "families": frozen}, f, indent=2)
    log.info("\ntop of frontier by best OOS WR:\n%s",
             fr.dropna(subset=["oos_best_wr"]).nlargest(10, "oos_best_wr").to_string(index=False))
    log.info("frozen candidates: %d", len(frozen))


if __name__ == "__main__":
    main()
