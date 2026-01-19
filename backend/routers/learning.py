"""
Learning API Router
Endpoints for prediction tracking, outcome checking, and learning insights.
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from typing import Optional, List
from pydantic import BaseModel

from database.supabase_client import is_db_available, get_init_error
from services.prediction_logger import get_recent_predictions
from services.outcome_tracker import (
    check_pending_outcomes,
    get_accuracy_summary,
    get_multi_target_accuracy,
    check_multi_target_outcome,
)
from services.target_config import get_symbol_config, SYMBOL_CONFIGS
from services.learning_analyzer import (
    analyze_factor_correlations,
    generate_learning_insights,
    save_insights_to_db,
    get_active_insights,
)
from services.adaptive_tp_sl import (
    calculate_adaptive_tp_sl,
    get_learned_adjustments,
    AdaptiveTPSL,
)

router = APIRouter(prefix="/api/learning", tags=["learning"])


class HealthResponse(BaseModel):
    db_available: bool
    message: str


class AccuracySummary(BaseModel):
    symbol: Optional[str]
    period_days: int
    check_interval: str
    total_predictions: int
    ml_accuracy: Optional[float]
    ml_correct_count: Optional[int]
    claude_accuracy: Optional[float]
    claude_correct_count: Optional[int]
    both_correct_rate: Optional[float]
    either_correct_rate: Optional[float]


@router.get("/health")
async def learning_health():
    """Check if learning system database is available."""
    available = is_db_available()
    init_error = get_init_error()
    return {
        "db_available": available,
        "message": "Database connected" if available else "Database not configured.",
        "init_error": init_error
    }


@router.get("/predictions")
async def get_predictions(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(50, ge=1, le=200),
    unchecked_only: bool = Query(False, description="Only unchecked predictions")
):
    """Get recent predictions from database."""
    if not is_db_available():
        return {"error": "Database not available", "predictions": []}
    
    predictions = await get_recent_predictions(symbol, limit, unchecked_only)
    return {"predictions": predictions, "count": len(predictions)}


@router.post("/check-outcomes")
async def trigger_outcome_check(
    check_interval: str = Query("24h", description="Interval to check: 1h, 4h, 24h, 48h, 7d")
):
    """
    Manually trigger outcome checking for pending predictions.
    This would normally run as a scheduled job.
    """
    if not is_db_available():
        return {"error": "Database not available", "outcomes_checked": 0}
    
    outcomes = await check_pending_outcomes(check_interval)
    
    correct_count = sum(1 for o in outcomes if o.get("ml_correct"))
    
    return {
        "outcomes_checked": len(outcomes),
        "ml_correct": correct_count,
        "ml_incorrect": len(outcomes) - correct_count,
        "check_interval": check_interval
    }


@router.get("/accuracy")
async def get_accuracy(
    symbol: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    check_interval: str = Query("24h")
):
    """Get accuracy summary for recent predictions."""
    if not is_db_available():
        return {"error": "Database not available"}
    
    summary = await get_accuracy_summary(symbol, days, check_interval)
    return summary


@router.get("/factor-analysis")
async def get_factor_analysis(
    symbol: Optional[str] = Query(None),
    days: int = Query(30, ge=7, le=180),
    min_samples: int = Query(10, ge=5)
):
    """Analyze which factors correlate with correct/incorrect predictions."""
    if not is_db_available():
        return {"error": "Database not available"}
    
    analysis = await analyze_factor_correlations(symbol, days, min_samples)
    return analysis


@router.post("/generate-insights")
async def trigger_insight_generation(
    symbol: Optional[str] = Query(None),
    days: int = Query(30, ge=7, le=180),
    save_to_db: bool = Query(True, description="Save insights to database")
):
    """
    Generate learning insights based on historical performance.
    This would normally run as a scheduled job.
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    insights = await generate_learning_insights(symbol, days)
    
    saved = 0
    if save_to_db and insights:
        saved = await save_insights_to_db(insights)
    
    return {
        "insights_generated": len(insights),
        "insights_saved": saved,
        "insights": insights
    }


@router.get("/insights")
async def get_insights(symbol: Optional[str] = Query(None)):
    """Get active learning insights."""
    if not is_db_available():
        return {"error": "Database not available", "insights": []}
    
    insights = await get_active_insights(symbol)
    return {"insights": insights, "count": len(insights)}


