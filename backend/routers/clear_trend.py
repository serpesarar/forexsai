"""
Clear Trend Analysis API
==========================
Simplified trend analysis for NASDAQ and XAUUSD.
- Current price centered and prominent
- Clear support/resistance levels with distances
- Trend direction and strength
- Easy to understand for quick decisions
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter
import numpy as np

from services.data_fetcher import fetch_ohlc_data, fetch_latest_price
from services.technical_indicators import calculate_ema, calculate_atr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clear-trend", tags=["clear-trend"])


def _get_pip_value(symbol: str) -> float:
    """Get pip/point value for symbol."""
    symbol_upper = (symbol or "").upper()
    if "XAU" in symbol_upper:
        return 0.1  # Gold moves in 0.1 increments
    elif "NDX" in symbol_upper or "NAS" in symbol_upper:
        return 1.0  # NASDAQ moves in 1 point increments
    return 0.01


def _calculate_pips_distance(price1: float, price2: float, pip_value: float) -> float:
    """Calculate distance in pips/points."""
    return abs(price1 - price2) / pip_value


def _find_support_resistance_levels(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    current_price: float,
    pip_value: float
) -> Dict[str, Any]:
    """
    Find clear support and resistance levels using swing highs/lows.
    Returns levels with distances from current price.
    """
    # Find swing highs and lows (fractal method)
    swing_highs = []
    swing_lows = []
    period = 3
    
    for i in range(period, len(closes) - period):
        if highs[i] == max(highs[i-period:i+period+1]):
            swing_highs.append(float(highs[i]))
        if lows[i] == min(lows[i-period:i+period+1]):
            swing_lows.append(float(lows[i]))
    
    # Get recent levels (last 5)
    recent_highs = swing_highs[-5:] if len(swing_highs) >= 5 else swing_highs
    recent_lows = swing_lows[-5:] if len(swing_lows) >= 5 else swing_lows
    
    # Calculate pivot point (classic)
    high_20 = float(np.max(highs[-20:])) if len(highs) >= 20 else float(np.max(highs))
    low_20 = float(np.min(lows[-20:])) if len(lows) >= 20 else float(np.min(lows))
    pivot = (high_20 + low_20 + current_price) / 3
    
    # Calculate Fibonacci levels
    range_20 = high_20 - low_20
    r1 = pivot + (range_20 * 0.382)
    r2 = pivot + (range_20 * 0.618)  # Strong resistance
    r3 = high_20
    s1 = pivot - (range_20 * 0.382)
    s2 = pivot - (range_20 * 0.618)  # Strong support
    s3 = low_20
    
    # Build levels list with distances
    levels = []
    
    # Resistance levels (above current price)
    for i, (price, name, strength) in enumerate([
        (r3, "R3 (High)", "normal"),
        (r2, "R2 (Strong)", "strong"),
        (r1, "R1", "normal"),
    ]):
        if price > current_price:
            distance = _calculate_pips_distance(price, current_price, pip_value)
            levels.append({
                "type": "resistance",
                "name": name,
                "price": round(price, 2),
                "distance": round(distance, 1),
                "distance_display": f"+{round(distance, 1)} pts" if pip_value == 1.0 else f"+{round(distance, 1)} pips",
                "strength": strength,
                "is_next": i == 1  # R2 is typically the next major level
            })
    
    # Current price level
    levels.append({
        "type": "current",
        "name": "Current Price",
        "price": round(current_price, 2),
        "distance": 0,
        "distance_display": "HERE",
        "strength": "current"
    })
    
    # Support levels (below current price)
    for i, (price, name, strength) in enumerate([
        (s1, "S1", "normal"),
        (s2, "S2 (Strong)", "strong"),
        (s3, "S3 (Low)", "normal"),
    ]):
        if price < current_price:
            distance = _calculate_pips_distance(price, current_price, pip_value)
            levels.append({
                "type": "support",
                "name": name,
                "price": round(price, 2),
                "distance": round(distance, 1),
                "distance_display": f"-{round(distance, 1)} pts" if pip_value == 1.0 else f"-{round(distance, 1)} pips",
                "strength": strength,
                "is_next": i == 1  # S2 is typically the next major level
            })
    
    # Find nearest support and resistance
    resistances = [l for l in levels if l["type"] == "resistance"]
    supports = [l for l in levels if l["type"] == "support"]
    
    nearest_resistance = min(resistances, key=lambda x: x["distance"]) if resistances else None
    nearest_support = min(supports, key=lambda x: x["distance"]) if supports else None
    
    return {
        "all_levels": sorted(levels, key=lambda x: x["price"], reverse=True),
        "nearest_resistance": nearest_resistance,
        "nearest_support": nearest_support,
        "pivot": round(pivot, 2),
        "range_high": round(high_20, 2),
        "range_low": round(low_20, 2),
    }


def _calculate_trend(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray
) -> Dict[str, Any]:
    """
    Calculate simple trend direction and strength.
    """
    if len(closes) < 50:
        return {
            "direction": "NEUTRAL",
            "strength": 0,
            "strength_percent": 0,
            "description": "Insufficient data"
        }
    
    # Calculate EMAs
    ema_20 = calculate_ema(closes, 20) or closes[-1]
    ema_50 = calculate_ema(closes, 50) or closes[-1]
    ema_200 = calculate_ema(closes, 200) if len(closes) >= 200 else (calculate_ema(closes, len(closes)) if len(closes) >= 20 else float(closes[-1]))
    
    current_price = float(closes[-1])
    
    # Trend direction based on EMA position
    if current_price > ema_20 > ema_50:
        direction = "UP"
        description = "Uptrend - Price above EMA20 and EMA50"
    elif current_price < ema_20 < ema_50:
        direction = "DOWN"
        description = "Downtrend - Price below EMA20 and EMA50"
    elif current_price > ema_20:
        direction = "UP"
        description = "Weak uptrend - Price above EMA20 but mixed"
    elif current_price < ema_20:
        direction = "DOWN"
        description = "Weak downtrend - Price below EMA20 but mixed"
    else:
        direction = "NEUTRAL"
        description = "Neutral - Price near EMAs"
    
    # Calculate trend strength (0-100)
    # Based on how far price is from EMA50 relative to recent volatility
    atr = calculate_atr(highs, lows, closes, 14) or (current_price * 0.001)
    distance_from_ema50 = abs(current_price - ema_50)
    strength_raw = min(100, (distance_from_ema50 / (atr * 3)) * 100)
    
    # Adjust strength based on alignment
    if direction == "UP" and ema_20 > ema_50:
        strength = int(strength_raw * 1.2)
    elif direction == "DOWN" and ema_20 < ema_50:
        strength = int(strength_raw * 1.2)
    else:
        strength = int(strength_raw * 0.7)
    
    strength = min(100, max(0, strength))
    
    return {
        "direction": direction,
        "strength": strength,
        "strength_percent": strength,
        "description": description,
        "ema_20": round(ema_20, 2),
        "ema_50": round(ema_50, 2),
        "ema_200": round(ema_200, 2) if ema_200 else 0,
    }


def _calculate_trade_zones(
    current_price: float,
    support: Optional[Dict],
    resistance: Optional[Dict],
    trend: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate suggested entry, target, and stop zones.
    """
    if trend["direction"] == "UP":
        # In uptrend: buy near support, target next resistance
        entry_zone = {
            "min": round(current_price * 0.998, 2),
            "max": round(current_price * 1.002, 2),
            "description": "Current area or pullback"
        }
        target = resistance["price"] if resistance else round(current_price * 1.01, 2)
        stop = support["price"] if support else round(current_price * 0.99, 2)
        suggestion = "BUY zone active - Look for entries near support"
    elif trend["direction"] == "DOWN":
        # In downtrend: sell near resistance, target next support
        entry_zone = {
            "min": round(current_price * 0.998, 2),
            "max": round(current_price * 1.002, 2),
            "description": "Current area or bounce"
        }
        target = support["price"] if support else round(current_price * 0.99, 2)
        stop = resistance["price"] if resistance else round(current_price * 1.01, 2)
        suggestion = "SELL zone active - Look for entries near resistance"
    else:
        # Neutral: wait for breakout
        entry_zone = None
        target = None
        stop = None
        suggestion = "NEUTRAL - Wait for clear direction"
    
    return {
        "suggestion": suggestion,
        "entry_zone": entry_zone,
        "target": round(target, 2) if target else None,
        "stop": round(stop, 2) if stop else None,
    }


