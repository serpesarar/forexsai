"""
Model Comparison Background Service
Runs EMEL and PULSE models in background and logs predictions for comparison.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from utils.safe_supabase import safe_get_data, safe_get_error
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
    model_name: str  # "EMEL", "PULSE_ALGO", "PULSE_ML"
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
    "PULSE_ALGO": [],
    "PULSE_ML": []
}

async def run_model_comparison(symbol: str = "NDX.INDX", timeframe: str = "M15") -> Dict[str, Any]:
    """
    Run EMEL, PULSE (Algo) and PULSE (ML) models on same data and compare signals.
    Returns comparison result.
    """
    try:
        # Import model endpoints
        from routers.emel_pulse import get_emel_analysis, get_pulse_analysis, get_pulse_ml_analysis
        
        # Run all models
        emel_result = await get_emel_analysis(symbol, timeframe)
        pulse_algo_result = await get_pulse_analysis(symbol, timeframe)
        pulse_ml_result = await get_pulse_ml_analysis(symbol, timeframe)
        
        # Extract signals
        emel_signal = emel_result.get("signal", "HOLD")
        pulse_algo_signal = pulse_algo_result.get("signal", "HOLD")
        pulse_ml_signal = pulse_ml_result.get("signal", "HOLD")
        
        emel_confidence = emel_result.get("confidence", 0)
        pulse_algo_confidence = pulse_algo_result.get("trend_strength", 0) * 100
        pulse_ml_confidence = pulse_ml_result.get("confidence", 0)
        
        # Log all predictions for tracking
        current_price = emel_result.get("price", 0)
        
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "timeframe": timeframe,
            "price": current_price,
            "models": {
                "EMEL": {
                    "signal": emel_signal,
                    "confidence": emel_confidence,
                    "checks": f"{emel_result.get('summary', {}).get('green_count', 0)}/9",
                    "type": "ML (Strict)"
                },
                "PULSE_ALGO": {
                    "signal": pulse_algo_signal,
                    "confidence": pulse_algo_confidence,
                    "trend_strength": pulse_algo_result.get("trend_strength", 0),
                    "type": "Algorithmic"
                },
                "PULSE_ML": {
                    "signal": pulse_ml_signal,
                    "confidence": pulse_ml_confidence,
                    "type": "ML (Flexible)"
                }
            },
            "agreement": emel_signal == pulse_algo_signal == pulse_ml_signal,
            "combined_signal": _combine_signals(emel_signal, pulse_algo_signal, pulse_ml_signal)
        }
        
        # Store for analysis (In-memory buffer)
        _comparison_results["EMEL"].append(_create_log_entry(emel_signal, emel_confidence, current_price))
        _comparison_results["PULSE_ALGO"].append(_create_log_entry(pulse_algo_signal, pulse_algo_confidence, current_price))
        _comparison_results["PULSE_ML"].append(_create_log_entry(pulse_ml_signal, pulse_ml_confidence, current_price))
        
        # Note: Database logging is handled inside the endpoints themselves now.
        # Except for EMEL which might need manual logging if we want to track it specifically
        # But get_emel_analysis doesn't log by default, so we should log it here if needed.
        # Actually, let's let each endpoint handle its own logging or log here if they don't.
        # Pulse endpoints log themselves. EMEL logs via log_prediction if it finds a signal.
        
        return comparison
        
    except Exception as e:
        logger.error(f"Model comparison error: {e}")
        return {"error": str(e)}


def _create_log_entry(signal, confidence, price):
    return {
        "time": datetime.now(),
        "signal": signal,
        "confidence": confidence,
        "price": price
    }


def _combine_signals(emel: str, pulse_algo: str, pulse_ml: str) -> str:
    """
    Combine 3 signals.
    Priority: EMEL > PULSE_ML > PULSE_ALGO
    But confirmation increases confidence.
    """
    signals = [s for s in [emel, pulse_algo, pulse_ml] if s in ["BUY", "SELL"]]
    
    if not signals:
        return "HOLD"
        
    # If all agree
    if len(set(signals)) == 1 and len(signals) == 3:
        return f"STRONG_{signals[0]}"
        
    # If majority agree
    from collections import Counter
    counts = Counter(signals)
    most_common, count = counts.most_common(1)[0]
    
    if count >= 2:
        return most_common
        
    # If disagreement, trust EMEL
    if emel in ["BUY", "SELL"]:
        return emel
        
    # If EMEL is HOLD, check Pulse ML
    if pulse_ml in ["BUY", "SELL"]:
        return pulse_ml
        
    return "HOLD"


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

async def get_model_performance_stats(days: int = 7) -> Dict[str, Any]:
    """
    Get performance statistics for all 3 models.
    """
    if not is_db_available():
        return {"error": "Database not available"}
    
    client = get_supabase_client()
    if not client:
        return {"error": "No database connection"}
    
    try:
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()
        
        # Helper to fetch stats
        async def fetch_stats(strategy_name):
            res = client.table("prediction_logs").select(
                "id, symbol, ml_direction, ml_confidence, actual_outcome, outcome_checked"
            ).eq("strategy", strategy_name).gte("created_at", cutoff_iso).execute()
            return res.get("data", [])

        emel_data = await fetch_stats("EMEL")
        pulse_algo_data = await fetch_stats("PULSE") # Old pulse logs
        pulse_ml_data = await fetch_stats("PULSE_ML")
        
        # Calculate stats
        def calc_stats(data: List[Dict]) -> Dict[str, Any]:
            if not data:
                return {"total": 0, "accuracy": 0}
            
            total = len(data)
            checked = len([d for d in data if d.get("outcome_checked")])
            correct = len([d for d in data if d.get("actual_outcome") == d.get("ml_direction")])
            
            return {
                "total": total,
                "checked": checked,
                "correct": correct,
                "accuracy": round(correct / checked * 100, 1) if checked > 0 else 0,
                "signals": {
                    "BUY": len([d for d in data if d.get("ml_direction") == "BUY"]),
                    "SELL": len([d for d in data if d.get("ml_direction") == "SELL"])
                }
            }
        
        return {
            "period_days": days,
            "models": {
                "EMEL": calc_stats(emel_data),
                "PULSE_ALGO": calc_stats(pulse_algo_data),
                "PULSE_ML": calc_stats(pulse_ml_data)
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
                if safe_get_error(result):
                    logger.warning(f"Comparison error for {symbol}/{tf}: {result['error']}")
                else:
                    logger.info(f"Model comparison completed: {symbol}/{tf} - EMEL:{result['emel']['signal']} PULSE:{result['pulse']['signal']}")
            except Exception as e:
                logger.error(f"Scheduled comparison error: {e}")
            
            await asyncio.sleep(1)  # Rate limit
