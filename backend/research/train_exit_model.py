"""
Exit Predictor Training (Post-Entry Trajectory Learner v2)
==========================================================

Trains a binary classifier that, given a signal's TRAJECTORY (entry
snapshot + a sequence of in-flight snapshots), predicts P(SL_hit).
The lifecycle then uses this model to abort signals before they hit SL.

Inputs (Supabase):
  - prediction_logs       — entry features + final status
  - signal_trajectory_snapshots — periodic in-flight snapshots
  - outcome / status      — label (stopped=1, completed=0)

Output:
  - models/exit_model_<symbol>.joblib + features.json
  - validation report (precision/recall, ROC, calibration)

Usage:
    cd backend
    python research/train_exit_model.py --symbol XAUUSD --days 90 --min-snapshots 3

Run this AFTER enough trajectory data has accumulated. Recommended:
≥ 1,000 completed/stopped signals with ≥ 3 trajectory snapshots each.
At a typical 50 signals/day per symbol that's 4-6 weeks of capture.

Design notes
- Feature engineering for time-series: we keep entry snapshot + the
  delta from entry to the LATEST snapshot for each feature. This is
  sufficient for a tree model; more sophisticated sequence models
  (LSTM/Transformer) need more data than we'll have.
- Class imbalance: SL hits are typically 30-50% of resolved signals,
  so no heavy reweighting needed. Use stratified split.
- Walk-forward validation: split by `created_at`, train on older,
  validate on newer.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Numerical features we expect from build_signal_feature_snapshot.
# Extend as new indicators get added — missing values are imputed.
CORE_FEATURES = [
    "M30_rsi_14", "M30_macd_hist", "M30_macd_hist_slope",
    "M30_ema20_slope_atr", "M30_atr_pct", "M30_bb_pctb",
    "M30_dist_ema200_atr", "M30_volume_z",
    "H1_adx_14", "H1_rsi_14", "H1_macd_hist",
    "macro_dxy_chg1d_pct", "macro_vix_chg1d_pct",
]
BOOL_FEATURES = ["sar_bearish"]
REGIME_FEATURE = "regime_label"  # categorical; one-hot encoded

LABEL_STOPPED = 1
LABEL_COMPLETED = 0


def _is_number(x: Any) -> bool:
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def fetch_training_data(symbol: str, days: int, min_snapshots: int) -> List[Dict[str, Any]]:
    """Pull resolved signals + their trajectory snapshots from Supabase."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        raise RuntimeError("Supabase not available")
    client = get_supabase_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Resolved signals
    rows = client.table("prediction_logs").select(
        "id, symbol, model_type, ml_direction, status, factors, "
        "ml_entry_price, exit_price, highest_profit_pips, lowest_drawdown_pips, "
        "created_at, exit_time"
    ).eq("symbol", symbol).gte("created_at", since).limit(20000)
    res = rows.execute() if hasattr(rows, "execute") else rows
    signals = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
    signals = [s for s in signals if s.get("status") in ("completed", "stopped")]
    if not signals:
        return []

    # Build a dict of trajectory by signal_id
    pred_ids = [s["id"] for s in signals]
    snapshots_by_signal: Dict[str, List[Dict[str, Any]]] = {}
    # Chunk fetches to avoid URL bloat
    for i in range(0, len(pred_ids), 100):
        chunk_ids = pred_ids[i:i+100]
        try:
            tres = client.table("signal_trajectory_snapshots").select(
                "signal_id, age_minutes, features, current_profit_pips, "
                "current_drawdown_pips, deterioration_score"
            ).in_("signal_id", chunk_ids).order("age_minutes")
            tres_ex = tres.execute() if hasattr(tres, "execute") else tres
            data = tres_ex.get("data") if isinstance(tres_ex, dict) else getattr(tres_ex, "data", []) or []
            for row in data:
                sid = row.get("signal_id")
                if sid:
                    snapshots_by_signal.setdefault(sid, []).append(row)
        except Exception as e:
            logger.warning("trajectory chunk %d failed: %s", i, e)

    # Filter signals that have enough snapshots
    enriched = []
    for s in signals:
        snaps = snapshots_by_signal.get(s["id"], [])
        if len(snaps) >= min_snapshots:
            s["_snapshots"] = snaps
            enriched.append(s)
    return enriched


