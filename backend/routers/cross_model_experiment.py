"""
Cross-Model Experiment endpoints.

Public reads only — there's no mutation here. The experiment cron writes
to prediction_logs internally and the dashboard reads stats from there.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Query

from services.cross_model_experiment_service import (
    EXPERIMENT_MODEL_TYPE,
    EXPERIMENT_STRATEGY,
    EXPERIMENT_SYMBOL,
    EXPERIMENT_TIMEFRAME,
    experiment_stats,
    get_cached_preview,
    is_enabled,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/experiments/cross-model", tags=["Cross-Model Experiment"])


@router.get("/info")
async def info():
    """Static metadata about the experiment."""
    return {
        "enabled": is_enabled(),
        "model_type": EXPERIMENT_MODEL_TYPE,
        "strategy": EXPERIMENT_STRATEGY,
        "symbol": EXPERIMENT_SYMBOL,
        "timeframe": EXPERIMENT_TIMEFRAME,
        "description": (
            "Runs the NASDAQ ML model (model_lgbm_nasdaq.joblib) against "
            "XAUUSD candle data. Predictions are logged to prediction_logs "
            "with model_type=ml_cross_xau_nasdaq but NOT mirrored to "
            "meta_signals, so the MT5 auto-trader does not act on them. "
            "Lifecycle TP/SL evaluation is the same as every other model."
        ),
    }


@router.get("/preview")
async def preview():
    """Live cross-model prediction (60s in-memory cache)."""
    return await get_cached_preview()


@router.get("/stats")
async def stats(days: int = Query(14, ge=1, le=180)):
    """Roll-up: real WR, net pips, recent signals."""
    return await experiment_stats(days)
