"""
Risk/Reward Calculator Service
==============================
Pure mathematical calculation for position sizing, stop-loss, take-profit.
NO DeepSeek/AI - Mathematical formulas only for instant results.
"""

import numpy as np
from typing import Dict, Literal, Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class RiskParameters:
    account_size: float
    risk_per_trade_pct: float
    max_portfolio_heat_pct: float
    kelly_fraction: float


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_levels(candles: list, current_price: float) -> Dict[str, List[float]]:
    """Extract simple nearby support/resistance levels from recent candles."""
    if not candles:
        return {"support": [], "resistance": []}

    recent = candles[-30:] if len(candles) >= 30 else candles
    lows = sorted({_to_float(c.get("low")) for c in recent if _to_float(c.get("low")) > 0})
    highs = sorted({_to_float(c.get("high")) for c in recent if _to_float(c.get("high")) > 0})

    supports = [level for level in lows if level < current_price]
    resistances = [level for level in highs if level > current_price]

    return {
        "support": supports[-3:],
        "resistance": resistances[:3],
    }


def _resolve_position_fraction(kelly: Dict) -> float:
    """Convert Kelly output into a safe execution fraction."""
    recommendation = str(kelly.get("recommendation") or "insufficient_data")
    fractional = max(0.0, _to_float(kelly.get("fractional_kelly")) / 100.0)

    if recommendation in {"avoid", "insufficient_data"}:
        return 0.0
    if recommendation == "minimal":
        return min(max(fractional, 0.03), 0.06)
    if recommendation == "conservative":
        return min(max(fractional, 0.05), 0.12)
    if recommendation == "moderate":
        return min(max(fractional, 0.08), 0.18)
    return min(max(fractional, 0.10), 0.25)


def calculate_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """Calculate Average True Range."""
    if len(closes) < period + 1:
        return abs(closes[-1] - closes[0]) if len(closes) > 1 else closes[-1] * 0.01
    
    tr1 = highs[1:] - lows[1:]
    tr2 = np.abs(highs[1:] - closes[:-1])
    tr3 = np.abs(lows[1:] - closes[:-1])
    
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    atr = np.mean(tr[-period:])
    
    return float(atr)


def calculate_kelly_criterion(
    win_rate: float,
    avg_win: float,
    avg_loss: float
) -> Dict:
    """
    Calculate Kelly Criterion for optimal position sizing.
    Kelly % = (BP - Q) / B
    Where: B = avg_win/avg_loss, P = win_rate, Q = 1-P
    """
    if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
        return {
            "kelly_pct": 0.0,
            "fractional_kelly": 0.0,
            "recommendation": "insufficient_data",
            "reason": "Win/loss history is insufficient for reliable Kelly sizing.",
            "edge_ratio": 0.0,
        }
    
    b = avg_win / avg_loss  # Average win/loss ratio
    p = win_rate
    q = 1 - p
    
    kelly_pct = (b * p - q) / b
    
    # Cap Kelly at reasonable bounds
    kelly_pct = max(-1, min(1, kelly_pct))
    
    # Fractional Kelly (more conservative)
    fractional_kelly = kelly_pct * 0.25  # Use 1/4 Kelly for safety
    
    if kelly_pct <= 0:
        recommendation = "avoid"
        reason = "Negative expected value"
    elif kelly_pct < 0.1:
        recommendation = "minimal"
        reason = "Low edge"
    elif kelly_pct < 0.25:
        recommendation = "conservative"
        reason = "Moderate edge"
    elif kelly_pct < 0.5:
        recommendation = "moderate"
        reason = "Good edge"
    else:
        recommendation = "aggressive"
        reason = "Strong edge (use caution)"
    
    return {
        "kelly_pct": round(kelly_pct * 100, 2),
        "fractional_kelly": round(fractional_kelly * 100, 2),
        "recommendation": recommendation,
        "reason": reason,
        "edge_ratio": round(b, 2)
    }


