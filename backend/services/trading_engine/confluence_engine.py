"""
Confluence Engine - Çok Faktörlü Değerlendirme
Trend %30, Momentum %20, Yapı %25, Formasyon %15, Temporal %10
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from .constants import CONFLUENCE_WEIGHTS, PriceStructure
from .mtf_analyzer import TimeframeAnalysis
from .regime_detector import RegimeAnalysis


@dataclass
class ConfluenceResult:
    """Konfluans Analiz Sonucu"""
    total_score: float
    direction: str
    confidence: str  # VERY_HIGH, HIGH, MODERATE, LOW, INSUFFICIENT
    trend_score: float
    momentum_score: float
    structure_score: float
    pattern_score: float
    temporal_score: float
    supporting_factors: List[str] = field(default_factory=list)
    opposing_factors: List[str] = field(default_factory=list)
    neutral_factors: List[str] = field(default_factory=list)
    minimums_met: bool = True
    failed_minimums: List[str] = field(default_factory=list)


class ConfluenceEngine:
    """
    Konfluans Motoru - Entry Kalitesi Değerlendirmesi
    
    Minimum skor: 0.55 (TRADE)
    Önerilen: 0.65+ (QUALITY TRADE)
    Mükemmel: 0.80+ (A+ SETUP)
    """
    
    def calculate(
        self,
        direction: str,
        tf_analyses: Dict[str, TimeframeAnalysis],
        regime: RegimeAnalysis,
        current_price: float,
        patterns: Optional[List[Dict]] = None
    ) -> ConfluenceResult:
        """Konfluans skoru hesapla"""
        
        scores = {}
        supporting, opposing, neutral = [], [], []
        
        # 1. TREND (%30)
        scores["trend"] = self._eval_trend(direction, tf_analyses, regime)
        self._categorize("Trend", scores["trend"], supporting, opposing, neutral)
        
        # 2. MOMENTUM (%20)
        scores["momentum"] = self._eval_momentum(direction, tf_analyses)
        self._categorize("Momentum", scores["momentum"], supporting, opposing, neutral)
        
        # 3. STRUCTURE (%25)
        scores["structure"] = self._eval_structure(direction, tf_analyses, current_price)
        self._categorize("Yapı", scores["structure"], supporting, opposing, neutral)
        
        # 4. PATTERN (%15)
        scores["pattern"] = self._eval_patterns(direction, patterns)
        self._categorize("Formasyon", scores["pattern"], supporting, opposing, neutral)
        
        # 5. TEMPORAL (%10)
        scores["temporal"] = self._eval_temporal()
        self._categorize("Seans", scores["temporal"], supporting, opposing, neutral)
        
        # Total weighted score (-1 to 1 -> 0 to 1)
        raw_total = sum(scores[cat] * CONFLUENCE_WEIGHTS[cat] for cat in scores)
        total_score = (raw_total + 1) / 2
        
        # Confidence level
        if total_score >= 0.80:
            confidence = "VERY_HIGH"
        elif total_score >= 0.70:
            confidence = "HIGH"
        elif total_score >= 0.60:
            confidence = "MODERATE"
        elif total_score >= 0.50:
            confidence = "LOW"
        else:
            confidence = "INSUFFICIENT"
        
        # Minimum checks
        minimums_met = True
        failed = []
        
        if scores["trend"] < -0.2:
            minimums_met = False
            failed.append("Trend karşıt")
        if scores["structure"] < -0.3:
            minimums_met = False
            failed.append("Yapı desteklemiyor")
        if regime.position_size_multiplier == 0:
            minimums_met = False
            failed.append("Rejim trade'e uygun değil")
        
        return ConfluenceResult(
            total_score=round(total_score, 3),
            direction=direction,
            confidence=confidence,
            trend_score=round((scores["trend"] + 1) / 2, 3),
            momentum_score=round((scores["momentum"] + 1) / 2, 3),
            structure_score=round((scores["structure"] + 1) / 2, 3),
            pattern_score=round((scores["pattern"] + 1) / 2, 3),
            temporal_score=round((scores["temporal"] + 1) / 2, 3),
            supporting_factors=supporting,
            opposing_factors=opposing,
            neutral_factors=neutral,
            minimums_met=minimums_met,
            failed_minimums=failed
        )
    
    def _eval_trend(self, direction: str, tf_analyses: Dict[str, TimeframeAnalysis], regime: RegimeAnalysis) -> float:
        """Trend değerlendirmesi (-1 to 1)"""
        score = 0.0
        
        tf_weights = {"1D": 0.4, "4H": 0.35, "1H": 0.25}
        for tf, analysis in tf_analyses.items():
            weight = tf_weights.get(tf, 0.1)
            if analysis.trend == direction:
                score += weight * (analysis.confidence / 100)
            elif analysis.trend == "NEUTRAL":
                pass
            else:
                score -= weight * (analysis.confidence / 100)
        
        # Regime bonus
        if regime.trend_direction == direction:
            score += 0.2
        elif regime.trend_direction and regime.trend_direction != direction:
            score -= 0.3
        
        return max(-1, min(1, score))
    
    def _eval_momentum(self, direction: str, tf_analyses: Dict[str, TimeframeAnalysis]) -> float:
        """Momentum değerlendirmesi (-1 to 1)"""
        score = 0.0
        
        for tf, analysis in tf_analyses.items():
            r = analysis.rsi
            
            if direction == "LONG":
                if 40 < r < 60:
                    score += 0.1
                elif r < 30:
                    score += 0.3
                elif r > 70:
                    score -= 0.2
            else:
                if 40 < r < 60:
                    score += 0.1
                elif r > 70:
                    score += 0.3
                elif r < 30:
                    score -= 0.2
        
        return max(-1, min(1, score))
    
    def _eval_structure(self, direction: str, tf_analyses: Dict[str, TimeframeAnalysis], current_price: float) -> float:
        """Yapı değerlendirmesi (-1 to 1)"""
        score = 0.0
        count = 0
        
        for tf, analysis in tf_analyses.items():
            structure = analysis.structure
            
            if direction == "LONG":
                if structure == PriceStructure.HIGHER_HIGHS:
                    score += 0.4
                elif structure == PriceStructure.LOWER_LOWS:
                    score -= 0.4
                elif structure == PriceStructure.CONTRACTING_RANGE:
                    score += 0.1
            else:
                if structure == PriceStructure.LOWER_LOWS:
                    score += 0.4
                elif structure == PriceStructure.HIGHER_HIGHS:
                    score -= 0.4
                elif structure == PriceStructure.CONTRACTING_RANGE:
                    score += 0.1
            
            # EMA proximity
            if analysis.key_levels:
                ema20 = analysis.key_levels.get("ema20", current_price)
                dist_pct = abs(current_price - ema20) / current_price * 100
                
                if dist_pct < 0.5:
                    if direction == "LONG" and current_price > ema20:
                        score += 0.2
                    elif direction == "SHORT" and current_price < ema20:
                        score += 0.2
            
            count += 1
        
        return max(-1, min(1, score / count if count else 0))
    
    def _eval_patterns(self, direction: str, patterns: Optional[List[Dict]]) -> float:
        """Formasyon değerlendirmesi (-1 to 1)"""
        if not patterns:
            return 0.0
        
        score = 0.0
        for p in patterns:
            p_dir = p.get("direction", "NEUTRAL")
            quality = p.get("quality", 0.5)
            
            if p_dir == direction:
                score += quality * 0.5
            elif p_dir != "NEUTRAL":
                score -= quality * 0.3
        
        return max(-1, min(1, score))
    
    def _eval_temporal(self) -> float:
        """Seans değerlendirmesi (-1 to 1)"""
        hour = datetime.utcnow().hour
        
        if 7 <= hour <= 11:      # London
            return 0.2
        elif 13 <= hour <= 17:   # NY
            return 0.3
        elif 12 <= hour <= 16:   # Overlap
            return 0.4
        elif 0 <= hour <= 4:     # Asia
            return -0.1
        return 0.0
    
    def _categorize(self, name: str, score: float, supp: List, opp: List, neut: List):
        """Faktörü kategorize et"""
        if score > 0.2:
            supp.append(f"{name} (+{score:.0%})")
        elif score < -0.2:
            opp.append(f"{name} ({score:.0%})")
        else:
            neut.append(name)
