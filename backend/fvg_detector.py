"""
Fair Value Gap (FVG) Detector
Detects imbalances in price action where large candle movements create gaps
that price tends to fill later.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from typing import List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class FVGType(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class FVGConfig:
    min_gap_percent: float = 0.05  # Minimum gap size as % of price
    min_body_percent: float = 0.3  # Minimum body size as % of candle range
    lookback_candles: int = 100  # How many candles to analyze
    atr_multiplier: float = 0.5  # Minimum gap size in ATR units


@dataclass
class FairValueGap:
    index: int  # Candle index where FVG formed (middle candle)
    type: str  # bullish or bearish
    gap_high: float  # Upper boundary of the gap
    gap_low: float  # Lower boundary of the gap
    gap_size: float  # Size of gap in price units
    gap_percent: float  # Size of gap as percentage
    impulse_size: float  # Size of the impulse candle
    timestamp: int  # Timestamp of formation
    is_filled: bool  # Whether gap has been filled
    fill_percent: float  # How much of gap has been filled (0-100)
    fill_index: Optional[int]  # Index where gap was filled
    is_valid: bool  # Still a valid trading zone
    score: float  # Quality score (0-100)
    
    def to_dict(self):
        return asdict(self)


class FVGDetector:
    """
    Detects Fair Value Gaps in price action.
    
    A Fair Value Gap occurs when:
    - Bullish: Candle 1's high < Candle 3's low (gap up)
    - Bearish: Candle 1's low > Candle 3's high (gap down)
    
    These gaps represent areas of imbalance where price moved too quickly,
    often leading to price returning to fill these gaps.
    """
    
    def __init__(self, config: Optional[FVGConfig] = None):
        self.config = config or FVGConfig()
    
    def detect(self, candles: List[Candle]) -> List[FairValueGap]:
        """Detect all FVGs in the given candles."""
        if len(candles) < 3:
            return []
        
        fvgs: List[FairValueGap] = []
        atr = self._calculate_atr(candles, 14)
        
        for i in range(2, min(len(candles), self.config.lookback_candles)):
            fvg = self._check_fvg(candles, i, atr)
            if fvg:
                # Check if filled by subsequent candles
                self._check_fill_status(fvg, candles, i)
                fvgs.append(fvg)
        
        # Sort by timestamp descending (most recent first)
        fvgs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return fvgs
    
    def _check_fvg(self, candles: List[Candle], index: int, atr: float) -> Optional[FairValueGap]:
        """Check if there's an FVG at the given index (middle candle)."""
        c1 = candles[index - 2]  # First candle
        c2 = candles[index - 1]  # Middle candle (impulse)
        c3 = candles[index]      # Third candle
        
        # Check for bullish FVG: c1.high < c3.low
        if c1.high < c3.low:
            gap_low = c1.high
            gap_high = c3.low
            gap_size = gap_high - gap_low
            gap_percent = (gap_size / c2.close) * 100
            
            # Validate gap size
            if gap_percent < self.config.min_gap_percent:
                return None
            if atr > 0 and gap_size < atr * self.config.atr_multiplier:
                return None
            
            impulse_size = c2.close - c2.open
            body_ratio = abs(impulse_size) / (c2.high - c2.low) if (c2.high - c2.low) > 0 else 0
            
            if body_ratio < self.config.min_body_percent:
                return None
            
            score = self._calculate_score(gap_percent, body_ratio, True, atr, gap_size)
            
            return FairValueGap(
                index=index - 1,
                type=FVGType.BULLISH.value,
                gap_high=round(gap_high, 4),
                gap_low=round(gap_low, 4),
                gap_size=round(gap_size, 4),
                gap_percent=round(gap_percent, 4),
                impulse_size=round(abs(impulse_size), 4),
                timestamp=c2.timestamp,
                is_filled=False,
                fill_percent=0.0,
                fill_index=None,
                is_valid=True,
                score=round(score, 2),
            )
        
        # Check for bearish FVG: c1.low > c3.high
        if c1.low > c3.high:
            gap_low = c3.high
            gap_high = c1.low
            gap_size = gap_high - gap_low
            gap_percent = (gap_size / c2.close) * 100
            
            # Validate gap size
            if gap_percent < self.config.min_gap_percent:
                return None
            if atr > 0 and gap_size < atr * self.config.atr_multiplier:
                return None
            
            impulse_size = c2.open - c2.close
            body_ratio = abs(impulse_size) / (c2.high - c2.low) if (c2.high - c2.low) > 0 else 0
            
            if body_ratio < self.config.min_body_percent:
                return None
            
            score = self._calculate_score(gap_percent, body_ratio, False, atr, gap_size)
            
            return FairValueGap(
                index=index - 1,
                type=FVGType.BEARISH.value,
                gap_high=round(gap_high, 4),
                gap_low=round(gap_low, 4),
                gap_size=round(gap_size, 4),
                gap_percent=round(gap_percent, 4),
                impulse_size=round(abs(impulse_size), 4),
                timestamp=c2.timestamp,
                is_filled=False,
                fill_percent=0.0,
                fill_index=None,
                is_valid=True,
                score=round(score, 2),
            )
        
        return None
    
    def _check_fill_status(self, fvg: FairValueGap, candles: List[Candle], formation_index: int) -> None:
        """Check if and how much the FVG has been filled."""
        gap_size = fvg.gap_high - fvg.gap_low
        max_fill = 0.0
        fill_index = None
        
        for i in range(formation_index + 1, len(candles)):
            candle = candles[i]
            
            if fvg.type == FVGType.BULLISH.value:
                # Bullish FVG is filled when price drops into the gap
                if candle.low <= fvg.gap_high:
                    fill_amount = fvg.gap_high - max(candle.low, fvg.gap_low)
                    fill_pct = (fill_amount / gap_size) * 100 if gap_size > 0 else 0
                    if fill_pct > max_fill:
                        max_fill = min(100.0, fill_pct)
                        fill_index = i
            else:
                # Bearish FVG is filled when price rises into the gap
                if candle.high >= fvg.gap_low:
                    fill_amount = min(candle.high, fvg.gap_high) - fvg.gap_low
                    fill_pct = (fill_amount / gap_size) * 100 if gap_size > 0 else 0
                    if fill_pct > max_fill:
                        max_fill = min(100.0, fill_pct)
                        fill_index = i
        
        fvg.fill_percent = round(max_fill, 2)
        fvg.is_filled = max_fill >= 100.0
        fvg.fill_index = fill_index
        fvg.is_valid = not fvg.is_filled and max_fill < 50.0
    
    def _calculate_score(
        self,
        gap_percent: float,
        body_ratio: float,
        is_bullish: bool,
        atr: float,
        gap_size: float,
    ) -> float:
        """Calculate quality score for the FVG."""
        score = 40.0  # Base score
        
        # Gap size score (larger gaps = higher score, up to 25 points)
        gap_score = min(25.0, gap_percent * 10)
        score += gap_score
        
        # Body ratio score (stronger impulse = higher score, up to 20 points)
        score += body_ratio * 20
        
        # ATR-relative size (up to 15 points)
        if atr > 0:
            atr_ratio = gap_size / atr
            score += min(15.0, atr_ratio * 7.5)
        
        return float(min(100.0, max(0.0, score)))
    
    def _calculate_atr(self, candles: List[Candle], period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(candles) < period + 1:
            return 0.0
        
        tr_values = []
        for i in range(1, min(len(candles), period + 1)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i - 1].close
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
            tr_values.append(tr)
        
        return sum(tr_values) / len(tr_values) if tr_values else 0.0
    
    def get_unfilled_fvgs(self, candles: List[Candle]) -> List[FairValueGap]:
        """Get only unfilled and valid FVGs."""
        all_fvgs = self.detect(candles)
        return [fvg for fvg in all_fvgs if fvg.is_valid and not fvg.is_filled]
    
    def get_nearest_fvg(
        self,
        candles: List[Candle],
        current_price: float,
        fvg_type: Optional[str] = None,
    ) -> Optional[FairValueGap]:
        """Get the nearest unfilled FVG to current price."""
        unfilled = self.get_unfilled_fvgs(candles)
        
        if fvg_type:
            unfilled = [f for f in unfilled if f.type == fvg_type]
        
        if not unfilled:
            return None
        
        # Sort by distance to current price
        def distance(fvg: FairValueGap) -> float:
            mid = (fvg.gap_high + fvg.gap_low) / 2
            return abs(current_price - mid)
        
        return min(unfilled, key=distance)
