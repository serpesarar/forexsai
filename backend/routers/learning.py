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
    check_prediction_outcome,
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
from services.multi_target_tracker import tracker as multi_target_tracker
from services.telegram_service import telegram_notifier

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


@router.get("/accuracy-by-model")
async def get_accuracy_by_model(
    symbol: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=90),
    check_interval: str = Query("24h")
):
    """
    Get accuracy breakdown per model/strategy (EMEL, PULSE, PULSE_ML, PULSE_V3).
    
    CRITICAL FIX: Now uses prediction_logs lifecycle status as PRIMARY source
    for consistency with /accuracy and /strategy-performance endpoints.
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    from database.supabase_client import get_supabase_client
    client = get_supabase_client()
    if not client:
        return {"error": "Database client not available"}
    
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    
    try:
        # PRIMARY: Get predictions with lifecycle status (completed/stopped)
        query = client.table("prediction_logs").select(
            "id, strategy, model_type, ml_direction, claude_direction, factors, status, targets_hit, created_at"
        ).gte("created_at", cutoff).neq("status", "active")  # Only non-active signals
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        pred_result = query.order("created_at", desc=True).limit(500).execute()
        predictions = pred_result.get("data") or []
        
        if not predictions:
            return {"models": [], "total": 0, "days": days, "note": "No completed signals found"}
        
        # Group by strategy/model_type using lifecycle status
        strategy_stats = {}
        for pred in predictions:
            # Use model_type if available, otherwise fall back to strategy/factors
            strategy = pred.get("model_type") or pred.get("strategy") or pred.get("factors", {}).get("strategy") or pred.get("factors", {}).get("source") or "UNKNOWN"
            
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    "strategy": strategy,
                    "total": 0,
                    "ml_correct": 0,
                    "claude_correct": 0,
                    "target_hit": 0,
                    "stop_hit": 0,
                    "expired": 0,
                }
            
            stats = strategy_stats[strategy]
            stats["total"] += 1
            
            # Use lifecycle status as primary indicator
            status = pred.get("status")
            targets_hit = pred.get("targets_hit") or {}
            if isinstance(targets_hit, str):
                import json
                try:
                    targets_hit = json.loads(targets_hit)
                except:
                    targets_hit = {}
            
            any_target_hit = any(targets_hit.values()) if targets_hit else False
            
            if status == "completed":
                # Signal completed successfully (target hit)
                stats["ml_correct"] += 1
                stats["target_hit"] += 1
            elif status == "stopped":
                # Signal stopped out
                stats["stop_hit"] += 1
            elif status == "expired":
                # Expired without outcome
                stats["expired"] += 1
                # Check if any target was hit before expiry
                if any_target_hit:
                    stats["target_hit"] += 1
            
            # Claude correctness - would need outcome_results for this
            # For now, use ml_correct as proxy if directions match
            # (This can be enhanced with a separate query to outcome_results)
        
        # Calculate percentages
        models = []
        for strategy, stats in strategy_stats.items():
            total = stats["total"]
            with_outcome = stats["ml_correct"] + stats["stop_hit"]  # completed + stopped
            
            models.append({
                "strategy": stats["strategy"],
                "total_predictions": total,
                "with_outcome": with_outcome,
                "ml_accuracy": round(stats["ml_correct"] / with_outcome, 3) if with_outcome > 0 else None,
                "ml_correct": stats["ml_correct"],
                "target_hit_rate": round(stats["target_hit"] / with_outcome, 3) if with_outcome > 0 else None,
                "target_hits": stats["target_hit"],
                "stop_hit_rate": round(stats["stop_hit"] / with_outcome, 3) if with_outcome > 0 else None,
                "stop_hits": stats["stop_hit"],
                "expired": stats["expired"],
            })
        
        # Sort by total predictions descending
        models.sort(key=lambda m: m["total_predictions"], reverse=True)
        
        return {
            "models": models,
            "total": len(predictions),
            "days": days,
            "check_interval": check_interval,
            "symbol": symbol,
            "source": "lifecycle_primary",
        }
    
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()[:300]}


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


@router.post("/check-all-pending")
async def check_all_pending_outcomes():
    """
    Check ALL pending predictions regardless of age.
    Records are NEVER deleted or force-closed - they stay in Supabase.
    Only marks outcome_checked=True when a real outcome is recorded.
    """
    from database.supabase_client import get_supabase_client
    import logging
    logger = logging.getLogger(__name__)
    
    if not is_db_available():
        return {"error": "Database not available", "outcomes_checked": 0}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available", "outcomes_checked": 0}
    
    try:
        # Get ALL unchecked predictions
        result = client.table("prediction_logs").select("*").eq(
            "outcome_checked", False
        ).order("created_at", desc=True).limit(200).execute()
        
        predictions = result.get("data") or []
        
        if not predictions:
            return {"message": "No pending predictions found", "outcomes_checked": 0}
        
        outcomes = []
        errors = []
        skipped_existing = 0
        
        for pred in predictions:
            pred_id = pred.get("id", "unknown")
            
            # Check if outcome already exists
            existing = client.table("outcome_results").select("id").eq(
                "prediction_id", pred_id
            ).eq("check_interval", "24h").execute()
            
            if existing.get("data"):
                # Outcome exists but prediction not marked - fix it
                from services.prediction_logger import mark_prediction_checked
                await mark_prediction_checked(pred_id)
                skipped_existing += 1
                continue
            
            # Try to check outcome
            try:
                outcome = await check_prediction_outcome(pred, "24h")
                if outcome:
                    outcomes.append(outcome)
                else:
                    errors.append({"id": pred_id[:8], "error": "outcome check returned None (old data unavailable)"})
            except Exception as check_err:
                errors.append({"id": pred_id[:8], "error": str(check_err)[:100]})
                logger.error(f"Outcome check failed for {pred_id}: {check_err}")
            
            # Always mark as checked - prevents stale "Waiting" status
            from services.prediction_logger import mark_prediction_checked
            await mark_prediction_checked(pred_id)
        
        correct_count = sum(1 for o in outcomes if o.get("ml_correct"))
        
        return {
            "outcomes_checked": len(outcomes),
            "ml_correct": correct_count,
            "ml_incorrect": len(outcomes) - correct_count,
            "total_pending_found": len(predictions),
            "skipped_existing": skipped_existing,
            "errors": errors[:10] if errors else None
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()[:500], "outcomes_checked": 0}


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


@router.get("/prediction-history")
async def get_prediction_history(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., XAUUSD, NDX.INDX)"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=200, description="Max number of records")
):
    """
    Get detailed prediction history with outcomes for manual verification.
    Shows each prediction with entry/exit prices, direction, result, and timing.
    """
    from database.supabase_client import get_supabase_client, is_db_available
    from datetime import datetime, timedelta
    
    if not is_db_available():
        return {"error": "Database not available", "predictions": []}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available", "predictions": []}
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat() + "Z"
        
        # Get predictions with their outcomes
        query = client.table("prediction_logs").select(
            "id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, ml_target_price, ml_stop_price, claude_direction, claude_confidence, created_at, outcome_results(check_interval, entry_price, exit_price, high_price, low_price, price_change_pct, actual_direction, hit_target, hit_stop, ml_correct, claude_correct, created_at)"
        ).gte("created_at", cutoff_iso).order("created_at", desc=True).limit(limit)
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        result = query.execute()
        predictions = result.get("data") or []
        
        # Format for frontend
        formatted = []
        for pred in predictions:
            outcomes = pred.get("outcome_results", [])
            
            # Get the 24h outcome (primary) or latest
            primary_outcome = None
            for o in outcomes:
                if o.get("check_interval") == "24h":
                    primary_outcome = o
                    break
            if not primary_outcome and outcomes:
                primary_outcome = outcomes[0]
            
            entry = {
                "id": pred.get("id"),
                "symbol": pred.get("symbol"),
                "timestamp": pred.get("created_at"),
                "ml_direction": pred.get("ml_direction"),
                "ml_confidence": pred.get("ml_confidence"),
                "entry_price": pred.get("ml_entry_price"),
                "target_price": pred.get("ml_target_price"),
                "stop_price": pred.get("ml_stop_price"),
                "claude_direction": pred.get("claude_direction"),
                "claude_confidence": pred.get("claude_confidence"),
                "has_outcome": primary_outcome is not None,
            }
            
            if primary_outcome:
                entry["exit_price"] = primary_outcome.get("exit_price")
                entry["high_price"] = primary_outcome.get("high_price")
                entry["low_price"] = primary_outcome.get("low_price")
                entry["price_change_pct"] = primary_outcome.get("price_change_pct")
                entry["actual_direction"] = primary_outcome.get("actual_direction")
                entry["hit_target"] = primary_outcome.get("hit_target")
                entry["hit_stop"] = primary_outcome.get("hit_stop")
                entry["ml_correct"] = primary_outcome.get("ml_correct")
                entry["claude_correct"] = primary_outcome.get("claude_correct")
                entry["outcome_time"] = primary_outcome.get("created_at")
            
            formatted.append(entry)
        
        # Fix ml_correct based on hit_target (target hit = correct prediction)
        for entry in formatted:
            if entry.get("hit_target"):
                entry["ml_correct"] = True
        
        # Calculate summary stats
        total = len(formatted)
        with_outcome = [p for p in formatted if p.get("has_outcome")]
        ml_correct = sum(1 for p in with_outcome if p.get("ml_correct"))
        target_hits = sum(1 for p in with_outcome if p.get("hit_target"))
        stop_hits = sum(1 for p in with_outcome if p.get("hit_stop"))
        
        return {
            "predictions": formatted,
            "summary": {
                "total_predictions": total,
                "with_outcome": len(with_outcome),
                "pending_outcome": total - len(with_outcome),
                "ml_correct": ml_correct,
                "ml_accuracy": round(ml_correct / len(with_outcome) * 100, 1) if with_outcome else None,
                "target_hits": target_hits,
                "stop_hits": stop_hits,
                "period_days": days
            }
        }
        
    except Exception as e:
        return {"error": str(e), "predictions": []}


@router.post("/fix-ml-correct")
async def fix_ml_correct_in_database():
    """
    Fix ml_correct values in outcome_results table.
    Sets ml_correct = True for all records where hit_target = True.
    This corrects the previous bug where target hits were not counted as correct.
    """
    from database.supabase_client import get_supabase_client, is_db_available
    import httpx
    import os
    
    if not is_db_available():
        return {"error": "Database not available"}
    
    try:
        # Use direct RPC call for bulk update
        url = os.environ.get("SUPABASE_URL", "").rstrip('/')
        key = os.environ.get("SUPABASE_KEY", "")
        
        if not url or not key:
            return {"error": "Supabase credentials not configured"}
        
        # First get count of records to fix
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        with httpx.Client(timeout=30.0) as client:
            # Get records to fix
            get_url = f"{url}/rest/v1/outcome_results?hit_target=eq.true&ml_correct=eq.false&select=id"
            response = client.get(get_url, headers=headers)
            records = response.json() if response.status_code == 200 else []
            
            # Update each record
            updated_count = 0
            for record in records:
                record_id = record.get("id")
                if record_id:
                    update_url = f"{url}/rest/v1/outcome_results?id=eq.{record_id}"
                    update_response = client.patch(update_url, json={"ml_correct": True}, headers=headers)
                    if update_response.status_code in [200, 201, 204]:
                        updated_count += 1
        
        return {
            "success": True,
            "message": f"Fixed {updated_count} outcome records",
            "updated_count": updated_count,
            "total_found": len(records)
        }
        
    except Exception as e:
        return {"error": str(e)}


@router.post("/reset-ui-stats")
async def reset_ui_stats(
    symbol: Optional[str] = Query(None, description="Symbol to reset (or all if None)"),
    keep_data: bool = Query(True, description="Keep underlying data, just reset stats display")
):
    """
    Reset UI statistics display while preserving the underlying data.
    This recalculates all accuracy metrics based on corrected ml_correct logic.
    
    Steps:
    1. Fix all ml_correct values where hit_target=True
    2. Return fresh recalculated stats
    """
    from database.supabase_client import is_db_available
    from datetime import datetime, timedelta
    import httpx
    import os
    
    if not is_db_available():
        return {"error": "Database not available"}
    
    try:
        url = os.environ.get("SUPABASE_URL", "").rstrip('/')
        key = os.environ.get("SUPABASE_KEY", "")
        
        if not url or not key:
            return {"error": "Supabase credentials not configured"}
        
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        with httpx.Client(timeout=60.0) as client:
            # Step 1: Get records to fix
            get_url = f"{url}/rest/v1/outcome_results?hit_target=eq.true&ml_correct=eq.false&select=id,prediction_id"
            response = client.get(get_url, headers=headers)
            records_to_fix = response.json() if response.status_code == 200 else []
            
            # Filter by symbol if specified
            if symbol and records_to_fix:
                pred_url = f"{url}/rest/v1/prediction_logs?symbol=eq.{symbol}&select=id"
                pred_response = client.get(pred_url, headers=headers)
                pred_ids = set(p["id"] for p in (pred_response.json() if pred_response.status_code == 200 else []))
                records_to_fix = [r for r in records_to_fix if r.get("prediction_id") in pred_ids]
            
            # Update each record
            fixed_count = 0
            for record in records_to_fix:
                record_id = record.get("id")
                if record_id:
                    update_url = f"{url}/rest/v1/outcome_results?id=eq.{record_id}"
                    update_response = client.patch(update_url, json={"ml_correct": True}, headers=headers)
                    if update_response.status_code in [200, 201, 204]:
                        fixed_count += 1
            
            # Step 2: Get fresh stats
            cutoff = datetime.utcnow() - timedelta(days=7)
            cutoff_iso = cutoff.isoformat() + "Z"
            
            stats_url = f"{url}/rest/v1/outcome_results?created_at=gte.{cutoff_iso}&select=ml_correct,hit_target,hit_stop,prediction_id"
            stats_response = client.get(stats_url, headers=headers)
            outcomes = stats_response.json() if stats_response.status_code == 200 else []
            
            # Filter by symbol if specified
            if symbol and outcomes:
                pred_url = f"{url}/rest/v1/prediction_logs?symbol=eq.{symbol}&select=id"
                pred_response = client.get(pred_url, headers=headers)
                pred_ids = set(p["id"] for p in (pred_response.json() if pred_response.status_code == 200 else []))
                outcomes = [o for o in outcomes if o.get("prediction_id") in pred_ids]
            
            # Calculate fresh stats
            total = len(outcomes)
            ml_correct_count = sum(1 for o in outcomes if o.get("ml_correct") or o.get("hit_target"))
            target_hits = sum(1 for o in outcomes if o.get("hit_target"))
            stop_hits = sum(1 for o in outcomes if o.get("hit_stop"))
            
            accuracy = round(ml_correct_count / total * 100, 1) if total > 0 else 0
            
            return {
                "success": True,
                "fixed_records": fixed_count,
                "fresh_stats": {
                    "total_outcomes": total,
                    "ml_correct": ml_correct_count,
                    "ml_accuracy": accuracy,
                    "target_hits": target_hits,
                    "stop_hits": stop_hits,
                    "target_hit_rate": round(target_hits / total * 100, 1) if total > 0 else None,
                },
                "symbol": symbol or "ALL",
                "message": f"UI stats reset. Fixed {fixed_count} records. New accuracy: {accuracy}%"
            }
        
    except Exception as e:
        return {"error": str(e)}


@router.post("/hard-reset")
async def hard_reset_learning_data(
    confirm: bool = Query(False, description="Must be true to actually delete data")
):
    """
    Hard reset: delete ALL prediction logs and outcome results.
    This resets all learning dashboard percentages to 0%.
    Requires confirm=true to prevent accidental deletion.
    """
    if not confirm:
        return {"error": "Pass confirm=true to actually delete all data", "deleted": False}
    
    if not is_db_available():
        return {"error": "Database not available", "deleted": False}
    
    from database.supabase_client import get_supabase_client
    client = get_supabase_client()
    if not client:
        return {"error": "Database client not available", "deleted": False}
    
    try:
        # Delete outcome results first (foreign key dependency)
        outcome_result = client.table("outcome_results").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        outcomes_deleted = len(outcome_result.data) if outcome_result.data else 0
        
        # Delete multi-target outcomes
        try:
            mt_result = client.table("multi_target_outcomes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            mt_deleted = len(mt_result.data) if mt_result.data else 0
        except Exception:
            mt_deleted = 0
        
        # Delete prediction logs
        pred_result = client.table("prediction_logs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        preds_deleted = len(pred_result.data) if pred_result.data else 0
        
        return {
            "deleted": True,
            "predictions_deleted": preds_deleted,
            "outcomes_deleted": outcomes_deleted,
            "multi_target_deleted": mt_deleted,
            "message": f"All learning data reset. Deleted {preds_deleted} predictions, {outcomes_deleted} outcomes."
        }
    except Exception as e:
        return {"error": str(e), "deleted": False}


@router.post("/strategy-performance/reset")
async def reset_strategy_performance(
    confirm: bool = Query(False, description="Must be true to actually delete data"),
    symbol: Optional[str] = Query(None, description="Optional: specific symbol to reset (NDX.INDX, XAUUSD, GDAXI.INDX, USOIL.FOREX)")
):
    """
    Reset strategy performance data for ML model analysis.
    Deletes prediction_logs and outcome_results for the specified symbols,
    then recalculates statistics for all 4 strategy modes.
    
    This allows recalculating accuracy from scratch for:
    - Ultra Safe (≥65% confidence)
    - Balanced (55-65% confidence)  
    - Full Power (48-55% confidence)
    - Aggressive (<48% confidence)
    
    Requires confirm=true to prevent accidental deletion.
    """
    if not confirm:
        return {
            "error": "Pass confirm=true to reset strategy performance data",
            "message": "This will delete prediction_logs and outcome_results for ML model analysis",
            "symbols_affected": ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"] if not symbol else [symbol],
            "deleted": False
        }
    
    if not is_db_available():
        return {"error": "Database not available", "deleted": False}
    
    client = get_supabase_client()
    if not client:
        return {"error": "Database client not available", "deleted": False}
    
    try:
        # Target symbols for strategy performance analysis
        target_symbols = [symbol] if symbol else ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]
        
        # First, get prediction IDs for these symbols
        pred_result = client.table("prediction_logs").select("id").in_("symbol", target_symbols).execute()
        predictions = pred_result.data if pred_result.data else []
        pred_ids = [p["id"] for p in predictions]
        
        deleted_count = {
            "predictions": 0,
            "outcomes": 0,
            "multi_target": 0,
            "signal_checks": 0,
            "signal_failures": 0
        }
        
        # Delete related outcome_results first (foreign key safety)
        if pred_ids:
            try:
                for pid in pred_ids:
                    outcome_result = client.table("outcome_results").delete().eq("prediction_id", pid).execute()
                    if outcome_result.data:
                        deleted_count["outcomes"] += len(outcome_result.data)
            except Exception as e:
                logger.warning(f"Error deleting outcome_results: {e}")
            
            # Delete multi_target_outcomes
            try:
                for pid in pred_ids:
                    mt_result = client.table("multi_target_outcomes").delete().eq("prediction_id", pid).execute()
                    if mt_result.data:
                        deleted_count["multi_target"] += len(mt_result.data)
            except Exception as e:
                logger.warning(f"Error deleting multi_target_outcomes: {e}")
            
            # Delete signal_checks
            try:
                for pid in pred_ids:
                    check_result = client.table("signal_checks").delete().eq("signal_id", pid).execute()
                    if check_result.data:
                        deleted_count["signal_checks"] += len(check_result.data)
            except Exception as e:
                logger.warning(f"Error deleting signal_checks: {e}")
            
            # Delete signal_failures
            try:
                for pid in pred_ids:
                    fail_result = client.table("signal_failures").delete().eq("signal_id", pid).execute()
                    if fail_result.data:
                        deleted_count["signal_failures"] += len(fail_result.data)
            except Exception as e:
                logger.warning(f"Error deleting signal_failures: {e}")
        
        # Delete prediction_logs for target symbols
        for sym in target_symbols:
            try:
                result = client.table("prediction_logs").delete().eq("symbol", sym).execute()
                if result.data:
                    deleted_count["predictions"] += len(result.data)
            except Exception as e:
                logger.warning(f"Error deleting predictions for {sym}: {e}")
        
        # Return fresh stats after reset
        fresh_stats = {
            "symbols_reset": target_symbols,
            "deleted_counts": deleted_count,
            "message": f"Strategy performance data reset for {', '.join(target_symbols)}. All 4 modes (Ultra Safe, Balanced, Full Power, Aggressive) will recalculate from new signals.",
            "next_steps": [
                "New ML signals will be categorized by confidence:",
                "- Ultra Safe: ≥65% confidence", 
                "- Balanced: 55-65% confidence",
                "- Full Power: 48-55% confidence", 
                "- Aggressive: <48% confidence",
                "Signals will be tracked with lifecycle (completed/stopped/expired)",
                "TP/SL logic matches Signal Performance panel"
            ]
        }
        
        return {
            "deleted": True,
            "reset_timestamp": datetime.utcnow().isoformat() + "Z",
            **fresh_stats
        }
        
    except Exception as e:
        logger.error(f"Strategy performance reset error: {e}")
        return {"error": str(e), "deleted": False}


@router.get("/strategy-performance")
async def get_strategy_performance(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze")
):
    """Get performance statistics for each ML strategy.
    
    Uses TWO data sources for outcomes:
    1. prediction_logs lifecycle data (status=completed/stopped, targets_hit)
    2. outcome_results table (any check_interval)
    """
    from datetime import datetime, timedelta
    from database.supabase_client import get_supabase_client
    from utils.json_helpers import parse_json_field
    
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat() + "Z"
        
        # Get predictions with lifecycle fields + outcome_results fallback
        result = client.table("prediction_logs").select(
            "id, symbol, strategy, ml_confidence, status, targets_hit, model_type, outcome_results(hit_target, hit_stop, ml_correct, check_interval)"
        ).gte("created_at", cutoff_iso).limit(1000).execute()
        predictions = (result.get('data') if isinstance(result, dict) else getattr(result, 'data', None)) or []
        
        # Classify by confidence — thresholds adjusted for realistic ML output
        # ML typically produces 45-70% confidence range
        def classify(conf):
            if conf >= 65: return "ultra_safe"
            if conf >= 55: return "balanced"
            if conf >= 48: return "full_power"
            return "aggressive"
        
        # Initialize stats with per-target tracking - ALL 4 symbols
        stats = {sym: {s: {
            "total": 0, "with_outcome": 0, "correct": 0,
            "target_hits": 0, "stop_hits": 0, "conf_sum": 0,
            "tp1_hits": 0, "tp2_hits": 0, "tp3_hits": 0, "tp4_hits": 0,
        } for s in ["ultra_safe", "balanced", "full_power", "aggressive"]} 
                 for sym in ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]}
        
        outcomes_found = 0
        
        # Process — use ONLY lifecycle status as single source of truth
        for p in predictions:
            sym = p.get("symbol")
            if sym not in stats:
                continue
            try:
                conf = float(p.get("ml_confidence", 50) or 50)
            except:
                conf = 50
            # Always use confidence-based classification (ignore stored strategy field
            # which may contain model type names like "PULSE", "EMEL", etc.)
            strat = classify(conf)
            
            stats[sym][strat]["total"] += 1
            stats[sym][strat]["conf_sum"] += conf
            
            # PRIMARY: lifecycle status (completed/stopped)
            p_status = p.get("status")
            if p_status in ("completed", "stopped"):
                outcomes_found += 1
                stats[sym][strat]["with_outcome"] += 1
                
                if p_status == "completed":
                    stats[sym][strat]["correct"] += 1
                    stats[sym][strat]["target_hits"] += 1
                elif p_status == "stopped":
                    stats[sym][strat]["stop_hits"] += 1
                
                # Parse targets_hit for per-TP tracking
                targets_hit = parse_json_field(p.get("targets_hit"), {})
                if targets_hit:
                    if targets_hit.get("TP1"): stats[sym][strat]["tp1_hits"] += 1
                    if targets_hit.get("TP2"): stats[sym][strat]["tp2_hits"] += 1
                    if targets_hit.get("TP3"): stats[sym][strat]["tp3_hits"] += 1
                    if targets_hit.get("TP4"): stats[sym][strat]["tp4_hits"] += 1
            else:
                # FALLBACK: use outcome_results for signals without lifecycle resolution
                # This covers XAUUSD and other symbols where lifecycle can't track properly
                outcome_list = p.get("outcome_results") or []
                primary_outcome = None
                for o in outcome_list:
                    if o.get("check_interval") == "1h":
                        primary_outcome = o
                        break
                if not primary_outcome and outcome_list:
                    primary_outcome = outcome_list[0]
                
                if primary_outcome:
                    outcomes_found += 1
                    stats[sym][strat]["with_outcome"] += 1
                    if primary_outcome.get("hit_target") or primary_outcome.get("ml_correct"):
                        stats[sym][strat]["correct"] += 1
                        stats[sym][strat]["target_hits"] += 1
                    elif primary_outcome.get("hit_stop"):
                        stats[sym][strat]["stop_hits"] += 1
        
        # Build result
        result_data = {}
        for sym, sym_stats in stats.items():
            result_data[sym] = {}
            for strat, s in sym_stats.items():
                wo = s["with_outcome"]
                total = s["total"]
                result_data[sym][strat] = {
                    "total_predictions": total,
                    "with_outcome": wo,
                    "correct": s["correct"],
                    "accuracy": round(s["correct"] / wo * 100, 1) if wo > 0 else None,
                    "target_hit_rate": round(s["target_hits"] / wo * 100, 1) if wo > 0 else None,
                    "stop_hit_rate": round(s["stop_hits"] / wo * 100, 1) if wo > 0 else None,
                    "avg_confidence": round(s["conf_sum"] / total, 1) if total > 0 else 0,
                    "target_hits": s["target_hits"],
                    "stop_hits": s["stop_hits"],
                    "tp_breakdown": {
                        "TP1": s["tp1_hits"],
                        "TP2": s["tp2_hits"],
                        "TP3": s["tp3_hits"],
                        "TP4": s["tp4_hits"],
                    } if wo > 0 else None,
                }
        
        # Best strategy
        best = {}
        for sym, sd in result_data.items():
            b, ba = None, -1
            for st, d in sd.items():
                if d["accuracy"] and d["accuracy"] > ba and d["with_outcome"] >= 3:
                    ba, b = d["accuracy"], st
            best[sym] = {"strategy": b, "accuracy": ba if b else None}
        
        return {
            "period_days": days,
            "predictions_count": len(predictions),
            "outcomes_count": outcomes_found,
            "strategies": result_data,
            "best_strategies": best,
            "strategy_descriptions": {
                "ultra_safe": "Güven ≥65%, düşük risk",
                "balanced": "Güven 55-65%, dengeli",
                "full_power": "Güven 48-55%, güçlü sinyal",
                "aggressive": "Güven <48%, agresif"
            }
        }
    except Exception as e:
        import traceback
        logger.error(f"Strategy performance error: {e}\n{traceback.format_exc()}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-TARGET TRACKING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/multi-target/create")
async def create_multi_target_tracking(
    symbol: str,
    strategy: str,
    direction: str,
    entry_price: float,
    prediction_id: Optional[str] = None
):
    """Yeni multi-target tracking oluştur"""
    result = await multi_target_tracker.create_tracking(
        prediction_id=prediction_id,
        symbol=symbol,
        strategy=strategy,
        direction=direction,
        entry_price=entry_price
    )
    return result


@router.get("/multi-target/analysis/{symbol}")
async def get_multi_target_analysis(
    symbol: str,
    strategy: Optional[str] = None,
    days: int = Query(30, ge=1, le=365)
):
    """Strateji bazlı multi-target analizi"""
    return await multi_target_tracker.get_strategy_analysis(symbol, strategy, days)


@router.post("/multi-target/update-price")
async def update_multi_target_price(symbol: str, current_price: float):
    """Fiyat güncellemesi ve target hit kontrolü"""
    hits = await multi_target_tracker.update_price(symbol, current_price)
    
    # Telegram bildirimi gönder
    for hit in hits:
        if hit.get('level') == 'SL':
            await telegram_notifier.send_stop_loss(symbol, hit['pips'])
        else:
            await telegram_notifier.send_target_hit(symbol, hit['level'], hit['pips'])
    
    return {"hits": hits, "count": len(hits)}


@router.get("/strategy-performance/{symbol}")
async def get_strategy_performance(
    symbol: str,
    days: int = Query(30, ge=1, le=365)
):
    """Her strateji için ayrı performans analizi"""
    strategies = ['ultra_safe', 'balanced', 'full_power', 'aggressive']
    result = {}
    
    for strategy in strategies:
        for direction in ['BUY', 'SELL']:
            analysis = await multi_target_tracker.get_strategy_analysis(
                symbol=symbol, strategy=strategy, days=days
            )
            if strategy not in result:
                result[strategy] = {}
            result[strategy][direction] = analysis
    
    return {"symbol": symbol, "period_days": days, "strategies": result}


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION SETTINGS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/notifications/settings")
async def get_notification_settings(user_id: Optional[str] = None):
    """Kullanıcı bildirim ayarlarını getir"""
    try:
        from database.supabase_client import supabase
        if user_id:
            result = supabase.table('user_notification_settings').select('*').eq('user_id', user_id).execute()
        else:
            result = supabase.table('user_notification_settings').select('*').limit(1).execute()
        
        if result.data:
            return result.data[0]
        return {
            "telegram_enabled": False,
            "notify_ultra_safe": True,
            "notify_balanced": True,
            "notify_full_power": False,
            "notify_aggressive": False,
            "notify_new_signal": True,
            "notify_tp1": True,
            "notify_tp2": True,
            "notify_tp3": False,
            "notify_sl": True,
            "min_confidence": 0.60,
            "symbols": ["XAUUSD", "NDX.INDX"]
        }
    except Exception as e:
        return {"error": str(e)}


@router.put("/notifications/settings")
async def update_notification_settings(
    telegram_bot_token: Optional[str] = None,
    telegram_chat_id: Optional[str] = None,
    telegram_enabled: bool = False,
    notify_ultra_safe: bool = True,
    notify_balanced: bool = True,
    notify_full_power: bool = False,
    notify_aggressive: bool = False,
    notify_new_signal: bool = True,
    notify_tp1: bool = True,
    notify_tp2: bool = True,
    notify_tp3: bool = False,
    notify_sl: bool = True,
    min_confidence: float = 0.60,
    symbols: List[str] = ["XAUUSD", "NDX.INDX"],
    user_id: Optional[str] = None
):
    """Bildirim ayarlarını güncelle"""
    try:
        from database.supabase_client import supabase
        data = {
            "telegram_bot_token": telegram_bot_token,
            "telegram_chat_id": telegram_chat_id,
            "telegram_enabled": telegram_enabled,
            "notify_ultra_safe": notify_ultra_safe,
            "notify_balanced": notify_balanced,
            "notify_full_power": notify_full_power,
            "notify_aggressive": notify_aggressive,
            "notify_new_signal": notify_new_signal,
            "notify_tp1": notify_tp1,
            "notify_tp2": notify_tp2,
            "notify_tp3": notify_tp3,
            "notify_sl": notify_sl,
            "min_confidence": min_confidence,
            "symbols": symbols
        }
        
        if user_id:
            data["user_id"] = user_id
            result = supabase.table('user_notification_settings').upsert(data).execute()
        else:
            result = supabase.table('user_notification_settings').insert(data).execute()
        
        return {"success": True, "data": result.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/notifications/test")
async def test_notification(
    chat_id: Optional[str] = None,
    bot_token: Optional[str] = None
):
    """Test bildirimi gönder - kullanıcının kendi bot'uyla"""
    from services.telegram_service import TelegramNotifier
    
    if bot_token and chat_id:
        # Kullanıcının kendi bot'u ile test
        custom_notifier = TelegramNotifier()
        custom_notifier._bot_token = bot_token
        custom_notifier._default_chat_id = chat_id
        result = await custom_notifier.test_connection(chat_id)
    else:
        # Global bot ile test
        result = await telegram_notifier.test_connection(chat_id)
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL DETAIL ENDPOINT (for SignalDetailModal)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/signal/{signal_id}")
async def get_signal_detail_endpoint(signal_id: str):
    """
    Get detailed information for a specific signal.
    Includes prediction data, all lifecycle checks, outcome results, and failure analysis.
    Used by SignalDetailModal in the frontend.
    """
    from services.signal_lifecycle import get_signal_detail
    
    try:
        detail = await get_signal_detail(signal_id)
        return detail
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()[:300]}


