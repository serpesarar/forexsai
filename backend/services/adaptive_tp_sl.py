"""
Adaptive TP/SL Learning Service

This service analyzes why trades failed at certain price levels and learns
to predict better TP/SL zones based on:
- Technical indicators at failure points (RSI, MACD, Volume)
- Support/Resistance levels
- Fibonacci retracement levels
- Historical success/failure patterns

The goal is to dynamically adjust TP/SL based on market conditions.
"""
from __future__ import annotations

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from database.supabase_client import get_supabase_client, is_db_available
from services.data_fetcher import fetch_intraday_candles, fetch_latest_price
from services.target_config import get_symbol_config, pips_from_price_change

logger = logging.getLogger(__name__)


@dataclass
class FailureAnalysis:
    """Analysis of why a trade failed at a specific price level"""
    prediction_id: str
    symbol: str
    direction: str
    entry_price: float
    failure_price: float
    failure_reason: str
    rsi_at_failure: Optional[float]
    volume_change: Optional[float]
    nearest_resistance: Optional[float]
    nearest_support: Optional[float]
    fib_level_hit: Optional[str]
    macd_divergence: bool
    recommendation: str


@dataclass
class AdaptiveTPSL:
    """Dynamically calculated TP/SL levels"""
    entry: float
    tp1: float
    tp2: float
    tp3: float
    stop_loss: float
    confidence: float
    reasoning: List[str]
    fib_levels: Dict[str, float]
    key_levels: List[Dict[str, Any]]


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """Calculate RSI indicator"""
    if len(closes) < period + 1:
        return 50.0
    
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)


def calculate_macd(closes: List[float]) -> Tuple[float, float, bool]:
    """Calculate MACD and detect divergence"""
    if len(closes) < 26:
        return 0.0, 0.0, False
    
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    macd_line = ema12 - ema26
    
    # Simple signal line approximation
    signal = calculate_ema(closes[-9:], 9) if len(closes) >= 9 else macd_line
    
    # Detect divergence (price up but MACD down or vice versa)
    price_trend = closes[-1] > closes[-5] if len(closes) >= 5 else True
    macd_trend = macd_line > 0
    divergence = price_trend != macd_trend
    
    return macd_line, signal, divergence


def calculate_ema(data: List[float], period: int) -> float:
    """Calculate Exponential Moving Average"""
    if len(data) < period:
        return np.mean(data) if data else 0.0
    
    multiplier = 2 / (period + 1)
    ema = data[0]
    
    for price in data[1:]:
        ema = (price - ema) * multiplier + ema
    
    return ema


def calculate_fibonacci_levels(
    high: float, 
    low: float, 
    direction: str
) -> Dict[str, float]:
    """
    Calculate Fibonacci retracement and extension levels
    Similar to the image: 0.382, 0.5, 0.618, 0.764, 1.0, 1.618
    """
    diff = high - low
    
    if direction == "BUY":
        # Uptrend: measure from low
        return {
            "0.0": low,
            "0.236": low + diff * 0.236,
            "0.382": low + diff * 0.382,
            "0.5": low + diff * 0.5,
            "0.618": low + diff * 0.618,
            "0.764": low + diff * 0.764,
            "1.0": high,
            "1.272": high + diff * 0.272,
            "1.618": high + diff * 0.618,
        }
    else:
        # Downtrend: measure from high
        return {
            "0.0": high,
            "0.236": high - diff * 0.236,
            "0.382": high - diff * 0.382,
            "0.5": high - diff * 0.5,
            "0.618": high - diff * 0.618,
            "0.764": high - diff * 0.764,
            "1.0": low,
            "1.272": low - diff * 0.272,
            "1.618": low - diff * 0.618,
        }


def find_support_resistance(
    candles: List[Dict],
    current_price: float,
    lookback: int = 50
) -> Tuple[List[float], List[float]]:
    """
    Find support and resistance levels from recent price action
    Uses swing highs/lows detection
    """
    if len(candles) < 5:
        return [], []
    
    highs = [c.get("high", 0) for c in candles[-lookback:]]
    lows = [c.get("low", float("inf")) for c in candles[-lookback:]]
    
    resistances = []
    supports = []
    
    # Find swing highs (resistance)
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            resistances.append(highs[i])
    
    # Find swing lows (support)
    for i in range(2, len(lows) - 2):
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
           lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            supports.append(lows[i])
    
    # Filter to levels near current price (within 2%)
    price_range = current_price * 0.02
    resistances = [r for r in resistances if r > current_price and r < current_price + price_range]
    supports = [s for s in supports if s < current_price and s > current_price - price_range]
    
    return sorted(set(resistances)), sorted(set(supports), reverse=True)


