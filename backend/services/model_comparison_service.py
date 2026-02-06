"""
Model Comparison Background Service
Runs EMEL and PULSE models in background and logs predictions for comparison.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from database.supabase_client import get_supabase_client, is_db_available
from services.prediction_logger import log_prediction

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ModelSignal:
    model_name: str  # "EMEL" or "PULSE"
    symbol: str
    timeframe: str
    signal: str  # "BUY", "SELL", "HOLD"
    confidence: float
    entry_price: float
    target_price: float
    stop_price: float
    timestamp: datetime
    checks_passed: int
    total_checks: int
    notes: List[str]


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARISON TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

_comparison_results: Dict[str, List[Dict[str, Any]]] = {
    "EMEL": [],
    "PULSE": []
}

async def run_model_comparison(symbol: str = "NDX.INDX", timeframe: str = "M15") -> Dict[str, Any]:
    """
    Run both EMEL and PULSE models on same data and compare signals.
    Returns comparison result.
    """
    try:
        # Import model endpoints
        from routers.emel_pulse import get_emel_analysis, get_pulse_analysis
        
        # Run both models
        emel_result = await get_emel_analysis(symbol, timeframe)
        pulse_result = await get_pulse_analysis(symbol, timeframe)
        
        # Extract signals
        emel_signal = emel_result.get("signal", "HOLD")
        pulse_signal = pulse_result.get("signal", "HOLD")
        
        emel_confidence = emel_result.get("confidence", 0)
        pulse_confidence = pulse_result.get("trend_strength", 0) * 100
        
        # Log both predictions for tracking
        current_price = emel_result.get("price", 0)
        
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "timeframe": timeframe,
            "price": current_price,
            "emel": {
                "signal": emel_signal,
                "confidence": emel_confidence,
                "checks": f"{emel_result.get('summary', {}).get('green_count', 0)}/9",
                "rejections": emel_result.get("summary", {}).get("rejections", [])
            },
            "pulse": {
                "signal": pulse_signal,
                "confidence": pulse_confidence,
                "trend_strength": pulse_result.get("trend_strength", 0),
                "rr_ratio": pulse_result.get("rr_ratio", 0)
            },
            "agreement": emel_signal == pulse_signal,
            "combined_signal": _combine_signals(emel_signal, pulse_signal, emel_confidence, pulse_confidence)
        }
        
        # Store for analysis
        _comparison_results["EMEL"].append({
            "time": datetime.now(),
            "signal": emel_signal,
            "confidence": emel_confidence,
            "price": current_price
        })
        _comparison_results["PULSE"].append({
            "time": datetime.now(),
            "signal": pulse_signal,
            "confidence": pulse_confidence,
            "price": current_price
        })
        
        # Log to DB if signal exists
        if emel_signal in ["BUY", "SELL"]:
            await log_prediction(
                symbol=symbol,
                context={"source": "EMEL_COMPARISON", "ta": emel_result.get("ta", {})},
                analysis={"final_decision": emel_signal, "confidence": emel_confidence, "model_used": "EMEL-9-Check"},
                timeframe=timeframe,
                strategy="EMEL"
            )
            
        if pulse_signal in ["BUY", "SELL"]:
            await log_prediction(
                symbol=symbol,
                context={"source": "PULSE_COMPARISON", "ta": pulse_result.get("ta", {})},
                analysis={"final_decision": pulse_signal, "confidence": pulse_confidence, "model_used": "PULSE-Scalp"},
                timeframe=timeframe,
                strategy="PULSE"
            )
        
        return comparison
        
    except Exception as e:
        logger.error(f"Model comparison error: {e}")
        return {"error": str(e)}


def _combine_signals(
    emel_signal: str, 
    pulse_signal: str, 
    emel_confidence: float, 
    pulse_confidence: float
) -> str:
    """
    Combine EMEL and PULSE signals with weighted confidence.
    EMEL has higher weight (0.7) because it's more conservative.
    """
    # If both agree, use that signal
    if emel_signal == pulse_signal:
        return emel_signal
    
    # If disagreement, prefer EMEL (more conservative)
    if emel_signal in ["BUY", "SELL"]:
        return emel_signal
    
    # If EMEL is HOLD but PULSE has strong signal
    if pulse_confidence > 80:
        return pulse_signal
    
    return "HOLD"


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

async def get_model_performance_stats(days: int = 7) -> Dict[str, Any]:
    """
    Get performance statistics for both models.
    Retrieves from prediction_logs and calculates accuracy.
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if not client:
        return {"error": "No database connection"}
    
    try:
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()
        
        # Get EMEL predictions
        emel_result = client.table("prediction_logs").select(
            "id, created_at, symbol, ml_direction, ml_confidence, claude_direction, actual_outcome, outcome_checked"
        ).eq("strategy", "EMEL").gte("created_at", cutoff_iso).execute()
        
        # Get PULSE predictions
        pulse_result = client.table("prediction_logs").select(
            "id, created_at, symbol, ml_direction, ml_confidence, claude_direction, actual_outcome, outcome_checked"
        ).eq("strategy", "PULSE").gte("created_at", cutoff_iso).execute()
        
        emel_data = emel_result.get("data", [])
        pulse_data = pulse_result.get("data", [])
        
        # Calculate stats
        def calc_stats(data: List[Dict]) -> Dict[str, Any]:
            if not data:
                return {"total": 0, "checked": 0, "correct": 0, "accuracy": 0}
            
            total = len(data)
            checked = len([d for d in data if d.get("outcome_checked")])
            correct = len([d for d in data if d.get("actual_outcome") == d.get("ml_direction")])
            
            return {
                "total": total,
                "checked": checked,
                "correct": correct,
                "accuracy": round(correct / checked * 100, 1) if checked > 0 else 0,
                "buy_signals": len([d for d in data if d.get("ml_direction") == "BUY"]),
                "sell_signals": len([d for d in data if d.get("ml_direction") == "SELL"]),
                "avg_confidence": round(sum(d.get("ml_confidence", 0) for d in data) / len(data), 1) if data else 0
            }
        
        return {
            "period_days": days,
            "emel": calc_stats(emel_data),
            "pulse": calc_stats(pulse_data),
            "comparison": {
                "emel_signal_count": len(emel_data),
                "pulse_signal_count": len(pulse_data),
                "pulse_vs_emel_ratio": round(len(pulse_data) / len(emel_data), 2) if emel_data else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Performance stats error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# BACKGROUND SCHEDULER INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

async def schedule_model_comparison():
    """
    Periodically run model comparison.
    Called by background_scheduler.
    """
    symbols = ["NDX.INDX", "XAUUSD"]
    timeframes = ["M15", "H1"]
    
    for symbol in symbols:
        for tf in timeframes:
            try:
                result = await run_model_comparison(symbol, tf)
                if result.get("error"):
                    logger.warning(f"Comparison error for {symbol}/{tf}: {result['error']}")
                else:
                    logger.info(f"Model comparison completed: {symbol}/{tf} - EMEL:{result['emel']['signal']} PULSE:{result['pulse']['signal']}")
            except Exception as e:
                logger.error(f"Scheduled comparison error: {e}")
            
            await asyncio.sleep(1)  # Rate limit