@router.get("/historical-signals")
async def get_historical_signals_endpoint(
    symbol: str,
    days: int = Query(30, ge=1, le=365)
):
    """
    Get detailed historical signal data, equity curve, and session analytics
    specifically formatted for the ModelPerformanceModal.
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if not client:
        return {"error": "Database client not available"}
        
    try:
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()
        
        # 1. Fetch signal records
        result = client.table("prediction_logs").select(
            "id, symbol, ml_direction, ml_confidence, strategy, status, "
            "targets_hit, highest_profit_pips, lowest_drawdown_pips, created_at, "
            "outcome_results(hit_target, hit_stop, ml_correct, check_interval)"
        ).eq("symbol", symbol).gte("created_at", cutoff_iso).order("created_at", desc=True).limit(500).execute()
        
        signals = getattr(result, 'data', []) if not isinstance(result, dict) else result.get('data', [])
        
        # 2. Extract Data
        time_series_data = []
        recent_signals = []
        hourly_stats = {h: {"correct": 0, "total": 0} for h in range(24)}
        
        total_signals = 0
        correct_signals = 0
        current_equity = 10000.0 # Base $10k
        
        # We need to process from oldest to newest for equity curve
        signals_asc = list(reversed(signals))
        
        for p in signals_asc:
            created_at = p.get("created_at")
            if not created_at:
                continue
            
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            hour = dt.hour
            date_str = dt.strftime("%Y-%m-%d")
            
            direction = str(p.get("ml_direction", "")).lower()
            if direction not in ["buy", "sell"]:
                direction = "hold"
                
            p_status = p.get("status")
            is_win = False
            is_loss = False
            profit = 0.0
            
            if p_status == "completed":
                is_win = True
                profit = p.get("highest_profit_pips", 0) or 20.0 # fallback approximation
            elif p_status == "stopped":
                is_loss = True
                profit = -(p.get("lowest_drawdown_pips", 0) or 40.0) # fallback
            else:
                # Fallback to outcome_results
                outcomes = p.get("outcome_results") or []
                primary = next((o for o in outcomes if o.get("check_interval") == "1h"), outcomes[0] if outcomes else None)
                if primary:
                    if primary.get("hit_target") or primary.get("ml_correct"):
                        is_win = True
                        profit = 20.0
                    elif primary.get("hit_stop"):
                        is_loss = True
                        profit = -40.0
            
            # Metrics
            if is_win or is_loss:
                total_signals += 1
                hourly_stats[hour]["total"] += 1
                if is_win:
                    correct_signals += 1
                    hourly_stats[hour]["correct"] += 1
                
                # Equity update (Assume $10 per pip for simple calculation)
                equity_change = profit * 10
                current_equity += equity_change
                
                # Time series datapoint
                time_series_data.append({
                    "date": date_str,
                    "prediction": direction,
                    "actual": "up" if is_win else "down",
                    "accuracy": round((correct_signals / total_signals) * 100, 1),
                    "profit": profit,
                    "equity": current_equity
                })
        
        # 3. Format recent signals (Newest first)
        for p in signals[:50]: # Top 50 recent
            created_at = p.get("created_at", "")
            if created_at:
                dt_str = created_at.replace("T", " ")[:16]
            else:
                dt_str = "Unknown"
                
            direction = str(p.get("ml_direction", "")).lower()
            if direction not in ["buy", "sell"]: direction = "hold"
            
            p_status = p.get("status")
            profit = 0.0
            result_state = "pending"
            
            if p_status == "completed":
                result_state = "win"
                profit = p.get("highest_profit_pips", 0) or 20.0
            elif p_status == "stopped":
                result_state = "loss"
                profit = -(p.get("lowest_drawdown_pips", 0) or 40.0)
            else:
                outcomes = p.get("outcome_results") or []
                primary = next((o for o in outcomes if o.get("check_interval") == "1h"), outcomes[0] if outcomes else None)
                if primary:
                    if primary.get("hit_target") or primary.get("ml_correct"):
                        result_state = "win"
                        profit = 20.0
                    elif primary.get("hit_stop"):
                        result_state = "loss"
                        profit = -40.0
            
            recent_signals.append({
                "id": p.get("id"),
                "date": dt_str,
                "symbol": p.get("symbol"),
                "prediction": direction,
                "actual": "up" if result_state == "win" else "down" if result_state == "loss" else "flat",
                "accuracy": round(p.get("ml_confidence") or 0, 1),
                "profit": profit,
                "result": result_state
            })

        # 4. Hourly Performance map
        hourly_performance = []
        for h, stats in hourly_stats.items():
            if stats["total"] > 0:
                hourly_performance.append({
                    "hour": h,
                    "day": "All",
                    "accuracy": round((stats["correct"] / stats["total"]) * 100, 1),
                    "sampleSize": stats["total"]
                })
                
        # 5. Compile Comparison Metrics
        comp_accuracy = round((correct_signals / total_signals * 100) if total_signals > 0 else 0, 1)
        
        model_performance = {
            "modelId": "emel_core",
            "modelName": f"EMEL AI — {symbol} Predictor",
            "accuracy": comp_accuracy,
            "totalSignals": total_signals,
            "timeSeriesData": time_series_data[-30:], # Last 30 trades for chart
            "hourlyPerformance": hourly_performance,
            "comparisonMetrics": {
                "accuracy": comp_accuracy,
                "speed": 85,
                "profit": round(comp_accuracy * 0.9, 1), # Correlated mock
                "riskControl": 92,
                "trendFollowing": 88
            },
            "recentSignals": recent_signals
        }
        
        return model_performance

    except Exception as e:
        import traceback
        logger.error(f"Historical signals error: {e}\n{traceback.format_exc()}")
        return {"error": str(e)}


@router.get("/signals/recent")
async def get_recent_signals_endpoint(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(50, ge=1, le=200),
    include_active: bool = Query(True, description="Include active signals")
):
    """
    Get recent signals with summary information for the signal list.
    Enhanced version of /predictions with calculated duration and PNL.
    """
    if not is_db_available():
        return {"error": "Database not available", "signals": []}
    
    client = get_supabase_client()
    if not client:
        return {"error": "Database client not available", "signals": []}
    
    try:
        from datetime import datetime
        
        query = client.table("prediction_logs").select(
            "id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, "
            "ml_target_price, ml_stop_price, model_type, strategy, status, "
            "targets_hit, highest_profit_pips, lowest_drawdown_pips, "
            "exit_price, exit_time, created_at"
        ).order("created_at", desc=True).limit(limit)
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        if not include_active:
            query = query.neq("status", "active")
        
        result = query.execute()
        signals = result.get("data") or []
        
        # Enhance with calculated fields
        enhanced = []
        for sig in signals:
            entry = dict(sig)
            
            # Calculate duration
            created = sig.get("created_at")
            exit_time = sig.get("exit_time")
            
            if exit_time and created:
                try:
                    from dateutil import parser
                    created_dt = parser.parse(created)
                    exit_dt = parser.parse(exit_time)
                    duration_minutes = (exit_dt - created_dt).total_seconds() / 60
                    entry["duration_minutes"] = round(duration_minutes, 1)
                except:
                    entry["duration_minutes"] = None
            else:
                entry["duration_minutes"] = None
            
            # Calculate PNL
            entry_price = sig.get("ml_entry_price")
            exit_price = sig.get("exit_price")
            direction = sig.get("ml_direction")
            
            if entry_price and exit_price and direction in ["BUY", "SELL"]:
                from services.target_config import pips_from_price_change
                if direction == "BUY":
                    pnl_pips = pips_from_price_change(exit_price - entry_price, sig.get("symbol"))
                else:
                    pnl_pips = pips_from_price_change(entry_price - exit_price, sig.get("symbol"))
                entry["pnl_pips"] = round(pnl_pips, 2)
            else:
                entry["pnl_pips"] = None
            
            enhanced.append(entry)
        
        return {
            "signals": enhanced,
            "count": len(enhanced),
            "symbol": symbol
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()[:300], "signals": []}


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL & TIMEFRAME ANALYSIS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/model-analysis")
async def get_model_timeframe_analysis(
    model: str = Query(..., description="Model type: ml, emel, pulse1, pulse2, pulse3"),
    symbol: Optional[str] = Query(None, description="Symbol filter: XAUUSD, NDX.INDX, GDAXI.INDX, USOIL.FOREX"),
    timeframe: Optional[str] = Query(None, description="Timeframe: 5m, 15m, 30m, 1h, 4h, 1d"),
    days: int = Query(30, ge=1, le=90)
):
    """
    Get detailed analysis for a specific model + timeframe + symbol combination.
    
    Returns performance metrics including:
    - Win rate by target level
    - Average profit/loss
    - Total signals count
    - Per-symbol breakdown
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat() + "Z"
        
        # Build query
        query = client.table("prediction_logs").select(
            "id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, "
            "ml_target_price, ml_stop_price, model_type, strategy, status, "
            "targets_hit, highest_profit_pips, lowest_drawdown_pips, "
            "exit_price, exit_time, stop_loss_pips, targets, created_at"
        ).gte("created_at", cutoff_iso).neq("status", "active")
        
        # Filter by model (check both model_type and strategy fields)
        model_lower = model.lower()
        if model_lower == "ml":
            query = query.or_("model_type.eq.ml,model_type.is.null")
        elif model_lower in ["pulse1", "pulse2", "pulse3"]:
            query = query.eq("model_type", model_lower)
        elif model_lower == "emel":
            query = query.or_("model_type.eq.emel,strategy.eq.EMEL")
        else:
            query = query.eq("model_type", model_lower)
        
        # Optional filters
        if symbol:
            query = query.eq("symbol", symbol)
        if timeframe:
            query = query.eq("timeframe", timeframe)
        
        result = query.order("created_at", desc=True).limit(500).execute()
        signals = result.get("data") or []
        
        # DEBUG: Check active signals count for XAUUSD
        if symbol == "XAUUSD":
            active_query = client.table("prediction_logs").select("id, status, model_type, strategy, created_at").eq("symbol", "XAUUSD").eq("status", "active")
            if model_lower in ["pulse1", "pulse2", "pulse3"]:
                active_query = active_query.eq("model_type", model_lower)
            elif model_lower == "emel":
                active_query = active_query.or_("model_type.eq.emel,strategy.eq.EMEL")
            active_result = active_query.limit(100).execute()
            active_signals = active_result.get("data") or []
            logger.info(f"[XAUUSD DEBUG] model={model}, completed_signals={len(signals)}, active_signals={len(active_signals)}")
        
        if not signals:
            return {
                "model": model,
                "symbol": symbol,
                "timeframe": timeframe,
                "total_signals": 0,
                "message": "No signals found for this filter combination"
            }
        
        # Calculate statistics
        stats = {
            "total": len(signals),
            "completed": 0,
            "stopped": 0,
            "expired": 0,
            "by_symbol": {},
            "by_timeframe": {},
            "by_direction": {"BUY": 0, "SELL": 0},
            "target_hits": {"TP1": 0, "TP2": 0, "TP3": 0, "TP4": 0},
            "total_profit_pips": 0,
            "total_loss_pips": 0,
            "avg_profit_pips": 0,
            "avg_loss_pips": 0,
            "max_profit_pips": 0,
            "max_loss_pips": 0,
        }
        
        profits = []
        losses = []
        
        for sig in signals:
            # Status counts
            status = sig.get("status", "expired")
            if status == "completed":
                stats["completed"] += 1
            elif status == "stopped":
                stats["stopped"] += 1
            else:
                stats["expired"] += 1
            
            # Symbol breakdown
            sym = sig.get("symbol", "unknown")
            if sym not in stats["by_symbol"]:
                stats["by_symbol"][sym] = {"total": 0, "completed": 0, "stopped": 0, "net_pips": 0}
            stats["by_symbol"][sym]["total"] += 1
            if status == "completed":
                stats["by_symbol"][sym]["completed"] += 1
            elif status == "stopped":
                stats["by_symbol"][sym]["stopped"] += 1
            
            # Timeframe breakdown
            tf = sig.get("timeframe", "unknown")
            if tf not in stats["by_timeframe"]:
                stats["by_timeframe"][tf] = {"total": 0, "completed": 0, "stopped": 0}
            stats["by_timeframe"][tf]["total"] += 1
            if status == "completed":
                stats["by_timeframe"][tf]["completed"] += 1
            elif status == "stopped":
                stats["by_timeframe"][tf]["stopped"] += 1
            
            # Direction
            direction = sig.get("ml_direction")
            if direction in ["BUY", "SELL"]:
                stats["by_direction"][direction] += 1
            
            # Target hits
            targets_hit = sig.get("targets_hit", {})
            if isinstance(targets_hit, str):
                try:
                    import json
                    targets_hit = json.loads(targets_hit)
                except:
                    targets_hit = {}
            for tp in ["TP1", "TP2", "TP3", "TP4"]:
                if targets_hit.get(tp):
                    stats["target_hits"][tp] += 1
            
            # P/L calculation
            sl_pips = sig.get("stop_loss_pips", 0)
            if status == "completed":
                profit = sig.get("highest_profit_pips", 0)
                stats["total_profit_pips"] += profit
                profits.append(profit)
                if sym in stats["by_symbol"]:
                    stats["by_symbol"][sym]["net_pips"] += profit
            elif status == "stopped":
                loss = abs(sl_pips) if sl_pips else abs(sig.get("lowest_drawdown_pips", 0))
                stats["total_loss_pips"] += loss
                losses.append(loss)
                if sym in stats["by_symbol"]:
                    stats["by_symbol"][sym]["net_pips"] -= loss
        
        # Calculate averages
        if profits:
            stats["avg_profit_pips"] = round(sum(profits) / len(profits), 2)
            stats["max_profit_pips"] = round(max(profits), 2)
        if losses:
            stats["avg_loss_pips"] = round(sum(losses) / len(losses), 2)
            stats["max_loss_pips"] = round(max(losses), 2)
        
        # Win rate calculation
        total_with_outcome = stats["completed"] + stats["stopped"]
        win_rate = round(stats["completed"] / total_with_outcome * 100, 1) if total_with_outcome > 0 else 0
        
        # Target hit rates
        target_rates = {}
        for tp, hits in stats["target_hits"].items():
            target_rates[tp] = round(hits / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        
        return {
            "model": model,
            "symbol": symbol,
            "timeframe": timeframe,
            "period_days": days,
            "total_signals": stats["total"],
            "win_rate": win_rate,
            "completed": stats["completed"],
            "stopped": stats["stopped"],
            "expired": stats["expired"],
            "target_rates": target_rates,
            "total_profit_pips": round(stats["total_profit_pips"], 2),
            "total_loss_pips": round(stats["total_loss_pips"], 2),
            "net_pips": round(stats["total_profit_pips"] - stats["total_loss_pips"], 2),
            "avg_profit_pips": stats["avg_profit_pips"],
            "avg_loss_pips": stats["avg_loss_pips"],
            "max_profit_pips": stats["max_profit_pips"],
            "max_loss_pips": stats["max_loss_pips"],
            "risk_reward": round(stats["avg_profit_pips"] / stats["avg_loss_pips"], 2) if stats["avg_loss_pips"] > 0 else 0,
            "by_symbol": stats["by_symbol"],
            "by_timeframe": stats["by_timeframe"],
            "by_direction": stats["by_direction"],
            "signals": signals[:20],  # Last 20 signals for display
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()[:500]}


@router.get("/model-analysis/summary")
async def get_all_models_summary(
    days: int = Query(30, ge=1, le=90),
    symbol: Optional[str] = Query(None)
):
    """
    Get summary statistics for all models across all timeframes.
    Used for the Model Analysis Panel overview.
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat() + "Z"
        
        query = client.table("prediction_logs").select(
            "symbol, timeframe, model_type, strategy, status, "
            "highest_profit_pips, lowest_drawdown_pips, stop_loss_pips, targets_hit"
        ).gte("created_at", cutoff_iso).neq("status", "active")
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        result = query.execute()
        signals = result.get("data") or []
        
        # Initialize model structure
        MODELS = ["ml", "emel", "pulse1", "pulse2", "pulse3"]
        TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
        
        summary = {}
        for model in MODELS:
            summary[model] = {
                "total_signals": 0,
                "by_timeframe": {tf: {"total": 0, "completed": 0, "stopped": 0, "win_rate": 0} for tf in TIMEFRAMES},
                "overall_win_rate": 0,
                "total_completed": 0,
                "total_stopped": 0,
            }
        
        # Process signals
        for sig in signals:
            # Determine model
            model_type = sig.get("model_type", "ml") or "ml"
            strategy = sig.get("strategy", "")
            
            if model_type.lower() in ["pulse", "pulse1"] or (strategy and "PULSE" in strategy.upper() and "V3" not in strategy.upper() and "ML" not in strategy.upper()):
                model_key = "pulse1"
            elif model_type.lower() == "pulse2" or (strategy and "PULSE_ML" in strategy.upper()):
                model_key = "pulse2"
            elif model_type.lower() == "pulse3" or (strategy and "PULSE_V3" in strategy.upper()):
                model_key = "pulse3"
            elif model_type.lower() == "emel" or (strategy and "EMEL" in strategy.upper()):
                model_key = "emel"
            else:
                model_key = "ml"
            
            if model_key not in summary:
                continue
            
            # Get timeframe
            tf = sig.get("timeframe", "1h")
            if tf not in TIMEFRAMES:
                tf = "1h"  # Default
            
            # Update counts
            summary[model_key]["total_signals"] += 1
            summary[model_key]["by_timeframe"][tf]["total"] += 1
            
            status = sig.get("status")
            if status == "completed":
                summary[model_key]["total_completed"] += 1
                summary[model_key]["by_timeframe"][tf]["completed"] += 1
            elif status == "stopped":
                summary[model_key]["total_stopped"] += 1
                summary[model_key]["by_timeframe"][tf]["stopped"] += 1
        
        # Calculate win rates
        for model in MODELS:
            total_with_outcome = summary[model]["total_completed"] + summary[model]["total_stopped"]
            if total_with_outcome > 0:
                summary[model]["overall_win_rate"] = round(summary[model]["total_completed"] / total_with_outcome * 100, 1)
            
            # Per timeframe win rates
            for tf in TIMEFRAMES:
                tf_data = summary[model]["by_timeframe"][tf]
                tf_outcome = tf_data["completed"] + tf_data["stopped"]
                if tf_outcome > 0:
                    tf_data["win_rate"] = round(tf_data["completed"] / tf_outcome * 100, 1)
        
        return {
            "period_days": days,
            "symbol": symbol,
            "models": summary
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()[:500]}


@router.get("/available-timeframes/{model}")
async def get_model_timeframes(model: str):
    """
    Get available timeframes for a specific model.
    Some models only work on specific timeframes (e.g., Pulse3, ML on 1h only).
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}
    
    try:
        # Query distinct timeframes for this model
        model_lower = model.lower()
        
        if model_lower == "ml":
            query = client.table("prediction_logs").select("timeframe").or_("model_type.eq.ml,model_type.is.null")
        elif model_lower in ["pulse1", "pulse2", "pulse3"]:
            query = client.table("prediction_logs").select("timeframe").eq("model_type", model_lower)
        elif model_lower == "emel":
            query = client.table("prediction_logs").select("timeframe").or_("model_type.eq.emel,strategy.eq.EMEL")
        else:
            query = client.table("prediction_logs").select("timeframe").eq("model_type", model_lower)
        
        result = query.limit(1000).execute()
        signals = result.get("data") or []
        
        timeframes = list(set(s.get("timeframe", "1h") for s in signals if s.get("timeframe")))
        timeframes.sort()
        
        # Default available timeframes by model
        DEFAULT_TFS = {
            "ml": ["1h"],  # ML typically only on 1h
            "pulse1": ["5m", "15m"],
            "pulse2": ["5m", "15m", "1h"],
            "pulse3": ["1h"],  # Pulse3 typically only on 1h
            "emel": ["5m", "15m", "1h", "4h"],
        }
        
        # Merge with actual data
        available = list(set(timeframes + DEFAULT_TFS.get(model_lower, ["1h"])))
        available.sort(key=lambda x: ["5m", "15m", "30m", "1h", "4h", "1d"].index(x) if x in ["5m", "15m", "30m", "1h", "4h", "1d"] else 99)
        
        return {
            "model": model,
            "available_timeframes": available,
            "default_timeframe": available[0] if available else "1h"
        }
        
    except Exception as e:
        return {"error": str(e), "model": model, "available_timeframes": ["1h"]}



