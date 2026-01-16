"""
Outcome Tracker Service
Checks predictions after specified intervals to see if they were correct.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database.supabase_client import get_supabase_client, is_db_available
from services.data_fetcher import fetch_latest_price
from services.prediction_logger import mark_prediction_checked
from services.target_config import (
    get_symbol_config,
    calculate_target_prices,
    calculate_stoploss_price,
    pips_from_price_change,
)

logger = logging.getLogger(__name__)

FLAT_THRESHOLD_PCT = 0.1

# Check intervals including 1h
CHECK_INTERVALS = ["1h", "4h", "24h", "48h", "7d"]


def _determine_actual_direction(price_change_pct: float) -> str:
    """Determine actual price direction based on percentage change."""
    if price_change_pct > FLAT_THRESHOLD_PCT:
        return "UP"
    elif price_change_pct < -FLAT_THRESHOLD_PCT:
        return "DOWN"
    return "FLAT"


def _is_prediction_correct(predicted: str, actual: str) -> bool:
    """Check if prediction was correct."""
    if predicted == "HOLD":
        return actual == "FLAT"
    if predicted == "BUY":
        return actual == "UP"
    if predicted == "SELL":
        return actual == "DOWN"
    return False


async def check_prediction_outcome(
    prediction: Dict[str, Any],
    check_interval: str = "24h"
) -> Optional[Dict[str, Any]]:
    """
    Check the outcome of a single prediction.
    
    Args:
        prediction: Prediction record from database
        check_interval: Time interval to check ('1h', '4h', '24h', '48h', '7d')
    
    Returns:
        Outcome result dict if successful, None otherwise
    """
    if not is_db_available():
        return None
    
    client = get_supabase_client()
    if client is None:
        return None
    
    symbol = prediction.get("symbol")
    entry_price = prediction.get("ml_entry_price")
    target_price = prediction.get("ml_target_price")
    stop_price = prediction.get("ml_stop_price")
    
    if not symbol or entry_price is None:
        logger.warning(f"Invalid prediction data: {prediction.get('id')}")
        return None
    
    try:
        current_price = await fetch_latest_price(symbol)
        if current_price is None:
            logger.warning(f"Could not fetch current price for {symbol}")
            return None
        
        price_change_pct = ((current_price - entry_price) / entry_price) * 100
        actual_direction = _determine_actual_direction(price_change_pct)
        
        hit_target = False
        hit_stop = False
        if target_price and current_price >= target_price:
            hit_target = True
        if stop_price and current_price <= stop_price:
            hit_stop = True
        
        ml_direction = prediction.get("ml_direction", "HOLD")
        claude_direction = prediction.get("claude_direction")
        
        ml_correct = _is_prediction_correct(ml_direction, actual_direction)
        claude_correct = _is_prediction_correct(claude_direction, actual_direction) if claude_direction else None
        
        outcome = {
            "prediction_id": prediction.get("id"),
            "check_interval": check_interval,
            "entry_price": float(entry_price),
            "exit_price": float(current_price),
            "price_change_pct": round(price_change_pct, 4),
            "actual_direction": actual_direction,
            "hit_target": hit_target,
            "hit_stop": hit_stop,
            "ml_correct": ml_correct,
            "claude_correct": claude_correct,
        }
        
        result = client.table("outcome_results").insert(outcome).execute()
        
        if result.get("data"):
            logger.info(f"Recorded outcome for prediction {prediction.get('id')}: ML {'✓' if ml_correct else '✗'}")
            return outcome
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to check prediction outcome: {e}")
        return None


async def check_pending_outcomes(check_interval: str = "24h") -> List[Dict[str, Any]]:
    """
    Check outcomes for all pending predictions that are old enough.
    
    Args:
        check_interval: Which interval to check ('1h', '4h', '24h', '48h', '7d')
    
    Returns:
        List of outcome results
    """
    if not is_db_available():
        return []
    
    client = get_supabase_client()
    if client is None:
        return []
    
    interval_hours = {
        "1h": 1,
        "4h": 4,
        "24h": 24,
        "48h": 48,
        "7d": 168,
    }
    
    hours = interval_hours.get(check_interval, 24)
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    cutoff_iso = cutoff.isoformat() + "Z"
    
    try:
        result = client.table("prediction_logs").select("*").eq(
            "outcome_checked", False
        ).lt("created_at", cutoff_iso).limit(100).execute()
        
        predictions = result.get("data") or []
        
        if not predictions:
            logger.info(f"No pending predictions older than {check_interval}")
            return []
        
        logger.info(f"Checking {len(predictions)} pending predictions for {check_interval} outcomes")
        
        outcomes = []
        for pred in predictions:
            existing = client.table("outcome_results").select("id").eq(
                "prediction_id", pred["id"]
            ).eq("check_interval", check_interval).execute()
            
            if existing.get("data"):
                continue
            
            outcome = await check_prediction_outcome(pred, check_interval)
            if outcome:
                outcomes.append(outcome)
            
            if check_interval == "24h":
                await mark_prediction_checked(pred["id"])
        
        return outcomes
        
    except Exception as e:
        logger.error(f"Failed to check pending outcomes: {e}")
        return []


async def get_accuracy_summary(
    symbol: Optional[str] = None,
    days: int = 7,
    check_interval: str = "24h"
) -> Dict[str, Any]:
    """
    Get accuracy summary for recent predictions.
    
    Args:
        symbol: Filter by symbol (optional)
        days: Number of days to look back
        check_interval: Which outcome interval to use
    
    Returns:
        Summary dict with accuracy metrics
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_iso = cutoff.isoformat() + "Z"
    
    try:
        query = client.table("outcome_results").select(
            "*, prediction_logs!inner(symbol, ml_direction, claude_direction, factors)"
        ).eq("check_interval", check_interval).gte("created_at", cutoff_iso)
        
        if symbol:
            query = query.eq("prediction_logs.symbol", symbol)
        
        result = query.execute()
        outcomes = result.get("data") or []
        
        if not outcomes:
            return {
                "symbol": symbol,
                "period_days": days,
                "check_interval": check_interval,
                "total_predictions": 0,
                "ml_accuracy": None,
                "claude_accuracy": None,
            }
        
        total = len(outcomes)
        ml_correct = sum(1 for o in outcomes if o.get("ml_correct"))
        claude_outcomes = [o for o in outcomes if o.get("claude_correct") is not None]
        claude_correct = sum(1 for o in claude_outcomes if o.get("claude_correct"))
        
        both_correct = sum(1 for o in outcomes if o.get("ml_correct") and o.get("claude_correct"))
        either_correct = sum(1 for o in outcomes if o.get("ml_correct") or o.get("claude_correct"))
        
        return {
            "symbol": symbol,
            "period_days": days,
            "check_interval": check_interval,
            "total_predictions": total,
            "ml_accuracy": round(ml_correct / total, 3) if total > 0 else None,
            "ml_correct_count": ml_correct,
            "claude_accuracy": round(claude_correct / len(claude_outcomes), 3) if claude_outcomes else None,
            "claude_correct_count": claude_correct,
            "both_correct_rate": round(both_correct / total, 3) if total > 0 else None,
            "either_correct_rate": round(either_correct / total, 3) if total > 0 else None,
        }
        
    except Exception as e:
        logger.error(f"Failed to get accuracy summary: {e}")
        return {"error": str(e)}


