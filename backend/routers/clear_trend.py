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
        return 1.0   # Gold: 1 pip = $1.00
    elif "NDX" in symbol_upper or "NAS" in symbol_upper:
        return 1.0   # NASDAQ: 1 point
    elif "GDAXI" in symbol_upper or "DAX" in symbol_upper:
        return 1.0   # DAX: 1 point
    elif "OIL" in symbol_upper or "USOIL" in symbol_upper or "CL" in symbol_upper:
        return 0.01  # Oil: cents
    return 1.0


def _get_unit_label(symbol: str) -> str:
    symbol_upper = (symbol or "").upper()
    if "OIL" in symbol_upper or "USOIL" in symbol_upper:
        return "pts"
    return "pts"


def _calculate_pips_distance(price1: float, price2: float, pip_value: float) -> float:
    """Calculate distance in pips/points."""
    return abs(price1 - price2) / pip_value


def _calc_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """Calculate Average True Range."""
    n = len(closes)
    if n < 2:
        return float(closes[-1]) * 0.001
    trs = []
    for i in range(1, min(period + 1, n)):
        tr = max(
            float(highs[i]) - float(lows[i]),
            abs(float(highs[i]) - float(closes[i - 1])),
            abs(float(lows[i]) - float(closes[i - 1])),
        )
        trs.append(tr)
    return float(np.mean(trs)) if trs else float(closes[-1]) * 0.001


