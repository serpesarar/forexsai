"""
Strategy Auto-Optimization Loop — API Router
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/optimizer", tags=["strategy-optimizer"])


@router.get("/run")
async def run_optimizer(
    days: int = Query(default=14, ge=1, le=90, description="Lookback days for strategy scoring"),
) -> Dict[str, Any]:
    """
    Run the full Strategy Auto-Optimization Loop.
    Returns per-symbol risk scores, strategy rankings, and recommendations.
    """
    from services.strategy_optimizer_service import run_optimization, serialize_result

    try:
        result = await run_optimization(days=days)
        return serialize_result(result)
    except Exception as e:
        logger.error(f"Optimizer error: {e}", exc_info=True)
        return {
            "error": str(e),
            "global_risk_score": 50,
            "global_risk_level": "MODERATE",
            "symbols": [],
            "strategy_scores": {},
            "optimization_notes": [f"Error: {e}"],
        }
