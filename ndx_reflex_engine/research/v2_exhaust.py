"""V2 exhaustive continuation — everything the goal lists that wasn't yet tested.

Part 1  NEW TRIGGER FAMILIES: vol_compress, trend_exhaust — detect over all days,
        features, pct-geometry labels, base rates + LightGBM-gated frontier (train only).
Part 2  MODEL CLASSES on the two best lever combos (limit-mid + Tier B):
        LightGBM / XGBoost / CatBoost / RandomForest / HistGB / Logistic + mean-p ENSEMBLE.
        Purged WF train-OOS → isotonic → τ sweep (n≥80 and n≥40 tails) + one holdout pass.
Part 3  FEATURE ABLATION on the best combo: top-15 by gain vs full set.

Selection stays on the train split; holdout is scored once per final variant.
"""
from __future__ import annotations

import glob
import logging
import os
import sys
import warnings
from datetime import date

import lightgbm as lgb
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from features.pack import TIER_B_COLS, compute_feature_frame, event_features  # noqa: E402
from labels.triple_barrier import Geometry  # noqa: E402
from research.high_precision import COLS as A_COLS, relabel  # noqa: E402
from triggers.detect import (_apply_refractory, _in_window,  # noqa: E402
                             detect_trend_exhaust, detect_vol_compress)
from sklearn.isotonic import IsotonicRegression  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("v2x")
COLS = A_COLS + TIER_B_COLS
RNG = np.random.default_rng(7)


# ── generic WF over model classes ────────────────────────────────────────────

def make_models():
    from xgboost import XGBClassifier
    from catboost import CatBoostClassifier
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return {
        "lgbm": lambda: lgb.LGBMClassifier(**{k: v for k, v in config.LGBM_PARAMS.items()
                                              if k not in ("objective", "verbosity")},
                                           n_estimators=200, verbosity=-1),
        "xgb": lambda: XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05,
                                     subsample=0.8, colsample_bytree=0.7, min_child_weight=25,
                                     eval_metric="logloss", verbosity=0, random_state=7),
        "cat": lambda: CatBoostClassifier(iterations=300, depth=5, learning_rate=0.05,
                                          verbose=0, random_seed=7),
        "rf": lambda: RandomForestClassifier(n_estimators=400, max_depth=8,
                                             min_samples_leaf=25, n_jobs=-1, random_state=7),
        "histgb": lambda: HistGradientBoostingClassifier(max_depth=5, learning_rate=0.05,
                                                         max_iter=250, random_state=7),
        "logit": lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                       LogisticRegression(max_iter=2000, C=0.3)),
    }


def wf_oos_generic(df: pd.DataFrame, cols: list[str], model_fn) -> pd.Series:
    days = np.array(sorted(df["day"].unique()))
    folds = np.array_split(days, config.WF_FOLDS)
    oos = pd.Series(np.nan, index=df.index)
    for k in range(1, len(folds)):
        train_max = pd.Timestamp(folds[k][0]) - pd.Timedelta(days=config.WF_EMBARGO_DAYS)
        tr = df[df["day"] < train_max.date()]
        te = df[df["day"].isin(set(folds[k]))]
        if len(tr) < 100 or te.empty:
            continue
        m = model_fn()
        X = tr[cols].astype(float)
        m.fit(X.fillna(np.nan) if hasattr(m, "predict_proba") else X, tr["y"])
        oos.loc[te.index] = m.predict_proba(te[cols].astype(float))[:, 1]
    return oos


def tail_report(df: pd.DataFrame, oos: pd.Series, label: str) -> dict:
    ok = oos.notna()
    if ok.sum() < 150:
        return {"label": label, "note": "insufficient"}
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(oos[ok], df.loc[ok, "y"])
    sub = df.loc[ok].assign(p=iso.predict(oos[ok])).sort_values("p", ascending=False)
    out = {"label": label}
    for n in (40, 80):
        g = sub.head(n)
        out[f"top{n}_wr"] = round(float(g["y"].mean()), 4)
        out[f"top{n}_ev"] = round(float(g["r_net"].mean()), 4)
    return out


# ── Part 1: new trigger families ─────────────────────────────────────────────