def _find_support_resistance_levels(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    current_price: float,
    pip_value: float,
    symbol: str = "",
) -> Dict[str, Any]:
    """
    Improved S/R detection using swing-high/low clustering + touch-count scoring.

    Algorithm:
    1. Detect all swing highs/lows via 3-bar fractal across full candle history
    2. Cluster nearby swings within 0.7 × ATR (same price zone)
    3. Score each cluster: touch_count + recency bonus
    4. Pick the 3 closest resistance clusters above price and 3 support clusters below
    5. Fall back to Fibonacci pivot levels when swing data is insufficient
    """
    n = len(closes)
    atr = _calc_atr(highs, lows, closes, 14)
    cluster_threshold = atr * 0.7

    unit = _get_unit_label(symbol)

    # ── 1. Fractal swing detection ──────────────────────────────────────────
    period = 3
    swing_highs: List[tuple] = []  # (price, candle_index)
    swing_lows: List[tuple] = []

    for i in range(period, n - period):
        h_window = highs[i - period: i + period + 1]
        l_window = lows[i - period: i + period + 1]
        if float(highs[i]) >= float(np.max(h_window)):
            swing_highs.append((float(highs[i]), i))
        if float(lows[i]) <= float(np.min(l_window)):
            swing_lows.append((float(lows[i]), i))

    # ── 2. Cluster nearby swings ─────────────────────────────────────────────
    def cluster_swings(swings: List[tuple]) -> List[dict]:
        if not swings:
            return []
        sorted_swings = sorted(swings, key=lambda x: x[0])
        clusters: List[dict] = []
        for price, idx in sorted_swings:
            placed = False
            for c in clusters:
                if abs(price - c["center"]) <= cluster_threshold:
                    c["prices"].append(price)
                    c["indices"].append(idx)
                    c["center"] = float(np.mean(c["prices"]))
                    c["latest_idx"] = max(c["indices"])
                    placed = True
                    break
            if not placed:
                clusters.append({
                    "center": price,
                    "prices": [price],
                    "indices": [idx],
                    "latest_idx": idx,
                })
        # Score: touches + recency factor
        for c in clusters:
            touches = len(c["prices"])
            recency = c["latest_idx"] / max(n, 1)
            c["score"] = touches + recency * 0.5
            c["touch_count"] = touches
        return clusters

    res_swings = [(p, i) for p, i in swing_highs if p > current_price]
    sup_swings = [(p, i) for p, i in swing_lows if p < current_price]

    res_clusters = cluster_swings(res_swings)
    sup_clusters = cluster_swings(sup_swings)

    # Sort by proximity to current price, take top 3
    res_nearest = sorted(res_clusters, key=lambda c: c["center"] - current_price)[:3]
    sup_nearest = sorted(sup_clusters, key=lambda c: current_price - c["center"])[:3]

    # ── 3. Fibonacci fallback when swing data thin ───────────────────────────
    window = min(50, n)
    high_ref = float(np.max(highs[-window:]))
    low_ref = float(np.min(lows[-window:]))
    pivot = (high_ref + low_ref + current_price) / 3
    rng = high_ref - low_ref

    def fib_res_levels() -> List[dict]:
        out = []
        for mult in (0.382, 0.618, 1.0):
            p = pivot + rng * mult
            if p > current_price:
                out.append({"center": p, "touch_count": 1, "score": 0.5, "is_fib": True})
        return sorted(out, key=lambda c: c["center"] - current_price)

    def fib_sup_levels() -> List[dict]:
        out = []
        for mult in (0.382, 0.618, 1.0):
            p = pivot - rng * mult
            if p < current_price:
                out.append({"center": p, "touch_count": 1, "score": 0.5, "is_fib": True})
        return sorted(out, key=lambda c: current_price - c["center"])

    if len(res_nearest) < 2:
        existing_prices = {round(c["center"], 1) for c in res_nearest}
        for fb in fib_res_levels():
            if round(fb["center"], 1) not in existing_prices:
                res_nearest.append(fb)
            if len(res_nearest) >= 3:
                break
        res_nearest = sorted(res_nearest, key=lambda c: c["center"] - current_price)[:3]

    if len(sup_nearest) < 2:
        existing_prices = {round(c["center"], 1) for c in sup_nearest}
        for fb in fib_sup_levels():
            if round(fb["center"], 1) not in existing_prices:
                sup_nearest.append(fb)
            if len(sup_nearest) >= 3:
                break
        sup_nearest = sorted(sup_nearest, key=lambda c: current_price - c["center"])[:3]

    # ── 4. Build output levels ───────────────────────────────────────────────
    levels: List[dict] = []
    res_names = ["R1", "R2", "R3"]

    for i, c in enumerate(res_nearest):
        price = round(c["center"], 2)
        distance = abs(price - current_price) / pip_value
        touches = c.get("touch_count", 1)
        strength = "strong" if touches >= 2 else "normal"
        touch_tag = f" (×{touches})" if touches >= 2 else ""
        levels.append({
            "type": "resistance",
            "name": f"{res_names[i]}{touch_tag}",
            "price": price,
            "distance": round(distance, 1),
            "distance_display": f"+{round(distance, 1)} {unit}",
            "strength": strength,
            "is_next": i == 0,
            "touch_count": touches,
        })

    levels.append({
        "type": "current",
        "name": "Current Price",
        "price": round(current_price, 2),
        "distance": 0,
        "distance_display": "HERE",
        "strength": "current",
    })

    sup_names = ["S1", "S2", "S3"]
    for i, c in enumerate(sup_nearest):
        price = round(c["center"], 2)
        distance = abs(price - current_price) / pip_value
        touches = c.get("touch_count", 1)
        strength = "strong" if touches >= 2 else "normal"
        touch_tag = f" (×{touches})" if touches >= 2 else ""
        levels.append({
            "type": "support",
            "name": f"{sup_names[i]}{touch_tag}",
            "price": price,
            "distance": round(distance, 1),
            "distance_display": f"-{round(distance, 1)} {unit}",
            "strength": strength,
            "is_next": i == 0,
            "touch_count": touches,
        })

    resistances = [l for l in levels if l["type"] == "resistance"]
    supports = [l for l in levels if l["type"] == "support"]
    nearest_resistance = min(resistances, key=lambda x: x["distance"]) if resistances else None
    nearest_support = min(supports, key=lambda x: x["distance"]) if supports else None

    return {
        "all_levels": sorted(levels, key=lambda x: x["price"], reverse=True),
        "nearest_resistance": nearest_resistance,
        "nearest_support": nearest_support,
        "pivot": round(pivot, 2),
        "range_high": round(high_ref, 2),
        "range_low": round(low_ref, 2),
    }


