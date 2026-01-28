"""
Slippage Monitor Service
========================
Real-time broker slippage tracking and automatic position size adjustment.

What it does:
- Tracks difference between signal price and executed price
- Alerts when average slippage exceeds threshold
- Automatically reduces position size during high slippage periods
- Logs all executions for analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, asdict
import json
import os

logger = logging.getLogger(__name__)

# In-memory storage (would be Supabase in production)
_execution_logs: List[Dict] = []
_slippage_config = {
    "threshold_pips": 3.0,           # Alert if avg slippage > 3 pips
    "adjustment_factor": 0.7,         # Reduce position by 30% if threshold exceeded
    "lookback_trades": 10,            # Check last 10 trades
    "current_multiplier": 1.0,        # Current position size multiplier
    "last_alert": None,
    "high_slippage_mode": False,
}

# Pip values for different instruments
PIP_VALUES = {
    "XAUUSD": 0.1,      # Gold: 1 pip = $0.10
    "NDX.INDX": 1.0,    # NASDAQ: 1 pip = 1 point
    "NASDAQ": 1.0,
}


@dataclass
class ExecutionLog:
    signal_id: str
    symbol: str
    signal_price: float
    filled_price: float
    slippage_pips: float
    direction: str
    broker: str
    timestamp: str
    is_favorable: bool  # True if slippage was in our favor


@dataclass
class SlippageStats:
    average_slippage: float
    max_slippage: float
    min_slippage: float
    favorable_count: int
    unfavorable_count: int
    total_trades: int
    position_multiplier: float
    high_slippage_mode: bool
    last_10_trades: List[Dict]


def get_pip_value(symbol: str) -> float:
    """Get pip value for a symbol."""
    normalized = symbol.upper()
    if "XAU" in normalized:
        return PIP_VALUES["XAUUSD"]
    elif "NDX" in normalized or "NASDAQ" in normalized:
        return PIP_VALUES["NDX.INDX"]
    return 0.01  # Default


def calculate_slippage(
    signal_price: float,
    filled_price: float,
    direction: str,
    symbol: str
) -> tuple[float, bool]:
    """
    Calculate slippage in pips and determine if favorable.
    
    Returns:
        (slippage_pips, is_favorable)
        
    Example:
        - BUY signal at 2750.00, filled at 2750.30 = 3 pips unfavorable
        - BUY signal at 2750.00, filled at 2749.80 = 2 pips favorable
        - SELL signal at 2750.00, filled at 2749.70 = 3 pips unfavorable
    """
    pip_value = get_pip_value(symbol)
    price_diff = filled_price - signal_price
    slippage_pips = abs(price_diff) / pip_value
    
    # Determine if slippage was favorable
    if direction.upper() in ["BUY", "LONG"]:
        is_favorable = price_diff < 0  # Got a better (lower) price
    else:  # SELL
        is_favorable = price_diff > 0  # Got a better (higher) price
    
    return round(slippage_pips, 2), is_favorable


async def log_execution(
    signal_id: str,
    symbol: str,
    signal_price: float,
    filled_price: float,
    direction: str,
    broker: str = "mt5"
) -> ExecutionLog:
    """
    Log a trade execution and calculate slippage.
    
    This should be called after every trade is executed.
    """
    global _execution_logs, _slippage_config
    
    slippage_pips, is_favorable = calculate_slippage(
        signal_price, filled_price, direction, symbol
    )
    
    log = ExecutionLog(
        signal_id=signal_id,
        symbol=symbol,
        signal_price=signal_price,
        filled_price=filled_price,
        slippage_pips=slippage_pips,
        direction=direction,
        broker=broker,
        timestamp=datetime.utcnow().isoformat() + "Z",
        is_favorable=is_favorable
    )
    
    _execution_logs.append(asdict(log))
    
    # Keep only last 100 logs in memory
    if len(_execution_logs) > 100:
        _execution_logs = _execution_logs[-100:]
    
    # Check if we need to adjust position size
    await _check_and_adjust_position_size()
    
    logger.info(
        f"Execution logged: {symbol} {direction} | "
        f"Signal: {signal_price} → Filled: {filled_price} | "
        f"Slippage: {slippage_pips} pips ({'favorable' if is_favorable else 'UNFAVORABLE'})"
    )
    
    return log


async def _check_and_adjust_position_size():
    """
    Check average slippage and adjust position size if needed.
    """
    global _slippage_config
    
    if len(_execution_logs) < 5:
        return  # Not enough data
    
    # Get last N trades (unfavorable slippage only)
    lookback = _slippage_config["lookback_trades"]
    recent_logs = _execution_logs[-lookback:]
    
    unfavorable_slippages = [
        log["slippage_pips"] 
        for log in recent_logs 
        if not log.get("is_favorable", False)
    ]
    
    if not unfavorable_slippages:
        # All slippage was favorable, reset multiplier
        if _slippage_config["current_multiplier"] < 1.0:
            _slippage_config["current_multiplier"] = min(
                1.0, 
                _slippage_config["current_multiplier"] + 0.1
            )
            _slippage_config["high_slippage_mode"] = False
            logger.info(f"Slippage improved, multiplier increased to {_slippage_config['current_multiplier']}")
        return
    
    avg_slippage = sum(unfavorable_slippages) / len(unfavorable_slippages)
    
    if avg_slippage > _slippage_config["threshold_pips"]:
        # High slippage detected - reduce position size
        _slippage_config["current_multiplier"] = _slippage_config["adjustment_factor"]
        _slippage_config["high_slippage_mode"] = True
        _slippage_config["last_alert"] = datetime.utcnow().isoformat()
        
        logger.warning(
            f"🚨 HIGH SLIPPAGE ALERT: Avg {avg_slippage:.2f} pips > threshold {_slippage_config['threshold_pips']} pips. "
            f"Position size reduced to {_slippage_config['adjustment_factor'] * 100}%"
        )
    elif _slippage_config["high_slippage_mode"]:
        # Slippage is back to normal, gradually increase multiplier
        if avg_slippage < _slippage_config["threshold_pips"] * 0.5:
            _slippage_config["current_multiplier"] = min(
                1.0,
                _slippage_config["current_multiplier"] + 0.1
            )
            if _slippage_config["current_multiplier"] >= 1.0:
                _slippage_config["high_slippage_mode"] = False
            logger.info(f"Slippage normalizing, multiplier: {_slippage_config['current_multiplier']}")


def get_position_multiplier() -> float:
    """
    Get current position size multiplier based on slippage.
    
    Returns:
        1.0 = Normal position size
        0.7 = Reduced by 30% due to high slippage
    """
    return _slippage_config["current_multiplier"]


def is_high_slippage_mode() -> bool:
    """Check if we're in high slippage mode."""
    return _slippage_config["high_slippage_mode"]