def calculate_stop_loss(
    current_price: float,
    direction: Literal["long", "short"],
    atr: float,
    method: Literal["atr", "support_resistance", "fixed"] = "atr",
    support_levels: Optional[List[float]] = None,
    resistance_levels: Optional[List[float]] = None,
    atr_multiplier: float = 1.5
) -> Dict:
    """Calculate optimal stop-loss level."""
    
    if method == "atr":
        distance = atr * atr_multiplier
        sl_price = current_price - distance if direction == "long" else current_price + distance
        
    elif method == "support_resistance" and (
        (direction == "long" and support_levels) or
        (direction == "short" and resistance_levels)
    ):
        if direction == "long":
            # Find nearest support below current price
            valid_supports = [s for s in support_levels if s < current_price * 0.995]
            sl_price = max(valid_supports) if valid_supports else current_price - atr * 1.5
        else:
            # Find nearest resistance above current price
            valid_resistances = [r for r in resistance_levels if r > current_price * 1.005]
            sl_price = min(valid_resistances) if valid_resistances else current_price + atr * 1.5
    else:
        # Fixed percentage
        pct = 0.015  # 1.5%
        sl_price = current_price * (1 - pct) if direction == "long" else current_price * (1 + pct)
    
    distance = abs(current_price - sl_price)
    distance_pct = (distance / current_price) * 100
    
    return {
        "price": round(sl_price, 2),
        "distance": round(distance, 2),
        "distance_pct": round(distance_pct, 2),
        "method": method
    }


def calculate_take_profits(
    entry_price: float,
    stop_loss: float,
    direction: Literal["long", "short"],
    risk_reward_targets: List[float] = [1.5, 2.5, 3.5]
) -> List[Dict]:
    """Calculate take-profit levels based on R:R ratios."""
    
    risk = abs(entry_price - stop_loss)
    if risk == 0:
        return []
    
    take_profits = []
    for rr in risk_reward_targets:
        if direction == "long":
            tp_price = entry_price + (risk * rr)
        else:
            tp_price = entry_price - (risk * rr)
        
        take_profits.append({
            "level": len(take_profits) + 1,
            "price": round(tp_price, 2),
            "r_r_ratio": rr,
            "distance_pct": round((abs(tp_price - entry_price) / entry_price) * 100, 2)
        })
    
    return take_profits


def calculate_position_size(
    account_size: float,
    risk_per_trade_pct: float,
    entry_price: float,
    stop_loss: float,
    kelly_fraction: float = 0.25
) -> Dict:
    """Calculate optimal position size."""
    
    risk_amount = account_size * (risk_per_trade_pct / 100)
    risk_per_unit = abs(entry_price - stop_loss)
    
    if risk_per_unit == 0:
        return {
            "base_units": 0,
            "units": 0,
            "position_value": 0,
            "risk_amount": risk_amount,
            "risk_pct": risk_per_trade_pct,
            "kelly_applied": 0,
            "error": "Invalid stop-loss distance"
        }
    
    # Base position size
    base_units = risk_amount / risk_per_unit
    
    # Apply Kelly fraction
    safe_kelly_fraction = max(0.0, min(0.25, kelly_fraction))
    kelly_adjusted_units = base_units * safe_kelly_fraction
    
    position_value = kelly_adjusted_units * entry_price
    
    # Check if position exceeds account (leverage consideration)
    max_position_value = account_size * 50  # Assume 50:1 max leverage for forex
    
    if position_value > max_position_value:
        kelly_adjusted_units = max_position_value / entry_price
        position_value = max_position_value
    
    return {
        "base_units": round(base_units, 2),
        "units": round(kelly_adjusted_units, 2),
        "position_value": round(position_value, 2),
        "risk_amount": round(risk_amount, 2),
        "risk_pct": risk_per_trade_pct,
        "kelly_applied": round(safe_kelly_fraction, 4)
    }