@router.get("/dashboard")
async def get_learning_dashboard(
    symbol: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30)
):
    """
    Get a complete learning dashboard with accuracy, insights, and factor analysis.
    """
    if not is_db_available():
        return {
            "db_available": False,
            "message": "Database not configured. Set SUPABASE_URL and SUPABASE_KEY in .env"
        }
    
    accuracy = await get_accuracy_summary(symbol, days, "24h")
    insights = await get_active_insights(symbol)
    
    factor_analysis = {}
    if accuracy.get("total_predictions", 0) >= 10:
        factor_analysis = await analyze_factor_correlations(symbol, days=30, min_samples=10)
    
    return {
        "db_available": True,
        "symbol": symbol,
        "period_days": days,
        "accuracy": accuracy,
        "active_insights": insights[:10],
        "factor_analysis": factor_analysis if "error" not in factor_analysis else None
    }


@router.get("/target-config/{symbol}")
async def get_target_config(symbol: str):
    """Get target and stoploss configuration for a symbol."""
    config = get_symbol_config(symbol)
    return {
        "symbol": symbol,
        "pip_value": config.pip_value,
        "targets": [{"name": t.name, "pips": t.pips} for t in config.targets],
        "stoploss_pips": config.stoploss_pips,
    }


@router.get("/target-configs")
async def get_all_target_configs():
    """Get target configurations for all symbols."""
    configs = {}
    for symbol, config in SYMBOL_CONFIGS.items():
        configs[symbol] = {
            "pip_value": config.pip_value,
            "targets": [{"name": t.name, "pips": t.pips} for t in config.targets],
            "stoploss_pips": config.stoploss_pips,
        }
    return configs


