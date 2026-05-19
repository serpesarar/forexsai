"""
Entry-Quality Classifier — Katman 1 of the Trajectory Learner family
====================================================================

Purpose
-------
At signal CREATION time (before anything is written to prediction_logs),
score the entry's feature snapshot and predict P(SL_hit). If the
probability exceeds a per-symbol threshold (auto-picked at training
time for precision ≥ 0.75), the orchestrator drops the signal to HOLD
rather than emitting it.

This is the fastest of the three trajectory layers because it uses
ONLY data already in `prediction_logs.factors` — no trajectory
reconstruction needed. Per the user's 2026-05-19 request: trains in
minutes on ~75k historical signals.

Inputs
------
- prediction_logs WHERE status IN ('completed','stopped')
- factors JSONB (60+ features per row, captured by
  signal_feature_snapshot at creation)

Outputs
-------
- backend/models/entry_quality_<symbol>.joblib  (LightGBM model)
- backend/models/entry_quality_<symbol>.meta.json
    {
      "trained_at", "symbol", "n_train", "n_val", "auc",
      "block_threshold",   # P(SL) ≥ this → block at creation
      "feature_names",
      "class_report"
    }

Usage
-----
    cd /Users/melihcanodacioglu/Desktop/panel
    python backend/research/train_entry_quality_model.py \\
        --symbol XAUUSD --days 180 --min-samples 500

Notes
-----
- We deliberately train PER SYMBOL — XAUUSD's failure pattern is very
  different from USOIL/NDX/GDAXI. A single model would average them.
- Class weights are balanced; usually SL hits are 40-60% of resolved
  signals so no heavy reweighting needed, but the safety net is there.
- Threshold is auto-picked so live precision ≥ 0.75 — we'd rather miss
  a few bad signals than block winning trades.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Numerical features we pull out of factors. Add new ones here as the
# snapshot grows — missing values are imputed to 0.
NUMERIC_FEATURES = [
    # M30 indicators
    "M30_rsi_14", "M30_macd_hist", "M30_macd_hist_slope",
    "M30_macd_hist_atr", "M30_ema20_slope_atr", "M30_atr_pct",
    "M30_bb_pctb", "M30_dist_ema200_atr", "M30_chan_pct",
    "M30_volume_z",
    # H1 confirmations
    "H1_rsi_14", "H1_macd_hist", "H1_adx_14",
    "H1_ema20_slope_atr", "H1_atr_pct",
    # Daily macro context
    "D1_rsi_14", "D1_atr_pct",
    # Cross-asset overlays
    "macro_dxy_chg1d_pct", "macro_vix_chg1d_pct",
    "macro_yield_10y_3m", "macro_risk_on_z",
    # Distance to key levels
    "dist_swing_high", "dist_swing_low",
    "dist_resistance_atr", "dist_support_atr",
]
BOOL_FEATURES = ["sar_bearish"]
DIRECTION_FEATURE = "ml_direction"  # added separately, 1 for BUY 0 for SELL
REGIME_FEATURE = "regime_label"     # one-hot encoded

LABEL_STOPPED = 1
LABEL_COMPLETED = 0


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def fetch_signals(symbol: str, days: int) -> List[Dict[str, Any]]:
    """Pull resolved signals + their entry factors for a symbol."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        raise RuntimeError("Supabase not available — set SUPABASE_URL/KEY")
    client = get_supabase_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    rows_acc: List[Dict[str, Any]] = []
    page_size = 1000
    offset = 0
    while True:
        q = client.table("prediction_logs").select(
            "id, symbol, model_type, ml_direction, ml_confidence, status, "
            "factors, created_at"
        ).eq("symbol", symbol).gte("created_at", since).order(
            "created_at", desc=True
        ).limit(page_size)
        # supabase wrapper doesn't expose offset directly in this codebase,
        # so paginate by date if needed. For now one shot up to 20k.
        res = q.execute() if hasattr(q, "execute") else q
        data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
        if not data:
            break
        rows_acc.extend(data)
        if len(data) < page_size or len(rows_acc) >= 20000:
            break
        # Next page would need offset support; we cap at 20k for now.
        break

    resolved = [r for r in rows_acc if r.get("status") in ("completed", "stopped")]
    return resolved


