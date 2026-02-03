"""
EKSİK #5: Pattern Timeframe Önceliği
Çakışan pattern'lerde TF önceliğine göre karar verme
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from .constants import TF_PRIORITY

logger = logging.getLogger(__name__)


@dataclass
class PatternResolutionResult:
    """Pattern çözümleme sonucu"""
    resolved_patterns: List[Dict[str, Any]]
    dominant_pattern: Optional[Dict[str, Any]]
    dominant_direction: Optional[str]
    ignored_patterns: List[Dict[str, Any]]
    has_conflict: bool
    conflict_severity: str  # 'none', 'minor', 'major'
    confidence_adjustment: float  # 0.0 - 1.0


class PatternPrioritizer:
    """
    Pattern Timeframe Önceliği Sistemi
    
    Kurallar:
    - En yüksek TF'deki pattern dominant
    - Dominant pattern'ın tersi yöndeki pattern'ler ignore edilir
    - Aynı yöndeki pattern'ler güçlendirme sağlar
    - Conflict severity'e göre confidence ayarlanır
    """
    
    def __init__(self):
        pass
    
    def resolve_conflicts(
        self, 
        patterns: List[Dict[str, Any]]
    ) -> PatternResolutionResult:
        """
        Pattern çakışmalarını TF önceliğine göre çöz.
        
        Pattern format:
        {
            'name': str,
            'timeframe': '1H', '15m', '4H', etc.,
            'direction': 'BULLISH' / 'BEARISH' / 'NEUTRAL',
            'confidence': float (0-1),
            'status': 'CONFIRMED' / 'FORMING'
        }
        """
        if not patterns:
            return PatternResolutionResult(
                resolved_patterns=[],
                dominant_pattern=None,
                dominant_direction=None,
                ignored_patterns=[],
                has_conflict=False,
                conflict_severity='none',
                confidence_adjustment=1.0
            )
        
        # TF priority'ye göre sırala
        sorted_patterns = sorted(
            patterns,
            key=lambda p: TF_PRIORITY.get(p.get('timeframe', '5m'), 0),
            reverse=True
        )
        
        # Dominant pattern (en yüksek TF)
        dominant = sorted_patterns[0]
        dominant_direction = self._normalize_direction(dominant.get('direction', 'NEUTRAL'))
        
        # Pattern'leri filtrele
        resolved = [dominant]
        ignored = []
        
        bullish_count = 0
        bearish_count = 0
        
        for p in patterns:
            p_dir = self._normalize_direction(p.get('direction', 'NEUTRAL'))
            if p_dir == 'BULLISH':
                bullish_count += 1
            elif p_dir == 'BEARISH':
                bearish_count += 1
        
        for p in sorted_patterns[1:]:
            p_direction = self._normalize_direction(p.get('direction', 'NEUTRAL'))
            
            if p_direction == dominant_direction:
                # Aynı yön - kabul et
                resolved.append(p)
            elif p_direction == 'NEUTRAL':
                # Neutral - kabul et
                resolved.append(p)
            else:
                # Ters yön - ignore et
                ignored.append(p)
                logger.info(
                    f"Pattern ignored due to TF priority: {p.get('name')} ({p.get('timeframe')}) "
                    f"vs dominant {dominant.get('name')} ({dominant.get('timeframe')})"
                )
        
        # Conflict severity hesapla
        has_conflict = len(ignored) > 0
        
        if not has_conflict:
            conflict_severity = 'none'
            confidence_adjustment = 1.0
        elif bullish_count > 0 and bearish_count > 0:
            # Her iki yönde de pattern var
            total = bullish_count + bearish_count
            ratio = min(bullish_count, bearish_count) / total
            
            if ratio > 0.4:  # Yaklaşık eşit
                conflict_severity = 'major'
                confidence_adjustment = 0.6
            else:
                conflict_severity = 'minor'
                confidence_adjustment = 0.85
        else:
            conflict_severity = 'minor'
            confidence_adjustment = 0.9
        
        # Dominant direction'ı BUY/SELL formatına çevir
        final_direction = None
        if dominant_direction == 'BULLISH':
            final_direction = 'BUY'
        elif dominant_direction == 'BEARISH':
            final_direction = 'SELL'
        
        return PatternResolutionResult(
            resolved_patterns=resolved,
            dominant_pattern=dominant,
            dominant_direction=final_direction,
            ignored_patterns=ignored,
            has_conflict=has_conflict,
            conflict_severity=conflict_severity,
            confidence_adjustment=confidence_adjustment
        )
    
    def _normalize_direction(self, direction: str) -> str:
        """Direction'ı normalize et"""
        d = direction.upper() if direction else 'NEUTRAL'
        if d in ['BULLISH', 'BUY', 'LONG', 'UP']:
            return 'BULLISH'
        elif d in ['BEARISH', 'SELL', 'SHORT', 'DOWN']:
            return 'BEARISH'
        return 'NEUTRAL'
    
    def get_pattern_consensus(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Pattern'lerden konsensüs çıkar.
        
        Returns:
            {
                'direction': 'BUY' / 'SELL' / 'NEUTRAL',
                'strength': float (0-1),
                'pattern_count': int,
                'confirmed_count': int
            }
        """
        if not patterns:
            return {
                'direction': 'NEUTRAL',
                'strength': 0,
                'pattern_count': 0,
                'confirmed_count': 0
            }
        
        resolution = self.resolve_conflicts(patterns)
        
        confirmed = [p for p in resolution.resolved_patterns 
                    if p.get('status', '').upper() == 'CONFIRMED']
        
        strength = 0.0
        if resolution.resolved_patterns:
            # Ortalama confidence
            avg_conf = sum(p.get('confidence', 0.5) for p in resolution.resolved_patterns) / len(resolution.resolved_patterns)
            # Confirmed bonus
            confirmed_ratio = len(confirmed) / len(resolution.resolved_patterns) if resolution.resolved_patterns else 0
            # Conflict penalty
            strength = avg_conf * (0.7 + 0.3 * confirmed_ratio) * resolution.confidence_adjustment
        
        return {
            'direction': resolution.dominant_direction or 'NEUTRAL',
            'strength': round(strength, 3),
            'pattern_count': len(resolution.resolved_patterns),
            'confirmed_count': len(confirmed),
            'ignored_count': len(resolution.ignored_patterns),
            'conflict_severity': resolution.conflict_severity
        }


# Global instance
pattern_prioritizer = PatternPrioritizer()


def resolve_pattern_conflicts(patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Kolay kullanım için wrapper fonksiyon.
    """
    result = pattern_prioritizer.resolve_conflicts(patterns)
    return {
        'resolved_patterns': result.resolved_patterns,
        'dominant_direction': result.dominant_direction,
        'ignored_patterns': result.ignored_patterns,
        'has_conflict': result.has_conflict,
        'conflict_severity': result.conflict_severity,
        'confidence_adjustment': result.confidence_adjustment
    }
