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
    """Get accuracy breakdown per model/strategy (EMEL, PULSE, PULSE_ML, PULSE_V3)."""
    if not is_db_available():
        return {"error": "Database not available"}
    
    from database.supabase_client import get_supabase_client
    client = get_supabase_client()
    if not client:
        return {"error": "Database client not available"}
    
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    
    try:
        # Get all predictions with outcomes in the time range
        query = client.table("prediction_logs").select(
            "id, strategy, ml_direction, claude_direction, factors, created_at"
        ).gte("created_at", cutoff).eq("outcome_checked", True)
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        pred_result = query.order("created_at", desc=True).limit(500).execute()
        predictions = pred_result.get("data") or []
        
        if not predictions:
            return {"models": [], "total": 0, "days": days}
        
        # Get outcome results for these predictions
        pred_ids = [p["id"] for p in predictions]
        
        # Build a map of prediction_id -> outcome
        outcome_map = {}
        # Fetch in batches of 50
        for i in range(0, len(pred_ids), 50):
            batch = pred_ids[i:i+50]
            for pid in batch:
                outcome_result = client.table("outcome_results").select(
                    "prediction_id, ml_correct, claude_correct, hit_target, hit_stop"
                ).eq("prediction_id", pid).eq("check_interval", check_interval).execute()
                outcomes = outcome_result.get("data") or []
                if outcomes:
                    outcome_map[pid] = outcomes[0]
        
        # Group by strategy
        strategy_stats = {}
        for pred in predictions:
            strategy = pred.get("strategy") or pred.get("factors", {}).get("strategy") or pred.get("factors", {}).get("source") or "UNKNOWN"
            
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    "strategy": strategy,
                    "total": 0,
                    "ml_correct": 0,
                    "claude_correct": 0,
                    "target_hit": 0,
                    "stop_hit": 0,
                    "no_outcome": 0,
                }
            
            stats = strategy_stats[strategy]
            stats["total"] += 1
            
            outcome = outcome_map.get(pred["id"])
            if outcome:
                if outcome.get("ml_correct"):
                    stats["ml_correct"] += 1
                if outcome.get("claude_correct"):
                    stats["claude_correct"] += 1
                if outcome.get("hit_target"):
                    stats["target_hit"] += 1
                if outcome.get("hit_stop"):
                    stats["stop_hit"] += 1
            else:
                stats["no_outcome"] += 1
        
        # Calculate percentages
        models = []
        for strategy, stats in strategy_stats.items():
            total = stats["total"]
            with_outcome = total - stats["no_outcome"]
            models.append({
                "strategy": stats["strategy"],
                "total_predictions": total,
                "with_outcome": with_outcome,
                "ml_accuracy": round(stats["ml_correct"] / with_outcome, 3) if with_outcome > 0 else None,
                "ml_correct": stats["ml_correct"],
                "claude_accuracy": round(stats["claude_correct"] / with_outcome, 3) if with_outcome > 0 else None,
                "claude_correct": stats["claude_correct"],
                "target_hit_rate": round(stats["target_hit"] / with_outcome, 3) if with_outcome > 0 else None,
                "target_hits": stats["target_hit"],
                "stop_hit_rate": round(stats["stop_hit"] / with_outcome, 3) if with_outcome > 0 else None,
                "stop_hits": stats["stop_hit"],
            })
        
        # Sort by total predictions descending
        models.sort(key=lambda m: m["total_predictions"], reverse=True)
        
        return {
            "models": models,
            "total": len(predictions),
            "days": days,
            "check_interval": check_interval,
            "symbol": symbol,
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
        
        # Get predictions with lifecycle fields
        result = client.table("prediction_logs").select(
            "id, symbol, strategy, ml_confidence, status, targets_hit, model_type"
        ).gte("created_at", cutoff_iso).limit(500).execute()
        predictions = (result.get('data') if isinstance(result, dict) else getattr(result, 'data', None)) or []
        
        # Get outcomes from outcome_results (ANY check_interval, not just 24h)
        outcome_result = client.table("outcome_results").select(
            "prediction_id, ml_correct, hit_target, hit_stop"
        ).limit(1000).execute()
        outcomes_list = (outcome_result.get('data') if isinstance(outcome_result, dict) else getattr(outcome_result, 'data', None)) or []
        outcomes_map = {o.get("prediction_id"): o for o in outcomes_list if o.get("prediction_id")}
        
        # Classify by confidence — thresholds adjusted for realistic ML output
        # ML typically produces 45-70% confidence range
        def classify(conf):
            if conf >= 65: return "ultra_safe"
            if conf >= 55: return "balanced"
            if conf >= 48: return "full_power"
            return "aggressive"
        
        # Initialize stats with per-target tracking
        stats = {sym: {s: {
            "total": 0, "with_outcome": 0, "correct": 0,
            "target_hits": 0, "stop_hits": 0, "conf_sum": 0,
            "tp1_hits": 0, "tp2_hits": 0, "tp3_hits": 0, "tp4_hits": 0,
        } for s in ["ultra_safe", "balanced", "full_power", "aggressive"]} 
                 for sym in ["NDX.INDX", "XAUUSD"]}
        
        outcomes_found = 0
        
        # Process
        for p in predictions:
            sym = p.get("symbol")
            if sym not in stats:
                continue
            try:
                conf = float(p.get("ml_confidence", 50) or 50)
            except:
                conf = 50
            strat = p.get("strategy") or classify(conf)
            if strat not in stats[sym]:
                strat = classify(conf)
            
            stats[sym][strat]["total"] += 1
            stats[sym][strat]["conf_sum"] += conf
            
            # Check for outcome from EITHER source
            has_outcome = False
            hit_target = False
            hit_stop = False
            
            # Source 1: prediction_logs lifecycle status (primary — more reliable)
            p_status = p.get("status")
            if p_status in ("completed", "stopped"):
                has_outcome = True
                if p_status == "completed":
                    hit_target = True
                elif p_status == "stopped":
                    hit_stop = True
                
                # Parse targets_hit for per-TP tracking
                targets_hit = parse_json_field(p.get("targets_hit"), {})
                if targets_hit:
                    if targets_hit.get("TP1"): stats[sym][strat]["tp1_hits"] += 1
                    if targets_hit.get("TP2"): stats[sym][strat]["tp2_hits"] += 1
                    if targets_hit.get("TP3"): stats[sym][strat]["tp3_hits"] += 1
                    if targets_hit.get("TP4"): stats[sym][strat]["tp4_hits"] += 1
            
            # Source 2: outcome_results table (fallback)
            if not has_outcome:
                outcome = outcomes_map.get(p.get("id"))
                if outcome:
                    has_outcome = True
                    ot = outcome.get("hit_target", False)
                    os_ = outcome.get("hit_stop", False)
                    # If both hit_target and hit_stop are true, 
                    # the signal ultimately lost — prioritize stop
                    if os_:
                        hit_stop = True
                        hit_target = False
                    elif ot:
                        hit_target = True
            
            if has_outcome:
                outcomes_found += 1
                stats[sym][strat]["with_outcome"] += 1
                # A signal is either correct OR stopped, never both
                if hit_target and not hit_stop:
                    stats[sym][strat]["correct"] += 1
                    stats[sym][strat]["target_hits"] += 1
                elif hit_stop:
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
