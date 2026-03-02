"""
Order Block Detector V2 - Independent Detection Algorithms
===========================================================

Each structure (CHoCH, BOS, FVG, OB) has its OWN detection algorithm.
No single algorithm detects all - they are separate analyses.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from enum import Enum
import numpy as np


class StructureType(Enum):
    CHOCH = "choch"  # Change of Character
    BOS = "bos"      # Break of Structure
    FVG = "fvg"      # Fair Value Gap
    OB = "ob"        # Order Block


@dataclass
class Candle:
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class SwingPoint:
    """Swing High or Low point"""
    index: int
    price: float
    type: str  # "high" or "low"


@dataclass
class CHoCH:
    """Change of Character - Trend reversal signal"""
    index: int
    type: str  # "bullish" or "bearish"
    price: float
    prev_swing: float
    strength: str  # "strong", "moderate", "weak"
    
    def to_dict(self):
        return {
            "detected": True,
            "type": self.type,
            "index": self.index,
            "price": round(self.price, 2),
            "prev_swing": round(self.prev_swing, 2),
            "strength": self.strength
        }


@dataclass
class BOS:
    """Break of Structure - Trend continuation signal"""
    index: int
    type: str  # "bullish" or "bearish"
    price: float
    broken_level: float
    confirmation: bool
    
    def to_dict(self):
        return {
            "detected": True,
            "type": self.type,
            "index": self.index,
            "price": round(self.price, 2),
            "broken_level": round(self.broken_level, 2),
            "confirmation": self.confirmation
        }


@dataclass
class FVG:
    """Fair Value Gap - Imbalance zone"""
    index: int
    direction: str  # "bullish" or "bearish"
    high: float
    low: float
    size: float
    filled: bool
    fill_percentage: float
    
    def to_dict(self):
        return {
            "detected": True,
            "direction": self.direction,
            "high": round(self.high, 2),
            "low": round(self.low, 2),
            "size": round(self.size, 2),
            "filled": self.filled,
            "fill_percentage": round(self.fill_percentage, 1)
        }


@dataclass
class OrderBlock:
    """Order Block - Institutional zone"""
    index: int
    type: str  # "bullish" or "bearish"
    zone_low: float
    zone_high: float
    open: float
    close: float
    score: int  # 0-100
    strength: str  # "strong", "moderate", "weak"
    tested: bool
    mitigated: bool
    
    def to_dict(self):
        return {
            "detected": True,
            "type": self.type,
            "zone_low": round(self.zone_low, 2),
            "zone_high": round(self.zone_high, 2),
            "score": self.score,
            "strength": self.strength,
            "tested": self.tested,
            "mitigated": self.mitigated,
            "has_choch": False,  # For frontend compatibility
            "has_bos": False,
            "has_fvg": False
        }


@dataclass
class MarketStructure:
    """Complete market structure analysis"""
    choch_list: List[CHoCH]
    bos_list: List[BOS]
    fvg_list: List[FVG]
    ob_list: List[OrderBlock]
    trend: str  # "bullish", "bearish", "ranging"
    
    def to_dict(self):
        return {
            "choch": [c.to_dict() for c in self.choch_list[-3:]],  # Last 3
            "bos": [b.to_dict() for b in self.bos_list[-3:]],
            "fvg": [f.to_dict() for f in self.fvg_list[-5:]],  # Last 5
            "order_blocks": [ob.to_dict() for ob in self.ob_list[:5]],  # Top 5
            "trend": self.trend,
            "counts": {
                "choch": len(self.choch_list),
                "bos": len(self.bos_list),
                "fvg": len(self.fvg_list),
                "ob": len(self.ob_list)
            }
        }


class CHoCHDetector:
    """
    CHoCH (Change of Character) Detection Algorithm
    ================================================
    Detects trend reversals by identifying breaks of previous swing points
    against the established trend.
    
    Bullish CHoCH: Price breaks above previous swing high in a downtrend
    Bearish CHoCH: Price breaks below previous swing low in an uptrend
    """
    
    @staticmethod
    def detect(candles: List[Candle], swings: List[SwingPoint]) -> List[CHoCH]:
        if len(swings) < 3 or len(candles) < 20:
            return []
        
        choch_list = []
        
        # Determine initial trend
        recent_swings = swings[-10:] if len(swings) >= 10 else swings
        higher_highs = sum(1 for i in range(1, len(recent_swings)) 
                          if recent_swings[i].type == "high" and 
                          recent_swings[i].price > recent_swings[i-1].price)
        lower_lows = sum(1 for i in range(1, len(recent_swings)) 
                        if recent_swings[i].type == "low" and 
                        recent_swings[i].price < recent_swings[i-1].price)
        
        trend = "bullish" if higher_highs > lower_lows else "bearish"
        
        # Detect CHoCH
        for i in range(2, len(swings)):
            current = swings[i]
            prev = swings[i-1]
            prev_prev = swings[i-2]
            
            if trend == "bearish":
                # Bullish CHoCH: Break above previous swing high
                if current.type == "high" and prev.type == "high":
                    if current.price > prev_prev.price:
                        displacement = (current.price - prev_prev.price) / prev_prev.price * 100
                        strength = "strong" if displacement > 1.5 else "moderate" if displacement > 0.8 else "weak"
                        choch_list.append(CHoCH(
                            index=current.index,
                            type="bullish",
                            price=current.price,
                            prev_swing=prev_prev.price,
                            strength=strength
                        ))
                        trend = "bullish"  # Trend changed
            
            else:  # bullish trend
                # Bearish CHoCH: Break below previous swing low
                if current.type == "low" and prev.type == "low":
                    if current.price < prev_prev.price:
                        displacement = (prev_prev.price - current.price) / prev_prev.price * 100
                        strength = "strong" if displacement > 1.5 else "moderate" if displacement > 0.8 else "weak"
                        choch_list.append(CHoCH(
                            index=current.index,
                            type="bearish",
                            price=current.price,
                            prev_swing=prev_prev.price,
                            strength=strength
                        ))
                        trend = "bearish"  # Trend changed
        
        return choch_list


class BOSDetector:
    """
    BOS (Break of Structure) Detection Algorithm
    ============================================
    Detects trend continuation by identifying breaks of previous swing points
    in the direction of the established trend.
    
    Bullish BOS: Price breaks above previous swing high in an uptrend
    Bearish BOS: Price breaks below previous swing low in a downtrend
    """
    
    @staticmethod
    def detect(candles: List[Candle], swings: List[SwingPoint]) -> List[BOS]:
        if len(swings) < 3 or len(candles) < 20:
            return []
        
        bos_list = []
        
        # Determine trend
        recent_swings = swings[-10:] if len(swings) >= 10 else swings
        higher_highs = sum(1 for i in range(1, len(recent_swings)) 
                          if recent_swings[i].type == "high" and 
                          recent_swings[i].price > recent_swings[i-1].price)
        lower_lows = sum(1 for i in range(1, len(recent_swings)) 
                        if recent_swings[i].type == "low" and 
                        recent_swings[i].price < recent_swings[i-1].price)
        
        trend = "bullish" if higher_highs > lower_lows else "bearish"
        
        # Detect BOS
        for i in range(1, len(swings)):
            current = swings[i]
            prev = swings[i-1]
            
            if trend == "bullish":
                # Bullish BOS: Higher high
                if current.type == "high" and prev.type == "high":
                    if current.price > prev.price:
                        # Check for confirmation (close above)
                        candle = candles[current.index]
                        confirmation = candle.close > prev.price
                        bos_list.append(BOS(
                            index=current.index,
                            type="bullish",
                            price=current.price,
                            broken_level=prev.price,
                            confirmation=confirmation
                        ))
            
            else:  # bearish
                # Bearish BOS: Lower low
                if current.type == "low" and prev.type == "low":
                    if current.price < prev.price:
                        candle = candles[current.index]
                        confirmation = candle.close < prev.price
                        bos_list.append(BOS(
                            index=current.index,
                            type="bearish",
                            price=current.price,
                            broken_level=prev.price,
                            confirmation=confirmation
                        ))
        
        return bos_list


class FVGDetector:
    """
    FVG (Fair Value Gap) Detection Algorithm
    ========================================
    Detects price imbalances where price jumps without overlapping.
    
    Bullish FVG: Candle[i-2].high < Candle[i].low (gap up)
    Bearish FVG: Candle[i-2].low > Candle[i].high (gap down)
    """
    
    @staticmethod
    def detect(candles: List[Candle]) -> List[FVG]:
        if len(candles) < 10:
            return []
        
        fvg_list = []
        current_price = candles[-1].close
        
        for i in range(2, len(candles)):
            c_prev2 = candles[i-2]
            c_current = candles[i]
            
            # Bullish FVG
            if c_prev2.high < c_current.low:
                gap_size = c_current.low - c_prev2.high
                
                # Check if filled
                filled = False
                fill_pct = 0.0
                for j in range(i, len(candles)):
                    if candles[j].low <= c_prev2.high:
                        filled = True
                        fill_pct = 100.0
                        break
                    elif candles[j].low < c_current.low:
                        fill_pct = ((c_current.low - candles[j].low) / gap_size) * 100
                
                if not filled:
                    fill_pct = max(0, fill_pct)
                
                fvg_list.append(FVG(
                    index=i,
                    direction="bullish",
                    high=c_current.low,
                    low=c_prev2.high,
                    size=gap_size,
                    filled=filled,
                    fill_percentage=fill_pct
                ))
            
            # Bearish FVG
            elif c_prev2.low > c_current.high:
                gap_size = c_prev2.low - c_current.high
                
                # Check if filled
                filled = False
                fill_pct = 0.0
                for j in range(i, len(candles)):
                    if candles[j].high >= c_prev2.low:
                        filled = True
                        fill_pct = 100.0
                        break
                    elif candles[j].high > c_current.high:
                        fill_pct = ((candles[j].high - c_current.high) / gap_size) * 100
                
                if not filled:
                    fill_pct = max(0, fill_pct)
                
                fvg_list.append(FVG(
                    index=i,
                    direction="bearish",
                    high=c_prev2.low,
                    low=c_current.high,
                    size=gap_size,
                    filled=filled,
                    fill_percentage=fill_pct
                ))
        
        return fvg_list


class OrderBlockDetector:
    """
    Order Block Detection Algorithm
    ===============================
    Detects institutional order blocks where smart money accumulated.
    
    Bullish OB: Bearish candle followed by strong bullish displacement
    Bearish OB: Bullish candle followed by strong bearish displacement
    """
    
    @staticmethod
    def detect(candles: List[Candle], swings: List[SwingPoint]) -> List[OrderBlock]:
        if len(candles) < 20:
            return []
        
        ob_list = []
        
        # Calculate ATR for displacement
        atr = OrderBlockDetector._calculate_atr(candles, 14)
        
        for i in range(1, len(candles) - 1):
            c_prev = candles[i-1]
            c_current = candles[i]
            c_next = candles[i+1]
            
            # Bullish Order Block
            if c_prev.close < c_prev.open:  # Previous bearish
                displacement = c_next.close - c_current.close
                if displacement > atr * 1.5:  # Strong displacement
                    score = min(100, int((displacement / atr) * 20))
                    strength = "strong" if score > 70 else "moderate" if score > 50 else "weak"
                    
                    # Check if tested/mitigated
                    tested = False
                    mitigated = False
                    for j in range(i+1, len(candles)):
                        if candles[j].low <= c_current.low:
                            mitigated = True
                            break
                        elif candles[j].low <= c_current.high and candles[j].low >= c_current.low:
                            tested = True
                    
                    ob_list.append(OrderBlock(
                        index=i,
                        type="bullish",
                        zone_low=c_current.low,
                        zone_high=c_current.high,
                        open=c_current.open,
                        close=c_current.close,
                        score=score,
                        strength=strength,
                        tested=tested,
                        mitigated=mitigated
                    ))
            
            # Bearish Order Block
            elif c_prev.close > c_prev.open:  # Previous bullish
                displacement = c_current.close - c_next.close
                if displacement > atr * 1.5:  # Strong displacement
                    score = min(100, int((displacement / atr) * 20))
                    strength = "strong" if score > 70 else "moderate" if score > 50 else "weak"
                    
                    # Check if tested/mitigated
                    tested = False
                    mitigated = False
                    for j in range(i+1, len(candles)):
                        if candles[j].high >= c_current.high:
                            mitigated = True
                            break
                        elif candles[j].high >= c_current.low and candles[j].high <= c_current.high:
                            tested = True
                    
                    ob_list.append(OrderBlock(
                        index=i,
                        type="bearish",
                        zone_low=c_current.low,
                        zone_high=c_current.high,
                        open=c_current.open,
                        close=c_current.close,
                        score=score,
                        strength=strength,
                        tested=tested,
                        mitigated=mitigated
                    ))
        
        # Sort by score (descending)
        ob_list.sort(key=lambda x: x.score, reverse=True)
        return ob_list
    
    @staticmethod
    def _calculate_atr(candles: List[Candle], period: int) -> float:
        if len(candles) < period + 1:
            return 1.0
        
        ranges = []
        for i in range(1, len(candles)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i-1].close
            ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
        
        return float(np.mean(ranges[-period:]))


class SwingDetector:
    """
    Swing Point Detection
    =====================
    Detects swing highs and lows using fractal method.
    """
    
    @staticmethod
    def detect(candles: List[Candle], period: int = 2) -> List[SwingPoint]:
        if len(candles) < period * 2 + 1:
            return []
        
        swings = []
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        
        for i in range(period, len(candles) - period):
            # Swing High
            if highs[i] == max(highs[i-period:i+period+1]):
                swings.append(SwingPoint(index=i, price=highs[i], type="high"))
            
            # Swing Low
            elif lows[i] == min(lows[i-period:i+period+1]):
                swings.append(SwingPoint(index=i, price=lows[i], type="low"))
        
        return swings


class MarketStructureAnalyzer:
    """
    Main analyzer that combines all detection algorithms
    """
    
    @staticmethod
    def analyze(candles: List[Candle]) -> MarketStructure:
        # Step 1: Detect swing points
        swings = SwingDetector.detect(candles, period=2)
        
        # Step 2: Run independent detection algorithms
        choch_list = CHoCHDetector.detect(candles, swings)
        bos_list = BOSDetector.detect(candles, swings)
        fvg_list = FVGDetector.detect(candles)
        ob_list = OrderBlockDetector.detect(candles, swings)
        
        # Step 3: Determine trend
        trend = MarketStructureAnalyzer._determine_trend(candles, swings)
        
        return MarketStructure(
            choch_list=choch_list,
            bos_list=bos_list,
            fvg_list=fvg_list,
            ob_list=ob_list,
            trend=trend
        )
    
    @staticmethod
    def _determine_trend(candles: List[Candle], swings: List[SwingPoint]) -> str:
        if len(swings) < 4:
            return "ranging"
        
        recent = swings[-6:]
        highs = [s for s in recent if s.type == "high"]
        lows = [s for s in recent if s.type == "low"]
        
        if len(highs) >= 2 and len(lows) >= 2:
            higher_highs = highs[-1].price > highs[-2].price
            higher_lows = lows[-1].price > lows[-2].price
            
            if higher_highs and higher_lows:
                return "bullish"
            elif not higher_highs and not higher_lows:
                return "bearish"
        
        return "ranging"


# Convenience function
def detect_all(candles: List[Candle]) -> Dict:
    """
    Main entry point - detects all market structures
    """
    structure = MarketStructureAnalyzer.analyze(candles)
    return structure.to_dict()
