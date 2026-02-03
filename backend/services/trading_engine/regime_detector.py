"""
Market Regime Detector
5 farklı piyasa rejimi tespiti
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from .constants import MarketRegime, PriceStructure, ADX_STRONG, ADX_WEAK
from .helpers import adx, atr, find_swing_points, analyze_price_structure


@dataclass
class RegimeAnalysis:
    """Piyasa Rejimi Analizi"""
    regime: MarketRegime
    adx: float
    adx_trend: str
    price_structure: PriceStructure
    volatility_percentile: float
    trend_direction: Optional[str]
    confidence: float
    strategy_recommendation: str
    counter_trend_allowed: bool
    position_size_multiplier: float
    reasoning: List[str] = field(default_factory=list)


class MarketRegimeDetector:
    """
    Piyasa Rejimi Tespiti - ADX + Price Structure
    
    Rejimler:
    1. STRONG_TREND_UP/DOWN - ADX>30, güçlü yapı
    2. WEAK_TREND - ADX 20-30
    3. RANGE_BOUND - ADX<20, yatay
    4. LOW_VOL_COMPRESSION - Düşük vol, patlama yakın
    5. HIGH_VOL_CHOPPY - Kaotik, trade yapma
    6. TREND_EXHAUSTING - Trend bitiyor
    """
    
    def detect(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> RegimeAnalysis:
        """Piyasa rejimini tespit et"""
        
        # ADX hesapla
        adx_val, plus_di, minus_di = adx(highs, lows, closes, 14)
        
        # Kısa dönem ADX
        adx_short, _, _ = adx(highs[-30:], lows[-30:], closes[-30:], 7) if len(closes) > 30 else (adx_val, 0, 0)
        adx_trend = "rising" if adx_short > adx_val else ("falling" if adx_short < adx_val * 0.9 else "flat")
        
        # Volatilite percentile
        atr_val = atr(highs, lows, closes, 14)
        atr_history = []
        for i in range(30, len(closes), 10):
            atr_history.append(atr(highs[max(0,i-14):i], lows[max(0,i-14):i], closes[max(0,i-14):i], 14))
        vol_percentile = (sum(1 for a in atr_history if a < atr_val) / len(atr_history) * 100) if atr_history else 50
        
        # Price structure
        swing_highs, swing_lows = find_swing_points(highs, lows, 5)
        price_structure = analyze_price_structure(swing_highs, swing_lows)
        
        # Rejim belirleme
        reasoning = []
        
        if adx_val > ADX_STRONG:
            if adx_trend == "rising":
                if price_structure == PriceStructure.HIGHER_HIGHS:
                    regime = MarketRegime.STRONG_TREND_UP
                    trend_dir = "UP"
                    reasoning.append(f"ADX={adx_val:.1f} güçlü, yükseliyor, HH+HL yapısı")
                elif price_structure == PriceStructure.LOWER_LOWS:
                    regime = MarketRegime.STRONG_TREND_DOWN
                    trend_dir = "DOWN"
                    reasoning.append(f"ADX={adx_val:.1f} güçlü, yükseliyor, LH+LL yapısı")
                else:
                    regime = MarketRegime.WEAK_TREND
                    trend_dir = "UP" if plus_di > minus_di else "DOWN"
                    reasoning.append(f"ADX güçlü ama yapı belirsiz")
            else:
                regime = MarketRegime.TREND_EXHAUSTING
                trend_dir = "UP" if plus_di > minus_di else "DOWN"
                reasoning.append(f"ADX={adx_val:.1f} düşüyor, trend yoruluyor")
        
        elif adx_val < ADX_WEAK:
            if vol_percentile < 30:
                regime = MarketRegime.LOW_VOL_COMPRESSION
                trend_dir = None
                reasoning.append(f"ADX={adx_val:.1f} düşük, volatilite %{vol_percentile:.0f} - sıkışma")
            else:
                regime = MarketRegime.RANGE_BOUND
                trend_dir = None
                reasoning.append(f"ADX={adx_val:.1f} düşük, yatay piyasa")
        
        else:
            if vol_percentile > 70:
                regime = MarketRegime.HIGH_VOL_CHOPPY
                trend_dir = None
                reasoning.append(f"Orta ADX={adx_val:.1f} ama yüksek vol - choppy")
            else:
                regime = MarketRegime.WEAK_TREND
                trend_dir = "UP" if plus_di > minus_di else "DOWN"
                reasoning.append(f"ADX={adx_val:.1f} orta, zayıf trend")
        
        # Strateji önerisi
        strategy_map = {
            MarketRegime.STRONG_TREND_UP: ("Trend takibi LONG, pullback entry", False, 1.0),
            MarketRegime.STRONG_TREND_DOWN: ("Trend takibi SHORT, pullback entry", False, 1.0),
            MarketRegime.WEAK_TREND: ("Temkinli, küçük pozisyon", True, 0.5),
            MarketRegime.TREND_EXHAUSTING: ("Dikkatli ol, diverjans ara", True, 0.3),
            MarketRegime.RANGE_BOUND: ("Mean reversion, range extreme", True, 0.5),
            MarketRegime.LOW_VOL_COMPRESSION: ("Breakout bekle", False, 0.7),
            MarketRegime.HIGH_VOL_CHOPPY: ("TİCARET YAPMA", False, 0.0),
        }
        
        strategy, counter_allowed, size_mult = strategy_map.get(regime, ("Belirsiz", False, 0.3))
        
        # Confidence
        di_spread = abs(plus_di - minus_di)
        confidence = min(100, adx_val * 0.5 + di_spread * 2)
        
        return RegimeAnalysis(
            regime=regime,
            adx=round(adx_val, 1),
            adx_trend=adx_trend,
            price_structure=price_structure,
            volatility_percentile=round(vol_percentile, 1),
            trend_direction=trend_dir,
            confidence=round(confidence, 1),
            strategy_recommendation=strategy,
            counter_trend_allowed=counter_allowed,
            position_size_multiplier=size_mult,
            reasoning=reasoning
        )