@router.get("/multi-target-accuracy")
async def get_target_accuracy(
    symbol: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    check_interval: str = Query("1h", description="Check interval: 1h, 4h, 24h")
):
    """
    Get accuracy broken down by target levels (TP1, TP2, TP3).
    Shows hit rate for each target and stoploss.
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    result = await get_multi_target_accuracy(symbol, days, check_interval)
    return result


@router.post("/check-outcomes-1h")
async def trigger_1h_outcome_check():
    """
    Trigger 1-hour outcome check for predictions older than 1 hour.
    """
    if not is_db_available():
        return {"error": "Database not available", "outcomes_checked": 0}
    
    outcomes = await check_pending_outcomes("1h")
    
    correct_count = sum(1 for o in outcomes if o.get("ml_correct"))
    
    return {
        "outcomes_checked": len(outcomes),
        "ml_correct": correct_count,
        "ml_incorrect": len(outcomes) - correct_count,
        "check_interval": "1h"
    }


@router.get("/multi-target-dashboard")
async def get_multi_target_dashboard(
    symbol: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30)
):
    """
    Get complete multi-target dashboard with accuracy per target level.
    """
    if not is_db_available():
        return {
            "db_available": False,
            "message": "Database not configured"
        }
    
    # Get config
    config = get_symbol_config(symbol) if symbol else None
    config_data = None
    if config:
        config_data = {
            "pip_value": config.pip_value,
            "targets": [{"name": t.name, "pips": t.pips} for t in config.targets],
            "stoploss_pips": config.stoploss_pips,
        }
    
    # Get accuracy for multiple intervals
    accuracy_1h = await get_multi_target_accuracy(symbol, days, "1h")
    accuracy_24h = await get_multi_target_accuracy(symbol, days, "24h")
    
    # Basic accuracy
    basic_accuracy = await get_accuracy_summary(symbol, days, "24h")
    
    return {
        "db_available": True,
        "symbol": symbol,
        "period_days": days,
        "config": config_data,
        "accuracy_1h": accuracy_1h if "error" not in accuracy_1h else None,
        "accuracy_24h": accuracy_24h if "error" not in accuracy_24h else None,
        "basic_accuracy": basic_accuracy if "error" not in basic_accuracy else None,
    }


# ============================================================
# ERROR ANALYSIS ENDPOINTS (Self-Learning System)
# ============================================================

@router.get("/error-analyses")
async def get_error_analyses(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(20, ge=1, le=100),
    error_type: Optional[str] = Query(None, description="Filter by error type")
):
    """Get error analysis records for failed predictions."""
    from database.supabase_client import get_supabase_client, is_db_available
    
    if not is_db_available():
        return {"error": "Database not available", "data": []}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available", "data": []}
    
    try:
        query = client.table("error_analysis").select(
            "*, prediction_logs(symbol, ml_direction, ml_confidence, created_at)"
        ).order("created_at", desc=True).limit(limit)
        
        if error_type:
            query = query.eq("error_type", error_type)
        
        result = query.execute()
        analyses = result.get("data") or []
        
        # Filter by symbol if needed
        if symbol:
            analyses = [a for a in analyses if a.get("prediction_logs", {}).get("symbol") == symbol]
        
        return {
            "count": len(analyses),
            "data": analyses
        }
        
    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/learning-feedback")
async def get_learning_feedback(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    active_only: bool = Query(True, description="Only active feedback")
):
    """Get learning feedback rules that affect predictions."""
    from database.supabase_client import get_supabase_client, is_db_available
    
    if not is_db_available():
        return {"error": "Database not available", "data": []}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available", "data": []}
    
    try:
        query = client.table("learning_feedback").select("*").order("created_at", desc=True)
        
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.execute()
        feedbacks = result.get("data") or []
        
        if symbol:
            feedbacks = [f for f in feedbacks if f.get("symbol") is None or f.get("symbol") == symbol]
        
        return {
            "count": len(feedbacks),
            "data": feedbacks
        }
        
    except Exception as e:
        return {"error": str(e), "data": []}


@router.post("/trigger-error-analysis")
async def trigger_error_analysis(
    hours_ago: int = Query(4, ge=1, le=48, description="Analyze predictions older than X hours"),
    limit: int = Query(5, ge=1, le=20)
):
    """Manually trigger error analysis for failed predictions."""
    from services.error_analysis_service import check_and_analyze_failed_predictions
    
    try:
        analyses = await check_and_analyze_failed_predictions(hours_ago=hours_ago, limit=limit)
        return {
            "success": True,
            "analyzed_count": len(analyses),
            "analyses": analyses
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/self-learning-status")
async def get_self_learning_status(symbol: Optional[str] = Query(None)):
    """Get overall status of the self-learning system."""
    from database.supabase_client import get_supabase_client, is_db_available
    
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}
    
    try:
        # Count predictions
        pred_result = client.table("prediction_logs").select("id", count="exact").execute()
        total_predictions = len(pred_result.get("data") or [])
        
        # Count outcomes
        out_result = client.table("outcome_results").select("id", count="exact").execute()
        total_outcomes = len(out_result.get("data") or [])
        
        # Count error analyses
        err_result = client.table("error_analysis").select("id", count="exact").execute()
        total_error_analyses = len(err_result.get("data") or [])
        
        # Count active feedback rules
        fb_result = client.table("learning_feedback").select("id").eq("is_active", True).execute()
        active_feedback_rules = len(fb_result.get("data") or [])
        
        # Get recent error types distribution
        recent_errors = client.table("error_analysis").select(
            "error_type, is_fake_move"
        ).order("created_at", desc=True).limit(50).execute()
        
        error_distribution = {}
        fake_move_count = 0
        for e in (recent_errors.get("data") or []):
            et = e.get("error_type", "unknown")
            error_distribution[et] = error_distribution.get(et, 0) + 1
            if e.get("is_fake_move"):
                fake_move_count += 1
        
        return {
            "system_active": True,
            "total_predictions": total_predictions,
            "total_outcomes": total_outcomes,
            "total_error_analyses": total_error_analyses,
            "active_feedback_rules": active_feedback_rules,
            "recent_error_distribution": error_distribution,
            "fake_move_rate": round(fake_move_count / max(1, len(recent_errors.get("data") or [])), 2),
            "learning_coverage": round(total_error_analyses / max(1, total_outcomes) * 100, 1)
        }
        
    except Exception as e:
        return {"error": str(e)}


# ============================================
# ADAPTIVE TP/SL ENDPOINTS
# ============================================

class AdaptiveTPSLRequest(BaseModel):
    symbol: str
    direction: str
    entry_price: float


class AdaptiveTPSLResponse(BaseModel):
    entry: float
    tp1: float
    tp2: float
    tp3: float
    stop_loss: float
    confidence: float
    reasoning: List[str]
    fib_levels: dict
    key_levels: List[dict]
    learned_adjustments: dict


@router.post("/adaptive-tp-sl", response_model=AdaptiveTPSLResponse)
async def get_adaptive_tp_sl(request: AdaptiveTPSLRequest):
    """
    Calculate adaptive TP/SL levels based on:
    - Current market structure (S/R levels)
    - Fibonacci retracement/extension
    - RSI and volume analysis
    - Historical failure patterns (learned adjustments)
    
    This endpoint learns from past failures and adjusts recommendations.
    """
    # Calculate adaptive levels
    result = await calculate_adaptive_tp_sl(
        symbol=request.symbol,
        direction=request.direction,
        entry_price=request.entry_price
    )
    
    # Get learned adjustments from historical failures
    learned = await get_learned_adjustments(request.symbol, request.direction)
    
    # Apply learned confidence modifier
    adjusted_confidence = result.confidence + learned.get("confidence_modifier", 0)
    adjusted_confidence = min(95, max(30, adjusted_confidence))
    
    return AdaptiveTPSLResponse(
        entry=result.entry,
        tp1=result.tp1,
        tp2=result.tp2,
        tp3=result.tp3,
        stop_loss=result.stop_loss,
        confidence=adjusted_confidence,
        reasoning=result.reasoning,
        fib_levels=result.fib_levels,
        key_levels=result.key_levels,
        learned_adjustments=learned
    )


@router.get("/failure-patterns")
async def get_failure_patterns(
    symbol: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get historical failure patterns for analysis.
    Shows why trades failed at certain levels.
    """
    if not is_db_available():
        return {"error": "Database not available", "patterns": []}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available", "patterns": []}
    
    try:
        query = client.table("failure_analyses").select("*")
        
        if symbol:
            query = query.eq("symbol", symbol)
        if direction:
            query = query.eq("direction", direction)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        patterns = result.get("data") or []
        
        # Aggregate failure reasons
        reason_stats = {}
        for p in patterns:
            for reason in (p.get("failure_reason") or "").split("|"):
                if reason:
                    reason_stats[reason] = reason_stats.get(reason, 0) + 1
        
        return {
            "patterns": patterns,
            "count": len(patterns),
            "reason_stats": reason_stats
        }
        
    except Exception as e:
        return {"error": str(e), "patterns": []}