async def check_multi_target_outcome(
    prediction: Dict[str, Any],
    check_interval: str = "1h"
) -> Optional[Dict[str, Any]]:
    """
    Check prediction outcome with multiple target levels.
    
    Args:
        prediction: Prediction record from database
        check_interval: Time interval ('1h', '4h', '24h', etc.)
    
    Returns:
        Outcome with target hit information
    """
    if not is_db_available():
        return None
    
    client = get_supabase_client()
    if client is None:
        return None
    
    symbol = prediction.get("symbol")
    entry_price = prediction.get("ml_entry_price")
    ml_direction = prediction.get("ml_direction", "HOLD")
    claude_direction = prediction.get("claude_direction")
    
    if not symbol or entry_price is None:
        return None
    
    try:
        current_price = await fetch_latest_price(symbol)
        if current_price is None:
            return None
        
        config = get_symbol_config(symbol)
        
        # Calculate targets and stoploss
        targets = calculate_target_prices(entry_price, ml_direction, symbol)
        stoploss = calculate_stoploss_price(entry_price, ml_direction, symbol)
        
        # Price change in pips
        price_change = current_price - entry_price
        pips_moved = pips_from_price_change(abs(price_change), symbol)
        if ml_direction == "SELL":
            pips_moved = -pips_moved if price_change > 0 else pips_moved
        else:
            pips_moved = pips_moved if price_change > 0 else -pips_moved
        
        # Check each target
        targets_hit = {}
        for target_name, target_price in targets.items():
            if ml_direction == "BUY":
                targets_hit[target_name] = current_price >= target_price
            elif ml_direction == "SELL":
                targets_hit[target_name] = current_price <= target_price
            else:
                targets_hit[target_name] = False
        
        # Check stoploss
        hit_stoploss = False
        if ml_direction == "BUY":
            hit_stoploss = current_price <= stoploss
        elif ml_direction == "SELL":
            hit_stoploss = current_price >= stoploss
        
        # Direction-based correctness
        price_change_pct = ((current_price - entry_price) / entry_price) * 100
        actual_direction = _determine_actual_direction(price_change_pct)
        ml_correct = _is_prediction_correct(ml_direction, actual_direction)
        claude_correct = _is_prediction_correct(claude_direction, actual_direction) if claude_direction else None
        
        outcome = {
            "prediction_id": prediction.get("id"),
            "check_interval": check_interval,
            "entry_price": float(entry_price),
            "exit_price": float(current_price),
            "price_change_pct": round(price_change_pct, 4),
            "pips_moved": round(pips_moved, 1),
            "actual_direction": actual_direction,
            "targets_hit": targets_hit,
            "hit_stoploss": hit_stoploss,
            "stoploss_price": stoploss,
            "target_prices": targets,
            "ml_correct": ml_correct,
            "claude_correct": claude_correct,
        }
        
        # Store in database with extended data
        db_outcome = {
            "prediction_id": prediction.get("id"),
            "check_interval": check_interval,
            "entry_price": float(entry_price),
            "exit_price": float(current_price),
            "price_change_pct": round(price_change_pct, 4),
            "actual_direction": actual_direction,
            "hit_target": any(targets_hit.values()),
            "hit_stop": hit_stoploss,
            "ml_correct": ml_correct,
            "claude_correct": claude_correct,
        }
        
        client.table("outcome_results").insert(db_outcome).execute()
        
        return outcome
        
    except Exception as e:
        logger.error(f"Failed to check multi-target outcome: {e}")
        return None


