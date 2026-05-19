"""
Entry-Quality Inference Service
================================

Loads the per-symbol Entry-Quality classifier (trained by
backend/research/train_entry_quality_model.py) and scores a candidate
signal's entry features at creation time.

Public API
----------
    score_entry(symbol, direction, ml_confidence, factors) -> dict
        {
            "p_sl": 0..1,
            "should_block": bool,
            "threshold": 0..1,
            "reason": str,
        }

If no model is available for the symbol, returns p_sl=None and
should_block=False (fail-open — never block trades on missing model).
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Lazy cache — load each model once
_MODEL_CACHE: Dict[str, Any] = {}
_META_CACHE: Dict[str, Dict[str, Any]] = {}
_LOAD_LOCK = threading.Lock()

# Override threshold from env var if set (e.g. ENTRY_QUALITY_THRESHOLD_XAUUSD=0.65)
_ENV_PREFIX = "ENTRY_QUALITY_THRESHOLD_"

# Directory containing the trained models
_DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "models"


def _model_paths(symbol: str, model_dir: Optional[Path] = None
                  ) -> tuple[Path, Path]:
    """Return (joblib_path, meta_path) for a symbol."""
    base = model_dir or _DEFAULT_MODEL_DIR
    sym_key = symbol.replace(".", "_")
    return base / f"entry_quality_{sym_key}.joblib", \
           base / f"entry_quality_{sym_key}.meta.json"


def _load(symbol: str) -> Optional[tuple[Any, Dict[str, Any]]]:
    """Load model + meta. Caches forever (process lifetime). Returns None on miss."""
    with _LOAD_LOCK:
        if symbol in _MODEL_CACHE:
            return _MODEL_CACHE[symbol], _META_CACHE[symbol]
        model_path, meta_path = _model_paths(symbol)
        if not model_path.exists() or not meta_path.exists():
            return None
        try:
            import joblib
            model = joblib.load(model_path)
            with open(meta_path) as fp:
                meta = json.load(fp)
            _MODEL_CACHE[symbol] = model
            _META_CACHE[symbol] = meta
            logger.info(
                "[entry_quality] loaded %s (auc=%.3f, threshold=%.2f)",
                symbol, meta.get("auc", 0), meta.get("block_threshold", 0.7)
            )
            return model, meta
        except Exception as e:
            logger.warning("[entry_quality] load %s failed: %s", symbol, e)
            return None


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _build_row(meta: Dict[str, Any], direction: str, ml_confidence: float,
                factors: Dict[str, Any]) -> list[float]:
    """Reconstruct the feature vector in the SAME order as training."""
    feature_names = meta.get("feature_names") or []
    row: list[float] = []
    for name in feature_names:
        if name == "direction_is_buy":
            row.append(1.0 if direction == "BUY" else 0.0)
        elif name == "ml_confidence":
            row.append(_safe_float(ml_confidence))
        elif name.startswith("regime_"):
            target = name.replace("regime_", "", 1)
            current = str(factors.get("regime_label") or "").lower()
            row.append(1.0 if current == target else 0.0)
        elif name in ("sar_bearish",):
            row.append(1.0 if factors.get(name) else 0.0)
        else:
            row.append(_safe_float(factors.get(name)))
    return row


def score_entry(symbol: str, direction: str, ml_confidence: float,
                 factors: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score a candidate signal. Returns:
        {p_sl, should_block, threshold, reason, model_available}

    Never raises — failure paths return should_block=False (fail open).
    """
    out: Dict[str, Any] = {
        "p_sl": None,
        "should_block": False,
        "threshold": None,
        "reason": "no_model",
        "model_available": False,
    }
    try:
        if direction not in ("BUY", "SELL"):
            out["reason"] = "non_directional"
            return out

        loaded = _load(symbol)
        if loaded is None:
            return out
        model, meta = loaded
        threshold = float(meta.get("block_threshold", 0.7))
        # Env override (per-symbol)
        env_key = _ENV_PREFIX + symbol.replace(".", "_").upper()
        env_val = os.getenv(env_key)
        if env_val is not None:
            try:
                threshold = float(env_val)
            except ValueError:
                pass

        row = _build_row(meta, direction, ml_confidence, factors or {})
        try:
            import numpy as np
            proba = model.predict_proba(np.array([row], dtype=float))[0, 1]
            p_sl = float(proba)
        except Exception as e:
            logger.debug("[entry_quality] inference failed: %s", e)
            out["reason"] = "inference_error"
            return out

        out["p_sl"] = round(p_sl, 4)
        out["threshold"] = round(threshold, 4)
        out["model_available"] = True
        if p_sl >= threshold:
            out["should_block"] = True
            out["reason"] = f"entry_quality_block (p_sl={p_sl:.2f} ≥ {threshold:.2f})"
        else:
            out["reason"] = "ok"
        return out
    except Exception as e:
        logger.debug("[entry_quality] score_entry error: %s", e)
        out["reason"] = f"error:{str(e)[:60]}"
        return out


def available_symbols(model_dir: Optional[Path] = None) -> list[str]:
    """List symbols with a trained model available."""
    base = model_dir or _DEFAULT_MODEL_DIR
    if not base.exists():
        return []
    syms = []
    for p in base.glob("entry_quality_*.joblib"):
        # entry_quality_XAUUSD.joblib → XAUUSD
        # entry_quality_NDX_INDX.joblib → NDX.INDX (.→_ during training)
        sym = p.stem.replace("entry_quality_", "", 1)
        # Heuristic: restore single dot if "_INDX"/"_FOREX" suffix
        for suffix in ("_INDX", "_FOREX"):
            if sym.endswith(suffix):
                sym = sym[:-len(suffix)] + suffix.replace("_", ".")
                break
        syms.append(sym)
    return syms
