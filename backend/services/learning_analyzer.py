"""
Learning Analyzer Service
Analyzes prediction outcomes to identify patterns and improve future predictions.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict

from backend.database.supabase_client import get_supabase_client, is_db_available

logger = logging.getLogger(__name__)


async def analyze_factor_correlations(
    symbol: Optional[str] = None,
    days: int = 30,
    min_samples: int = 10
) -> Dict[str, Any]:
    """
    Analyze which factors correlate with correct/incorrect predictions.
    
    Args:
        symbol: Filter by symbol (optional)
        days: Number of days to analyze
        min_samples: Minimum samples required for analysis
    
    Returns:
        Factor correlation analysis
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
            "ml_correct, claude_correct, prediction_logs!inner(symbol, factors)"
        ).eq("check_interval", "24h").gte("created_at", cutoff_iso)
        
        if symbol:
            query = query.eq("prediction_logs.symbol", symbol)
        
        result = query.execute()
        outcomes = result.data or []
        
        if len(outcomes) < min_samples:
            return {
                "symbol": symbol,
                "period_days": days,
                "sample_size": len(outcomes),
                "message": f"Not enough samples (need {min_samples})",
                "correlations": {}
            }
        
        factor_stats = defaultdict(lambda: {
            "correct_values": [],
            "incorrect_values": [],
            "correct_count": 0,
            "incorrect_count": 0
        })
        
        categorical_stats = defaultdict(lambda: defaultdict(lambda: {"correct": 0, "total": 0}))
        
        for outcome in outcomes:
            ml_correct = outcome.get("ml_correct", False)
            prediction = outcome.get("prediction_logs", {})
            factors = prediction.get("factors", {}) or {}
            
            for factor_name, value in factors.items():
                if value is None:
                    continue
                
                if isinstance(value, (int, float)):
                    stats = factor_stats[factor_name]
                    if ml_correct:
                        stats["correct_values"].append(float(value))
                        stats["correct_count"] += 1
                    else:
                        stats["incorrect_values"].append(float(value))
                        stats["incorrect_count"] += 1
                
                elif isinstance(value, str):
                    cat_stats = categorical_stats[factor_name][value]
                    cat_stats["total"] += 1
                    if ml_correct:
                        cat_stats["correct"] += 1
        
        numeric_analysis = {}
        for factor_name, stats in factor_stats.items():
            correct_vals = stats["correct_values"]
            incorrect_vals = stats["incorrect_values"]
            
            if len(correct_vals) >= 3 and len(incorrect_vals) >= 3:
                avg_when_correct = sum(correct_vals) / len(correct_vals)
                avg_when_incorrect = sum(incorrect_vals) / len(incorrect_vals)
                
                diff_pct = ((avg_when_correct - avg_when_incorrect) / max(abs(avg_when_incorrect), 0.001)) * 100
                
                numeric_analysis[factor_name] = {
                    "avg_when_correct": round(avg_when_correct, 4),
                    "avg_when_incorrect": round(avg_when_incorrect, 4),
                    "difference_pct": round(diff_pct, 2),
                    "samples_correct": len(correct_vals),
                    "samples_incorrect": len(incorrect_vals),
                    "insight": _generate_numeric_insight(factor_name, avg_when_correct, avg_when_incorrect)
                }
        
        categorical_analysis = {}
        for factor_name, value_stats in categorical_stats.items():
            factor_analysis = {}
            for value, stats in value_stats.items():
                if stats["total"] >= 3:
                    accuracy = stats["correct"] / stats["total"]
                    factor_analysis[value] = {
                        "accuracy": round(accuracy, 3),
                        "sample_size": stats["total"],
                        "correct_count": stats["correct"]
                    }
            if factor_analysis:
                categorical_analysis[factor_name] = factor_analysis
        
        return {
            "symbol": symbol,
            "period_days": days,
            "sample_size": len(outcomes),
            "numeric_factors": numeric_analysis,
            "categorical_factors": categorical_analysis,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze factor correlations: {e}")
        return {"error": str(e)}


def _generate_numeric_insight(factor_name: str, avg_correct: float, avg_incorrect: float) -> str:
    """Generate a human-readable insight for a numeric factor."""
    diff = avg_correct - avg_incorrect
    
    if abs(diff) < 0.01 * max(abs(avg_correct), abs(avg_incorrect), 1):
        return "Belirgin fark yok"
    
    direction = "yüksek" if diff > 0 else "düşük"
    
    insights = {
        "rsi_14": f"Doğru tahminlerde RSI daha {direction}",
        "rsi_7": f"Doğru tahminlerde kısa vadeli RSI daha {direction}",
        "volume_ratio": f"Doğru tahminlerde hacim oranı daha {direction}",
        "ema20_distance_pct": f"Doğru tahminlerde EMA20 uzaklığı daha {direction}",
        "vix": f"Doğru tahminlerde VIX daha {direction}",
        "dxy": f"Doğru tahminlerde DXY daha {direction}",
        "boll_zscore": f"Doğru tahminlerde Bollinger Z-skoru daha {direction}",
        "atr_pct": f"Doğru tahminlerde ATR yüzdesi daha {direction}",
        "adx": f"Doğru tahminlerde trend gücü (ADX) daha {direction}",
    }
    
    return insights.get(factor_name, f"Doğru tahminlerde değer daha {direction}")


async def generate_learning_insights(
    symbol: Optional[str] = None,
    days: int = 30
) -> List[Dict[str, Any]]:
    """
    Generate learning insights based on historical prediction performance.
    
    Args:
        symbol: Filter by symbol (optional)
        days: Number of days to analyze
    
    Returns:
        List of insight objects
    """
    if not is_db_available():
        return []
    
    client = get_supabase_client()
    if client is None:
        return []
    
    insights = []
    
    try:
        correlations = await analyze_factor_correlations(symbol, days)
        
        if "error" not in correlations:
            numeric_factors = correlations.get("numeric_factors", {})
            
            for factor_name, analysis in numeric_factors.items():
                diff_pct = abs(analysis.get("difference_pct", 0))
                
                if diff_pct > 20:
                    insights.append({
                        "insight_type": "factor_correlation",
                        "symbol": symbol,
                        "factor": factor_name,
                        "severity": "high" if diff_pct > 50 else "medium",
                        "data": analysis,
                        "recommendation": f"{factor_name} faktörü tahmin doğruluğunu önemli ölçüde etkiliyor. Bu faktöre dikkat et."
                    })
            
            categorical_factors = correlations.get("categorical_factors", {})
            
            for factor_name, value_stats in categorical_factors.items():
                for value, stats in value_stats.items():
                    accuracy = stats.get("accuracy", 0.5)
                    sample_size = stats.get("sample_size", 0)
                    
                    if sample_size >= 5:
                        if accuracy < 0.35:
                            insights.append({
                                "insight_type": "warning",
                                "symbol": symbol,
                                "factor": factor_name,
                                "value": value,
                                "severity": "high",
                                "data": stats,
                                "recommendation": f"{factor_name}={value} koşulunda tahmin doğruluğu çok düşük ({accuracy:.0%}). Bu durumda dikkatli ol."
                            })
                        elif accuracy > 0.70:
                            insights.append({
                                "insight_type": "recommendation",
                                "symbol": symbol,
                                "factor": factor_name,
                                "value": value,
                                "severity": "positive",
                                "data": stats,
                                "recommendation": f"{factor_name}={value} koşulunda tahmin doğruluğu yüksek ({accuracy:.0%}). Bu durumda güven artır."
                            })
        
        return insights
        
    except Exception as e:
        logger.error(f"Failed to generate learning insights: {e}")
        return []


async def save_insights_to_db(insights: List[Dict[str, Any]]) -> int:
    """
    Save generated insights to database.
    
    Args:
        insights: List of insight objects
    
    Returns:
        Number of insights saved
    """
    if not is_db_available() or not insights:
        return 0
    
    client = get_supabase_client()
    if client is None:
        return 0
    
    saved = 0
    try:
        for insight in insights:
            record = {
                "symbol": insight.get("symbol"),
                "insight_type": insight.get("insight_type", "recommendation"),
                "sample_size": insight.get("data", {}).get("sample_size", 0),
                "data": {
                    "factor": insight.get("factor"),
                    "value": insight.get("value"),
                    "severity": insight.get("severity"),
                    "recommendation": insight.get("recommendation"),
                    **insight.get("data", {})
                },
                "is_active": True
            }
            
            result = client.table("learning_insights").insert(record).execute()
            if result.data:
                saved += 1
        
        return saved
        
    except Exception as e:
        logger.error(f"Failed to save insights: {e}")
        return saved


async def get_active_insights(symbol: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get active learning insights for use in analysis.
    
    Args:
        symbol: Filter by symbol (optional)
    
    Returns:
        List of active insights
    """
    if not is_db_available():
        return []
    
    client = get_supabase_client()
    if client is None:
        return []
    
    try:
        query = client.table("learning_insights").select("*").eq("is_active", True)
        
        if symbol:
            query = query.or_(f"symbol.eq.{symbol},symbol.is.null")
        
        query = query.order("created_at", desc=True).limit(50)
        
        result = query.execute()
        return result.data or []
        
    except Exception as e:
        logger.error(f"Failed to get active insights: {e}")
        return []


async def get_learning_context_for_prompt(symbol: str) -> str:
    """
    Generate a context string for Claude prompt based on learning insights.
    
    Args:
        symbol: Trading symbol
    
    Returns:
        Context string to add to Claude prompt
    """
    insights = await get_active_insights(symbol)
    
    if not insights:
        return ""
    
    warnings = []
    recommendations = []
    
    for insight in insights:
        data = insight.get("data", {})
        rec = data.get("recommendation", "")
        severity = data.get("severity", "")
        
        if severity == "high" or insight.get("insight_type") == "warning":
            warnings.append(rec)
        elif severity == "positive" or insight.get("insight_type") == "recommendation":
            recommendations.append(rec)
    
    context_parts = []
    
    if warnings:
        context_parts.append("⚠️ GEÇMİŞ PERFORMANS UYARILARI:")
        for w in warnings[:5]:
            context_parts.append(f"  - {w}")
    
    if recommendations:
        context_parts.append("✓ OLUMLU KOŞULLAR:")
        for r in recommendations[:5]:
            context_parts.append(f"  - {r}")
    
    return "\n".join(context_parts)
