"""
XAUUSD model training — walk-forward LightGBM with isotonic calibration.

Design:
  - TWO MODELS, not one: a BUY-side and a SELL-side classifier, each predicting
    P(its-direction-profitable). At inference, take the higher P (with a margin
    threshold) — this fixes the BUY/SELL win-rate asymmetry of the legacy model
    (BUY 37.9% vs SELL 52.8%).
  - Triple-barrier label (TP=1.5×ATR, SL=1.0×ATR, horizon=24×M30=12h).
  - Walk-forward purged CV (5 folds, gap=horizon to prevent label leakage).
  - Isotonic calibration on each fold's validation set.
  - class_weight='balanced' inside LGBM to fight class imbalance.

Run:
    python xauusdegitim/train.py [--horizon 24] [--tp 1.5] [--sl 1.0]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from loader import load_xauusd, load_macros  # noqa: E402
from features import build_dataset  # noqa: E402

import lightgbm as lgb  # noqa: E402
from sklearn.isotonic import IsotonicRegression  # noqa: E402
from sklearn.metrics import roc_auc_score, brier_score_loss  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "artifacts"
OUT_DIR.mkdir(exist_ok=True)


def lgbm_params(seed: int = 42) -> dict:
    return dict(
        objective="binary",
        learning_rate=0.03,
        num_leaves=63,
        max_depth=-1,
        min_data_in_leaf=200,
        feature_fraction=0.85,
        bagging_fraction=0.85,
        bagging_freq=5,
        lambda_l2=1.0,
        n_estimators=600,
        verbose=-1,
        seed=seed,
        class_weight="balanced",
        deterministic=True,
    )


def walk_forward_folds(n: int, n_folds: int = 5, gap: int = 24):
    """Yields (train_idx, val_idx) — strictly forward, with a `gap` purge between train end and val start."""
    fold_size = n // (n_folds + 1)
    for k in range(n_folds):
        train_end = fold_size * (k + 1)
        val_start = train_end + gap
        val_end = val_start + fold_size
        if val_end > n:
            break
        yield np.arange(0, train_end), np.arange(val_start, val_end)


def fit_side(X: pd.DataFrame, y_long_pl: pd.Series, side: str, args) -> dict:
    """side='BUY' uses long_pl_atr; side='SELL' uses short_pl_atr (passed in as y_long_pl)."""
    # Binary target: profitable trade = pl > 0 with margin
    y_bin = (y_long_pl > 0.3).astype(int)  # +0.3 ATR profit minimum (filter timeouts near zero)
    mask = y_long_pl.notna() & X.notna().all(axis=1)
    Xc = X.loc[mask].reset_index(drop=True)
    yc = y_bin.loc[mask].reset_index(drop=True)
    pl = y_long_pl.loc[mask].reset_index(drop=True)
    n = len(Xc)
    print(f"\n=== {side} side training ({n} usable samples, positive class rate {yc.mean():.3f}) ===")

    fold_metrics = []
    iso_models = []
    boosters = []
    val_oof = np.full(n, np.nan)
    val_oof_calib = np.full(n, np.nan)

    for k, (tr, va) in enumerate(walk_forward_folds(n, n_folds=args.n_folds, gap=args.horizon)):
        X_tr, X_va = Xc.iloc[tr], Xc.iloc[va]
        y_tr, y_va = yc.iloc[tr], yc.iloc[va]
        pl_va = pl.iloc[va]

        booster = lgb.LGBMClassifier(**lgbm_params(seed=42 + k))
        booster.fit(
            X_tr, y_tr,
            eval_set=[(X_va, y_va)],
            callbacks=[lgb.early_stopping(50, verbose=False)],
        )
        p_raw = booster.predict_proba(X_va)[:, 1]
        # Isotonic calibration trained on first half of val, applied to second half
        half = len(va) // 2
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(p_raw[:half], y_va.values[:half])
        p_cal = iso.transform(p_raw)

        val_oof[va] = p_raw
        val_oof_calib[va] = p_cal

        # Bias-aware metric: simulated P/L if we trade the top X% confidence signals
        thresh_grid = [0.5, 0.55, 0.60, 0.65, 0.70]
        pnl_by_thresh = {}
        for t in thresh_grid:
            sel = p_cal >= t
            if sel.sum() == 0:
                pnl_by_thresh[t] = (0, 0.0, 0.0)
                continue
            n_sel = int(sel.sum())
            wr = float(yc.iloc[va][sel].mean())
            avg_pl = float(pl_va[sel].mean())
            pnl_by_thresh[t] = (n_sel, wr, avg_pl)

        fold_metrics.append({
            "fold": k,
            "n_train": len(tr),
            "n_val": len(va),
            "auc_raw": float(roc_auc_score(y_va, p_raw)),
            "auc_cal": float(roc_auc_score(y_va, p_cal)),
            "brier_raw": float(brier_score_loss(y_va, p_raw)),
            "brier_cal": float(brier_score_loss(y_va, p_cal)),
            "thresh_pnl": pnl_by_thresh,
        })
        iso_models.append(iso)
        boosters.append(booster)
        print(f"  fold {k}: AUC raw={fold_metrics[-1]['auc_raw']:.3f}  cal={fold_metrics[-1]['auc_cal']:.3f}  "
              f"Brier cal={fold_metrics[-1]['brier_cal']:.3f}")
        for t, (ns, wr, ap) in pnl_by_thresh.items():
            print(f"    thresh {t:.2f}: n={ns:5d}  win-rate={wr:.3f}  avg_pl_atr={ap:+.3f}")

    # Final model: refit on ALL data (no holdout) — used in production
    print(f"  fitting FINAL {side} on all {n} samples...")
    final = lgb.LGBMClassifier(**lgbm_params())
    final.fit(Xc, yc)
    # Final calibrator: fit on out-of-fold predictions (more honest than fold-internal)
    valid = np.isfinite(val_oof)
    iso_final = IsotonicRegression(out_of_bounds="clip")
    iso_final.fit(val_oof[valid], yc.values[valid])

    fi = pd.Series(final.feature_importances_, index=Xc.columns).sort_values(ascending=False)
    print(f"\n  Top 15 features ({side}):")
    for f, v in fi.head(15).items():
        print(f"    {f:35s} {v}")

    return {
        "side": side,
        "fold_metrics": fold_metrics,
        "feature_importance": fi.to_dict(),
        "final_model": final,
        "iso_final": iso_final,
        "X_columns": list(Xc.columns),
    }


def save_artifacts(buy_res: dict, sell_res: dict, args):
    import joblib
    bundle = {
        "buy_model": buy_res["final_model"],
        "buy_calibrator": buy_res["iso_final"],
        "sell_model": sell_res["final_model"],
        "sell_calibrator": sell_res["iso_final"],
        "feature_columns": buy_res["X_columns"],
        "config": {"horizon_bars": args.horizon, "tp_atr": args.tp, "sl_atr": args.sl,
                   "n_folds": args.n_folds, "version": "v2"},
    }
    out = OUT_DIR / "model_xauusd_v2.joblib"
    joblib.dump(bundle, out)
    print(f"\nSaved bundle → {out}")

    # Metrics report
    report = {
        "buy": {"folds": buy_res["fold_metrics"], "top_features": dict(list(buy_res["feature_importance"].items())[:30])},
        "sell": {"folds": sell_res["fold_metrics"], "top_features": dict(list(sell_res["feature_importance"].items())[:30])},
        "config": bundle["config"],
    }
    (OUT_DIR / "training_report.json").write_text(json.dumps(report, indent=2, default=float))
    print(f"Saved metrics → {OUT_DIR / 'training_report.json'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=24, help="Triple-barrier horizon in M30 bars (24=12h)")
    ap.add_argument("--tp", type=float, default=1.5)
    ap.add_argument("--sl", type=float, default=1.0)
    ap.add_argument("--n-folds", type=int, default=5)
    ap.add_argument("--broker-offset", type=int, default=3)
    ap.add_argument("--holdout-days", type=int, default=60,
                    help="Reserve last N days as untouched hold-out (final model never sees them).")
    args = ap.parse_args()

    print(f"Loading XAUUSD data (broker offset GMT+{args.broker_offset})...")
    xau = load_xauusd(broker_offset_h=args.broker_offset)
    macros = load_macros(broker_offset_h=args.broker_offset) if (Path(__file__).resolve().parent / "data/raw").exists() else None

    if "M30" not in xau or "H1" not in xau or "H4" not in xau:
        print("ERROR: M30/H1/H4 timeframes required.", file=sys.stderr)
        sys.exit(1)

    print("\nBuilding feature matrix...")
    X, y = build_dataset(xau["M30"], xau["H1"], xau["H4"], macros=macros, horizon_bars=args.horizon)
    # Drop rows where label is undefined (last `horizon_bars` and any with NaN long_pl)
    valid_idx = y["long_pl_atr"].notna() & y["short_pl_atr"].notna()
    X = X.loc[valid_idx]
    y = y.loc[valid_idx]

    # Hold-out cutoff — bars on/after this timestamp are RESERVED for backtest
    holdout_cutoff = X.index.max() - pd.Timedelta(days=args.holdout_days)
    train_mask = X.index < holdout_cutoff
    print(f"\n  hold-out cutoff: {holdout_cutoff}  "
          f"(train rows: {train_mask.sum()}, holdout rows: {(~train_mask).sum()})")
    X = X.loc[train_mask]
    y = y.loc[train_mask]
    print(f"  X shape: {X.shape}  features: {X.shape[1]}")
    print(f"  y long_label dist:  {dict(y['long_label'].value_counts())}")
    print(f"  y short_label dist: {dict(y['short_label'].value_counts())}")
    print(f"  long_pl_atr: mean={y['long_pl_atr'].mean():+.3f}  median={y['long_pl_atr'].median():+.3f}")
    print(f"  short_pl_atr: mean={y['short_pl_atr'].mean():+.3f}  median={y['short_pl_atr'].median():+.3f}")

    buy_res = fit_side(X, y["long_pl_atr"], "BUY", args)
    sell_res = fit_side(X, y["short_pl_atr"], "SELL", args)

    save_artifacts(buy_res, sell_res, args)
    print("\n=== TRAINING COMPLETE ===")


if __name__ == "__main__":
    main()