@router.get("/tp-success-analysis")
async def get_tp_success_analysis(
    symbol: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90)
):
    """
    Analyze which TP levels are most successful and at what conditions.
    Returns insights for dynamic TP optimization.
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}
    
    try:
        from datetime import datetime, timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        
        query = client.table("multi_target_outcomes").select("*").gte("created_at", cutoff)
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        result = query.execute()
        outcomes = result.get("data") or []
        
        if not outcomes:
            return {
                "total": 0,
                "tp_analysis": {},
                "optimal_tp": None,
                "recommendations": []
            }
        
        # Analyze each TP level
        tp_stats = {
            "tp1": {"hit": 0, "total": 0},
            "tp2": {"hit": 0, "total": 0},
            "tp3": {"hit": 0, "total": 0},
            "sl": {"hit": 0, "total": 0}
        }
        
        for o in outcomes:
            for tp in ["tp1", "tp2", "tp3"]:
                if o.get(f"{tp}_hit") is not None:
                    tp_stats[tp]["total"] += 1
                    if o.get(f"{tp}_hit"):
                        tp_stats[tp]["hit"] += 1
            
            if o.get("sl_hit") is not None:
                tp_stats["sl"]["total"] += 1
                if o.get("sl_hit"):
                    tp_stats["sl"]["hit"] += 1
        
        # Calculate success rates
        tp_analysis = {}
        for tp, stats in tp_stats.items():
            if stats["total"] > 0:
                tp_analysis[tp] = {
                    "success_rate": round(stats["hit"] / stats["total"] * 100, 1),
                    "hit_count": stats["hit"],
                    "total": stats["total"]
                }
        
        # Determine optimal TP (highest success rate with good volume)
        optimal_tp = None
        best_score = 0
        for tp in ["tp1", "tp2", "tp3"]:
            if tp in tp_analysis:
                # Score = success_rate * log(total) to balance rate and volume
                import math
                score = tp_analysis[tp]["success_rate"] * math.log(tp_analysis[tp]["total"] + 1)
                if score > best_score:
                    best_score = score
                    optimal_tp = tp
        
        # Generate recommendations
        recommendations = []
        if tp_analysis.get("tp1", {}).get("success_rate", 0) > 80:
            recommendations.append("TP1 has high success - consider taking partial profits here")
        if tp_analysis.get("tp3", {}).get("success_rate", 0) < 40:
            recommendations.append("TP3 rarely hit - consider using TP2 as final target")
        if tp_analysis.get("sl", {}).get("success_rate", 0) > 30:
            recommendations.append("High SL hit rate - consider wider stops or better entries")
        
        return {
            "total": len(outcomes),
            "tp_analysis": tp_analysis,
            "optimal_tp": optimal_tp,
            "recommendations": recommendations,
            "period_days": days
        }
        
    except Exception as e:
        return {"error": str(e)}