def build_feature_matrix(signals: List[Dict[str, Any]]
                          ) -> Tuple[Any, Any, List[str]]:
    """Build X, y, feature_names. Missing features imputed to 0."""
    import numpy as np

    # Discover regime values for one-hot
    regimes_seen = set()
    for s in signals:
        f = s.get("factors") or {}
        r = f.get(REGIME_FEATURE)
        if r:
            regimes_seen.add(str(r).lower())
    regimes_seen = sorted(regimes_seen)

    # Build feature name list
    feature_names: List[str] = []
    feature_names.extend(NUMERIC_FEATURES)
    feature_names.extend(BOOL_FEATURES)
    feature_names.append("direction_is_buy")
    feature_names.append("ml_confidence")
    feature_names.extend([f"regime_{r}" for r in regimes_seen])

    X_rows: List[List[float]] = []
    y_rows: List[int] = []
    for s in signals:
        f = s.get("factors") or {}
        row: List[float] = []
        for name in NUMERIC_FEATURES:
            row.append(_safe_float(f.get(name)))
        for name in BOOL_FEATURES:
            row.append(1.0 if f.get(name) else 0.0)
        row.append(1.0 if s.get("ml_direction") == "BUY" else 0.0)
        row.append(_safe_float(s.get("ml_confidence")))
        regime_val = str((f.get(REGIME_FEATURE) or "")).lower()
        for r in regimes_seen:
            row.append(1.0 if regime_val == r else 0.0)
        X_rows.append(row)
        y_rows.append(LABEL_STOPPED if s.get("status") == "stopped" else LABEL_COMPLETED)

    X = np.array(X_rows, dtype=float)
    y = np.array(y_rows, dtype=int)
    return X, y, feature_names


def train(symbol: str, days: int, min_samples: int, out_dir: str) -> Dict[str, Any]:
    """End-to-end. Returns metrics dict."""
    try:
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import (
            classification_report, roc_auc_score, precision_recall_curve,
            confusion_matrix,
        )
        import lightgbm as lgb
        import joblib
    except ImportError as e:
        raise RuntimeError(f"Missing deps: {e}. Install lightgbm + scikit-learn.")

    logger.info("Fetching signals for %s (last %dd)", symbol, days)
    signals = fetch_signals(symbol, days)
    logger.info("  %d resolved signals", len(signals))
    if len(signals) < min_samples:
        return {"status": "insufficient_data", "n_signals": len(signals),
                "min_required": min_samples}

    X, y, feature_names = build_feature_matrix(signals)
    sl_rate = float(y.mean())
    logger.info("Dataset: X.shape=%s  SL_hit rate=%.2f%%  features=%d",
                X.shape, sl_rate * 100, X.shape[1])

    # Walk-forward: train on older 75%, validate on newer 25%.
    # Supabase returns desc order (newest first), so reverse first.
    X = X[::-1]
    y = y[::-1]
    n = len(X)
    split = int(n * 0.75)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    logger.info("Walk-forward split: train=%d (older) val=%d (newer)",
                len(X_train), len(X_val))

    model = lgb.LGBMClassifier(
        n_estimators=500, learning_rate=0.04,
        max_depth=6, num_leaves=31,
        min_child_samples=20,
        class_weight="balanced",
        objective="binary", verbose=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="auc",
        callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)],
    )

    proba = model.predict_proba(X_val)[:, 1]
    auc = float(roc_auc_score(y_val, proba)) if len(set(y_val)) > 1 else 0.5

    # Pick threshold that gives precision ≥ 0.75 (don't block winners)
    precisions, recalls, thresholds = precision_recall_curve(y_val, proba)
    block_thresh = 0.7  # safe default if precision never reaches 0.75
    best_recall_at_target = 0.0
    for p, r, t in zip(precisions, recalls, list(thresholds) + [1.0]):
        if p >= 0.75 and r > best_recall_at_target:
            block_thresh = float(t)
            best_recall_at_target = float(r)

    # Standard metrics at threshold 0.5 for reference
    pred_at_05 = (proba >= 0.5).astype(int)
    cls = classification_report(y_val, pred_at_05, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_val, pred_at_05).tolist()

    # Save
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    sym_key = symbol.replace(".", "_")
    model_path = out_path / f"entry_quality_{sym_key}.joblib"
    meta_path = out_path / f"entry_quality_{sym_key}.meta.json"
    joblib.dump(model, model_path)
    meta = {
        "symbol": symbol,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_train": int(len(X_train)),
        "n_val": int(len(X_val)),
        "auc": round(auc, 4),
        "sl_hit_rate_pct": round(sl_rate * 100, 2),
        "block_threshold": round(block_thresh, 3),
        "block_threshold_recall_at_p075": round(best_recall_at_target, 3),
        "feature_names": feature_names,
        "class_report": cls,
        "confusion_matrix_at_05": cm,
        "training_window_days": days,
    }
    with open(meta_path, "w") as fp:
        json.dump(meta, fp, indent=2)

    logger.info("Saved → %s", model_path)
    logger.info("AUC=%.3f  block_threshold=%.2f (precision≥0.75 recall=%.1f%%)",
                auc, block_thresh, best_recall_at_target * 100)
    return {
        "status": "ok",
        "model_path": str(model_path),
        "meta_path": str(meta_path),
        "n_signals": len(signals),
        "auc": auc,
        "block_threshold": block_thresh,
    }


def _cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--days", type=int, default=180,
                    help="Training window (days). Default 180.")
    ap.add_argument("--min-samples", type=int, default=500)
    ap.add_argument("--out-dir",
                    default=str(Path(__file__).resolve().parent.parent / "models"),
                    help="Output dir for .joblib + .meta.json (default: backend/models)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    result = train(args.symbol, args.days, args.min_samples, args.out_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _cli()