def _calculate_trend(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    timeframe: str = "1H",
) -> Dict[str, Any]:
    """
    Calculate trend direction, strength, and a human-readable description.
    Uses EMA alignment (20/50/200) and ATR-normalized distance for strength.
    """
    if len(closes) < 20:
        return {
            "direction": "NEUTRAL",
            "strength": 0,
            "strength_percent": 0,
            "description": "Insufficient data",
        }

    tf_label = {
        "15M": "intraday", "15m": "intraday",
        "1H": "hourly", "1h": "hourly",
        "4H": "swing", "4h": "swing",
        "1D": "daily", "1d": "daily",
    }.get(timeframe, timeframe)

    ema_20 = calculate_ema(closes, 20) or float(closes[-1])
    ema_50 = calculate_ema(closes, 50) if len(closes) >= 50 else (calculate_ema(closes, len(closes)) or float(closes[-1]))
    ema_200 = calculate_ema(closes, 200) if len(closes) >= 200 else (calculate_ema(closes, max(20, len(closes))) or float(closes[-1]))

    current_price = float(closes[-1])
    atr = calculate_atr(highs, lows, closes, 14) or (current_price * 0.001)

    # Full EMA stack alignment
    full_bull = current_price > ema_20 > ema_50 > ema_200
    full_bear = current_price < ema_20 < ema_50 < ema_200
    partial_bull = current_price > ema_20 > ema_50
    partial_bear = current_price < ema_20 < ema_50

    if full_bull:
        direction = "UP"
        description = f"Strong uptrend — price above EMA20, EMA50 & EMA200 ({tf_label})"
    elif full_bear:
        direction = "DOWN"
        description = f"Strong downtrend — price below EMA20, EMA50 & EMA200 ({tf_label})"
    elif partial_bull:
        direction = "UP"
        description = f"Uptrend — price above EMA20 & EMA50 ({tf_label})"
    elif partial_bear:
        direction = "DOWN"
        description = f"Downtrend — price below EMA20 & EMA50 ({tf_label})"
    elif current_price > ema_20:
        direction = "UP"
        description = f"Weak uptrend — price above EMA20 only ({tf_label})"
    elif current_price < ema_20:
        direction = "DOWN"
        description = f"Weak downtrend — price below EMA20 only ({tf_label})"
    else:
        direction = "NEUTRAL"
        description = f"Neutral — price consolidating near EMAs ({tf_label})"

    # Strength: distance from EMA50 in ATR units (capped at 3 ATRs = 100%)
    dist_ema50 = abs(current_price - ema_50)
    strength_raw = min(100.0, (dist_ema50 / (atr * 3)) * 100)

    # Bonus for full EMA alignment
    if full_bull or full_bear:
        strength = int(min(100, strength_raw * 1.3))
    elif (partial_bull and direction == "UP") or (partial_bear and direction == "DOWN"):
        strength = int(min(100, strength_raw * 1.1))
    else:
        strength = int(strength_raw * 0.7)

    strength = max(0, min(100, strength))

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
        valid_symbols = ["NDX.INDX", "XAUUSD", "XAUUSD.FOREX", "GDAXI.INDX", "USOIL.FOREX"]
        symbol_key = symbol.upper()
        if symbol_key not in [s.upper() for s in valid_symbols]:
            return {
                "error": f"Symbol not supported. Use: {', '.join(valid_symbols)}"
            }

        # Normalize symbol for data fetching
        FETCH_MAP = {
            "XAUUSD": "XAUUSD.FOREX",
        }
        fetch_symbol = FETCH_MAP.get(symbol_key, symbol)
        
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
        trend = _calculate_trend(closes, highs, lows, timeframe)
        
        # Calculate support/resistance
        levels_data = _find_support_resistance_levels(highs, lows, closes, current_price, pip_value, symbol)
        
        # Calculate trade zones
        trade_zones = _calculate_trade_zones(
            current_price,
            levels_data["nearest_support"],
            levels_data["nearest_resistance"],
            trend
        )
        
        # Format price display
        sym_up = symbol.upper()
        if sym_up in ["XAUUSD", "XAUUSD.FOREX"]:
            price_display = f"{current_price:.2f}"
            price_decimals = 2
        elif "OIL" in sym_up or "USOIL" in sym_up:
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
                try:
                    # Fix for crash: timestamps from DataHub are in milliseconds (e.g. 1700000000000)
                    # fromtimestamp expects seconds. If ts > 30000000000 (year 2920), assume ms.
                    if ts > 30000000000:
                        ts = ts / 1000.0
                    dt = datetime.fromtimestamp(ts)
                except Exception:
                    # Fallback if conversion fails
                    dt = datetime.now()
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
