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
    candle_index_ago: int = 0  # How many candles ago this CHoCH occurred
    
    def to_dict(self):
        return {
            "detected": True,
            "type": self.type,
            "index": self.index,
            "price": round(self.price, 2),
            "prev_swing": round(self.prev_swing, 2),
            "strength": self.strength,
            "candle_index_ago": self.candle_index_ago
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
    
    @property
    def mid(self):
        """Midpoint of the FVG zone"""
        return (self.high + self.low) / 2
    
    def to_dict(self):
        return {
            "detected": True,
            "direction": self.direction,
            "high": round(self.high, 2),
            "low": round(self.low, 2),
            "size": round(self.size, 2),
            "filled": self.filled,
            "fill_percentage": round(self.fill_percentage, 1),
            "mid": round(self.mid, 2)
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
            "index": self.index,
            "zone_low": round(self.zone_low, 2),
            "zone_high": round(self.zone_high, 2),
            "score": self.score,
            "strength": self.strength,
            "tested": self.tested,
            "mitigated": self.mitigated,
            "has_choch": False,
            "has_bos": False,
            "has_fvg": False
        }


@dataclass
class TPSLProjection:
    """TP/SL projection based on swing range"""
    direction: str  # "bullish" or "bearish"
    entry_zone_low: float
    entry_zone_high: float
    stop_loss: float
    tp1: float  # 50% of swing range
    tp2: float  # 100% of swing range
    tp3: float  # 161.8% of swing range (Fibonacci extension)
    swing_low: float
    swing_high: float
    swing_range: float
    confidence: str  # "high", "medium", "low"

    def to_dict(self):
        return {
            "direction": self.direction,
            "entry_zone_low": round(self.entry_zone_low, 2),
            "entry_zone_high": round(self.entry_zone_high, 2),
            "stop_loss": round(self.stop_loss, 2),
            "tp1": round(self.tp1, 2),
            "tp2": round(self.tp2, 2),
            "tp3": round(self.tp3, 2),
            "swing_low": round(self.swing_low, 2),
            "swing_high": round(self.swing_high, 2),
            "swing_range": round(self.swing_range, 2),
            "confidence": self.confidence,
        }


@dataclass
class MarketStructure:
    """Complete market structure analysis"""
    choch_list: List[CHoCH]
    bos_list: List[BOS]
    fvg_list: List[FVG]
    ob_list: List[OrderBlock]
    swing_list: List[SwingPoint]
    trend: str  # "bullish", "bearish", "ranging"
    projection: Optional[TPSLProjection] = None
    
    def to_dict(self):
        return {
            "choch": [c.to_dict() for c in self.choch_list[-3:]],
            "bos": [b.to_dict() for b in self.bos_list[-3:]],
            "fvg": [f.to_dict() for f in self.fvg_list[-5:]],
            "order_blocks": [ob.to_dict() for ob in self.ob_list[:5]],
            "swing_points": [
                {"index": s.index, "price": round(s.price, 2), "type": s.type}
                for s in self.swing_list[-20:]
            ],
            "trend": self.trend,
            "projection": self.projection.to_dict() if self.projection else None,
            "counts": {
                "choch": len(self.choch_list),
                "bos": len(self.bos_list),
                "fvg": len(self.fvg_list),
                "ob": len(self.ob_list)
            }
        }


class SwingDetector:
    """Swing Point Detection using Fractals"""
    
    @staticmethod
    def detect(candles: List[Candle], period: int = 3) -> List[SwingPoint]:
        if len(candles) < period * 2 + 1:
            return []
        
        swings = []
        
        for i in range(period, len(candles) - period):
            # Swing High
            is_swing_high = True
            for j in range(1, period + 1):
                if candles[i].high <= candles[i-j].high or candles[i].high <= candles[i+j].high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swings.append(SwingPoint(index=i, price=candles[i].high, type="high"))
                continue
            
            # Swing Low
            is_swing_low = True
            for j in range(1, period + 1):
                if candles[i].low >= candles[i-j].low or candles[i].low >= candles[i+j].low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swings.append(SwingPoint(index=i, price=candles[i].low, type="low"))
        
        return swings


class CHoCHDetector:
    """
    CHoCH (Change of Character) Detection
    ======================================
    Detects when price breaks structure against the current trend.
    
    Bullish CHoCH: In a downtrend, price makes a higher high (breaks above previous lower high)
    Bearish CHoCH: In an uptrend, price makes a lower low (breaks below previous higher low)
    
    Now validates trend context: a CHoCH must occur AGAINST the prevailing micro-trend.
    """
    
    @staticmethod
    def detect(candles: List[Candle], swings: List[SwingPoint]) -> List[CHoCH]:
        if len(swings) < 4 or len(candles) < 20:
            return []
        
        choch_list = []
        
        highs = [s for s in swings if s.type == "high"]
        lows = [s for s in swings if s.type == "low"]
        
        if len(highs) < 2 or len(lows) < 2:
            return []
        
        # Compute a quick EMA-based micro-trend at each swing
        closes = np.array([c.close for c in candles])
        ema_fast = CHoCHDetector._ema(closes, 10)
        ema_slow = CHoCHDetector._ema(closes, 30)
        
        # Detect CHoCH by analyzing swing sequences WITH trend context
        for i in range(1, min(len(highs), len(lows))):
            # Bullish CHoCH: Higher high after lower highs — must be in a prior downtrend
            if i >= 2 and highs[i].price > highs[i-1].price:
                idx = highs[i].index
                # Validate prior downtrend: EMA fast < EMA slow before this swing
                lookback_idx = max(0, idx - 5)
                prior_downtrend = ema_fast[lookback_idx] < ema_slow[lookback_idx]
                
                if prior_downtrend:
                    displacement = (highs[i].price - highs[i-1].price) / highs[i-1].price * 100
                    strength = "strong" if displacement > 0.8 else "moderate" if displacement > 0.3 else "weak"
                    
                    choch_list.append(CHoCH(
                        index=idx,
                        type="bullish",
                        price=highs[i].price,
                        prev_swing=highs[i-1].price,
                        strength=strength,
                        candle_index_ago=len(candles) - 1 - idx
                    ))
            
            # Bearish CHoCH: Lower low after higher lows — must be in a prior uptrend
            if i >= 2 and lows[i].price < lows[i-1].price:
                idx = lows[i].index
                lookback_idx = max(0, idx - 5)
                prior_uptrend = ema_fast[lookback_idx] > ema_slow[lookback_idx]
                
                if prior_uptrend:
                    displacement = (lows[i-1].price - lows[i].price) / lows[i-1].price * 100
                    strength = "strong" if displacement > 0.8 else "moderate" if displacement > 0.3 else "weak"
                    
                    choch_list.append(CHoCH(
                        index=idx,
                        type="bearish",
                        price=lows[i].price,
                        prev_swing=lows[i-1].price,
                        strength=strength,
                        candle_index_ago=len(candles) - 1 - idx
                    ))
        
        return choch_list
    
    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        """Simple EMA calculation."""
        if len(data) < period:
            return data.copy()
        ema = np.zeros_like(data)
        ema[0] = data[0]
        k = 2.0 / (period + 1)
        for i in range(1, len(data)):
            ema[i] = data[i] * k + ema[i-1] * (1 - k)
        return ema


class BOSDetector:
    """
    BOS (Break of Structure) Detection
    ==================================
    Detects when price continues in trend direction.
    
    Bullish BOS: Higher high in uptrend (close must confirm above previous swing high)
    Bearish BOS: Lower low in downtrend (close must confirm below previous swing low)
    
    Validates trend direction before flagging BOS to avoid noise in ranging markets.
    """
    
    @staticmethod
    def detect(candles: List[Candle], swings: List[SwingPoint]) -> List[BOS]:
        if len(swings) < 4 or len(candles) < 10:
            return []
        
        bos_list = []
        
        # Calculate ATR for minimum displacement filter
        atr = BOSDetector._calculate_atr(candles, 14)
        min_displacement = atr * 0.15  # BOS must break by at least 15% of ATR
        
        highs = [s for s in swings if s.type == "high"]
        lows = [s for s in swings if s.type == "low"]
        
        # Bullish BOS: Consecutive higher highs in an uptrend context
        for i in range(1, len(highs)):
            displacement = highs[i].price - highs[i-1].price
            if displacement > min_displacement:
                candle = candles[highs[i].index]
                # Close must confirm break above previous swing high
                confirmation = candle.close > highs[i-1].price
                
                # Check for uptrend context: recent lows are also rising
                relevant_lows = [l for l in lows if l.index < highs[i].index]
                trend_ok = True
                if len(relevant_lows) >= 2:
                    trend_ok = relevant_lows[-1].price >= relevant_lows[-2].price
                
                if trend_ok:
                    bos_list.append(BOS(
                        index=highs[i].index,
                        type="bullish",
                        price=highs[i].price,
                        broken_level=highs[i-1].price,
                        confirmation=confirmation
                    ))
        
        # Bearish BOS: Consecutive lower lows in a downtrend context
        for i in range(1, len(lows)):
            displacement = lows[i-1].price - lows[i].price
            if displacement > min_displacement:
                candle = candles[lows[i].index]
                confirmation = candle.close < lows[i-1].price
                
                # Check for downtrend context: recent highs are also falling
                relevant_highs = [h for h in highs if h.index < lows[i].index]
                trend_ok = True
                if len(relevant_highs) >= 2:
                    trend_ok = relevant_highs[-1].price <= relevant_highs[-2].price
                
                if trend_ok:
                    bos_list.append(BOS(
                        index=lows[i].index,
                        type="bearish",
                        price=lows[i].price,
                        broken_level=lows[i-1].price,
                        confirmation=confirmation
                    ))
        
        return bos_list
    
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


class FVGDetector:
    """
    FVG (Fair Value Gap) Detection
    ==============================
    3-candle pattern: High[i-2] < Low[i] for bullish, Low[i-2] > High[i] for bearish
    
    Now filters with ATR-based minimum gap size to reduce noise from tiny gaps.
    """
    
    @staticmethod
    def detect(candles: List[Candle]) -> List[FVG]:
        if len(candles) < 15:
            return []

        fvg_list = []

        # Calculate ATR for minimum and MAXIMUM gap size filters
        atr = FVGDetector._calculate_atr(candles, 14)
        min_gap = atr * 0.25   # Gap must be at least 25% of ATR (filters noise)
        max_gap = atr * 10.0   # Gap must be at most 10× ATR (rejects cross-data-gap artifacts)

        # Estimate base bar interval from the first valid consecutive pair
        base_interval: float = 0.0
        for k in range(1, min(20, len(candles))):
            diff = candles[k].timestamp - candles[k - 1].timestamp
            if diff > 0:
                base_interval = diff
                break
        # Allow up to 6× the base interval between the outer candles of a 3-bar FVG
        max_time_span = base_interval * 6 if base_interval > 0 else 0.0

        for i in range(2, len(candles)):
            c_prev2 = candles[i-2]
            c_current = candles[i]

            # Time-continuity guard: skip if candles are not time-adjacent
            # (prevents cross-break-in-data false FVGs spanning extreme price ranges)
            if max_time_span > 0:
                time_span = c_current.timestamp - c_prev2.timestamp
                if time_span > max_time_span:
                    continue

            # Bullish FVG: Gap up (Low > Previous High)
            if c_current.low > c_prev2.high:
                gap_size = c_current.low - c_prev2.high

                # Filter out tiny gaps (noise) and enormous gaps (data artifacts)
                if gap_size < min_gap or gap_size > max_gap:
                    continue

                # Check if filled using ONLY the last candle (no future look-ahead)
                last_candle = candles[-1]
                filled = last_candle.low <= c_prev2.high
                fill_pct = 0.0
                if filled:
                    fill_pct = 100.0
                elif last_candle.low < c_current.low:
                    fill_pct = min(100, ((c_current.low - last_candle.low) / gap_size) * 100)

                fvg_list.append(FVG(
                    index=i,
                    direction="bullish",
                    high=c_current.low,
                    low=c_prev2.high,
                    size=gap_size,
                    filled=filled,
                    fill_percentage=fill_pct
                ))

            # Bearish FVG: Gap down (High < Previous Low)
            elif c_current.high < c_prev2.low:
                gap_size = c_prev2.low - c_current.high

                if gap_size < min_gap or gap_size > max_gap:
                    continue

                # Check if filled using ONLY the last candle (no future look-ahead)
                last_candle = candles[-1]
                filled = last_candle.high >= c_prev2.low
                fill_pct = 0.0
                if filled:
                    fill_pct = 100.0
                elif last_candle.high > c_current.high:
                    fill_pct = min(100, ((last_candle.high - c_current.high) / gap_size) * 100)

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


class OrderBlockDetector:
    """
    Order Block Detection
    =====================
    Bullish OB: Bearish candle before strong bullish move (displacement)
    Bearish OB: Bullish candle before strong bearish move (displacement)
    """
    
    @staticmethod
    def detect(candles: List[Candle], swings: List[SwingPoint]) -> List[OrderBlock]:
        if len(candles) < 20:
            return []

        ob_list = []
        atr = OrderBlockDetector._calculate_atr(candles, 14)
        volumes = np.array([c.volume for c in candles])
        avg_volume = float(np.mean(volumes)) if len(volumes) > 0 else 1.0

        # Estimate base bar interval for time-continuity guard
        base_interval: float = 0.0
        for k in range(1, min(20, len(candles))):
            diff = candles[k].timestamp - candles[k - 1].timestamp
            if diff > 0:
                base_interval = diff
                break
        max_bar_gap = base_interval * 6 if base_interval > 0 else 0.0

        for i in range(1, len(candles) - 2):
            c_prev = candles[i-1]
            c_current = candles[i]
            c_next = candles[i+1]

            # Time-continuity guard: skip OB if prev→current or current→next spans a
            # data break (e.g. stale-to-live candle seam after a Redis outage).
            if max_bar_gap > 0:
                if (c_current.timestamp - c_prev.timestamp) > max_bar_gap:
                    continue
                if (c_next.timestamp - c_current.timestamp) > max_bar_gap:
                    continue

            # Volume confirmation: OB candle or displacement candle should have above-average volume
            local_vol_avg = float(np.mean(volumes[max(0, i-20):i+1])) if i > 0 else avg_volume
            vol_ratio = volumes[i+1] / local_vol_avg if local_vol_avg > 0 else 1.0
            
            # Bullish Order Block: bearish candle before strong upward displacement
            if c_current.close < c_current.open:  # Current candle was bearish (the OB candle)
                displacement_up = c_next.close - c_current.open
                
                if displacement_up > atr * 1.2:  # Strong upward displacement
                    score = min(100, int(30 + (displacement_up / atr) * 12))
                    # Volume bonus
                    if vol_ratio > 1.2:
                        score = min(100, score + 10)
                    strength = "strong" if score > 70 else "moderate" if score > 50 else "weak"
                    
                    # Check tested/mitigated using ONLY the current (last) candle
                    # Mitigated = CLOSE below zone (confirmed break)
                    # Tested = wick into zone OR sweep below zone with close back inside
                    last_candle = candles[-1]
                    tested = False
                    mitigated = False
                    if last_candle.close < c_current.low:
                        mitigated = True
                    elif last_candle.low <= c_current.high:
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
            
            # Bearish Order Block: bullish candle before strong downward displacement
            elif c_current.close > c_current.open:  # Current candle was bullish (the OB candle)
                displacement_down = c_current.open - c_next.close
                
                if displacement_down > atr * 1.2:  # Strong downward displacement
                    score = min(100, int(30 + (displacement_down / atr) * 12))
                    if vol_ratio > 1.2:
                        score = min(100, score + 10)
                    strength = "strong" if score > 70 else "moderate" if score > 50 else "weak"
                    
                    # Check tested/mitigated using ONLY the current (last) candle
                    # Mitigated = CLOSE above zone (confirmed break)
                    # Tested = wick into zone OR sweep above zone with close back inside
                    last_candle = candles[-1]
                    tested = False
                    mitigated = False
                    if last_candle.close > c_current.high:
                        mitigated = True
                    elif last_candle.high >= c_current.low:
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
        
        # Sort by score descending, filter out mitigated OBs for primary display
        ob_list = [ob for ob in ob_list if not ob.mitigated]
        ob_list.sort(key=lambda x: x.score, reverse=True)
        return ob_list[:10]  # Return top 10
    
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


class MarketStructureAnalyzer:
    """Main analyzer combining all detection algorithms"""

    # ─── Symbol-specific TP/SL config ─────────────────────────────────────────
    # SL ATR multiplier: how many ATRs below/above swing low/high
    _SL_ATR: Dict[str, float] = {
        "NDX.INDX":    1.0,   # NASDAQ — wide SL, high intraday volatility
        "GDAXI.INDX":  0.8,   # DAX — slightly tighter
        "XAUUSD":      0.5,   # Gold — tightest, ranging instrument
        "USOIL.FOREX": 1.2,   # Oil — widest, EIA event risk
    }
    _DEFAULT_SL_ATR = 0.7

    # TP Fibonacci levels: fractions of swing_range projected from swing extreme
    # tp1=first target, tp2=second, tp3=extension
    _TP_FIBS: Dict[str, Tuple[float, float, float]] = {
        "NDX.INDX":    (1.0, 1.618, 2.0),    # NASDAQ loves momentum extensions
        "GDAXI.INDX":  (1.0, 1.272, 1.618),
        "XAUUSD":      (1.0, 1.618, 2.618),  # Gold: textbook fib extensions
        "USOIL.FOREX": (0.618, 1.0, 1.272),  # Oil: conservative (EIA reversals)
    }
    _DEFAULT_TP_FIBS: Tuple[float, float, float] = (1.0, 1.618, 2.0)

    @staticmethod
    def analyze(candles: List[Candle], swing_period: int = 3, symbol: str = "") -> MarketStructure:
        # Step 1: Detect swing points (period=3 reduces noise on intraday)
        swings = SwingDetector.detect(candles, period=swing_period)

        # Step 2: Run independent detection algorithms
        choch_list = CHoCHDetector.detect(candles, swings)
        bos_list = BOSDetector.detect(candles, swings)
        fvg_list = FVGDetector.detect(candles)
        ob_list = OrderBlockDetector.detect(candles, swings)

        # Step 3: Determine trend
        trend = MarketStructureAnalyzer._determine_trend(candles, swings)

        # Step 4: Calculate TP/SL projection (symbol-aware)
        projection = MarketStructureAnalyzer._calculate_projection(
            candles, swings, ob_list, fvg_list, trend, symbol=symbol
        )

        return MarketStructure(
            choch_list=choch_list,
            bos_list=bos_list,
            fvg_list=fvg_list,
            ob_list=ob_list,
            swing_list=swings,
            trend=trend,
            projection=projection,
        )
    
    @staticmethod
    def _determine_trend(candles: List[Candle], swings: List[SwingPoint]) -> str:
        if len(swings) < 4:
            return "ranging"
        
        # Use last 6 swings (or available) for more robust trend
        recent = swings[-6:] if len(swings) >= 6 else swings[-4:]
        highs = [s for s in recent if s.type == "high"]
        lows = [s for s in recent if s.type == "low"]
        
        if len(highs) >= 2 and len(lows) >= 2:
            higher_highs = highs[-1].price > highs[0].price
            higher_lows = lows[-1].price > lows[0].price
            lower_highs = highs[-1].price < highs[0].price
            lower_lows = lows[-1].price < lows[0].price
            
            if higher_highs and higher_lows:
                return "bullish"
            elif lower_highs and lower_lows:
                return "bearish"
        
        # Also check EMA alignment as tiebreaker
        if len(candles) >= 30:
            closes = np.array([c.close for c in candles])
            ema20 = CHoCHDetector._ema(closes, 20)
            ema50_period = min(50, len(candles) - 1)
            ema50 = CHoCHDetector._ema(closes, ema50_period)
            if ema20[-1] > ema50[-1] * 1.001:
                return "bullish"
            elif ema20[-1] < ema50[-1] * 0.999:
                return "bearish"
        
        return "ranging"


    @staticmethod
    def _calculate_projection(
        candles: List[Candle],
        swings: List[SwingPoint],
        ob_list: List[OrderBlock],
        fvg_list: List[FVG],
        trend: str,
        symbol: str = "",
    ) -> Optional[TPSLProjection]:
        """Calculate symbol-aware TP/SL projection based on swing range.

        Logic:
        - Swing range = most recent significant Swing High − Swing Low
        - SL = beyond swing extreme, ATR multiplier varies per symbol
        - TP1/2/3 = Fibonacci extensions projected from swing extreme
          Symbol-specific Fib levels (NDX: 1.0/1.618/2.0, Gold: 1.0/1.618/2.618)
        - Entry zone = nearest OB in direction, or 10% of range from extreme
        """
        if len(swings) < 4 or not candles:
            return None

        current_price = candles[-1].close

        recent_highs = [s for s in swings if s.type == "high"]
        recent_lows = [s for s in swings if s.type == "low"]
        if not recent_highs or not recent_lows:
            return None

        swing_high = max(recent_highs[-4:], key=lambda s: s.price)
        swing_low = min(recent_lows[-4:], key=lambda s: s.price)
        swing_range = swing_high.price - swing_low.price
        if swing_range <= 0:
            return None

        # ── Symbol-aware ATR multiplier for SL ────────────────────────────────
        sym_upper = (symbol or "").upper().strip()
        sl_atr_mult = MarketStructureAnalyzer._SL_ATR.get(sym_upper, MarketStructureAnalyzer._DEFAULT_SL_ATR)
        atr = FVGDetector._calculate_atr(candles, 14)
        sl_margin = atr * sl_atr_mult

        # ── Symbol-aware Fibonacci TP levels ──────────────────────────────────
        fib1, fib2, fib3 = MarketStructureAnalyzer._TP_FIBS.get(
            sym_upper, MarketStructureAnalyzer._DEFAULT_TP_FIBS
        )

        # ── Confidence score ────────────────────────────────────────────────
        confirmations = sum([bool(ob_list), bool(fvg_list), trend != "ranging"])
        confidence = "high" if confirmations >= 3 else "medium" if confirmations >= 2 else "low"

        mid = (swing_high.price + swing_low.price) / 2
        is_bullish = trend == "bullish" or (trend == "ranging" and current_price < mid)
        is_bearish = trend == "bearish" or (trend == "ranging" and current_price >= mid)

        if is_bullish:
            bull_obs = [ob for ob in ob_list if ob.type == "bullish"]
            if bull_obs:
                best_ob = bull_obs[0]
                entry_low, entry_high = best_ob.zone_low, best_ob.zone_high
            else:
                entry_low = swing_low.price
                entry_high = swing_low.price + swing_range * 0.1

            return TPSLProjection(
                direction="bullish",
                entry_zone_low=entry_low,
                entry_zone_high=entry_high,
                stop_loss=swing_low.price - sl_margin,
                tp1=swing_high.price + swing_range * (fib1 - 1.0),   # fib1=1.0 → swing high itself
                tp2=swing_high.price + swing_range * (fib2 - 1.0),
                tp3=swing_high.price + swing_range * (fib3 - 1.0),
                swing_low=swing_low.price,
                swing_high=swing_high.price,
                swing_range=swing_range,
                confidence=confidence,
            )

        if is_bearish:
            bear_obs = [ob for ob in ob_list if ob.type == "bearish"]
            if bear_obs:
                best_ob = bear_obs[0]
                entry_low, entry_high = best_ob.zone_low, best_ob.zone_high
            else:
                entry_low = swing_high.price - swing_range * 0.1
                entry_high = swing_high.price

            return TPSLProjection(
                direction="bearish",
                entry_zone_low=entry_low,
                entry_zone_high=entry_high,
                stop_loss=swing_high.price + sl_margin,
                tp1=swing_low.price - swing_range * (fib1 - 1.0),
                tp2=swing_low.price - swing_range * (fib2 - 1.0),
                tp3=swing_low.price - swing_range * (fib3 - 1.0),
                swing_low=swing_low.price,
                swing_high=swing_high.price,
                swing_range=swing_range,
                confidence=confidence,
            )

        return None


# Convenience function
def detect_all(candles: List[Candle], swing_period: int = 3, symbol: str = "") -> Dict:
    """Main entry point - detects all market structures"""
    structure = MarketStructureAnalyzer.analyze(candles, swing_period=swing_period, symbol=symbol)
    return structure.to_dict()