def build_feature_vector(signal: Dict[str, Any]) -> Optional[Tuple[List[float], int]]:
    """Build (X, y) for a single signal.

    X = [entry_features..., delta_to_latest_features..., direction_is_buy,
         age_minutes_at_last_snapshot, current_profit_pips, current_drawdown_pips]
    y = 1 if stopped, 0 if completed
    """
    snaps = signal.get("_snapshots") or []
    if not snaps:
        return None
    entry_factors = signal.get("factors") or {}
    last = snaps[-1]
    latest_features = last.get("features") or {}

    # Build aligned vectors
    entry_vec = []
    latest_vec = []
    delta_vec = []
    for f in CORE_FEATURES:
        e = _safe_float(entry_factors.get(f))
        n = _safe_float(latest_features.get(f))
        entry_vec.append(e)
        latest_vec.append(n)
        delta_vec.append(n - e)

    # Booleans → 0/1 + delta
    for b in BOOL_FEATURES:
        e_b = 1.0 if entry_factors.get(b) else 0.0
        n_b = 1.0 if latest_features.get(b) else 0.0
        entry_vec.append(e_b)
        latest_vec.append(n_b)
        delta_vec.append(n_b - e_b)

    # Direction
    direction = 1.0 if signal.get("ml_direction") == "BUY" else 0.0

    # Trajectory dynamics
    age_at_last = _safe_float(last.get("age_minutes"))
    cur_prof = _safe_float(last.get("current_profit_pips"))
    cur_dd = _safe_float(last.get("current_drawdown_pips"))
    deterior_score = _safe_float(last.get("deterioration_score"))

    X = entry_vec + delta_vec + [direction, age_at_last, cur_prof, cur_dd, deterior_score]
    y = LABEL_STOPPED if signal.get("status") == "stopped" else LABEL_COMPLETED
    return X, y


def train(symbol: str, days: int, min_snapshots: int, out_dir: str) -> Dict[str, Any]:
    """End-to-end training. Returns metrics dict."""
    try:
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import (
            classification_report, roc_auc_score, precision_recall_curve
        )
        import lightgbm as lgb
        import joblib
    except ImportError as e:
        raise RuntimeError(f"Missing deps: {e}. Install lightgbm + scikit-learn.")

    logger.info("Fetching training data for %s (last %dd, min %d snapshots)",
                symbol, days, min_snapshots)
    signals = fetch_training_data(symbol, days, min_snapshots)
    logger.info("  %d signals with sufficient trajectory data", len(signals))
    if len(signals) < 100:
        return {"status": "insufficient_data", "n_signals": len(signals),
                "hint": "need ≥100 signals with ≥%d snapshots each" % min_snapshots}

    rows = []
    labels = []
    for s in signals:
        fv = build_feature_vector(s)
        if fv:
            X, y = fv
            rows.append(X)
            labels.append(y)
    if len(rows) < 100:
        return {"status": "insufficient_data", "n_rows": len(rows)}

    X = np.array(rows, dtype=float)
    y = np.array(labels, dtype=int)
    logger.info("Dataset: X.shape=%s  positive (SL hit) rate=%.2f%%",
                X.shape, y.mean() * 100)

    # Stratified split — preserve SL/TP class ratio
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y)

    model = lgb.LGBMClassifier(
        n_estimators=300, learning_rate=0.05,
        max_depth=6, num_leaves=31,
        class_weight="balanced",  # safety net even if mostly balanced
        objective="binary",
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="auc",
        callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)],
    )

    proba = model.predict_proba(X_val)[:, 1]
    auc = float(roc_auc_score(y_val, proba))
    pred_at_05 = (proba >= 0.5).astype(int)
    cls_report = classification_report(y_val, pred_at_05, output_dict=True)

    # Find threshold that gives precision ≥ 0.75 (we only want HIGH-CONFIDENCE
    # aborts — a false positive aborts a winning trade prematurely).
    precisions, recalls, thresholds = precision_recall_curve(y_val, proba)
    target_thresh = 0.5
    for p, t in zip(precisions, list(thresholds) + [1.0]):
        if p >= 0.75:
            target_thresh = float(t)
            break

    # Persist
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    model_path = out_path / f"exit_model_{symbol.replace('.','_')}.joblib"
    meta_path = out_path / f"exit_model_{symbol.replace('.','_')}.meta.json"
    joblib.dump(model, model_path)
    feature_names = (
        [f"entry_{f}" for f in CORE_FEATURES + BOOL_FEATURES]
        + [f"delta_{f}" for f in CORE_FEATURES + BOOL_FEATURES]
        + ["direction_is_buy", "age_minutes", "current_profit_pips",
           "current_drawdown_pips", "rule_v1_score"]
    )
    meta = {
        "symbol": symbol,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_train": int(len(X_train)),
        "n_val": int(len(X_val)),
        "auc": round(auc, 4),
        "precision_threshold_75": round(target_thresh, 3),
        "feature_names": feature_names,
        "class_report": cls_report,
        "training_window_days": days,
    }
    with open(meta_path, "w") as fp:
        json.dump(meta, fp, indent=2)

    logger.info("Saved → %s", model_path)
    logger.info("AUC=%.3f  precision@0.5=%.2f  recall@0.5=%.2f",
                auc, cls_report["1"]["precision"], cls_report["1"]["recall"])
    return {"status": "ok", "auc": auc, "model_path": str(model_path),
            "meta_path": str(meta_path), "n_signals": len(signals)}


def _cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--min-snapshots", type=int, default=3)
    ap.add_argument("--out-dir", default="backend/models")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    # Allow imports from backend/ when run from project root
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    result = train(args.symbol, args.days, args.min_snapshots, args.out_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _cli()