async def get_multi_target_accuracy(
    symbol: Optional[str] = None,
    days: int = 7,
    check_interval: str = "1h"
) -> Dict[str, Any]:
    """
    Get accuracy summary broken down by target levels.
    
    Args:
        symbol: Filter by symbol
        days: Number of days to look back
        check_interval: Which interval to analyze
    
    Returns:
        Accuracy metrics per target level
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if client is None:
        return {"error": "Database client not available"}
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_iso = cutoff.isoformat() + "Z"
    
    try:
        # Get predictions with outcomes
        query = client.table("prediction_logs").select(
            "*, outcome_results(*)"
        ).gte("created_at", cutoff_iso)
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        result = query.execute()
        predictions = result.get("data") or []
        
        if not predictions:
            return {
                "symbol": symbol,
                "period_days": days,
                "check_interval": check_interval,
                "total_predictions": 0,
                "target_accuracy": {},
            }
        
        # Get symbol config for target names
        config = get_symbol_config(symbol) if symbol else None
        target_names = [t.name for t in config.targets] if config else ["TP1", "TP2", "TP3"]
        
        # Calculate live target accuracy by re-checking current prices
        target_stats = {name: {"hit": 0, "total": 0} for name in target_names}
        stoploss_stats = {"hit": 0, "total": 0}
        direction_stats = {"ml_correct": 0, "claude_correct": 0, "total": 0}
        
        for pred in predictions:
            entry_price = pred.get("ml_entry_price")
            ml_direction = pred.get("ml_direction")
            pred_symbol = pred.get("symbol")
            
            if not entry_price or ml_direction == "HOLD":
                continue
            
            # Get latest outcome for this prediction
            outcomes = pred.get("outcome_results", [])
            relevant_outcome = None
            for o in outcomes:
                if o.get("check_interval") == check_interval:
                    relevant_outcome = o
                    break
            
            if not relevant_outcome:
                continue
            
            exit_price = relevant_outcome.get("exit_price")
            if not exit_price:
                continue
            
            # Calculate targets for this prediction
            targets = calculate_target_prices(entry_price, ml_direction, pred_symbol)
            stoploss = calculate_stoploss_price(entry_price, ml_direction, pred_symbol)
            
            # Check each target
            for target_name, target_price in targets.items():
                if target_name not in target_stats:
                    target_stats[target_name] = {"hit": 0, "total": 0}
                
                target_stats[target_name]["total"] += 1
                
                if ml_direction == "BUY":
                    if exit_price >= target_price:
                        target_stats[target_name]["hit"] += 1
                elif ml_direction == "SELL":
                    if exit_price <= target_price:
                        target_stats[target_name]["hit"] += 1
            
            # Check stoploss
            stoploss_stats["total"] += 1
            if ml_direction == "BUY" and exit_price <= stoploss:
                stoploss_stats["hit"] += 1
            elif ml_direction == "SELL" and exit_price >= stoploss:
                stoploss_stats["hit"] += 1
            
            # Direction correctness
            direction_stats["total"] += 1
            if relevant_outcome.get("ml_correct"):
                direction_stats["ml_correct"] += 1
            if relevant_outcome.get("claude_correct"):
                direction_stats["claude_correct"] += 1
        
        # Calculate percentages
        target_accuracy = {}
        for name, stats in target_stats.items():
            if stats["total"] > 0:
                target_accuracy[name] = {
                    "hit_count": stats["hit"],
                    "total": stats["total"],
                    "hit_rate": round(stats["hit"] / stats["total"], 3),
                }
        
        stoploss_rate = round(stoploss_stats["hit"] / stoploss_stats["total"], 3) if stoploss_stats["total"] > 0 else 0
        
        return {
            "symbol": symbol,
            "period_days": days,
            "check_interval": check_interval,
            "total_predictions": len(predictions),
            "analyzed_predictions": direction_stats["total"],
            "target_accuracy": target_accuracy,
            "stoploss_hit_rate": stoploss_rate,
            "stoploss_hits": stoploss_stats["hit"],
            "ml_accuracy": round(direction_stats["ml_correct"] / direction_stats["total"], 3) if direction_stats["total"] > 0 else None,
            "claude_accuracy": round(direction_stats["claude_correct"] / direction_stats["total"], 3) if direction_stats["total"] > 0 else None,
        }
        
    except Exception as e:
        logger.error(f"Failed to get multi-target accuracy: {e}")
        return {"error": str(e)}