@router.get("/{symbol}")
async def get_clear_trend(symbol: str, timeframe: str = "1H"):
    """
    Get simplified trend analysis for a symbol.
    
    Returns:
    - Current price (prominent)
    - Trend direction and strength
    - Support/Resistance levels with distances
    - Suggested trade zones
    """
    try:
        # Validate symbol
        valid_symbols = ["NDX.INDX", "XAUUSD", "XAUUSD.FOREX"]
        symbol_key = symbol.upper()
        if symbol_key not in [s.upper() for s in valid_symbols]:
            return {
                "error": f"Symbol not supported. Use: {', '.join(valid_symbols)}"
            }
        
        # Normalize symbol for data fetching
        if symbol_key == "XAUUSD":
            fetch_symbol = "XAUUSD.FOREX"
        else:
            fetch_symbol = symbol
        
        # Get data
        candles = await fetch_ohlc_data(fetch_symbol, timeframe, limit=300)
        current_price = await fetch_latest_price(fetch_symbol)
        
        if not candles or len(candles) < 50:
            # Return mock data for testing when no real data available
            mock_price = 21547.8 if "NDX" in symbol else 2052.35
            mock_trend = "UP" if "NDX" in symbol else "DOWN"
            mock_strength = 75 if "NDX" in symbol else 65
            
            pip_value = _get_pip_value(symbol)
            
            # Mock levels
            if "NDX" in symbol:
                mock_levels = {
                    "all_levels": [
                        {"type": "resistance", "name": "R3 (High)", "price": 21700, "distance": 152.2, "distance_display": "+152.2 pts", "strength": "normal"},
                        {"type": "resistance", "name": "R2 (Strong)", "price": 21650, "distance": 102.2, "distance_display": "+102.2 pts", "strength": "strong", "is_next": True},
                        {"type": "current", "name": "Current Price", "price": mock_price, "distance": 0, "distance_display": "HERE", "strength": "current"},
                        {"type": "support", "name": "S1", "price": 21450, "distance": 97.8, "distance_display": "-97.8 pts", "strength": "normal"},
                        {"type": "support", "name": "S2 (Strong)", "price": 21350, "distance": 197.8, "distance_display": "-197.8 pts", "strength": "strong"},
                    ],
                    "nearest_resistance": {"type": "resistance", "name": "R2 (Strong)", "price": 21650, "distance": 102.2},
                    "nearest_support": {"type": "support", "name": "S1", "price": 21450, "distance": 97.8},
                    "pivot": 21550,
                    "range_high": 21700,
                    "range_low": 21300,
                }
            else:  # XAUUSD
                mock_levels = {
                    "all_levels": [
                        {"type": "resistance", "name": "R3 (High)", "price": 2070, "distance": 17.65, "distance_display": "+17.7 pips", "strength": "normal"},
                        {"type": "resistance", "name": "R2 (Strong)", "price": 2065, "distance": 12.65, "distance_display": "+12.7 pips", "strength": "strong", "is_next": True},
                        {"type": "current", "name": "Current Price", "price": mock_price, "distance": 0, "distance_display": "HERE", "strength": "current"},
                        {"type": "support", "name": "S1", "price": 2045, "distance": 7.35, "distance_display": "-7.4 pips", "strength": "normal"},
                        {"type": "support", "name": "S2 (Strong)", "price": 2040, "distance": 12.35, "distance_display": "-12.4 pips", "strength": "strong"},
                    ],
                    "nearest_resistance": {"type": "resistance", "name": "R2 (Strong)", "price": 2065, "distance": 12.65},
                    "nearest_support": {"type": "support", "name": "S1", "price": 2045, "distance": 7.35},
                    "pivot": 2055,
                    "range_high": 2070,
                    "range_low": 2040,
                }
            
            mock_trend_data = {
                "direction": mock_trend,
                "strength": mock_strength,
                "strength_percent": mock_strength,
                "description": f"Mock {mock_trend} trend for testing",
                "ema_20": round(mock_price * 0.998, 2),
                "ema_50": round(mock_price * 0.995, 2),
            }
            
            mock_trade_zones = {
                "suggestion": f"Mock {mock_trend} zone active - Test data",
                "entry_zone": {
                    "min": round(mock_price * 0.998, 2),
                    "max": round(mock_price * 1.002, 2),
                    "description": "Mock entry zone"
                },
                "target": mock_levels["nearest_resistance"]["price"] if mock_trend == "UP" else mock_levels["nearest_support"]["price"],
                "stop": mock_levels["nearest_support"]["price"] if mock_trend == "UP" else mock_levels["nearest_resistance"]["price"],
            }
            
            price_decimals = 1 if "NDX" in symbol else 2
            
            # Generate mock chart data
            from datetime import timedelta
            mock_count = 50
            mock_dates = [(datetime.now() - timedelta(minutes=i*15)).strftime("%H:%M") for i in range(mock_count)][::-1]
            # Simple random walk for closes
            mock_closes = [mock_price]
            import random
            for _ in range(mock_count - 1):
                change = random.uniform(-0.001, 0.001) * mock_price
                mock_closes.append(mock_closes[-1] + change)
            mock_closes = [round(c, price_decimals) for c in mock_closes]
            
            mock_chart_data = {
                "closes": mock_closes,
                "dates": mock_dates,
                "trend_channel": {
                    "upper": [round(c * 1.002, price_decimals) for c in mock_closes],
                    "lower": [round(c * 0.998, price_decimals) for c in mock_closes],
                    "middle": mock_closes
                }
            }
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "price": {
                    "current": round(mock_price, price_decimals),
                    "display": f"{mock_price:.{price_decimals}f}",
                    "decimals": price_decimals
                },
                "trend": mock_trend_data,
                "levels": mock_levels,
                "trade_zones": mock_trade_zones,
                "pip_value": pip_value,
                "chart_data": mock_chart_data,
                "explanations": {
                    "trend": "Trend direction based on EMA20 and EMA50 positioning",
                    "strength": "How strong the trend is (0-100). Above 70 is strong, below 30 is weak",
                    "support": "Price level where buying interest typically emerges",
                    "resistance": "Price level where selling pressure typically emerges",
                    "pivot": "Central pivot point calculated from recent high, low, and close",
                    "r1_r2": "Fibonacci resistance levels. R2 (0.618) is typically stronger",
                    "s1_s2": "Fibonacci support levels. S2 (0.618) is typically stronger",
                    "entry_zone": "Suggested price area for trade entry based on current trend",
                    "target": "Suggested take-profit level based on next S/R level",
                    "stop": "Suggested stop-loss level based on recent support/resistance"
                },
                "mock_data": True
            }
        
        if current_price is None:
            # Use last close if live price unavailable
            current_price = candles[-1]["close"]
        
        # Convert to numpy arrays
        closes = np.array([c["close"] for c in candles], dtype=np.float64)
        highs = np.array([c["high"] for c in candles], dtype=np.float64)
        lows = np.array([c["low"] for c in candles], dtype=np.float64)
        
        # Get pip value
        pip_value = _get_pip_value(symbol)
        
        # Calculate trend
        trend = _calculate_trend(closes, highs, lows)
        
        # Calculate support/resistance
        levels_data = _find_support_resistance_levels(highs, lows, closes, current_price, pip_value)
        
        # Calculate trade zones
        trade_zones = _calculate_trade_zones(
            current_price,
            levels_data["nearest_support"],
            levels_data["nearest_resistance"],
            trend
        )
        
        # Format price display
        if symbol.upper() in ["XAUUSD", "XAUUSD.FOREX"]:
            price_display = f"{current_price:.2f}"
            price_decimals = 2
        else:
            price_display = f"{current_price:.1f}"
            price_decimals = 1
        
        # Build chart data for frontend mini chart (200 candles for scrolling)
        chart_count = min(len(closes), 200)
        recent_closes = [round(float(c), price_decimals) for c in closes[-chart_count:]]
        
        # Extract dates for X-axis
        # Format: "HH:mm" for intraday, "MM-DD" for daily
        recent_dates = []
        raw_candles = candles[-chart_count:]
        for c in raw_candles:
            ts = c.get("timestamp")
            dt_str = c.get("date", "")
            if ts:
                dt = datetime.fromtimestamp(ts)
            elif dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except:
                    dt = datetime.now() # Fallback
            else:
                dt = datetime.now()
            
            if timeframe in ["1D", "D", "d", "daily", "eod"]:
                recent_dates.append(dt.strftime("%m-%d"))
            else:
                # Intraday
                recent_dates.append(dt.strftime("%H:%M"))

        # Linear regression trend channel (over all chart candles)
        channel_closes = closes[-chart_count:]
        x = np.arange(len(channel_closes), dtype=float)
        try:
            slope, intercept = np.polyfit(x, channel_closes.astype(float), 1)
            fitted = slope * x + intercept
            residual = channel_closes - fitted
            std_dev = float(np.std(residual))
            upper_band = [round(float(f + 2 * std_dev), price_decimals) for f in fitted]
            lower_band = [round(float(f - 2 * std_dev), price_decimals) for f in fitted]
            middle_line = [round(float(f), price_decimals) for f in fitted]
        except Exception:
            upper_band = recent_closes
            lower_band = recent_closes
            middle_line = recent_closes
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "price": {
                "current": round(current_price, price_decimals),
                "display": price_display,
                "decimals": price_decimals
            },
            "trend": trend,
            "levels": levels_data,
            "trade_zones": trade_zones,
            "pip_value": pip_value,
            "chart_data": {
                "closes": recent_closes,
                "dates": recent_dates,
                "trend_channel": {
                    "upper": upper_band,
                    "lower": lower_band,
                    "middle": middle_line,
                }
            },
            "explanations": {
                "trend": "Trend direction based on EMA20 and EMA50 positioning",
                "strength": "How strong the trend is (0-100). Above 70 is strong, below 30 is weak",
                "support": "Price level where buying interest typically emerges",
                "resistance": "Price level where selling pressure typically emerges",
                "pivot": "Central pivot point calculated from recent high, low, and close",
                "r1_r2": "Fibonacci resistance levels. R2 (0.618) is typically stronger",
                "s1_s2": "Fibonacci support levels. S2 (0.618) is typically stronger",
                "entry_zone": "Suggested price area for trade entry based on current trend",
                "target": "Suggested take-profit level based on next S/R level",
                "stop": "Suggested stop-loss level based on recent support/resistance"
            }
        }
        
    except Exception as e:
        logger.error(f"Clear trend analysis error for {symbol}: {e}")
        return {
            "error": f"Analysis failed: {str(e)}"
        }