def calculate_trailing_stop(
    entry_price: float,
    current_price: float,
    highest_price: float,
    lowest_price: float,
    direction: Literal["long", "short"],
    atr: float,
    activation_rr: float = 1.0,
    trail_distance_atr: float = 1.0
) -> Dict:
    """Calculate trailing stop parameters."""
    
    initial_risk = abs(entry_price - (entry_price - atr * 1.5 if direction == "long" else entry_price + atr * 1.5))
    current_profit = abs(current_price - entry_price)
    
    # Check if trailing stop should be activated
    current_rr = current_profit / initial_risk if initial_risk > 0 else 0
    activated = current_rr >= activation_rr
    
    if direction == "long":
        trail_distance = atr * trail_distance_atr
        optimal_trail = highest_price - trail_distance
        current_stop = max(entry_price, optimal_trail) if activated else entry_price - initial_risk
    else:
        trail_distance = atr * trail_distance_atr
        optimal_trail = lowest_price + trail_distance
        current_stop = min(entry_price, optimal_trail) if activated else entry_price + initial_risk
    
    return {
        "activated": activated,
        "activation_rr": activation_rr,
        "current_rr": round(current_rr, 2),
        "trail_price": round(current_stop, 2),
        "trail_distance": round(trail_distance, 2),
        "breakeven": current_price >= entry_price if direction == "long" else current_price <= entry_price
    }


def calculate_portfolio_heat(
    account_size: float,
    open_positions: List[Dict],
    current_prices: Dict[str, float]
) -> Dict:
    """Calculate total portfolio heat (aggregate risk)."""
    
    total_risk = 0
    position_details = []
    
    for pos in open_positions:
        symbol = pos["symbol"]
        entry = pos["entry_price"]
        stop = pos["stop_loss"]
        units = pos["units"]
        direction = pos["direction"]
        
        current = current_prices.get(symbol, entry)
        risk_per_unit = abs(entry - stop)
        position_risk = risk_per_unit * units
        
        # Unrealized P&L
        if direction == "long":
            unrealized = (current - entry) * units
        else:
            unrealized = (entry - current) * units
        
        total_risk += position_risk
        position_details.append({
            "symbol": symbol,
            "unrealized_pnl": round(unrealized, 2),
            "remaining_risk": round(position_risk, 2)
        })
    
    heat_pct = (total_risk / account_size) * 100 if account_size > 0 else 0
    
    return {
        "total_heat_pct": round(heat_pct, 2),
        "total_heat_amount": round(total_risk, 2),
        "max_heat_recommended": 20.0,
        "status": "safe" if heat_pct < 15 else "caution" if heat_pct < 25 else "danger",
        "positions": position_details
    }


def calculate_volatility_adjustment(
    closes: np.ndarray,
    lookback: int = 20
) -> Dict:
    """Calculate volatility-based risk adjustments."""
    
    if len(closes) < lookback:
        return {"adjustment": 1.0, "volatility_regime": "normal"}
    
    returns = np.diff(closes) / closes[:-1]
    current_vol = np.std(returns[-lookback:])
    historical_vol = np.std(returns[-lookback*3:]) if len(returns) >= lookback*3 else current_vol
    
    vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0
    
    if vol_ratio > 1.5:
        regime = "high"
        adjustment = 0.7  # Reduce position size by 30%
    elif vol_ratio < 0.7:
        regime = "low"
        adjustment = 1.2  # Increase position size by 20%
    else:
        regime = "normal"
        adjustment = 1.0
    
    return {
        "adjustment": adjustment,
        "volatility_regime": regime,
        "current_volatility": round(current_vol * 100, 2),
        "historical_volatility": round(historical_vol * 100, 2),
        "volatility_ratio": round(vol_ratio, 2)
    }