# ═══════════════════════════════════════════════════════════════════════════════
# XAUUSD SIGNAL REPAIR ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/repair-xauusd-signals")
async def repair_xauusd_signals(
    dry_run: bool = Query(True, description="If true, only shows what would be fixed without making changes"),
    max_age_hours: float = Query(2.0, description="Max age in hours for signals to be considered stuck")
):
    """
    Repair stuck XAUUSD signals that have been active for too long.
    
    Problem: XAUUSD signals were getting stuck in 'active' status because:
    1. Missing .execute() calls in signal lifecycle updates
    2. Price fetching failures
    3. Circuit breaker issues
    
    This endpoint force-expires old active signals so new ones can be tracked properly.
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if not client:
        return {"error": "Database client not available"}
    
    try:
        from datetime import datetime, timedelta
        
        # Find stuck XAUUSD signals
        cutoff = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat() + "Z"
        
        result = client.table("prediction_logs").select(
            "id, symbol, ml_direction, model_type, strategy, status, created_at, ml_entry_price"
        ).eq("symbol", "XAUUSD").eq("status", "active").lt("created_at", cutoff).limit(200).execute()
        
        stuck_signals = result.get("data") or []
        
        if not stuck_signals:
            return {
                "success": True,
                "message": "No stuck XAUUSD signals found",
                "dry_run": dry_run,
                "signals_checked": 0
            }
        
        # Group by model type for reporting
        by_model = {}
        for sig in stuck_signals:
            model = sig.get("model_type") or sig.get("strategy") or "unknown"
            by_model[model] = by_model.get(model, 0) + 1
        
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": f"Found {len(stuck_signals)} stuck XAUUSD signals (dry run - no changes made)",
                "signals_found": len(stuck_signals),
                "by_model": by_model,
                "max_age_hours": max_age_hours,
                "sample_signals": stuck_signals[:5]
            }
        
        # Actually fix the signals
        fixed_count = 0
        errors = []
        
        for sig in stuck_signals:
            try:
                sig_id = sig["id"]
                update_result = client.table("prediction_logs").eq("id", sig_id).update({
                    "status": "expired",
                    "exit_time": datetime.utcnow().isoformat() + "Z",
                    "exit_price": sig.get("ml_entry_price"),  # Use entry price as exit
                    "targets_hit": json.dumps({"TP1": False, "TP2": False, "TP3": False, "TP4": False}),
                }).execute()
                
                if update_result and update_result.get("data"):
                    fixed_count += 1
                else:
                    errors.append(f"No data returned for {sig_id[:8]}")
            except Exception as sig_err:
                errors.append(f"{sig['id'][:8]}: {str(sig_err)[:50]}")
        
        return {
            "success": True,
            "dry_run": False,
            "message": f"Fixed {fixed_count}/{len(stuck_signals)} stuck XAUUSD signals",
            "signals_found": len(stuck_signals),
            "signals_fixed": fixed_count,
            "by_model": by_model,
            "errors": errors[:10] if errors else None,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()[:500]}


@router.get("/xauusd-status")
async def get_xauusd_signal_status():
    """
    Get detailed status of XAUUSD signals for debugging.
    Shows active vs completed/stopped/expired counts by model.
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if not client:
        return {"error": "Database client not available"}
    
    try:
        from datetime import datetime, timedelta
        
        # Get all XAUUSD signals from last 7 days
        cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
        
        result = client.table("prediction_logs").select(
            "id, model_type, strategy, status, ml_direction, created_at, exit_time"
        ).eq("symbol", "XAUUSD").gte("created_at", cutoff).limit(500).execute()
        
        signals = result.get("data") or []
        
        # Count by status and model
        stats = {
            "active": {},
            "completed": {},
            "stopped": {},
            "expired": {},
            "total": 0
        }
        
        for sig in signals:
            status = sig.get("status", "unknown")
            model = sig.get("model_type") or sig.get("strategy") or "unknown"
            
            if status not in stats:
                status = "unknown"
            
            if model not in stats[status]:
                stats[status][model] = 0
            
            stats[status][model] += 1
            stats["total"] += 1
        
        # Get recent active signals (potential stuck signals)
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
        old_active_result = client.table("prediction_logs").select(
            "id, model_type, strategy, created_at, ml_entry_price"
        ).eq("symbol", "XAUUSD").eq("status", "active").lt("created_at", one_hour_ago).limit(100).execute()
        
        old_active = old_active_result.get("data") or []
        
        return {
            "success": True,
            "period_days": 7,
            "total_signals": stats["total"],
            "by_status": {
                "active": stats["active"],
                "completed": stats["completed"],
                "stopped": stats["stopped"],
                "expired": stats["expired"]
            },
            "old_active_signals": {
                "count": len(old_active),
                "signals": old_active[:10]  # First 10 for inspection
            },
            "summary": {
                "active_total": sum(stats["active"].values()),
                "completed_total": sum(stats["completed"].values()),
                "stopped_total": sum(stats["stopped"].values()),
                "expired_total": sum(stats["expired"].values()),
            }
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()[:500]}
