"""
Pandemic Sensitivity Index (PSI) — API Router
==============================================
Exposes the macro-overlay PSI gauge (basket-driven health-crisis early-warning
system) to the frontend dashboard.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pandemic-sensitivity", tags=["pandemic-sensitivity"])


@router.get("")
async def get_pandemic_sensitivity() -> Dict[str, Any]:
    """
    Latest Pandemic Sensitivity Index snapshot.

    Response:
        psi_score (0-100), risk_level, summary, market_impact (per symbol),
        baskets[] (each with contributors[], score, rationale).
    """
    try:
        from services.pandemic_sensitivity_service import get_snapshot, ensure_started, is_ready
        if not is_ready():
            # Lazy-start so cold endpoints still work even if lifespan task lagged
            await ensure_started()
        return {"success": True, "data": get_snapshot()}
    except Exception as e:
        logger.error("PSI snapshot error: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "data": {
                "psi_score": 0.0,
                "risk_level": "NORMAL",
                "risk_color": "#6b7280",
                "summary": f"PSI unavailable: {e}",
                "market_impact": {},
                "baskets": [],
                "historical_percentile": None,
                "generated_at": None,
                "age_minutes": 0.0,
            },
        }


@router.get("/history")
async def get_pandemic_sensitivity_history(
    days: int = Query(default=90, ge=30, le=180, description="Lookback days for the PSI sparkline"),
) -> Dict[str, Any]:
    """
    Reconstructed daily PSI series for the last `days` trading days.
    Computed from the cached basket history — no extra Yahoo fetches.
    """
    try:
        from services.pandemic_sensitivity_service import get_history_series, ensure_started, is_ready
        if not is_ready():
            await ensure_started()
        series = get_history_series(days=days)
        return {"success": True, "days": days, "points": len(series), "series": series}
    except Exception as e:
        logger.error("PSI history error: %s", e, exc_info=True)
        return {"success": False, "error": str(e), "series": []}


@router.get("/features")
async def get_pandemic_sensitivity_features() -> Dict[str, Any]:
    """
    ML-friendly feature payload (psi_score + per-basket scores).
    Consumed by ML feature pipeline if/when explicitly opted in.
    """
    try:
        from services.pandemic_sensitivity_service import get_ml_features, ensure_started, is_ready
        if not is_ready():
            await ensure_started()
        return {"success": True, "features": get_ml_features()}
    except Exception as e:
        logger.error("PSI features error: %s", e, exc_info=True)
        return {"success": False, "error": str(e), "features": {}}
