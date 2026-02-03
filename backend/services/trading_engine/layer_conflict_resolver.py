"""
EKSİK #8: Layer Veto Mekanizması
Critical, Technical, Context katmanları arasındaki çelişkileri çöz
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LayerResult:
    """Tek katman sonucu"""
    direction: str  # 'BUY', 'SELL', 'NEUTRAL'
    confidence: float  # 0-1
    factors: List[str]


@dataclass
class LayerConflictResult:
    """Katman çelişki çözümü sonucu"""
    resolved_direction: str
    resolved_confidence: float
    confidence_penalty: float
    has_conflict: bool
    conflict_type: str  # 'none', 'critical_vs_technical', 'majority_vote', 'full_conflict'
    reasoning: List[str]
    veto_applied: bool


class LayerConflictResolver:
    """
    Katman Çelişki Çözüm Sistemi
    
    Kurallar:
    1. Critical Layer VETO hakkına sahip (confidence > 70%)
    2. 2/3 çoğunluk kuralı
    3. Tam çelişkide (1-1-1) HOLD
    4. Critical + Technical çelişkisinde Critical kazanır
    """
    
    CRITICAL_VETO_THRESHOLD = 0.70
    MAJORITY_THRESHOLD = 2  # 3 katmandan en az 2'si
    
    def __init__(self):
        pass
    
    def resolve(
        self,
        critical: LayerResult,
        technical: LayerResult,
        context: LayerResult
    ) -> LayerConflictResult:
        """
        3 katman arasındaki çelişkileri çöz.
        """
        directions = [critical.direction, technical.direction, context.direction]
        confidences = [critical.confidence, technical.confidence, context.confidence]
        
        # Sayıları hesapla
        buy_count = sum(1 for d in directions if d in ['BUY', 'LONG'])
        sell_count = sum(1 for d in directions if d in ['SELL', 'SHORT'])
        neutral_count = sum(1 for d in directions if d in ['NEUTRAL', 'HOLD', None, ''])
        
        reasoning = []
        
        # Kural 1: Critical Layer veto hakkı
        if critical.confidence >= self.CRITICAL_VETO_THRESHOLD:
            critical_dir = critical.direction
            
            # Critical çok emin ama Technical farklı düşünüyor
            if technical.direction and technical.direction != critical_dir and technical.direction not in ['NEUTRAL', 'HOLD']:
                reasoning.append(f"Critical layer veto: {critical_dir} (conf: {critical.confidence:.0%})")
                reasoning.append(f"Technical layer disagreement ignored: {technical.direction}")
                
                return LayerConflictResult(
                    resolved_direction=critical_dir,
                    resolved_confidence=critical.confidence * 0.85,  # Küçük penalty
                    confidence_penalty=0.15,
                    has_conflict=True,
                    conflict_type='critical_vs_technical',
                    reasoning=reasoning,
                    veto_applied=True
                )
        
        # Kural 2: 2/3 çoğunluk
        if buy_count >= self.MAJORITY_THRESHOLD:
            reasoning.append(f"Çoğunluk kararı: BUY ({buy_count}/3 katman)")
            avg_conf = sum(c for d, c in zip(directions, confidences) if d in ['BUY', 'LONG']) / buy_count
            
            return LayerConflictResult(
                resolved_direction='BUY',
                resolved_confidence=avg_conf * (0.8 + 0.1 * buy_count),
                confidence_penalty=0 if buy_count == 3 else 0.1,
                has_conflict=buy_count < 3,
                conflict_type='majority_vote' if buy_count < 3 else 'none',
                reasoning=reasoning,
                veto_applied=False
            )
        
        if sell_count >= self.MAJORITY_THRESHOLD:
            reasoning.append(f"Çoğunluk kararı: SELL ({sell_count}/3 katman)")
            avg_conf = sum(c for d, c in zip(directions, confidences) if d in ['SELL', 'SHORT']) / sell_count
            
            return LayerConflictResult(
                resolved_direction='SELL',
                resolved_confidence=avg_conf * (0.8 + 0.1 * sell_count),
                confidence_penalty=0 if sell_count == 3 else 0.1,
                has_conflict=sell_count < 3,
                conflict_type='majority_vote' if sell_count < 3 else 'none',
                reasoning=reasoning,
                veto_applied=False
            )
        
        # Kural 3: Tam çelişki (1-1-1 veya belirsiz)
        if buy_count == 1 and sell_count == 1:
            reasoning.append(f"Katman çelişkisi: BUY={buy_count}, SELL={sell_count}, NEUTRAL={neutral_count}")
            reasoning.append("Konsensüs yok - HOLD önerisi")
            
            logger.warning(f"Layer conflict: BUY={buy_count}, SELL={sell_count} - resolving to HOLD")
            
            return LayerConflictResult(
                resolved_direction='HOLD',
                resolved_confidence=0.45,
                confidence_penalty=0.5,
                has_conflict=True,
                conflict_type='full_conflict',
                reasoning=reasoning,
                veto_applied=True
            )
        
        # Kural 4: Çoğunluk neutral ise
        if neutral_count >= 2:
            reasoning.append(f"Çoğunluk belirsiz: {neutral_count}/3 NEUTRAL")
            
            # En yüksek confidence olan yönü bul
            max_conf_idx = confidences.index(max(confidences))
            best_dir = directions[max_conf_idx]
            
            if best_dir in ['BUY', 'SELL', 'LONG', 'SHORT']:
                reasoning.append(f"En güçlü sinyal: {best_dir} ({confidences[max_conf_idx]:.0%})")
                return LayerConflictResult(
                    resolved_direction=best_dir if best_dir in ['BUY', 'SELL'] else ('BUY' if best_dir == 'LONG' else 'SELL'),
                    resolved_confidence=confidences[max_conf_idx] * 0.6,
                    confidence_penalty=0.4,
                    has_conflict=True,
                    conflict_type='majority_neutral',
                    reasoning=reasoning,
                    veto_applied=False
                )
            
            return LayerConflictResult(
                resolved_direction='HOLD',
                resolved_confidence=0.5,
                confidence_penalty=0.3,
                has_conflict=False,
                conflict_type='all_neutral',
                reasoning=reasoning,
                veto_applied=False
            )
        
        # Default: En yüksek ağırlıklı katmana göre (Critical > Technical > Context)
        if critical.direction not in ['NEUTRAL', 'HOLD', None, '']:
            return LayerConflictResult(
                resolved_direction=critical.direction,
                resolved_confidence=critical.confidence,
                confidence_penalty=0,
                has_conflict=False,
                conflict_type='none',
                reasoning=["Critical layer dominant"],
                veto_applied=False
            )
        
        if technical.direction not in ['NEUTRAL', 'HOLD', None, '']:
            return LayerConflictResult(
                resolved_direction=technical.direction,
                resolved_confidence=technical.confidence * 0.9,
                confidence_penalty=0.1,
                has_conflict=False,
                conflict_type='none',
                reasoning=["Technical layer fallback"],
                veto_applied=False
            )
        
        return LayerConflictResult(
            resolved_direction='HOLD',
            resolved_confidence=0.5,
            confidence_penalty=0,
            has_conflict=False,
            conflict_type='none',
            reasoning=["Tüm katmanlar belirsiz"],
            veto_applied=False
        )


# Global instance
layer_resolver = LayerConflictResolver()


def resolve_layer_conflict(
    critical_dir: str, critical_conf: float,
    technical_dir: str, technical_conf: float,
    context_dir: str, context_conf: float
) -> Dict[str, Any]:
    """
    Kolay kullanım için wrapper fonksiyon.
    """
    critical = LayerResult(direction=critical_dir, confidence=critical_conf, factors=[])
    technical = LayerResult(direction=technical_dir, confidence=technical_conf, factors=[])
    context = LayerResult(direction=context_dir, confidence=context_conf, factors=[])
    
    result = layer_resolver.resolve(critical, technical, context)
    
    return {
        'resolved_direction': result.resolved_direction,
        'resolved_confidence': result.resolved_confidence,
        'confidence_penalty': result.confidence_penalty,
        'has_conflict': result.has_conflict,
        'conflict_type': result.conflict_type,
        'reasoning': result.reasoning,
        'veto_applied': result.veto_applied
    }
