"""
Learning API Router
Endpoints for prediction tracking, outcome checking, and learning insights.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Query
from datetime import datetime, timedelta, timezone
from utils.safe_supabase import safe_get_data, safe_get_error
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from database.supabase_client import is_db_available, get_init_error, get_supabase_client
from order_block_detector import OrderBlockConfig
from services.prediction_logger import get_recent_predictions
from services.outcome_tracker import (
    check_pending_outcomes,
    check_prediction_outcome,
    get_accuracy_summary,
    get_multi_target_accuracy,
    check_multi_target_outcome,
)
from services.target_config import get_symbol_config, SYMBOL_CONFIGS, pips_from_price_change
from services.learning_analyzer import (
    analyze_factor_correlations,
    generate_learning_insights,
    save_insights_to_db,
    get_active_insights,
)
from services.ml_scope_policy import normalize_ml_scope
from services.adaptive_tp_sl import (
    calculate_adaptive_tp_sl,
    get_learned_adjustments,
    AdaptiveTPSL,
)
from services.signal_analytics import (
    TIMEFRAME_ORDER,
    MODEL_ORDER,
    classify_signal,
    coerce_float as analytics_coerce_float,
    normalize_model_type,
    parse_json_object,
    normalized_targets_hit,
    normalize_timeframe,
    realized_pips,
    resolved_exit_price,
    sort_models,
    sort_timeframes,
    summarize_scope,
)
from services.multi_target_tracker import tracker as multi_target_tracker
from services.order_block_service import service as order_block_service
from services.telegram_service import telegram_notifier

router = APIRouter(prefix="/api/learning", tags=["learning"])
logger = logging.getLogger(__name__)


_ALL_TIME_FLOOR = datetime(2000, 1, 1, tzinfo=timezone.utc)
_TRACKED_STRATEGY_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]
_ML_STRATEGY_ORDER = ["main", "ultra_safe", "balanced", "full_power", "aggressive", "nasdaq_precision"]
_ML_STRATEGY_DESCRIPTIONS = {
    "main": "Ham/orijinal ML akışı; preset filtre uygulanmadan loglanan ana model.",
    "ultra_safe": "Kritik + teknik katmanlarla en seçici preset.",
    "balanced": "Kritik + teknik + context dengeli preset.",
    "full_power": "Daha geniş sinyal akışı için düşük eşikli preset.",
    "aggressive": "En esnek preset; daha hızlı ve daha fazla sinyal arar.",
    "nasdaq_precision": "NASDAQ odaklı yüksek doğruluk preset'i.",
}
_AI_PANEL_SCOPE_ORDER = ["hourly_panel"]
_AI_PANEL_SCOPE_DESCRIPTIONS = {
    "hourly_panel": "CLAUDE AI ANALYSIS panelinden her saat force-refresh ile alınan actionable sinyaller.",
}
_SMC_TIMEFRAME_ORDER = ["5m", "15m", "1h", "4h"]
_SMC_TIMEFRAME_DESCRIPTIONS = {
    "5m": "En hızlı Smart Money Zones akışı; mikro yapı değişimlerini izler.",
    "15m": "Dengeli Smart Money Zones görünümü; kısa vadeli yapı ve OB/FVG takibi.",
    "1h": "Ana intraday Smart Money Zones görünümü; daha güçlü structure sinyalleri.",
    "4h": "Daha yavaş Smart Money Zones görünümü; major zone ve trend devamı odaklı.",
}


def _as_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: Optional[datetime] = None) -> str:
    return _as_utc(dt or _utc_now()).isoformat().replace("+00:00", "Z")


async def _fetch_prediction_logs_window(
    client,
    cutoff: datetime,
    *,
    select_fields: str,
) -> List[dict]:
    predictions: List[dict] = []
    end = _utc_now()
    cur = cutoff
    days_back = max(0, int((end - cutoff).total_seconds() // 86400))
    window_days = 1 if 0 < days_back <= 90 else 7 if 90 < days_back <= 365 else 30

    while cur < end:
        ds = cur.replace(hour=0, minute=0, second=0, microsecond=0)
        de = min(ds + timedelta(days=window_days), end)
        page_before: Optional[str] = None
        while True:
            query = client.table("prediction_logs").select(select_fields).gte("created_at", _utc_iso(ds)).lt(
                "created_at", _utc_iso(de)
            )
            if page_before:
                query = query.lt("created_at", page_before)

            batch = safe_get_data(query.order("created_at", desc=True).limit(1000).execute()) or []
            if not batch:
                break

            predictions.extend(batch)
            if len(batch) < 1000:
                break

            last_created_at = batch[-1].get("created_at")
            if not isinstance(last_created_at, str) or not last_created_at:
                logger.warning("Prediction log pagination cursor missing for %s - %s", _utc_iso(ds), _utc_iso(de))
                break
            if page_before == last_created_at:
                logger.warning("Prediction log pagination stalled for %s - %s at %s", _utc_iso(ds), _utc_iso(de), last_created_at)
                break

            page_before = last_created_at
        cur = de

    return predictions


async def _bootstrap_smc_predictions_if_empty() -> None:
    config = OrderBlockConfig(
        fractal_period=2,
        min_displacement_atr=1.0,
        min_score=45,
        zone_type="wick",
        max_tests=3,
    )

    for symbol in _TRACKED_STRATEGY_SYMBOLS:
        for timeframe in _SMC_TIMEFRAME_ORDER:
            try:
                await order_block_service.detect(
                    symbol,
                    timeframe,
                    500,
                    config,
                    use_cache=False,
                    log_signals=True,
                )
            except Exception as exc:
                logger.error("SMC bootstrap error for %s %s: %s", symbol, timeframe, exc)


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return _as_utc(value)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _average(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _duration_minutes(sig: dict) -> Optional[float]:
    created_at = _parse_iso_datetime(sig.get("created_at"))
    exit_time = _parse_iso_datetime(sig.get("exit_time"))
    if created_at is None or exit_time is None:
        return None
    return round((exit_time - created_at).total_seconds() / 60.0, 1)


def _resolve_ml_strategy_scope(sig: dict) -> Optional[str]:
    if normalize_model_type(sig) != "ml":
        return None

    candidates: List[str] = []
    for raw_value in (sig.get("strategy"), sig.get("model_type")):
        if isinstance(raw_value, str):
            normalized = raw_value.lower().strip()
            if normalized:
                candidates.append(normalized)

    factors = parse_json_object(sig.get("factors"))
    for key in ("strategy", "selected_strategy", "strategy_name", "preset", "preset_strategy"):
        raw_value = factors.get(key)
        if isinstance(raw_value, str):
            normalized = raw_value.lower().strip()
            if normalized:
                candidates.append(normalized)

    for candidate in candidates:
        resolved = normalize_ml_scope(candidate)
        if resolved and resolved != "main":
            return resolved

    return "main"


def _resolved_eligible_ml_strategy_scope(sig: dict) -> Optional[str]:
    scope = _resolve_ml_strategy_scope(sig)
    return scope


def _build_strategy_scope_metrics(scope: str, scope_signals: List[dict], *, symbol: Optional[str] = None) -> dict:
    summary = summarize_scope(scope_signals, default_symbol=symbol)
    resolved = summary["completed"] + summary["stopped"]
    tp_breakdown = {"TP1": 0, "TP2": 0, "TP3": 0, "TP4": 0}
    confidence_values: List[float] = []
    duration_values: List[float] = []
    win_durations: List[float] = []
    loss_durations: List[float] = []

    for sig in scope_signals:
        confidence = analytics_coerce_float(sig.get("ml_confidence"))
        if confidence is not None:
            confidence_values.append(confidence)

        classified_status, _, _ = classify_signal(sig, default_symbol=symbol)
        if classified_status not in {"completed", "stopped"}:
            continue

        targets_hit = normalized_targets_hit(sig, default_symbol=symbol)
        for tp_key in tp_breakdown:
            if targets_hit.get(tp_key):
                tp_breakdown[tp_key] += 1

        duration = _duration_minutes(sig)
        if duration is None:
            continue
        duration_values.append(duration)
        if classified_status == "completed":
            win_durations.append(duration)
        else:
            loss_durations.append(duration)

    tp_depth_rate = (
        (tp_breakdown["TP1"] + tp_breakdown["TP2"] * 2 + tp_breakdown["TP3"] * 3 + tp_breakdown["TP4"] * 4)
        / (resolved * 4)
        if resolved > 0
        else 0.0
    )
    avg_duration = _average(duration_values)
    tp1_rate = (tp_breakdown["TP1"] / resolved) if resolved > 0 else 0.0
    profit_norm = _clamp01(max(summary["avg_pips"], 0.0) / 20.0)
    win_rate_norm = (summary["win_rate"] or 0.0) / 100.0
    speed_norm = 0.5 if avg_duration is None else _clamp01(1.0 - max(avg_duration - 20.0, 0.0) / 220.0)
    endurance_norm = 0.35 if avg_duration is None else _clamp01(min(avg_duration, 480.0) / 480.0)
    reliability = _clamp01(resolved / 8.0) if resolved > 0 else 0.0

    quality_score = round(
        100.0 * reliability * (0.45 * win_rate_norm + 0.30 * tp_depth_rate + 0.25 * profit_norm),
        1,
    )
    scalp_score = round(
        100.0 * reliability * (0.40 * win_rate_norm + 0.20 * tp1_rate + 0.15 * profit_norm + 0.25 * speed_norm),
        1,
    )
    long_term_score = round(
        100.0 * reliability * (0.35 * win_rate_norm + 0.30 * tp_depth_rate + 0.25 * profit_norm + 0.10 * endurance_norm),
        1,
    )

    return {
        "scope": scope,
        "total_predictions": summary["total_signals"],
        "scored_signals": summary["scored_signals"],
        "resolved_signals": resolved,
        "with_outcome": resolved,
        "correct": summary["completed"],
        "completed": summary["completed"],
        "stopped": summary["stopped"],
        "expired": summary["expired"],
        "active": summary["active"],
        "accuracy": summary["win_rate"],
        "win_rate": summary["win_rate"],
        "target_hits": summary["completed"],
        "stop_hits": summary["stopped"],
        "target_hit_rate": round((summary["completed"] / resolved) * 100, 1) if resolved > 0 else None,
        "stop_hit_rate": round((summary["stopped"] / resolved) * 100, 1) if resolved > 0 else None,
        "avg_confidence": round(sum(confidence_values) / len(confidence_values), 1) if confidence_values else 0.0,
        "net_pips": summary["net_pips"],
        "avg_pips": summary["avg_pips"],
        "tp_breakdown": tp_breakdown,
        "tp_hit_rates": {
            tp_key: round((tp_count / resolved) * 100, 1) if resolved > 0 else None
            for tp_key, tp_count in tp_breakdown.items()
        },
        "avg_duration_minutes": avg_duration,
        "avg_win_duration_minutes": _average(win_durations),
        "avg_loss_duration_minutes": _average(loss_durations),
        "quality_score": quality_score,
        "scalp_score": scalp_score,
        "long_term_score": long_term_score,
    }


def _pick_scope_leader(scope_metrics: Dict[str, dict], score_key: str) -> dict:
    candidates = [metrics for metrics in scope_metrics.values() if metrics["resolved_signals"] >= 3]
    if not candidates:
        candidates = [metrics for metrics in scope_metrics.values() if metrics["resolved_signals"] > 0]
    if not candidates:
        return {
            "scope": None,
            "score": None,
            "resolved_signals": 0,
            "win_rate": None,
            "net_pips": None,
            "avg_duration_minutes": None,
        }

    best = max(
        candidates,
        key=lambda metrics: (
            metrics.get(score_key) or 0.0,
            metrics.get("resolved_signals") or 0,
            metrics.get("win_rate") or 0.0,
            metrics.get("net_pips") or 0.0,
        ),
    )
    return {
        "scope": best["scope"],
        "score": best.get(score_key),
        "resolved_signals": best.get("resolved_signals", 0),
        "win_rate": best.get("win_rate"),
        "net_pips": best.get("net_pips"),
        "avg_duration_minutes": best.get("avg_duration_minutes"),
    }


def _model_detail_hourly_contract(symbol: Optional[str], observed_hours: Optional[set[int]] = None) -> dict:
    normalized_symbol = (symbol or "").upper().strip()

    if normalized_symbol == "NDX.INDX":
        base_hours = list(range(9, 18))
        session_key = "us_cash"
        window_label = "09:00–17:00"
    elif normalized_symbol == "GDAXI.INDX":
        base_hours = list(range(7, 16))
        session_key = "xetra_cash"
        window_label = "07:00–15:00 UTC"
    elif normalized_symbol in {"USOIL.FOREX", "CL.F", "CL.COMM"}:
        base_hours = list(range(1, 24))
        session_key = "oil_extended"
        window_label = "01:00–23:00 UTC"
    elif normalized_symbol == "XAUUSD":
        base_hours = list(range(24))
        session_key = "continuous_weekday"
        window_label = "00:00–23:00 UTC"
    else:
        base_hours = list(range(24))
        session_key = "continuous"
        window_label = "00:00–23:00 UTC"

    normalized_observed = sorted(
        {
            hour
            for hour in (observed_hours or set())
            if isinstance(hour, int) and 0 <= hour <= 23
        }
    )
    visible_hours = base_hours or normalized_observed

    return {
        "hours": visible_hours,
        "window_label": window_label,
        "session_key": session_key,
    }


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
    days: int = Query(0, ge=0, le=1095),
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
    days: int = Query(0, ge=0, le=1095),
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
    
    try:
        # Day-by-day pagination to bypass Supabase 1000-row cap
        predictions = []
        start = (_utc_now() - timedelta(days=days)) if days > 0 else (_utc_now() - timedelta(days=90))
        end = _utc_now()
        cur = start
        while cur < end:
            ds = cur.replace(hour=0,minute=0,second=0,microsecond=0)
            de = ds + timedelta(days=1)
            q = client.table("prediction_logs").select(
                "id, strategy, model_type, ml_direction, claude_direction, factors, status, targets_hit, created_at"
            ).gte("created_at", _utc_iso(ds)).lt("created_at", _utc_iso(de)).neq("status", "active")
            if symbol:
                q = q.eq("symbol", symbol)
            batch = safe_get_data(q.order("created_at", desc=True).limit(1000).execute())
            if batch:
                predictions.extend(batch)
            cur = de
        
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
    days: int = Query(0, ge=0, le=1095)
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
    days: int = Query(0, ge=0, le=1095),
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
        
        predictions = safe_get_data(result)
        
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
            
            if safe_get_data(existing):
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
    days: int = Query(0, ge=0, le=1095)
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
        analyses = safe_get_data(result)
        
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
        feedbacks = safe_get_data(result)
        
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
        total_predictions = len(safe_get_data(pred_result))
        
        # Count outcomes
        out_result = client.table("outcome_results").select("id", count="exact").execute()
        total_outcomes = len(safe_get_data(out_result))
        
        # Count error analyses
        err_result = client.table("error_analysis").select("id", count="exact").execute()
        total_error_analyses = len(safe_get_data(err_result))
        
        # Count active feedback rules
        fb_result = client.table("learning_feedback").select("id").eq("is_active", True).execute()
        active_feedback_rules = len(safe_get_data(fb_result))
        
        # Get recent error types distribution
        recent_errors = client.table("error_analysis").select(
            "error_type, is_fake_move"
        ).order("created_at", desc=True).limit(50).execute()
        
        error_distribution = {}
        fake_move_count = 0
        for e in (safe_get_data(recent_errors)):
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
            "fake_move_rate": round(fake_move_count / max(1, len(safe_get_data(recent_errors))), 2),
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
        patterns = safe_get_data(result)
        
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
    days: int = Query(0, ge=0, le=1095)
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
        cutoff = _utc_iso(_utc_now() - timedelta(days=days)) if days > 0 else _utc_iso(_ALL_TIME_FLOOR)
        
        query = client.table("multi_target_outcomes").select("*").gte("created_at", cutoff)
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        result = query.execute()
        outcomes = safe_get_data(result)
        
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
    days: int = Query(0, ge=0, le=1095, description="Number of days to look back (0=all time)"),
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
        cutoff = (_utc_now() - timedelta(days=days)) if days > 0 else _ALL_TIME_FLOOR
        cutoff_iso = _utc_iso(cutoff)
        
        # Get predictions (no PostgREST join - custom httpx client doesn't support it)
        query = client.table("prediction_logs").select(
            "id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, ml_target_price, ml_stop_price, claude_direction, claude_confidence, created_at, status, targets_hit, highest_profit_pips, lowest_drawdown_pips, exit_price, exit_time"
        ).gte("created_at", cutoff_iso).order("created_at", desc=True).limit(limit)
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        result = query.execute()
        predictions = safe_get_data(result)
        
        # Format for frontend - use lifecycle status + targets_hit instead of outcome_results join
        formatted = []
        for pred in predictions:
            p_status = pred.get("status")
            has_outcome = p_status in ("completed", "stopped")
            is_correct = p_status == "completed"
            hit_target = p_status == "completed"
            hit_stop = p_status == "stopped"
            
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
                "has_outcome": has_outcome,
                "exit_price": pred.get("exit_price"),
                "hit_target": hit_target,
                "hit_stop": hit_stop,
                "ml_correct": is_correct,
                "outcome_time": pred.get("exit_time"),
            }
            
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
            cutoff = _utc_now() - timedelta(days=7)
            cutoff_iso = _utc_iso(cutoff)
            
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
            "reset_timestamp": _utc_iso(),
            **fresh_stats
        }
        
    except Exception as e:
        logger.error(f"Strategy performance reset error: {e}")
        return {"error": str(e), "deleted": False}


@router.get("/strategy-performance")
async def get_strategy_performance(
    days: int = Query(0, ge=0, le=1095, description="Number of days to analyze (0=all time)")
):
    """Get performance statistics for real ML strategy scopes plus raw main ML."""
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}
    
    try:
        cutoff = (_utc_now() - timedelta(days=days)) if days > 0 else _ALL_TIME_FLOOR
        select_fields = (
            "id, symbol, strategy, ml_confidence, status, targets_hit, targets, "
            "model_type, timeframe, created_at, highest_profit_pips, lowest_drawdown_pips, "
            "stop_loss_pips, ml_entry_price, exit_price, exit_time, ml_direction, factors, resolution_reason"
        )
        predictions = await _fetch_prediction_logs_window(client, cutoff, select_fields=select_fields)

        grouped_signals = {
            symbol: {scope: [] for scope in _ML_STRATEGY_ORDER}
            for symbol in _TRACKED_STRATEGY_SYMBOLS
        }
        all_ml_signals: List[dict] = []
        
        outcomes_found = 0
        eligible_outcomes_found = 0

        for p in predictions:
            sym = p.get("symbol")
            if sym not in grouped_signals:
                continue

            scope = _resolved_eligible_ml_strategy_scope(p)
            if scope is None:
                continue

            grouped_signals[sym][scope].append(p)
            all_ml_signals.append(p)

            classified_status, _, _ = classify_signal(p, default_symbol=sym)
            if classified_status in {None, "active"}:
                continue

            outcomes_found += 1

            if classified_status not in {"completed", "stopped"}:
                continue

            eligible_outcomes_found += 1

        result_data: Dict[str, Dict[str, dict]] = {}
        symbol_analysis: Dict[str, dict] = {}
        best = {}

        for sym, scoped_signals in grouped_signals.items():
            scope_metrics = {
                scope: _build_strategy_scope_metrics(scope, scoped_signals[scope], symbol=sym)
                for scope in _ML_STRATEGY_ORDER
            }
            quality_leader = _pick_scope_leader(scope_metrics, "quality_score")
            scalping_leader = _pick_scope_leader(scope_metrics, "scalp_score")
            long_term_leader = _pick_scope_leader(scope_metrics, "long_term_score")
            result_data[sym] = scope_metrics
            symbol_analysis[sym] = {
                "available_scopes": [scope for scope in _ML_STRATEGY_ORDER if scope_metrics[scope]["total_predictions"] > 0],
                "total_predictions": sum(metrics["total_predictions"] for metrics in scope_metrics.values()),
                "resolved_signals": sum(metrics["resolved_signals"] for metrics in scope_metrics.values()),
                "leaders": {
                    "quality": quality_leader,
                    "scalping": scalping_leader,
                    "long_term": long_term_leader,
                },
            }
            best_scope = quality_leader.get("scope")
            best[sym] = {
                "strategy": best_scope,
                "accuracy": scope_metrics.get(best_scope, {}).get("win_rate") if best_scope else None,
                "total_predictions": scope_metrics.get(best_scope, {}).get("total_predictions") if best_scope else None,
                "resolved_signals": scope_metrics.get(best_scope, {}).get("resolved_signals") if best_scope else None,
            }

        overall_scope_metrics = {
            scope: _build_strategy_scope_metrics(
                scope,
                [sig for sig in all_ml_signals if _resolved_eligible_ml_strategy_scope(sig) == scope],
            )
            for scope in _ML_STRATEGY_ORDER
        }

        return {
            "period_days": days,
            "predictions_count": len(predictions),
            "ml_predictions_count": len(all_ml_signals),
            "outcomes_count": outcomes_found,
            "eligible_outcomes_count": eligible_outcomes_found,
            "strategies": result_data,
            "symbols": symbol_analysis,
            "best_strategies": best,
            "strategy_order": _ML_STRATEGY_ORDER,
            "strategy_descriptions": _ML_STRATEGY_DESCRIPTIONS,
            "overall_summary": {
                "total_predictions": len(all_ml_signals),
                "resolved_signals": sum(metrics["resolved_signals"] for metrics in overall_scope_metrics.values()),
                "leaders": {
                    "quality": _pick_scope_leader(overall_scope_metrics, "quality_score"),
                    "scalping": _pick_scope_leader(overall_scope_metrics, "scalp_score"),
                    "long_term": _pick_scope_leader(overall_scope_metrics, "long_term_score"),
                },
            },
        }
    except Exception as e:
        import traceback
        logger.error(f"Strategy performance error: {e}\n{traceback.format_exc()}")
        return {"error": str(e)}


@router.get("/smc-performance")
async def get_smc_performance(
    days: int = Query(0, ge=0, le=1095, description="Number of days to analyze (0=all time)")
):
    if not is_db_available():
        return {"error": "Database not available"}

    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}

    try:
        cutoff = (_utc_now() - timedelta(days=days)) if days > 0 else _ALL_TIME_FLOOR
        select_fields = (
            "id, symbol, timeframe, strategy, model_type, ml_confidence, status, targets_hit, targets, "
            "highest_profit_pips, lowest_drawdown_pips, stop_loss_pips, ml_entry_price, exit_price, "
            "exit_time, ml_direction, factors, created_at, resolution_reason"
        )
        predictions = await _fetch_prediction_logs_window(client, cutoff, select_fields=select_fields)

        has_smc_history = any(
            p.get("symbol") in _TRACKED_STRATEGY_SYMBOLS
            and normalize_model_type(p) == "smc"
            and normalize_timeframe(p.get("timeframe")) in _SMC_TIMEFRAME_ORDER
            for p in predictions
        )
        if not has_smc_history:
            await _bootstrap_smc_predictions_if_empty()
            predictions = await _fetch_prediction_logs_window(client, cutoff, select_fields=select_fields)

        grouped_signals = {
            symbol: {timeframe: [] for timeframe in _SMC_TIMEFRAME_ORDER}
            for symbol in _TRACKED_STRATEGY_SYMBOLS
        }
        all_smc_signals: List[dict] = []
        outcomes_found = 0
        eligible_outcomes_found = 0

        for p in predictions:
            sym = p.get("symbol")
            if sym not in grouped_signals or normalize_model_type(p) != "smc":
                continue

            timeframe = normalize_timeframe(p.get("timeframe"))
            if timeframe not in _SMC_TIMEFRAME_ORDER:
                continue

            grouped_signals[sym][timeframe].append(p)
            all_smc_signals.append(p)

            classified_status, _, _ = classify_signal(p, default_symbol=sym)
            if classified_status in {None, "active", "direction_flip"}:
                continue

            outcomes_found += 1

            if classified_status not in {"completed", "stopped"}:
                continue

            eligible_outcomes_found += 1

        result_data: Dict[str, Dict[str, dict]] = {}
        symbol_analysis: Dict[str, dict] = {}

        for sym, timeframe_signals in grouped_signals.items():
            timeframe_metrics = {
                timeframe: _build_strategy_scope_metrics(timeframe, timeframe_signals[timeframe], symbol=sym)
                for timeframe in _SMC_TIMEFRAME_ORDER
            }
            quality_leader = _pick_scope_leader(timeframe_metrics, "quality_score")
            scalping_leader = _pick_scope_leader(timeframe_metrics, "scalp_score")
            long_term_leader = _pick_scope_leader(timeframe_metrics, "long_term_score")
            result_data[sym] = timeframe_metrics
            symbol_analysis[sym] = {
                "available_scopes": [timeframe for timeframe in _SMC_TIMEFRAME_ORDER if timeframe_metrics[timeframe]["total_predictions"] > 0],
                "total_predictions": sum(metrics["total_predictions"] for metrics in timeframe_metrics.values()),
                "resolved_signals": sum(metrics["resolved_signals"] for metrics in timeframe_metrics.values()),
                "leaders": {
                    "quality": quality_leader,
                    "scalping": scalping_leader,
                    "long_term": long_term_leader,
                },
            }

        overall_timeframe_metrics = {
            timeframe: _build_strategy_scope_metrics(
                timeframe,
                [sig for sig in all_smc_signals if normalize_timeframe(sig.get("timeframe")) == timeframe],
            )
            for timeframe in _SMC_TIMEFRAME_ORDER
        }

        return {
            "period_days": days,
            "smc_predictions_count": len(all_smc_signals),
            "outcomes_count": outcomes_found,
            "eligible_outcomes_count": eligible_outcomes_found,
            "timeframes": result_data,
            "symbols": symbol_analysis,
            "timeframe_order": _SMC_TIMEFRAME_ORDER,
            "timeframe_descriptions": _SMC_TIMEFRAME_DESCRIPTIONS,
            "overall_summary": {
                "total_predictions": len(all_smc_signals),
                "resolved_signals": sum(metrics["resolved_signals"] for metrics in overall_timeframe_metrics.values()),
                "leaders": {
                    "quality": _pick_scope_leader(overall_timeframe_metrics, "quality_score"),
                    "scalping": _pick_scope_leader(overall_timeframe_metrics, "scalp_score"),
                    "long_term": _pick_scope_leader(overall_timeframe_metrics, "long_term_score"),
                },
            },
        }
    except Exception as e:
        import traceback
        logger.error(f"SMC performance error: {e}\n{traceback.format_exc()}")
        return {"error": str(e)}


@router.get("/ai-panel-performance")
async def get_ai_panel_performance(
    days: int = Query(0, ge=0, le=1095, description="Number of days to analyze (0=all time)")
):
    if not is_db_available():
        return {"error": "Database not available"}

    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}

    try:
        cutoff = (_utc_now() - timedelta(days=days)) if days > 0 else _ALL_TIME_FLOOR
        predictions = []
        end = _utc_now()
        cur = cutoff
        window_days = 1
        while cur < end:
            ds = cur.replace(hour=0, minute=0, second=0, microsecond=0)
            de = min(ds + timedelta(days=window_days), end)
            batch = safe_get_data(client.table("prediction_logs").select(
                "id, symbol, strategy, ml_confidence, status, targets_hit, targets, "
                "model_type, timeframe, created_at, highest_profit_pips, lowest_drawdown_pips, "
                "stop_loss_pips, ml_entry_price, exit_price, exit_time, ml_direction, factors, resolution_reason"
            ).gte("created_at", _utc_iso(ds)).lt("created_at", _utc_iso(de)).order("created_at", desc=True).limit(1000).execute())
            if batch:
                predictions.extend(batch)
            cur = de

        snapshot_counts = {symbol: 0 for symbol in _TRACKED_STRATEGY_SYMBOLS}
        total_snapshots = 0
        cur = cutoff
        while cur < end:
            ds = cur.replace(hour=0, minute=0, second=0, microsecond=0)
            de = min(ds + timedelta(days=window_days), end)
            try:
                snapshot_batch = safe_get_data(client.table("ai_panel_signal_snapshots").select(
                    "id, symbol"
                ).gte("created_at", _utc_iso(ds)).lt("created_at", _utc_iso(de)).order("created_at", desc=True).limit(1000).execute()) or []
            except Exception:
                snapshot_batch = []
            if snapshot_batch:
                total_snapshots += len(snapshot_batch)
                for row in snapshot_batch:
                    symbol = row.get("symbol")
                    if symbol in snapshot_counts:
                        snapshot_counts[symbol] += 1
            cur = de

        grouped_signals = {
            symbol: {scope: [] for scope in _AI_PANEL_SCOPE_ORDER}
            for symbol in _TRACKED_STRATEGY_SYMBOLS
        }
        all_ai_signals: List[dict] = []
        outcomes_found = 0
        eligible_outcomes_found = 0

        for p in predictions:
            sym = p.get("symbol")
            if sym not in grouped_signals or normalize_model_type(p) != "ai_panel":
                continue

            grouped_signals[sym]["hourly_panel"].append(p)
            all_ai_signals.append(p)

            classified_status, _, _ = classify_signal(p, default_symbol=sym)
            if classified_status in {None, "active", "direction_flip"}:
                continue

            outcomes_found += 1

            if classified_status not in {"completed", "stopped"}:
                continue

            eligible_outcomes_found += 1

        result_data: Dict[str, Dict[str, dict]] = {}
        symbol_analysis: Dict[str, dict] = {}

        for sym, scoped_signals in grouped_signals.items():
            scope_metrics = {
                scope: _build_strategy_scope_metrics(scope, scoped_signals[scope], symbol=sym)
                for scope in _AI_PANEL_SCOPE_ORDER
            }
            quality_leader = _pick_scope_leader(scope_metrics, "quality_score")
            scalping_leader = _pick_scope_leader(scope_metrics, "scalp_score")
            long_term_leader = _pick_scope_leader(scope_metrics, "long_term_score")
            result_data[sym] = scope_metrics
            symbol_analysis[sym] = {
                "available_scopes": [scope for scope in _AI_PANEL_SCOPE_ORDER if scope_metrics[scope]["total_predictions"] > 0],
                "total_predictions": sum(metrics["total_predictions"] for metrics in scope_metrics.values()),
                "resolved_signals": sum(metrics["resolved_signals"] for metrics in scope_metrics.values()),
                "snapshot_count": snapshot_counts.get(sym, 0),
                "leaders": {
                    "quality": quality_leader,
                    "scalping": scalping_leader,
                    "long_term": long_term_leader,
                },
            }

        overall_scope_metrics = {
            scope: _build_strategy_scope_metrics(
                scope,
                [sig for sig in all_ai_signals if scope == "hourly_panel"],
            )
            for scope in _AI_PANEL_SCOPE_ORDER
        }

        return {
            "period_days": days,
            "ai_panel_predictions_count": len(all_ai_signals),
            "ai_panel_snapshots_count": total_snapshots,
            "outcomes_count": outcomes_found,
            "eligible_outcomes_count": eligible_outcomes_found,
            "strategies": result_data,
            "symbols": symbol_analysis,
            "panel_scope_order": _AI_PANEL_SCOPE_ORDER,
            "panel_descriptions": _AI_PANEL_SCOPE_DESCRIPTIONS,
            "overall_summary": {
                "total_predictions": len(all_ai_signals),
                "resolved_signals": sum(metrics["resolved_signals"] for metrics in overall_scope_metrics.values()),
                "leaders": {
                    "quality": _pick_scope_leader(overall_scope_metrics, "quality_score"),
                    "scalping": _pick_scope_leader(overall_scope_metrics, "scalp_score"),
                    "long_term": _pick_scope_leader(overall_scope_metrics, "long_term_score"),
                },
            },
        }
    except Exception as e:
        import traceback
        logger.error(f"AI panel performance error: {e}\n{traceback.format_exc()}")
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
    days: int = Query(0, ge=0, le=1095)
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
async def get_strategy_performance_by_symbol(
    symbol: str,
    days: int = Query(0, ge=0, le=1095)
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
    model: Optional[str] = Query(None, description="Filter by model type (ml, emel, pulse1, pulse2, pulse3, smc)"),
    days: int = Query(0, ge=0, le=1095)
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
    
    # Symbol reverse-mapping: frontend display name → DB symbol
    SYMBOL_MAP = {
        "NASDAQ": "NDX.INDX",
        "DAX": "GDAXI.INDX",
        "US OIL": "USOIL.FOREX",
        "OIL": "USOIL.FOREX",
        "CL.COMM": "USOIL.FOREX",
    }
    db_symbol = SYMBOL_MAP.get(symbol.upper(), symbol)
    
    # Model name mapping
    MODEL_NAMES = {
        "ml": ("ml_core", "ML Model"),
        "emel": ("emel_core", "EMEL 9-Check AI"),
        "pulse1": ("pulse1_algo", "Pulse 1 — Algo"),
        "pulse2": ("pulse2_ml", "Pulse 2 — ML Hybrid"),
        "pulse3": ("pulse3_scalp", "Pulse 3 — Scalp"),
    }
    resolved_model = (model or "").lower().strip()
    model_id, model_name_label = MODEL_NAMES.get(resolved_model, ("all_models", "All Models"))
        
    try:
        cutoff = (_utc_now() - timedelta(days=days)) if days > 0 else _ALL_TIME_FLOOR
        cutoff_iso = _utc_iso(cutoff)
        
        # 1. Fetch signal records
        query = client.table("prediction_logs").select(
            "id, symbol, ml_direction, ml_confidence, strategy, status, "
            "targets_hit, targets, highest_profit_pips, lowest_drawdown_pips, created_at, "
            "model_type, exit_price, exit_time, stop_loss_pips, ml_entry_price, timeframe, resolution_reason"
        ).eq("symbol", db_symbol).gte("created_at", cutoff_iso).order("created_at", desc=True).limit(500)
        
        result = query.execute()
        
        signals = safe_get_data(result)
        if resolved_model and resolved_model != "all":
            signals = [sig for sig in signals if normalize_model_type(sig) == resolved_model]
        
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
                
            classified_status, _, classified_pips = classify_signal(p, default_symbol=db_symbol)
            is_win = False
            is_loss = False
            profit = 0.0
            
            if classified_status == "completed":
                is_win = True
                profit = float(classified_pips or 0.0)
            elif classified_status == "stopped":
                is_loss = True
                profit = float(classified_pips or 0.0)
            
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
            
            classified_status, _, classified_pips = classify_signal(p, default_symbol=db_symbol)
            profit = 0.0
            result_state = "pending"
            
            if classified_status == "completed":
                result_state = "win"
                profit = float(classified_pips or 0.0)
            elif classified_status == "stopped":
                result_state = "loss"
                profit = float(classified_pips or 0.0)
            
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
        
        # Symbol display name for response
        SYM_LABELS = {
            "NDX.INDX": "NASDAQ",
            "GDAXI.INDX": "DAX",
            "USOIL.FOREX": "US OIL",
            "CL.F": "US OIL",
        }
        sym_display = SYM_LABELS.get(db_symbol, db_symbol)
        
        model_performance = {
            "modelId": model_id,
            "modelName": f"{model_name_label} — {sym_display} Predictor",
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


@router.get("/signals/matrix")
async def get_signals_matrix(
    model: str = Query("ml", description="Model type (ml, emel, emel_inverse, pulse1, pulse2, pulse3, smc)")
):
    """
    Returns the latest signal for each symbol and timeframe to populate the Heatmap Matrix.
    Fetches ALL recent signals and filters by model type in Python (avoids .or_() compatibility issues).
    """
    if not is_db_available():
        return {"error": "Database not available", "matrix": {}}
    
    client = get_supabase_client()
    if not client:
        return {"error": "Database client not available", "matrix": {}}
        
    try:
        # Fetch all recent signals (no model filter at DB level)
        result = client.table("prediction_logs").select(
            "symbol, timeframe, ml_direction, ml_confidence, created_at, status, model_type, strategy"
        ).order("created_at", desc=True).limit(1000).execute()
        
        all_signals = safe_get_data(result)
        
        # Filter by model type in Python
        model_lower = model.lower().strip()
        signals = [s for s in all_signals if _normalize_model_type(s) == model_lower]
        
        matrix = {}
        filled_combos = set()
        
        for sig in signals:
            sym = sig.get("symbol")
            tf = sig.get("timeframe", "1h").lower()
            direction = sig.get("ml_direction", "HOLD")
            conf = sig.get("ml_confidence", 50)
            status = sig.get("status", "unknown")
            created_at = sig.get("created_at")
            
            if not sym: continue
            
            combo_key = f"{sym}_{tf}"
            if combo_key in filled_combos:
                continue
                
            filled_combos.add(combo_key)
            if sym not in matrix:
                matrix[sym] = {}
                
            matrix[sym][tf] = {
                "direction": direction,
                "confidence": conf,
                "status": status,
                "age_hours": 0
            }
            
            if created_at:
                try:
                    from dateutil import parser
                    from datetime import datetime, timezone
                    created_dt = parser.parse(created_at)
                    now_dt = datetime.now(timezone.utc)
                    matrix[sym][tf]["age_hours"] = round((now_dt - created_dt).total_seconds() / 3600, 1)
                except:
                    pass
            
        return {"matrix": matrix}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()[:500], "matrix": {}}


@router.get("/signals/recent")
async def get_recent_signals_endpoint(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    model: Optional[str] = Query(None, description="Filter by model type (ml, emel, pulse1, pulse2, pulse3, smc)"),
    strategy_scope: Optional[str] = Query(None, description="Filter ML signals by resolved strategy scope (main, ultra_safe, balanced, full_power, aggressive, nasdaq_precision)"),
    days: int = Query(0, ge=0, le=1095, description="Days to look back (0=all available history)"),
    limit: int = Query(50, ge=1, le=200),
    include_active: bool = Query(True, description="Include active signals")
):
    """
    Get recent signals with summary information for the signal list.
    Enhanced version of /predictions with calculated duration and PNL.
    """
    if not isinstance(symbol, str):
        symbol = None
    if not isinstance(model, str):
        model = None
    if not isinstance(strategy_scope, str):
        strategy_scope = None

    if not is_db_available():
        return {"error": "Database not available", "signals": [], "count": 0, "symbol": symbol}
    
    client = get_supabase_client()
    if not client:
        return {"error": "Database client not available", "signals": [], "count": 0, "symbol": symbol}
    
    try:
        query = client.table("prediction_logs").select(
            "id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, "
            "ml_target_price, ml_stop_price, model_type, strategy, status, "
            "targets_hit, targets, highest_profit_pips, lowest_drawdown_pips, "
            "stop_loss_pips, exit_price, exit_time, created_at, factors"
        ).order("created_at", desc=True).limit(limit * 3)  # Fetch extra to allow for Python filtering

        if days > 0:
            cutoff = _utc_iso(_utc_now() - timedelta(days=days))
            query = query.gte("created_at", cutoff)
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        if not include_active:
            query = query.neq("status", "active")
        
        result = query.execute()
        all_signals = safe_get_data(result)
        
        signals = list(all_signals)

        if model:
            model_lower = model.lower().strip()
            signals = [s for s in signals if _normalize_model_type(s) == model_lower]

        if strategy_scope:
            strategy_scope = strategy_scope.lower().strip()
            signals = [s for s in signals if _resolved_eligible_ml_strategy_scope(s) == strategy_scope]

        signals = signals[:limit]

        enhanced = []
        for sig in signals:
            entry = dict(sig)

            entry["duration_minutes"] = _duration_minutes(sig)
            raw_status = (sig.get("status") or "unknown").lower().strip()
            normalized_status, _, pnl_pips = classify_signal(
                sig,
                default_symbol=sig.get("symbol") or symbol,
            )
            entry["status"] = normalized_status or raw_status or "unknown"
            entry["pnl_pips"] = round(pnl_pips, 2) if pnl_pips is not None else None
            entry["normalized_model"] = _normalize_model_type(sig)
            entry["strategy_scope"] = _resolved_eligible_ml_strategy_scope(sig)
            entry["exit_price"] = resolved_exit_price(sig, default_symbol=sig.get("symbol") or symbol)

            enhanced.append(entry)
        
        return {
            "signals": enhanced,
            "count": len(enhanced),
            "symbol": symbol,
            "strategy_scope": strategy_scope,
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()[:300],
            "signals": [],
            "count": 0,
            "symbol": symbol,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL & TIMEFRAME ANALYSIS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/model-analysis")
async def get_model_timeframe_analysis(
    model: str = Query(..., description="Model type: ml, emel, emel_inverse, pulse1, pulse2, pulse3, smc"),
    symbol: Optional[str] = Query(None, description="Symbol filter: XAUUSD, NDX.INDX, GDAXI.INDX, USOIL.FOREX"),
    timeframe: Optional[str] = Query(None, description="Timeframe: 5m, 15m, 30m, 1h, 4h, 1d"),
    days: int = Query(0, ge=0, le=1095)
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
        import logging as _logging
        _log = _logging.getLogger(__name__)
        
        cutoff = (_utc_now() - timedelta(days=days)) if days > 0 else _ALL_TIME_FLOOR
        cutoff_iso = _utc_iso(cutoff)
        model_lower = model.lower().strip()
        
        # Build query — no model filter at DB level (use Python filtering)
        query = client.table("prediction_logs").select(
            "id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, "
            "ml_target_price, ml_stop_price, model_type, strategy, status, "
            "targets_hit, highest_profit_pips, lowest_drawdown_pips, "
            "exit_price, exit_time, stop_loss_pips, targets, created_at, resolution_reason"
        ).gte("created_at", cutoff_iso).neq("status", "active")
        
        # Optional filters (symbol and timeframe are safe — no .or_() needed)
        if symbol:
            query = query.eq("symbol", symbol)
        if timeframe:
            query = query.eq("timeframe", timeframe)
        
        selected_timeframe = normalize_timeframe(timeframe) if timeframe else None
        if timeframe and selected_timeframe is None:
            return {
                "model": model,
                "symbol": symbol,
                "timeframe": timeframe,
                "total_signals": 0,
                "message": "No signals found for this filter combination"
            }

        result = query.order("created_at", desc=True).limit(1000).execute()
        all_signals = safe_get_data(result)
        
        # Filter by model in Python
        signals = [s for s in all_signals if _normalize_model_type(s) == model_lower]
        
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
            classified_status, _, scored_pips = classify_signal(sig, default_symbol=symbol)
            if classified_status not in {"completed", "stopped", "expired"}:
                continue

            if classified_status == "completed":
                stats["completed"] += 1
            elif classified_status == "stopped":
                stats["stopped"] += 1
            else:
                stats["expired"] += 1
            
            sym = sig.get("symbol", "unknown")
            if sym not in stats["by_symbol"]:
                stats["by_symbol"][sym] = {
                    "total": 0,
                    "completed": 0,
                    "stopped": 0,
                    "expired": 0,
                    "net_pips": 0,
                    "target_hits": {"TP1": 0, "TP2": 0, "TP3": 0, "TP4": 0},
                }
            stats["by_symbol"][sym]["total"] += 1
            if classified_status == "completed":
                stats["by_symbol"][sym]["completed"] += 1
            elif classified_status == "stopped":
                stats["by_symbol"][sym]["stopped"] += 1
            else:
                stats["by_symbol"][sym]["expired"] += 1
            
            tf = normalize_timeframe(sig.get("timeframe"))
            if tf:
                if tf not in stats["by_timeframe"]:
                    stats["by_timeframe"][tf] = {"total": 0, "completed": 0, "stopped": 0, "expired": 0}
                stats["by_timeframe"][tf]["total"] += 1
                if classified_status == "completed":
                    stats["by_timeframe"][tf]["completed"] += 1
                elif classified_status == "stopped":
                    stats["by_timeframe"][tf]["stopped"] += 1
                else:
                    stats["by_timeframe"][tf]["expired"] += 1
            
            direction = sig.get("ml_direction")
            if direction in ["BUY", "SELL"]:
                stats["by_direction"][direction] += 1
            
            targets_hit = normalized_targets_hit(sig, default_symbol=symbol)
            if classified_status in {"completed", "stopped"}:
                for tp in ["TP1", "TP2", "TP3", "TP4"]:
                    if targets_hit.get(tp):
                        stats["target_hits"][tp] += 1
                        stats["by_symbol"][sym]["target_hits"][tp] += 1
            
            if classified_status == "completed":
                profit = max(scored_pips or 0.0, 0.0)
                stats["total_profit_pips"] += profit
                profits.append(profit)
                if sym in stats["by_symbol"]:
                    stats["by_symbol"][sym]["net_pips"] += profit
            elif classified_status == "stopped":
                loss = abs(scored_pips or 0.0)
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
            target_rates[tp] = round(hits / total_with_outcome * 100, 1) if total_with_outcome > 0 else 0

        by_symbol = {}
        for sym, sym_stats in stats["by_symbol"].items():
            sym_total_with_outcome = sym_stats["completed"] + sym_stats["stopped"]
            by_symbol[sym] = {
                "total": sym_stats["total"],
                "completed": sym_stats["completed"],
                "stopped": sym_stats["stopped"],
                "expired": sym_stats["expired"],
                "net_pips": sym_stats["net_pips"],
                "win_rate": round(sym_stats["completed"] / sym_total_with_outcome * 100, 1) if sym_total_with_outcome > 0 else 0,
                "target_rates": {
                    tp: round(hits / sym_total_with_outcome * 100, 1) if sym_total_with_outcome > 0 else 0
                    for tp, hits in sym_stats["target_hits"].items()
                },
            }
        
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
            "by_symbol": by_symbol,
            "by_timeframe": stats["by_timeframe"],
            "by_direction": stats["by_direction"],
            "signals": signals[:20],  # Last 20 signals for display
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()[:500]}


@router.get("/model-analysis/summary")
async def get_all_models_summary(
    days: int = Query(0, ge=0, le=1095),
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
        cutoff = (_utc_now() - timedelta(days=days)) if days > 0 else _ALL_TIME_FLOOR
        cutoff_iso = _utc_iso(cutoff)
        
        # Day-by-day pagination to bypass Supabase 1000-row cap
        signals = []
        start = cutoff
        end = _utc_now()
        cur = start
        while cur < end:
            ds = cur.replace(hour=0,minute=0,second=0,microsecond=0)
            de = ds + timedelta(days=1)
            q = client.table("prediction_logs").select(
                "symbol, timeframe, model_type, strategy, status, "
                "highest_profit_pips, lowest_drawdown_pips, stop_loss_pips, targets_hit, created_at"
            ).gte("created_at", _utc_iso(ds)).lt("created_at", _utc_iso(de)).neq("status", "active")
            if symbol:
                q = q.eq("symbol", symbol)
            batch = safe_get_data(q.order("created_at", desc=True).limit(1000).execute())
            if batch:
                signals.extend(batch)
            cur = de
        
        # Initialize model structure
        MODELS = ["ml", "ai_panel", "emel", "emel_inverse", "pulse1", "pulse2", "pulse3", "smc"]
        TIMEFRAMES = list(TIMEFRAME_ORDER)
        
        summary = {}
        for model in MODELS:
            summary[model] = {
                "total_signals": 0,
                "by_timeframe": {tf: {"total": 0, "completed": 0, "stopped": 0, "expired": 0, "win_rate": 0} for tf in TIMEFRAMES},
                "overall_win_rate": 0,
                "total_completed": 0,
                "total_stopped": 0,
                "total_expired": 0,
            }
        
        for sig in signals:
            model_key = normalize_model_type(sig)
            
            if model_key not in summary:
                continue

            classified_status, _, _ = classify_signal(sig, default_symbol=symbol)
            if classified_status not in {"completed", "stopped", "expired"}:
                continue
            
            summary[model_key]["total_signals"] += 1
            tf = normalize_timeframe(sig.get("timeframe"))
            if tf:
                summary[model_key]["by_timeframe"][tf]["total"] += 1
            
            if classified_status == "completed":
                summary[model_key]["total_completed"] += 1
                if tf:
                    summary[model_key]["by_timeframe"][tf]["completed"] += 1
            elif classified_status == "stopped":
                summary[model_key]["total_stopped"] += 1
                if tf:
                    summary[model_key]["by_timeframe"][tf]["stopped"] += 1
            else:
                summary[model_key]["total_expired"] += 1
                if tf:
                    summary[model_key]["by_timeframe"][tf]["expired"] += 1
        
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
        # Query all recent signals and filter model type in Python
        model_lower = model.lower().strip()
        
        result = client.table("prediction_logs").select(
            "timeframe, model_type, strategy"
        ).limit(1000).execute()
        all_signals = safe_get_data(result)
        
        # Filter by model in Python
        signals = [s for s in all_signals if _normalize_model_type(s) == model_lower]
        
        timeframes = sort_timeframes(
            normalize_timeframe(s.get("timeframe")) for s in signals
        )
        
        # Default available timeframes by model
        DEFAULT_TFS = {
            "ml": ["1h"],  # ML typically only on 1h
            "pulse1": ["5m", "15m"],
            "pulse2": ["5m", "15m", "1h"],
            "pulse3": ["1h"],  # Pulse3 typically only on 1h
            "emel": ["5m", "15m", "1h", "4h"],
            "emel_inverse": ["5m", "15m", "1h", "4h"],
            "smc": ["5m", "15m", "30m", "1h", "4h", "1d"],
            "hybrid": ["1h"],
        }
        
        available = sort_timeframes(timeframes + DEFAULT_TFS.get(model_lower, ["1h"]))
        
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
        # Find stuck XAUUSD signals
        cutoff = _utc_iso(_utc_now() - timedelta(hours=max_age_hours))
        
        result = client.table("prediction_logs").select(
            "id, symbol, ml_direction, model_type, strategy, status, created_at, ml_entry_price"
        ).eq("symbol", "XAUUSD").eq("status", "active").lt("created_at", cutoff).limit(200).execute()
        
        stuck_signals = safe_get_data(result)
        
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
                    "exit_time": _utc_iso(),
                    "exit_price": sig.get("ml_entry_price"),  # Use entry price as exit
                    "targets_hit": {"TP1": False, "TP2": False, "TP3": False, "TP4": False},
                }).execute()
                
                if update_result and safe_get_data(update_result):
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
        # Get all XAUUSD signals from last 7 days
        cutoff = _utc_iso(_utc_now() - timedelta(days=7))
        
        result = client.table("prediction_logs").select(
            "id, model_type, strategy, status, ml_direction, created_at, exit_time"
        ).eq("symbol", "XAUUSD").gte("created_at", cutoff).limit(500).execute()
        
        signals = safe_get_data(result)
        
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
        one_hour_ago = _utc_iso(_utc_now() - timedelta(hours=1))
        old_active_result = client.table("prediction_logs").select(
            "id, model_type, strategy, created_at, ml_entry_price"
        ).eq("symbol", "XAUUSD").eq("status", "active").lt("created_at", one_hour_ago).limit(100).execute()
        
        old_active = safe_get_data(old_active_result)
        
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


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL DETAIL ANALYTICS — Comprehensive performance breakdown
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_model_type(sig: dict) -> str:
    """Normalize model_type from a prediction_logs record — same logic as dashboard."""
    return normalize_model_type(sig)


@router.get("/model-detail-analytics")
async def get_model_detail_analytics(
    model: Optional[str] = Query(None, description="Model type (ml, emel, pulse1, pulse2, pulse3, emel_inverse, smc, hybrid) or 'all'"),
    symbol: str = Query(..., description="Symbol (NDX.INDX, XAUUSD, GDAXI.INDX, USOIL.FOREX, CL.F)"),
    days: int = Query(0, ge=0, le=3650, description="Days to look back (0 = all available history)"),
    timeframe: Optional[str] = Query(None, description="Optional timeframe filter (5m, 15m, 30m, 1h, 4h, 1d, or 'all')")
):
    """
    Comprehensive model performance analytics for a model+symbol pair.
    Backward-compatible response with richer metadata for all-model and
    timeframe-aware drilldowns.
    """
    requested_model = (model or "all").lower().strip() or "all"
    resolved_model = "all" if requested_model in {"all", "*"} else requested_model
    selected_timeframe = (timeframe or "all").lower().strip() or "all"
    if selected_timeframe in {"*", "all"}:
        selected_timeframe = "all"
    default_hourly_contract = _model_detail_hourly_contract(symbol)

    def _empty_payload(
        error: Optional[str] = None,
        *,
        available_timeframes: Optional[List[str]] = None,
        available_models: Optional[List[str]] = None,
        model_comparison: Optional[list] = None,
        meta_overrides: Optional[dict] = None,
    ) -> dict:
        payload = {
            "model": resolved_model,
            "symbol": symbol,
            "overview": {
                "total_signals": 0,
                "win_rate": 0,
                "completed": 0,
                "stopped": 0,
                "expired": 0,
                "active": 0,
                "net_pips": 0,
                "avg_profit_pips": 0,
                "avg_loss_pips": 0,
                "risk_reward": 0,
                "sharpe_ratio": 0,
                "max_drawdown_pips": 0,
                "profit_factor": 0,
            },
            "hourly_heatmap": [],
            "timeframe_comparison": [],
            "daily_accuracy": [],
            "day_of_week": [],
            "tp_hit_rates": {},
            "recent_signals": [],
            "selected_timeframe": selected_timeframe,
            "available_timeframes": available_timeframes or [],
            "available_models": available_models or [],
            "model_comparison": model_comparison or [],
            "meta": {
                "requested_model": requested_model,
                "selected_model": resolved_model,
                "selected_timeframe": selected_timeframe,
                "available_timeframes": available_timeframes or [],
                "available_models": available_models or [],
                "days": days,
                "all_time": days == 0,
                "date_from": None,
                "date_to": None,
                "scope_total_signals": 0,
                "filtered_total_signals": 0,
                "hourly_visible_hours": default_hourly_contract["hours"],
                "hourly_window_label": default_hourly_contract["window_label"],
                "hourly_session_key": default_hourly_contract["session_key"],
            },
        }
        if meta_overrides:
            payload["meta"].update(meta_overrides)
        if error:
            payload["error"] = error
        return payload

    if not is_db_available():
        return _empty_payload(error="Database not available")

    client = get_supabase_client()
    if not client:
        return _empty_payload(error="Database client not available")

    try:
        from dateutil import parser as dt_parser
        import json as _json
        import math
        import logging as _logging
        _log = _logging.getLogger(__name__)

        tf_order = list(TIMEFRAME_ORDER)
        model_order = list(MODEL_ORDER)

        def _sort_timeframes(values: List[str]) -> List[str]:
            return sort_timeframes(values)

        def _sort_models(values: List[str]) -> List[str]:
            return sort_models(values)

        def _normalize_timeframe(value: Optional[str]) -> Optional[str]:
            return normalize_timeframe(value)

        def _coerce_float(value, default: Optional[float] = None) -> Optional[float]:
            return analytics_coerce_float(value, default)

        def _realized_pips(sig: dict) -> Optional[float]:
            return realized_pips(sig, default_symbol=symbol)

        def _parse_datetime(value: Optional[str]):
            if not value:
                return None
            try:
                parsed = dt_parser.parse(value)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except Exception:
                return None

        def _normalized_targets_hit(sig: dict):
            return normalized_targets_hit(sig, default_symbol=symbol)

        def _classify_signal(sig: dict):
            return classify_signal(sig, default_symbol=symbol)

        def _summarize_scope(scope_signals: List[dict]) -> dict:
            return summarize_scope(scope_signals, default_symbol=symbol)

        if days > 0:
            start_date = _utc_now() - timedelta(days=days)
        else:
            oldest_result = client.table("prediction_logs").select(
                "created_at"
            ).eq("symbol", symbol).order("created_at", desc=False).limit(1).execute()
            oldest_rows = safe_get_data(oldest_result) or []
            oldest_dt = _parse_datetime(oldest_rows[0].get("created_at")) if oldest_rows else None
            if oldest_dt is None:
                return _empty_payload(
                    meta_overrides={
                        "date_to": _utc_iso(),
                    }
                )
            start_date = _as_utc(oldest_dt)

        end_date = _utc_now()
        all_signals = []
        current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        while current < end_date:
            day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            result = client.table("prediction_logs").select(
                "id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, "
                "ml_target_price, ml_stop_price, model_type, strategy, status, "
                "targets_hit, highest_profit_pips, lowest_drawdown_pips, "
                "exit_price, exit_time, stop_loss_pips, targets, created_at, resolution_reason"
            ).eq("symbol", symbol).gte(
                "created_at", _utc_iso(day_start)
            ).lt(
                "created_at", _utc_iso(day_end)
            ).order("created_at", desc=True).limit(1000).execute()

            batch = safe_get_data(result)
            if batch:
                all_signals.extend(batch)
            current = day_end

        if not all_signals:
            return _empty_payload(
                meta_overrides={
                    "date_from": _utc_iso(start_date),
                    "date_to": _utc_iso(end_date),
                }
            )

        prepared_signals = []
        for sig in all_signals:
            created_dt = _parse_datetime(sig.get("created_at")) or _utc_now()
            prepared_signals.append({
                **sig,
                "_created_dt": created_dt,
                "_timeframe": _normalize_timeframe(sig.get("timeframe")),
                "_normalized_model": _normalize_model_type(sig),
            })

        comparison_model_source = prepared_signals if selected_timeframe == "all" else [
            sig for sig in prepared_signals if sig["_timeframe"] == selected_timeframe
        ]
        available_models = _sort_models(list({
            sig["_normalized_model"] for sig in comparison_model_source if sig.get("_normalized_model")
        }))

        model_scope_signals = prepared_signals if resolved_model == "all" else [
            sig for sig in prepared_signals if sig["_normalized_model"] == resolved_model
        ]
        available_timeframes = _sort_timeframes(list({
            sig["_timeframe"] for sig in model_scope_signals if sig.get("_timeframe")
        }))
        filtered_signals = model_scope_signals if selected_timeframe == "all" else [
            sig for sig in model_scope_signals if sig["_timeframe"] == selected_timeframe
        ]

        _log.info(
            "model-detail-analytics: %s raw → %s model-scope → %s filtered for model=%s timeframe=%s symbol=%s",
            len(prepared_signals),
            len(model_scope_signals),
            len(filtered_signals),
            resolved_model,
            selected_timeframe,
            symbol,
        )

        model_comparison = []
        model_groups = {}
        for sig in comparison_model_source:
            model_key = sig["_normalized_model"]
            model_groups.setdefault(model_key, []).append(sig)
        for model_key in _sort_models(list(model_groups.keys())):
            summary = _summarize_scope(model_groups[model_key])
            model_comparison.append({
                "model": model_key,
                "total": summary["total_signals"],
                "scored_signals": summary["scored_signals"],
                "completed": summary["completed"],
                "stopped": summary["stopped"],
                "expired": summary["expired"],
                "active": summary["active"],
                "win_rate": summary["win_rate"],
                "net_pips": summary["net_pips"],
                "avg_pips": summary["avg_pips"],
            })

        if not model_scope_signals:
            return _empty_payload(
                available_timeframes=available_timeframes,
                available_models=available_models,
                model_comparison=model_comparison,
                meta_overrides={
                    "date_from": _utc_iso(start_date),
                    "date_to": _utc_iso(end_date),
                },
            )

        if selected_timeframe != "all" and not filtered_signals:
            return _empty_payload(
                available_timeframes=available_timeframes,
                available_models=available_models,
                model_comparison=model_comparison,
                meta_overrides={
                    "date_from": _utc_iso(start_date),
                    "date_to": _utc_iso(end_date),
                    "scope_total_signals": len(model_scope_signals),
                },
            )

        now_utc = datetime.now(timezone.utc)
        total_signals = len(filtered_signals)
        completed = 0
        stopped = 0
        expired = 0
        active = 0
        total_profit_pips = 0.0
        total_loss_pips = 0.0
        win_pips_list = []
        loss_pips_list = []
        cumulative_pips = 0.0
        peak_pips = 0.0
        max_drawdown = 0.0

        # Aggregation buckets
        hourly_stats = {
            h: {"resolved_total": 0, "scored_total": 0, "wins": 0, "losses": 0, "pips": 0.0}
            for h in range(24)
        }
        tf_stats = {}
        daily_stats = {}
        tp_counts = {"TP1": 0, "TP2": 0, "TP3": 0, "TP4": 0}

        chronologically_sorted = sorted(filtered_signals, key=lambda sig: sig["_created_dt"])
        recent_signals_source = sorted(filtered_signals, key=lambda sig: sig["_created_dt"], reverse=True)

        for sig in chronologically_sorted:
            status, is_win, pips_change = _classify_signal(sig)
            created_dt = sig.get("_created_dt") or now_utc
            hour = created_dt.hour
            dow = created_dt.weekday()
            date_key = created_dt.strftime("%Y-%m-%d")
            
            if status == "active":
                active += 1
                continue
            if status is None or status == "direction_flip":
                continue

            if status == "completed":
                completed += 1
                total_profit_pips += pips_change or 0.0
                win_pips_list.append(pips_change or 0.0)
            elif status == "stopped":
                stopped += 1
                total_loss_pips += abs(pips_change or 0.0)
                loss_pips_list.append(abs(pips_change or 0.0))
            elif status == "expired":
                expired += 1
                continue

            # Cumulative pips for Sharpe / drawdown
            cumulative_pips += pips_change or 0.0
            if cumulative_pips > peak_pips:
                peak_pips = cumulative_pips
            dd = peak_pips - cumulative_pips
            if dd > max_drawdown:
                max_drawdown = dd

            # Hourly bucket
            hourly_stats[hour]["resolved_total"] += 1
            hourly_stats[hour]["pips"] += pips_change or 0.0

            # Timeframe bucket
            if sig["_timeframe"]:
                if sig["_timeframe"] not in tf_stats:
                    tf_stats[sig["_timeframe"]] = {"total": 0, "wins": 0, "pips": 0.0}
                tf_stats[sig["_timeframe"]]["total"] += 1
                if is_win:
                    tf_stats[sig["_timeframe"]]["wins"] += 1
                tf_stats[sig["_timeframe"]]["pips"] += pips_change or 0.0

            # Daily bucket
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "resolved_total": 0,
                    "scored_total": 0,
                    "wins": 0,
                    "losses": 0,
                    "pips": 0.0,
                    "cumulative": 0.0,
                    "dow": dow,
                }
            daily_stats[date_key]["resolved_total"] += 1
            daily_stats[date_key]["pips"] += pips_change or 0.0

            if status in {"completed", "stopped"}:
                hourly_stats[hour]["scored_total"] += 1
                daily_stats[date_key]["scored_total"] += 1
                if status == "completed":
                    hourly_stats[hour]["wins"] += 1
                    daily_stats[date_key]["wins"] += 1
                else:
                    hourly_stats[hour]["losses"] += 1
                    daily_stats[date_key]["losses"] += 1

            # TP hit rates
            th = _normalized_targets_hit(sig)
            if status in {"completed", "stopped"} and th:
                for tp_key in ["TP1", "TP2", "TP3", "TP4"]:
                    if th.get(tp_key):
                        tp_counts[tp_key] += 1

        # ── 3. Calculate derived metrics ──
        resolved = completed + stopped
        win_rate = (completed / resolved * 100) if resolved > 0 else 0
        avg_profit = (sum(win_pips_list) / len(win_pips_list)) if win_pips_list else 0
        avg_loss = (sum(loss_pips_list) / len(loss_pips_list)) if loss_pips_list else 0
        risk_reward = (avg_profit / avg_loss) if avg_loss > 0 else 0
        net_pips = total_profit_pips - total_loss_pips
        profit_factor = (total_profit_pips / total_loss_pips) if total_loss_pips > 0 else 0

        # Sharpe ratio (simplified: mean pips / std pips, annualized)
        all_pips = win_pips_list + [-lp for lp in loss_pips_list]
        sharpe = 0.0
        if len(all_pips) >= 2:
            mean_p = sum(all_pips) / len(all_pips)
            var_p = sum((p - mean_p) ** 2 for p in all_pips) / (len(all_pips) - 1)
            std_p = math.sqrt(var_p) if var_p > 0 else 1
            sharpe = round((mean_p / std_p) * math.sqrt(252), 2)

        # ── 4. Build response ──

        # Hourly heatmap
        observed_hours = {hour for hour, bucket in hourly_stats.items() if bucket["resolved_total"] > 0}
        hourly_contract = _model_detail_hourly_contract(symbol, observed_hours=observed_hours)
        hourly_heatmap = []
        for h in hourly_contract["hours"]:
            s = hourly_stats[h]
            hourly_heatmap.append({
                "hour": h,
                "total": s["scored_total"],
                "wins": s["wins"],
                "win_rate": round((s["wins"] / s["scored_total"] * 100) if s["scored_total"] > 0 else 0, 1),
                "avg_pips": round(s["pips"] / s["scored_total"], 1) if s["scored_total"] > 0 else 0,
            })

        # Timeframe comparison
        timeframe_comparison = []
        comparison_tf_groups = {}
        for sig in model_scope_signals:
            tf_key = sig.get("_timeframe")
            if not tf_key:
                continue
            comparison_tf_groups.setdefault(tf_key, []).append(sig)
        for tf_key in _sort_timeframes(list(comparison_tf_groups.keys())):
            summary = _summarize_scope(comparison_tf_groups[tf_key])
            if summary["scored_signals"] > 0:
                timeframe_comparison.append({
                    "tf": tf_key,
                    "total": summary["scored_signals"],
                    "active": summary["active"],
                    "win_rate": summary["win_rate"],
                    "net_pips": summary["net_pips"],
                    "avg_pips": summary["avg_pips"],
                })

        # Daily accuracy (sorted by date, with cumulative)
        sorted_dates = sorted(daily_stats.keys())
        daily_accuracy = []
        running_cum = 0.0
        for dk in sorted_dates:
            if dk == "unknown":
                continue
            ds = daily_stats[dk]
            running_cum += ds["pips"]
            daily_accuracy.append({
                "date": dk,
                "total": ds["resolved_total"],
                "wins": ds["wins"],
                "win_rate": round((ds["wins"] / ds["scored_total"] * 100) if ds["scored_total"] > 0 else 0, 1),
                "cumulative_pips": round(running_cum, 1),
            })

        # Day of week
        dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dow_daily_groups = {d: [] for d in range(7)}
        for day_bucket in daily_stats.values():
            day_dow = day_bucket.get("dow")
            if isinstance(day_dow, int) and 0 <= day_dow <= 6 and day_bucket.get("scored_total", 0) > 0:
                dow_daily_groups[day_dow].append(day_bucket)

        day_of_week = []
        for d in range(7):
            daily_buckets = dow_daily_groups[d]
            weekday_total = sum(bucket["scored_total"] for bucket in daily_buckets)
            wins = sum(bucket["wins"] for bucket in daily_buckets)
            avg_day_win_rate = (
                sum((bucket["wins"] / bucket["scored_total"] * 100) for bucket in daily_buckets if bucket["scored_total"] > 0)
                / len(daily_buckets)
            ) if daily_buckets else 0.0
            avg_day_pips = (
                sum(bucket["pips"] for bucket in daily_buckets) / len(daily_buckets)
            ) if daily_buckets else 0.0
            day_of_week.append({
                "day": dow_names[d],
                "day_short": dow_names[d][:3],
                "total": weekday_total,
                "wins": wins,
                "win_rate": round(avg_day_win_rate, 1),
                "avg_pips": round(avg_day_pips, 1),
            })

        # TP hit rates
        tp_hit_rates = {}
        for tp_key in ["TP1", "TP2", "TP3", "TP4"]:
            tp_hit_rates[tp_key] = round(
                (tp_counts[tp_key] / resolved * 100) if resolved > 0 else 0, 1
            )

        recent_signals = []
        for sig in recent_signals_source[:30]:
            recent_status, _, recent_pips = _classify_signal(sig)
            raw_status = (sig.get("status") or "unknown").lower().strip()
            recent_signals.append({
                "id": (sig.get("id") or "")[:8],
                "date": sig.get("created_at") or "",
                "direction": sig.get("ml_direction", "HOLD"),
                "confidence": round(_coerce_float(sig.get("ml_confidence"), 50.0) or 50.0, 1),
                "status": recent_status or raw_status or "unknown",
                "pips": round(recent_pips or 0.0, 1),
                "timeframe": sig.get("_timeframe") or "legacy",
                "entry_price": _coerce_float(sig.get("ml_entry_price")),
                "exit_price": resolved_exit_price(sig, default_symbol=symbol),
            })

        return {
            "model": resolved_model,
            "symbol": symbol,
            "overview": {
                "total_signals": total_signals,
                "win_rate": round(win_rate, 1),
                "completed": completed,
                "stopped": stopped,
                "expired": expired,
                "active": active,
                "net_pips": round(net_pips, 1),
                "avg_profit_pips": round(avg_profit, 1),
                "avg_loss_pips": round(avg_loss, 1),
                "risk_reward": round(risk_reward, 2),
                "sharpe_ratio": sharpe,
                "max_drawdown_pips": round(max_drawdown, 1),
                "profit_factor": round(profit_factor, 2),
            },
            "hourly_heatmap": hourly_heatmap,
            "timeframe_comparison": timeframe_comparison,
            "daily_accuracy": daily_accuracy[-60:],  # Last 60 days
            "day_of_week": day_of_week,
            "tp_hit_rates": tp_hit_rates,
            "recent_signals": recent_signals,
            "selected_timeframe": selected_timeframe,
            "available_timeframes": available_timeframes,
            "available_models": available_models,
            "model_comparison": model_comparison,
            "meta": {
                "requested_model": requested_model,
                "selected_model": resolved_model,
                "selected_timeframe": selected_timeframe,
                "available_timeframes": available_timeframes,
                "available_models": available_models,
                "days": days,
                "all_time": days == 0,
                "date_from": _utc_iso(start_date),
                "date_to": _utc_iso(end_date),
                "scope_total_signals": len(model_scope_signals),
                "filtered_total_signals": len(filtered_signals),
                "hourly_visible_hours": hourly_contract["hours"],
                "hourly_window_label": hourly_contract["window_label"],
                "hourly_session_key": hourly_contract["session_key"],
            },
        }

    except Exception as e:
        import traceback
        import logging as _logging
        _logging.getLogger(__name__).error(f"Model detail analytics error: {e}\n{traceback.format_exc()}")
        return _empty_payload(error=str(e), meta_overrides={"traceback": traceback.format_exc()[:500]})
