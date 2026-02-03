"""
Multi-Timeframe Analyzer
Hiyerarşik TF analizi: Weekly -> Daily -> 4H -> 1H -> 15m
"""
import asyncio
import logging
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from threading import Lock

from .constants import TIMEFRAME_WEIGHTS, PriceStructure, TF_APPROVAL_MATRIX
from .helpers import adx, rsi, ema, find_swing_points, analyze_price_structure, extract_ohlcv

logger = logging.getLogger(__name__)


@dataclass
class TimeframeAnalysis:
    """Tek bir timeframe için analiz sonucu"""
    timeframe: str
    trend: str  # UP, DOWN, NEUTRAL
    trend_strength: float
    adx: float
    plus_di: float
    minus_di: float
    ema_alignment: bool
    rsi: float
    structure: PriceStructure
    key_levels: Dict[str, float]
    confidence: float


class MultiTimeframeAnalyzer:
    """
    Multi-Timeframe Hiyerarşik Analiz
    
    Kural: En az 2 üst TF aynı yönde olmadan STRONG sinyal yok
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()
        self._cache_ttl = 60
    
    async def analyze_all_timeframes(
        self, 
        symbol: str,
        data_fetcher_func
    ) -> Dict[str, TimeframeAnalysis]:
        """Tüm timeframe'leri analiz et"""
        results = {}
        
        # Her TF için analiz (sıralı - data dependency)
        for tf in ["1D", "4H", "1H"]:
            try:
                analysis = await self._analyze_single_tf(symbol, tf, data_fetcher_func)
                results[tf] = analysis
            except Exception as e:
                logger.warning(f"TF analysis failed for {tf}: {e}")
                results[tf] = self._default_analysis(tf)
        
        return results
    
    async def _analyze_single_tf(
        self, 
        symbol: str, 
        timeframe: str,
        data_fetcher_func
    ) -> TimeframeAnalysis:
        """Tek TF analizi"""
        
        # Data fetch
        candles = await data_fetcher_func(symbol, timeframe, 200)
        
        if not candles or len(candles) < 50:
            return self._default_analysis(timeframe)
        
        opens, highs, lows, closes, volumes = extract_ohlcv(candles)
        
        # Indicators
        adx_val, plus_di, minus_di = adx(highs, lows, closes, 14)
        rsi_val = rsi(closes, 14)
        
        ema20 = ema(closes, 20)
        ema50 = ema(closes, 50)
        ema200 = ema(closes, min(200, len(closes)))
        
        current_price = float(closes[-1])
        
        # Trend
        di_spread = plus_di - minus_di
        if adx_val > 25 and abs(di_spread) > 10:
            trend = "UP" if di_spread > 0 else "DOWN"
            trend_strength = min(100, adx_val + abs(di_spread))
        elif adx_val < 20:
            trend = "NEUTRAL"
            trend_strength = adx_val
        else:
            trend = "UP" if di_spread > 5 else ("DOWN" if di_spread < -5 else "NEUTRAL")
            trend_strength = adx_val
        
        # EMA alignment
        ema_bullish = ema20 > ema50 > ema200
        ema_bearish = ema20 < ema50 < ema200
        ema_alignment = ema_bullish if trend == "UP" else (ema_bearish if trend == "DOWN" else False)
        
        # Structure
        swing_highs, swing_lows = find_swing_points(highs, lows, 3)
        structure = analyze_price_structure(swing_highs, swing_lows)
        
        # Key levels
        key_levels = {
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "ema200": round(ema200, 2),
            "last_swing_high": swing_highs[-1]["price"] if swing_highs else current_price,
            "last_swing_low": swing_lows[-1]["price"] if swing_lows else current_price
        }
        
        # Confidence
        confidence = self._calc_confidence(adx_val, di_spread, ema_alignment, structure)
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            trend_strength=round(trend_strength, 1),
            adx=round(adx_val, 1),
            plus_di=round(plus_di, 1),
            minus_di=round(minus_di, 1),
            ema_alignment=ema_alignment,
            rsi=round(rsi_val, 1),
            structure=structure,
            key_levels=key_levels,
            confidence=round(confidence, 1)
        )
    
    def _calc_confidence(self, adx_val: float, di_spread: float, ema_align: bool, structure: PriceStructure) -> float:
        """TF güven skoru hesapla"""
        score = 50.0
        
        if adx_val > 40: score += 20
        elif adx_val > 30: score += 15
        elif adx_val > 25: score += 10
        elif adx_val < 20: score -= 10
        
        if abs(di_spread) > 20: score += 15
        elif abs(di_spread) > 10: score += 10
        
        if ema_align: score += 10
        
        if structure in [PriceStructure.HIGHER_HIGHS, PriceStructure.LOWER_LOWS]:
            score += 10
        elif structure == PriceStructure.CHAOTIC:
            score -= 15
        
        return min(100, max(0, score))
    
    def _default_analysis(self, tf: str) -> TimeframeAnalysis:
        """Varsayılan analiz"""
        return TimeframeAnalysis(
            timeframe=tf,
            trend="NEUTRAL",
            trend_strength=0,
            adx=25,
            plus_di=50,
            minus_di=50,
            ema_alignment=False,
            rsi=50,
            structure=PriceStructure.CHAOTIC,
            key_levels={},
            confidence=0
        )
    
    def get_consensus(self, analyses: Dict[str, TimeframeAnalysis]) -> Dict[str, Any]:
        """MTF konsensüs hesapla"""
        if not analyses:
            return {"consensus": "NEUTRAL", "strength": 0, "aligned": False, "action": "NO_TRADE"}
        
        weighted_score = 0
        total_weight = 0
        
        for tf, analysis in analyses.items():
            weight = TIMEFRAME_WEIGHTS.get(tf, 0.1)
            dir_score = 1 if analysis.trend == "UP" else (-1 if analysis.trend == "DOWN" else 0)
            weighted_score += dir_score * weight * (analysis.confidence / 100)
            total_weight += weight
        
        normalized = weighted_score / total_weight if total_weight > 0 else 0
        
        # Alignment check
        trends = [a.trend for a in analyses.values()]
        non_neutral = [t for t in trends if t != "NEUTRAL"]
        aligned = len(set(non_neutral)) <= 1 if non_neutral else False
        
        if normalized > 0.3:
            consensus = "UP"
        elif normalized < -0.3:
            consensus = "DOWN"
        else:
            consensus = "NEUTRAL"
        
        # TF approval matrix check
        tf_tuple = tuple(analyses.get(tf, self._default_analysis(tf)).trend for tf in ["1D", "4H", "1H"])
        action_info = TF_APPROVAL_MATRIX.get(tf_tuple[:3], ("WAIT", 0.5, "low"))
        
        return {
            "consensus": consensus,
            "strength": round(abs(normalized) * 100, 1),
            "aligned": aligned,
            "score": round(normalized, 3),
            "action": action_info[0],
            "position_mult": action_info[1],
            "risk_profile": action_info[2]
        }