async def get_slippage_stats() -> SlippageStats:
    """
    Get slippage statistics for the last N trades.
    """
    lookback = _slippage_config["lookback_trades"]
    recent_logs = _execution_logs[-lookback:] if _execution_logs else []
    
    if not recent_logs:
        return SlippageStats(
            average_slippage=0,
            max_slippage=0,
            min_slippage=0,
            favorable_count=0,
            unfavorable_count=0,
            total_trades=0,
            position_multiplier=1.0,
            high_slippage_mode=False,
            last_10_trades=[]
        )
    
    slippages = [log["slippage_pips"] for log in recent_logs]
    favorable = sum(1 for log in recent_logs if log.get("is_favorable", False))
    
    return SlippageStats(
        average_slippage=round(sum(slippages) / len(slippages), 2),
        max_slippage=round(max(slippages), 2),
        min_slippage=round(min(slippages), 2),
        favorable_count=favorable,
        unfavorable_count=len(recent_logs) - favorable,
        total_trades=len(_execution_logs),
        position_multiplier=_slippage_config["current_multiplier"],
        high_slippage_mode=_slippage_config["high_slippage_mode"],
        last_10_trades=recent_logs
    )


async def get_slippage_adjustment() -> Dict:
    """
    Get slippage-based adjustments for signal generation.
    
    This is called by ml_prediction_service to adjust confidence/position.
    """
    stats = await get_slippage_stats()
    
    adjustment = {
        "position_multiplier": stats.position_multiplier,
        "high_slippage_mode": stats.high_slippage_mode,
        "average_slippage": stats.average_slippage,
        "warning": None,
        "confidence_penalty": 0,
    }
    
    if stats.high_slippage_mode:
        adjustment["warning"] = f"⚠️ High slippage ({stats.average_slippage:.1f} pips) - Position reduced 30%"
        adjustment["confidence_penalty"] = 5  # Reduce confidence by 5%
    
    # If slippage is extremely high, add extra penalty
    if stats.average_slippage > 5:
        adjustment["confidence_penalty"] = 10
        adjustment["warning"] = f"🚨 Extreme slippage ({stats.average_slippage:.1f} pips) - Consider waiting"
    
    return adjustment


# API endpoint handler
async def handle_execution_webhook(data: Dict) -> Dict:
    """
    Handle incoming execution webhook from broker.
    
    Expected data:
    {
        "signal_id": "abc123",
        "symbol": "XAUUSD",
        "signal_price": 2750.00,
        "filled_price": 2750.30,
        "direction": "BUY",
        "broker": "mt5"
    }
    """
    try:
        log = await log_execution(
            signal_id=data.get("signal_id", "unknown"),
            symbol=data.get("symbol", "XAUUSD"),
            signal_price=float(data.get("signal_price", 0)),
            filled_price=float(data.get("filled_price", 0)),
            direction=data.get("direction", "BUY"),
            broker=data.get("broker", "mt5")
        )
        
        stats = await get_slippage_stats()
        
        return {
            "success": True,
            "execution": asdict(log),
            "stats": asdict(stats)
        }
    except Exception as e:
        logger.error(f"Failed to log execution: {e}")
        return {
            "success": False,
            "error": str(e)
        }