def calculate_volume_profile(candles: List[Dict]) -> Dict[str, float]:
    """Calculate volume characteristics"""
    if len(candles) < 10:
        return {"avg": 0, "current": 0, "change_pct": 0}
    
    volumes = [c.get("volume", 0) for c in candles]
    avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
    current_volume = volumes[-1] if volumes else 0
    
    change_pct = ((current_volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0
    
    return {
        "avg": round(avg_volume, 2),
        "current": current_volume,
        "change_pct": round(change_pct, 2)
    }


async def analyze_failure_point(
    prediction: Dict[str, Any],
    failure_price: float,
    candles: List[Dict]
) -> FailureAnalysis:
    """
    Analyze why a trade failed at a specific price point
    
    This is the core learning function that identifies:
    - What technical condition caused the reversal
    - What indicator divergences existed
    - What S/R levels were hit
    """
    symbol = prediction.get("symbol", "")
    direction = prediction.get("ml_direction", "BUY")
    entry_price = prediction.get("ml_entry_price", 0)
    
    closes = [c.get("close", 0) for c in candles]
    
    # Calculate indicators at failure point
    rsi = calculate_rsi(closes)
    macd_line, signal, divergence = calculate_macd(closes)
    volume_profile = calculate_volume_profile(candles)
    
    # Find S/R levels
    resistances, supports = find_support_resistance(candles, failure_price)
    nearest_resistance = min(resistances) if resistances else None
    nearest_support = max(supports) if supports else None
    
    # Calculate Fibonacci levels
    recent_high = max(c.get("high", 0) for c in candles[-50:])
    recent_low = min(c.get("low", float("inf")) for c in candles[-50:])
    fib_levels = calculate_fibonacci_levels(recent_high, recent_low, direction)
    
    # Determine which Fib level was hit
    fib_hit = None
    for level_name, level_price in fib_levels.items():
        if abs(failure_price - level_price) / failure_price < 0.001:  # Within 0.1%
            fib_hit = level_name
            break
    
    # Determine failure reason
    reasons = []
    
    if direction == "BUY":
        if rsi > 70:
            reasons.append("RSI_OVERBOUGHT")
        if nearest_resistance and failure_price >= nearest_resistance * 0.999:
            reasons.append("HIT_RESISTANCE")
        if divergence:
            reasons.append("MACD_DIVERGENCE")
        if volume_profile["change_pct"] < -30:
            reasons.append("VOLUME_DECREASE")
    else:  # SELL
        if rsi < 30:
            reasons.append("RSI_OVERSOLD")
        if nearest_support and failure_price <= nearest_support * 1.001:
            reasons.append("HIT_SUPPORT")
        if divergence:
            reasons.append("MACD_DIVERGENCE")
        if volume_profile["change_pct"] < -30:
            reasons.append("VOLUME_DECREASE")
    
    if fib_hit:
        reasons.append(f"FIB_{fib_hit}")
    
    failure_reason = "|".join(reasons) if reasons else "UNKNOWN"
    
    # Generate recommendation
    if "HIT_RESISTANCE" in reasons or "HIT_SUPPORT" in reasons:
        recommendation = "Adjust TP to S/R level"
    elif "RSI_OVERBOUGHT" in reasons or "RSI_OVERSOLD" in reasons:
        recommendation = "Wait for RSI normalization before entry"
    elif "MACD_DIVERGENCE" in reasons:
        recommendation = "Reduce position size on divergence"
    elif "VOLUME_DECREASE" in reasons:
        recommendation = "Exit on volume decrease"
    else:
        recommendation = "Review market structure"
    
    return FailureAnalysis(
        prediction_id=prediction.get("id", ""),
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        failure_price=failure_price,
        failure_reason=failure_reason,
        rsi_at_failure=rsi,
        volume_change=volume_profile["change_pct"],
        nearest_resistance=nearest_resistance,
        nearest_support=nearest_support,
        fib_level_hit=fib_hit,
        macd_divergence=divergence,
        recommendation=recommendation
    )


async def calculate_adaptive_tp_sl(
    symbol: str,
    direction: str,
    entry_price: float,
    candles: Optional[List[Dict]] = None
) -> AdaptiveTPSL:
    """
    Calculate adaptive TP/SL levels based on:
    - Current market structure
    - Fibonacci levels
    - Support/Resistance
    - Historical success rates
    - Technical indicators
    """
    if candles is None:
        candles = await fetch_intraday_candles(symbol, interval="15m", limit=100)
    
    if not candles:
        # Fallback to default pip-based levels
        config = get_symbol_config(symbol)
        pip = config.pip_size
        return AdaptiveTPSL(
            entry=entry_price,
            tp1=entry_price + (20 * pip if direction == "BUY" else -20 * pip),
            tp2=entry_price + (30 * pip if direction == "BUY" else -30 * pip),
            tp3=entry_price + (50 * pip if direction == "BUY" else -50 * pip),
            stop_loss=entry_price + (-50 * pip if direction == "BUY" else 50 * pip),
            confidence=50.0,
            reasoning=["Using default pip-based levels"],
            fib_levels={},
            key_levels=[]
        )
    
    closes = [c.get("close", 0) for c in candles]
    
    # Get recent swing high/low for Fibonacci
    recent_high = max(c.get("high", 0) for c in candles[-50:])
    recent_low = min(c.get("low", float("inf")) for c in candles[-50:])
    
    # Calculate Fibonacci levels
    fib_levels = calculate_fibonacci_levels(recent_high, recent_low, direction)
    
    # Find S/R levels
    resistances, supports = find_support_resistance(candles, entry_price)
    
    # Calculate RSI for entry timing
    rsi = calculate_rsi(closes)
    
    # Calculate ATR for volatility-adjusted stops
    atr = calculate_atr(candles)
    
    reasoning = []
    confidence = 70.0
    
    # Determine TP levels based on Fibonacci and S/R
    if direction == "BUY":
        # TP1: First resistance or Fib 0.382 extension
        tp1_candidates = [fib_levels.get("0.618", entry_price * 1.002)]
        if resistances:
            tp1_candidates.append(resistances[0])
        tp1 = min(tp1_candidates)
        
        # TP2: Fib 0.764 or next resistance
        tp2 = fib_levels.get("0.764", tp1 * 1.005)
        
        # TP3: Fib 1.0 (full extension) or major resistance
        tp3 = fib_levels.get("1.0", tp2 * 1.01)
        
        # Stop Loss: Below support or ATR-based
        if supports:
            stop_loss = min(supports) - atr * 0.5
            reasoning.append(f"SL below support at {min(supports):.2f}")
        else:
            stop_loss = entry_price - atr * 2
            reasoning.append(f"SL based on 2x ATR ({atr:.2f})")
        
        if rsi > 70:
            confidence -= 20
            reasoning.append("⚠️ RSI overbought - reduced confidence")
        elif rsi < 30:
            confidence += 10
            reasoning.append("✅ RSI oversold - good entry for reversal")
            
    else:  # SELL
        # TP1: First support or Fib 0.382 extension down
        tp1_candidates = [fib_levels.get("0.618", entry_price * 0.998)]
        if supports:
            tp1_candidates.append(supports[0])
        tp1 = max(tp1_candidates)
        
        # TP2: Fib 0.764
        tp2 = fib_levels.get("0.764", tp1 * 0.995)
        
        # TP3: Fib 1.0
        tp3 = fib_levels.get("1.0", tp2 * 0.99)
        
        # Stop Loss: Above resistance or ATR-based
        if resistances:
            stop_loss = max(resistances) + atr * 0.5
            reasoning.append(f"SL above resistance at {max(resistances):.2f}")
        else:
            stop_loss = entry_price + atr * 2
            reasoning.append(f"SL based on 2x ATR ({atr:.2f})")
        
        if rsi < 30:
            confidence -= 20
            reasoning.append("⚠️ RSI oversold - reduced confidence")
        elif rsi > 70:
            confidence += 10
            reasoning.append("✅ RSI overbought - good entry for reversal")
    
    # Add Fibonacci reasoning
    reasoning.append(f"Fib levels: 0.618={fib_levels.get('0.618', 0):.2f}, 0.764={fib_levels.get('0.764', 0):.2f}")
    
    # Compile key levels for display
    key_levels = []
    for r in resistances[:3]:
        key_levels.append({"type": "resistance", "price": r})
    for s in supports[:3]:
        key_levels.append({"type": "support", "price": s})
    
    return AdaptiveTPSL(
        entry=entry_price,
        tp1=round(tp1, 5),
        tp2=round(tp2, 5),
        tp3=round(tp3, 5),
        stop_loss=round(stop_loss, 5),
        confidence=min(95, max(30, confidence)),
        reasoning=reasoning,
        fib_levels={k: round(v, 5) for k, v in fib_levels.items()},
        key_levels=key_levels
    )


def calculate_atr(candles: List[Dict], period: int = 14) -> float:
    """Calculate Average True Range"""
    if len(candles) < period + 1:
        return 0.0
    
    true_ranges = []
    for i in range(1, len(candles)):
        high = candles[i].get("high", 0)
        low = candles[i].get("low", 0)
        prev_close = candles[i-1].get("close", 0)
        
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    
    return np.mean(true_ranges[-period:]) if true_ranges else 0.0


async def save_failure_analysis(analysis: FailureAnalysis) -> bool:
    """Save failure analysis to database for learning"""
    if not is_db_available():
        return False
    
    client = get_supabase_client()
    if client is None:
        return False
    
    try:
        data = {
            "prediction_id": analysis.prediction_id,
            "symbol": analysis.symbol,
            "direction": analysis.direction,
            "entry_price": analysis.entry_price,
            "failure_price": analysis.failure_price,
            "failure_reason": analysis.failure_reason,
            "rsi_at_failure": analysis.rsi_at_failure,
            "volume_change": analysis.volume_change,
            "nearest_resistance": analysis.nearest_resistance,
            "nearest_support": analysis.nearest_support,
            "fib_level_hit": analysis.fib_level_hit,
            "macd_divergence": analysis.macd_divergence,
            "recommendation": analysis.recommendation,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        result = client.table("failure_analyses").insert(data).execute()
        return bool(result.get("data"))
        
    except Exception as e:
        logger.error(f"Failed to save failure analysis: {e}")
        return False


async def get_learned_adjustments(symbol: str, direction: str) -> Dict[str, Any]:
    """
    Get learned TP/SL adjustments based on historical failures
    
    Returns recommended adjustments to default TP/SL based on:
    - Most common failure reasons
    - Average failure distances from targets
    - Success rates at different levels
    """
    if not is_db_available():
        return {"adjustments": [], "confidence_modifier": 0}
    
    client = get_supabase_client()
    if client is None:
        return {"adjustments": [], "confidence_modifier": 0}
    
    try:
        result = client.table("failure_analyses").select("*").eq(
            "symbol", symbol
        ).eq("direction", direction).limit(100).execute()
        
        failures = result.get("data") or []
        
        if not failures:
            return {"adjustments": [], "confidence_modifier": 0}
        
        # Analyze failure patterns
        reason_counts = {}
        for f in failures:
            for reason in (f.get("failure_reason") or "").split("|"):
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        adjustments = []
        confidence_modifier = 0
        
        # Generate adjustments based on patterns
        total = len(failures)
        for reason, count in reason_counts.items():
            pct = (count / total) * 100
            if pct > 30:  # Significant pattern
                if "RESISTANCE" in reason:
                    adjustments.append({
                        "type": "tp",
                        "action": "Set TP below resistance levels",
                        "frequency": f"{pct:.0f}%"
                    })
                    confidence_modifier -= 5
                elif "RSI" in reason:
                    adjustments.append({
                        "type": "entry",
                        "action": "Wait for RSI confirmation",
                        "frequency": f"{pct:.0f}%"
                    })
                    confidence_modifier -= 10
                elif "VOLUME" in reason:
                    adjustments.append({
                        "type": "exit",
                        "action": "Trail stop on volume decrease",
                        "frequency": f"{pct:.0f}%"
                    })
                elif "FIB" in reason:
                    adjustments.append({
                        "type": "tp",
                        "action": f"Consider Fibonacci level {reason.replace('FIB_', '')}",
                        "frequency": f"{pct:.0f}%"
                    })
        
        return {
            "adjustments": adjustments,
            "confidence_modifier": confidence_modifier,
            "total_analyzed": total
        }
        
    except Exception as e:
        logger.error(f"Failed to get learned adjustments: {e}")
        return {"adjustments": [], "confidence_modifier": 0}