async def calculate_risk_analysis(
    symbol: str,
    current_price: float,
    direction: Literal["long", "short"],
    candles: list,
    account_size: float = 10000,
    risk_per_trade_pct: float = 1.0,
    win_rate: float = 0.55,
    avg_win: float = 100,
    avg_loss: float = 50
) -> dict:
    """
    Main entry point - Calculate complete risk analysis.
    
    Args:
        symbol: Trading symbol
        current_price: Current market price
        direction: Trade direction (long/short)
        candles: List of candle dicts
        account_size: Account size in USD
        risk_per_trade_pct: Risk per trade percentage
        win_rate: Historical win rate (0-1)
        avg_win: Average winning trade amount
        avg_loss: Average losing trade amount
    
    Returns:
        Risk analysis as dict (JSON serializable)
    """
    
    if not candles or len(candles) < 14:
        return {
            "error": "Insufficient candle data",
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    current_price = _to_float(current_price, _to_float(candles[-1].get("close")))
    if current_price <= 0:
        return {
            "error": "Invalid current price",
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # Convert to numpy arrays
    highs = np.array([_to_float(c.get("high")) for c in candles])
    lows = np.array([_to_float(c.get("low")) for c in candles])
    closes = np.array([_to_float(c.get("close")) for c in candles])
    
    # Calculate ATR
    atr = calculate_atr(highs, lows, closes)
    
    # Calculate Kelly Criterion
    kelly = calculate_kelly_criterion(win_rate, avg_win, avg_loss)
    extracted_levels = _extract_levels(candles, current_price)
    
    # Calculate Stop Loss
    stop_loss = calculate_stop_loss(
        current_price,
        direction,
        atr,
        method="support_resistance" if extracted_levels["support"] or extracted_levels["resistance"] else "atr",
        support_levels=extracted_levels["support"],
        resistance_levels=extracted_levels["resistance"],
    )
    
    # Calculate Take Profits
    take_profits = calculate_take_profits(current_price, stop_loss["price"], direction)
    
    # Calculate Position Size
    position_fraction = _resolve_position_fraction(kelly)
    position = calculate_position_size(
        account_size, risk_per_trade_pct,
        current_price, stop_loss["price"],
        kelly_fraction=position_fraction,
    )
    
    # Calculate Trailing Stop
    highest = np.max(closes[-20:])
    lowest = np.min(closes[-20:])
    trailing = calculate_trailing_stop(
        current_price, current_price, highest, lowest,
        direction, atr
    )
    
    # Volatility Adjustment
    vol_adj = calculate_volatility_adjustment(closes)
    
    # Apply volatility adjustment to position
    adjusted_position = {
        **position,
        "adjusted_units": round(position["units"] * vol_adj["adjustment"], 2),
        "volatility_adjustment": vol_adj["adjustment"]
    }

    if adjusted_position["adjusted_units"] <= 0:
        position_summary = "No trade size recommended until edge improves."
    else:
        position_summary = f"{adjusted_position['adjusted_units']} units"

    primary_target = f"R:R {take_profits[0]['r_r_ratio'] if take_profits else 'N/A'}"
    if take_profits:
        primary_target = f"TP1 {take_profits[0]['price']} ({take_profits[0]['r_r_ratio']}:1)"
    
    return {
        "symbol": symbol,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_price": round(current_price, 2),
        "direction": direction,
        "atr_14": round(atr, 2),
        "kelly_criterion": kelly,
        "stop_loss": stop_loss,
        "take_profits": take_profits,
        "position_sizing": adjusted_position,
        "trailing_stop": trailing,
        "volatility": vol_adj,
        "calculation_method": "pure_math",
        "data_quality": {
            "candles_used": len(candles),
            "supports_found": len(extracted_levels["support"]),
            "resistances_found": len(extracted_levels["resistance"]),
        },
        "recommendations": {
            "position_size": position_summary,
            "max_risk": f"{risk_per_trade_pct}% of account",
            "stop_loss": f"{stop_loss['distance_pct']}% away",
            "primary_target": primary_target,
        }
    }
