"""
Meta-Engine Router
API endpoints for the Meta-Intelligence Engine.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Query
from dataclasses import asdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meta", tags=["Meta-Engine"])


@router.get("/analyze/{symbol}")
async def meta_analyze(
    symbol: str,
    risk_profile: str = Query("balanced", pattern="^(conservative|balanced|aggressive)$"),
    min_confidence: float = Query(45, ge=0, le=100),
):
    """
    Get the meta-analysis signal for a symbol.
    Combines all 6 models into a single high-confidence signal.
    """
    try:
        from services.meta_analysis_engine import get_meta_signal

        signal = await get_meta_signal(
            symbol=symbol,
            risk_profile=risk_profile,
            min_confidence=min_confidence,
        )

        if signal is None:
            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "direction": "HOLD",
                    "confidence": 0,
                    "strength": "WEAK",
                    "source_combo": "",
                    "regime": "UNKNOWN",
                    "agreement_ratio": 0,
                    "technical_score": 0,
                    "passed_conditions": [],
                    "model_breakdown": {},
                    "message": "Insufficient model signals available",
                },
            }

        return {
            "success": True,
            "data": asdict(signal),
        }
    except Exception as e:
        logger.error(f"[MetaRouter] Analyze error for {symbol}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/combinations/{symbol}")
async def meta_combinations(
    symbol: str,
    regime: str = Query("UNKNOWN"),
):
    """
    Get combination performance stats for a symbol.
    Shows which model combinations historically perform best.
    """
    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if not client:
            return {"success": False, "error": "No database connection"}

        query = client.table("meta_combination_stats") \
            .select("*") \
            .eq("symbol", symbol) \
            .gte("total_signals", 3) \
            .order("win_rate", desc=True) \
            .limit(20)

        if regime != "UNKNOWN":
            query = query.eq("regime", regime)

        result = query.execute()
        rows = result.get("data", []) if isinstance(result, dict) else (result.data if hasattr(result, "data") else [])

        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "regime": regime,
                "combinations": rows or [],
                "total_combos": len(rows or []),
            },
        }
    except Exception as e:
        logger.error(f"[MetaRouter] Combinations error for {symbol}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/dashboard")
async def meta_dashboard():
    """
    Get meta-analysis summary for all 4 symbols.
    Returns a compact overview for the dashboard panel.
    """
    try:
        from services.meta_analysis_engine import get_meta_dashboard
        data = await get_meta_dashboard()
        return {
            "success": True,
            "data": data,
        }
    except Exception as e:
        logger.error(f"[MetaRouter] Dashboard error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/backfill")
async def meta_backfill():
    """
    Run historical backfill to populate combination stats
    from existing prediction_logs data.
    Should be called once to initialize the learning system.
    """
    try:
        from services.meta_signal_logger import backfill_combination_stats
        result = await backfill_combination_stats()
        return {
            "success": True,
            "data": result,
        }
    except Exception as e:
        logger.error(f"[MetaRouter] Backfill error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/history")
async def meta_history(
    symbol: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get recent meta-signal history.
    """
    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if not client:
            return {"success": False, "error": "No database connection"}

        query = client.table("meta_signals") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit)

        if symbol:
            query = query.eq("symbol", symbol)

        result = query.execute()
        rows = result.get("data", []) if isinstance(result, dict) else (result.data if hasattr(result, "data") else [])

        return {
            "success": True,
            "data": rows or [],
            "count": len(rows or []),
        }
    except Exception as e:
        logger.error(f"[MetaRouter] History error: {e}")
        return {"success": False, "error": str(e)}