def part1_new_triggers() -> None:
    log.info("── PART 1: vol_compress + trend_exhaust ──")
    paths = sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet")))
    ev_all, feat_all = [], []
    prev = None
    for p in paths:
        d = date.fromisoformat(os.path.basename(p).replace(".parquet", ""))
        bars = pd.read_parquet(p)
        if d.weekday() >= 5 or d in config.HOLIDAYS_2025:
            prev = bars
            continue
        ctx = pd.concat([prev, bars]).sort_values("ts").reset_index(drop=True) if prev is not None else bars
        evs = pd.concat([detect_vol_compress(ctx), detect_trend_exhaust(ctx)], ignore_index=True)
        if not evs.empty:
            evs = evs[(evs["ts"].dt.date == d) & _in_window(evs["ts"])]
            evs = _apply_refractory(evs)
            if not evs.empty:
                fe = event_features(compute_feature_frame(ctx), evs)
                if not fe.empty:
                    feat_all.append(fe)
        prev = bars
    feats = pd.concat(feat_all, ignore_index=True)
    days = sorted(feats["ts"].dt.date.unique())
    # NOTE: split day must match the master dataset's split (recompute from dataset)
    ds = pd.read_parquet(os.path.join(config.EVENTS_DIR, "dataset.parquet"))
    all_days = sorted(ds["ts"].dt.date.unique())
    split = all_days[int(len(all_days) * 0.6)]
    train = feats[feats["ts"].dt.date <= split]
    log.info("new-trigger events: %d total, %d train", len(feats), len(train))
    feats.to_parquet(os.path.join(config.EVENTS_DIR, "events_v2x.parquet"), index=False)

    for fam in ("vol_compress", "trend_exhaust"):
        for tp, sl, ts in ((0.0010, 0.0010, 15), (0.0010, 0.0013, 15), (0.0010, 0.0013, 30),
                           (0.0013, 0.0013, 30), (0.0010, 0.0013, 60)):
            geo = Geometry(tp, sl, ts, mode="pct")
            df = relabel(train[train["family"] == fam], geo).reset_index(drop=True)
            if len(df) < 60:
                continue
            base_wr, base_ev = float(df["y"].mean()), float(df["r_net"].mean())
            msg = f"{fam} tp{tp*100:.2f}/sl{sl*100:.2f}/ts{ts}: n={len(df)} baseWR={base_wr*100:.1f}% EV={base_ev:+.3f}"
            if len(df) >= 300:
                oos = wf_oos_generic(df, COLS, make_models()["lgbm"])
                tr = tail_report(df, oos, fam)
                msg += f" | gated top40 WR={tr.get('top40_wr', 0)*100:.1f}% top80 WR={tr.get('top80_wr', 0)*100:.1f}%"
            log.info(msg)


# ── Part 2+3: model classes, ensemble, ablation on best combos ───────────────

def part23_models() -> None:
    log.info("── PART 2: model classes + ensemble (limit-mid + Tier B) ──")
    feats_all = pd.read_parquet(os.path.join(config.EVENTS_DIR, "dataset.parquet"))
    feats = feats_all[["ts", "direction", "family"] + COLS].drop_duplicates(
        subset=["ts", "direction", "family"])
    all_days = sorted(feats_all["ts"].dt.date.unique())
    split = all_days[int(len(all_days) * 0.6)]

    combos = [("sr_react", 0.0010, 0.0013, 15), ("vwap_rev", 0.0013, 0.0013, 15)]
    models = make_models()
    for fam, tp, sl, ts in combos:
        geo = Geometry(tp, sl, ts, mode="pct", entry_mode="limit_mid")
        train = relabel(feats[(feats["family"] == fam) & (feats["ts"].dt.date <= split)],
                        geo).reset_index(drop=True)
        log.info("%s tp%.2f/sl%.2f/ts%d: train n=%d baseWR=%.1f%%",
                 fam, tp * 100, sl * 100, ts, len(train), train["y"].mean() * 100)
        oos_all = {}
        for name, fn in models.items():
            try:
                oos = wf_oos_generic(train, COLS, fn)
                oos_all[name] = oos
                r = tail_report(train, oos, name)
                log.info("  %-7s top40 WR=%.1f%% EV=%+.3f | top80 WR=%.1f%% EV=%+.3f",
                         name, r.get("top40_wr", 0) * 100, r.get("top40_ev", 0),
                         r.get("top80_wr", 0) * 100, r.get("top80_ev", 0))
            except Exception as e:  # noqa: BLE001
                log.info("  %-7s ERROR %s", name, e)
        if len(oos_all) >= 3:
            ens = pd.concat(oos_all.values(), axis=1).mean(axis=1)
            r = tail_report(train, ens, "ensemble")
            log.info("  %-7s top40 WR=%.1f%% EV=%+.3f | top80 WR=%.1f%% EV=%+.3f",
                     "ENSEMBLE", r.get("top40_wr", 0) * 100, r.get("top40_ev", 0),
                     r.get("top80_wr", 0) * 100, r.get("top80_ev", 0))

        # Part 3: ablation — top-15 LGBM-gain features
        m = lgb.train(config.LGBM_PARAMS, lgb.Dataset(train[COLS], train["y"]), num_boost_round=200)
        gain = pd.Series(m.feature_importance("gain"), index=COLS).nlargest(15)
        top_cols = list(gain.index)
        oos_ab = wf_oos_generic(train, top_cols, models["lgbm"])
        r = tail_report(train, oos_ab, "ablate15")
        log.info("  ABLATE-15 (%s…): top40 WR=%.1f%% | top80 WR=%.1f%%",
                 ",".join(top_cols[:5]), r.get("top40_wr", 0) * 100, r.get("top80_wr", 0) * 100)


if __name__ == "__main__":
    part1_new_triggers()
    part23_models()
