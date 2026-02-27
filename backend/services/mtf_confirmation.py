"""
Multi-Timeframe Confirmation Service
Validates signals across multiple timeframes for higher accuracy
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class MTFConfirmation:
    """Multi-timeframe signal confirmation"""
    
    # Timeframe weights (higher = more important)
    TIMEFRAME_WEIGHTS = {
        "1m": 0.5,
        "5m": 1.0,    # Entry timing
        "15m": 1.5,   # Short term trend
        "1h": 2.0,    # Primary trend (most important)
        "4h": 1.8,    # Medium term
        "1d": 1.5,    # Long term
    }
    
    @classmethod
    def calculate_trend_score(
        cls,
        timeframe_signals: Dict[str, str]  # {"5m": "BUY", "15m": "SELL", ...}
    ) -> Tuple[SignalStrength, float, Dict]:
        """
        Calculate trend strength across multiple timeframes
        
        Returns: (signal_strength, confidence_score, details)
        """
        if not timeframe_signals:
            return SignalStrength.NEUTRAL, 0.0, {"error": "No signals provided"}
        
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0
        
        breakdown = {}
        
        for tf, signal in timeframe_signals.items():
            weight = cls.TIMEFRAME_WEIGHTS.get(tf, 1.0)
            total_weight += weight
            
            if signal == "BUY":
                buy_score += weight
                breakdown[tf] = {"signal": "BUY", "weight": weight, "contribution": weight}
            elif signal == "SELL":
                sell_score += weight
                breakdown[tf] = {"signal": "SELL", "weight": weight, "contribution": -weight}
            else:
                breakdown[tf] = {"signal": "NEUTRAL", "weight": weight, "contribution": 0}
        
        # Calculate net score (-1.0 to +1.0)
        if total_weight > 0:
            net_score = (buy_score - sell_score) / total_weight
        else:
            net_score = 0.0
        
        # Determine signal strength
        if net_score >= 0.8:
            strength = SignalStrength.STRONG_BUY
        elif net_score >= 0.3:
            strength = SignalStrength.BUY
        elif net_score <= -0.8:
            strength = SignalStrength.STRONG_SELL
        elif net_score <= -0.3:
            strength = SignalStrength.SELL
        else:
            strength = SignalStrength.NEUTRAL
        
        # Calculate confidence (0.5 to 1.0)
        confidence = 0.5 + (abs(net_score) * 0.5)
        
        details = {
            "net_score": round(net_score, 3),
            "buy_score": round(buy_score, 2),
            "sell_score": round(sell_score, 2),
            "total_weight": total_weight,
            "breakdown": breakdown,
            "agreement_ratio": round(abs(buy_score - sell_score) / total_weight, 2) if total_weight > 0 else 0,
        }
        
        return strength, confidence, details
    
    @classmethod
    def should_take_signal(
        cls,
        primary_direction: str,  # Direction from primary timeframe (e.g., 5m)
        timeframe_signals: Dict[str, str],
        min_agreement: float = 0.5,  # Minimum agreement ratio (0-1)
        require_1h_alignment: bool = True,  # 1h must agree for XAU/USD
    ) -> Tuple[bool, str, Dict]:
        """
        Determine if signal should be taken based on MTF confirmation
        
        Returns: (should_take, reason, details)
        """
        strength, confidence, details = cls.calculate_trend_score(timeframe_signals)
        
        # Check 1h alignment (critical for XAU/USD)
        if require_1h_alignment:
            h1_signal = timeframe_signals.get("1h", "NEUTRAL")
            if h1_signal != primary_direction and h1_signal != "NEUTRAL":
                return False, f"1h timeframe disagrees: {h1_signal} vs {primary_direction}", details
        
        # Check minimum agreement
        if details["agreement_ratio"] < min_agreement:
            return False, f"Low agreement ratio: {details['agreement_ratio']:.2f} < {min_agreement}", details
        
        # Check signal strength
        if strength in [SignalStrength.NEUTRAL]:
            return False, "Signal strength is neutral", details
        
        if primary_direction == "BUY" and strength in [SignalStrength.SELL, SignalStrength.STRONG_SELL]:
            return False, f"Primary BUY but MTF shows {strength.value}", details
        
        if primary_direction == "SELL" and strength in [SignalStrength.BUY, SignalStrength.STRONG_BUY]:
            return False, f"Primary SELL but MTF shows {strength.value}", details
        
        return True, f"MTF confirmed: {strength.value} (conf: {confidence:.2f})", details
    
    @classmethod
    def get_required_timeframes(cls, symbol: str) -> List[str]:
        """Get required timeframes for symbol"""
        if symbol == "XAUUSD":
            # XAU/USD needs more confirmation due to volatility
            return ["5m", "15m", "1h"]
        elif symbol == "NDX.INDX":
            # NASDAQ
            return ["5m", "15m", "1h"]
        else:
            # Default
            return ["5m", "1h"]


# Convenience function
async def confirm_signal_mtf(
    symbol: str,
    primary_direction: str,
    timeframe_signals: Dict[str, str],
) -> Tuple[bool, str, Dict]:
    """
    Confirm signal with multi-timeframe analysis
    
    Args:
        symbol: Trading symbol
        primary_direction: Direction from entry timeframe (5m)
        timeframe_signals: Dict of timeframe -> signal
        
    Returns:
        (should_take, reason, details)
    """
    # Get required timeframes for symbol
    required = MTFConfirmation.get_required_timeframes(symbol)
    
    # Filter to only required timeframes
    filtered_signals = {
        tf: sig for tf, sig in timeframe_signals.items() 
        if tf in required
    }
    
    # Check if we have minimum required timeframes
    if len(filtered_signals) < 2:
        logger.warning(f"Insufficient timeframe data for {symbol}: {filtered_signals}")
        # Allow signal but with lower confidence
        return True, "Insufficient MTF data, allowing with caution", {
            "timeframes_available": list(filtered_signals.keys()),
            "timeframes_required": required,
        }
    
    # XAU/USD requires stricter confirmation
    require_1h = symbol == "XAUUSD"
    min_agreement = 0.4 if symbol == "XAUUSD" else 0.3
    
    return MTFConfirmation.should_take_signal(
        primary_direction, 
        filtered_signals,
        min_agreement=min_agreement,
        require_1h_alignment=require_1h
    )
