"""
Adaptive Target & Stop Loss Calculator
Dynamically adjusts TP/SL levels based on market volatility (ATR) and session
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone

from services.target_config import get_symbol_config, calculate_target_prices, calculate_stoploss_price
from services.data_fetcher import fetch_intraday_candles

logger = logging.getLogger(__name__)


class AdaptiveTargets:
    """Adaptive target calculator based on ATR and market conditions"""
    
    # Session volatility multipliers
    SESSION_MULTIPLIERS = {
        "asia": 0.8,      # Lower volatility in Asia
        "europe": 1.0,    # Normal volatility
        "us": 1.2,        # Higher volatility in US
        "overlap": 1.5,   # London-NY overlap (highest volatility)
    }
    
    # Symbol-specific base ATR periods
    ATR_PERIODS = {
        "XAUUSD": 14,
        "NDX.INDX": 10,
        "GDAXI.INDX": 10,
        "CL.F": 14,
    }
    
    @staticmethod
    def calculate_atr(symbol: str, period: int = 14) -> float:
        """Calculate Average True Range for a symbol"""
        try:
            candles = fetch_intraday_candles(symbol, interval="5m", limit=period + 10)
            if not candles or len(candles) < period:
                logger.warning(f"Insufficient candles for ATR calculation: {symbol}")
                return 0.0
            
            tr_values = []
            for i in range(1, len(candles)):
                high = candles[i].get("high", 0)
                low = candles[i].get("low", 0)
                prev_close = candles[i-1].get("close", 0)
                
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                
                tr = max(tr1, tr2, tr3)
                tr_values.append(tr)
            
            if len(tr_values) >= period:
                atr = sum(tr_values[-period:]) / period
                return atr
            return 0.0
            
        except Exception as e:
            logger.error(f"ATR calculation error for {symbol}: {e}")
            return 0.0
    
    @staticmethod
    def get_current_session() -> str:
        """Determine current trading session"""
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        # London: 08:00-17:00 UTC
        # NY: 13:00-22:00 UTC
        # Overlap: 13:00-17:00 UTC
        
        if 13 <= hour < 17:
            return "overlap"  # London-NY overlap (highest volatility)
        elif 8 <= hour < 13:
            return "europe"   # London only
        elif 13 <= hour < 22:
            return "us"       # NY only
        elif 0 <= hour < 8:
            return "asia"     # Asia session
        else:
            return "asia"     # After hours (treat as low volatility)
    
    @classmethod
    def get_adaptive_targets(
        cls, 
        symbol: str, 
        entry_price: float, 
        direction: str,
        base_confidence: float = 0.5
    ) -> Dict[str, any]:
        """
        Calculate adaptive TP/SL based on ATR and session
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            direction: BUY or SELL
            base_confidence: ML confidence (0-1) for TP adjustment
            
        Returns:
            Dictionary with adaptive targets and metadata
        """
        # Get base config
        base_config = get_symbol_config(symbol)
        
        # Calculate ATR
        atr_period = cls.ATR_PERIODS.get(symbol, 14)
        atr = cls.calculate_atr(symbol, atr_period)
        
        # Get current session
        session = cls.get_current_session()
        session_mult = cls.SESSION_MULTIPLIERS.get(session, 1.0)
        
        # Calculate adaptive multiplier based on ATR vs typical values
        if symbol == "XAUUSD":
            typical_atr = 15.0  # Typical XAU/USD ATR(14) on 5m
        elif symbol == "NDX.INDX":
            typical_atr = 25.0
        elif symbol == "GDAXI.INDX":
            typical_atr = 20.0
        elif symbol == "CL.F":
            typical_atr = 0.15
        else:
            typical_atr = atr if atr > 0 else 1.0
        
        # Volatility ratio (current vs typical)
        if typical_atr > 0 and atr > 0:
            vol_ratio = atr / typical_atr
        else:
            vol_ratio = 1.0
        
        # Confidence adjustment (higher confidence = wider targets for more profit)
        confidence_mult = 0.8 + (base_confidence * 0.4)  # 0.8 to 1.2 range
        
        # Final multiplier
        final_mult = session_mult * max(0.7, min(vol_ratio, 1.5)) * confidence_mult
        
        # Calculate adaptive targets
        if symbol == "XAUUSD":
            # ATR-based targets for XAU/USD
            tp1_pips = max(6, round(atr * 0.5))
            tp2_pips = max(10, round(atr * 0.9))
            tp3_pips = max(18, round(atr * 1.5))
            tp4_pips = max(30, round(atr * 2.5))
            sl_pips = max(12, round(atr * 1.0))  # SL = 1x ATR
        elif symbol in ["NDX.INDX", "GDAXI.INDX"]:
            # Index targets
            tp1_pips = max(12, round(atr * 0.5))
            tp2_pips = max(20, round(atr * 0.9))
            tp3_pips = max(30, round(atr * 1.3))
            tp4_pips = max(45, round(atr * 2.0))
            sl_pips = max(25, round(atr * 1.2))
        elif symbol == "CL.F":
            # Oil targets (percentage based)
            tp1_pips = 0.015
            tp2_pips = 0.03
            tp3_pips = 0.05
            tp4_pips = 0.08
            sl_pips = 0.04
        else:
            # Default
            tp1_pips = base_config.targets[0].pips * final_mult
            tp2_pips = base_config.targets[1].pips * final_mult
            tp3_pips = base_config.targets[2].pips * final_mult if len(base_config.targets) > 2 else tp2_pips * 1.5
            tp4_pips = base_config.targets[3].pips * final_mult if len(base_config.targets) > 3 else tp3_pips * 1.5
            sl_pips = base_config.stoploss_pips * max(0.8, min(vol_ratio, 1.3))
        
        # Calculate actual price levels
        mult = 1 if direction == "BUY" else -1
        
        targets = {
            "TP1": round(entry_price + (tp1_pips * mult), 4),
            "TP2": round(entry_price + (tp2_pips * mult), 4),
            "TP3": round(entry_price + (tp3_pips * mult), 4),
            "TP4": round(entry_price + (tp4_pips * mult), 4),
            "SL": round(entry_price - (sl_pips * mult), 4),
        }
        
        return {
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "atr": round(atr, 4),
            "session": session,
            "session_multiplier": session_mult,
            "volatility_ratio": round(vol_ratio, 2),
            "confidence_multiplier": round(confidence_mult, 2),
            "targets_pips": {
                "TP1": tp1_pips,
                "TP2": tp2_pips,
                "TP3": tp3_pips,
                "TP4": tp4_pips,
                "SL": sl_pips,
            },
            "targets": targets,
            "risk_reward": round((tp1_pips / sl_pips) if sl_pips > 0 else 0, 2),
        }
    
    @classmethod
    def should_filter_signal(
        cls,
        symbol: str,
        direction: str,
        dxy_direction: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Check if signal should be filtered based on correlation rules
        
        Returns: (should_filter, reason)
        """
        # XAU/USD - DXY negative correlation
        if symbol == "XAUUSD" and dxy_direction:
            if direction == "BUY" and dxy_direction == "UP":
                return True, "XAU BUY filtered: DXY is strengthening"
            if direction == "SELL" and dxy_direction == "DOWN":
                return True, "XAU SELL filtered: DXY is weakening"
        
        return False, ""


# Convenience function
async def get_adaptive_tp_sl(
    symbol: str, 
    direction: str, 
    entry_price: float,
    confidence: float = 0.5
) -> Dict:
    """Get adaptive TP/SL for a signal"""
    return AdaptiveTargets.get_adaptive_targets(symbol, entry_price, direction, confidence)
