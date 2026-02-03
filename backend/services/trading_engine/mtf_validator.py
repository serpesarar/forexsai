"""
EKSİK #2: MTF Hard Veto
Üst timeframe'lerde trend tersyönde ise HARD VETO
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MTFValidationResult:
    """MTF Validation sonucu"""
    allowed: bool
    reason: Optional[str]
    override_signal: Optional[str]  # HOLD veya None
    upper_tf_direction: Optional[str]
    upper_tf_confidence: float
    veto_level: str  # 'none', 'soft', 'hard'


class MTFValidator:
    """
    Multi-Timeframe Hard Veto Sistemi
    
    Kurallar:
    - 4H ve 1D trend tersyönde + confidence > 70% ise HARD VETO
    - 4H trend tersyönde + confidence > 60% ise SOFT VETO (confidence düşür)
    - Aksi halde izin ver
    """
    
    HARD_VETO_CONFIDENCE = 0.70  # Üst TF bu confidence üzerindeyse hard block
    SOFT_VETO_CONFIDENCE = 0.60  # Bu aralıkta confidence düşür
    
    def __init__(self):
        pass
    
    def validate(
        self, 
        symbol: str,
        proposed_direction: str,  # "BUY" veya "SELL"
        mtf_data: Dict[str, Any],
        current_confidence: float
    ) -> MTFValidationResult:
        """
        Üst timeframe'lere göre sinyal validasyonu.
        
        mtf_data format:
        {
            '4H': {'trend': 'UP'/'DOWN'/'NEUTRAL', 'confidence': 0.0-1.0, 'adx': float},
            '1D': {'trend': 'UP'/'DOWN'/'NEUTRAL', 'confidence': 0.0-1.0, 'adx': float},
            '1H': {...}
        }
        """
        # Proposed direction'ı normalize et
        proposed_normalized = "UP" if proposed_direction in ["BUY", "LONG", "UP"] else (
            "DOWN" if proposed_direction in ["SELL", "SHORT", "DOWN"] else "NEUTRAL"
        )
        
        # Üst TF verilerini al
        tf_4h = mtf_data.get('4H', {})
        tf_1d = mtf_data.get('1D', {})
        
        upper_direction = None
        upper_confidence = 0.0
        
        # 1D öncelikli, yoksa 4H
        if tf_1d.get('trend') and tf_1d.get('trend') != 'NEUTRAL':
            upper_direction = tf_1d['trend']
            upper_confidence = tf_1d.get('confidence', 0.5)
        elif tf_4h.get('trend') and tf_4h.get('trend') != 'NEUTRAL':
            upper_direction = tf_4h['trend']
            upper_confidence = tf_4h.get('confidence', 0.5)
        
        # Üst TF verisi yoksa izin ver
        if not upper_direction:
            return MTFValidationResult(
                allowed=True,
                reason=None,
                override_signal=None,
                upper_tf_direction=None,
                upper_tf_confidence=0,
                veto_level='none'
            )
        
        # Yön kontrolü
        is_counter_trend = (
            (proposed_normalized == "UP" and upper_direction == "DOWN") or
            (proposed_normalized == "DOWN" and upper_direction == "UP")
        )
        
        if not is_counter_trend:
            # Aynı yön - izin ver
            return MTFValidationResult(
                allowed=True,
                reason=f"MTF uyumu: {proposed_direction} = {upper_direction}",
                override_signal=None,
                upper_tf_direction=upper_direction,
                upper_tf_confidence=upper_confidence,
                veto_level='none'
            )
        
        # Counter-trend - confidence seviyesine göre karar ver
        if upper_confidence >= self.HARD_VETO_CONFIDENCE:
            # HARD VETO - Sinyal engelle
            logger.warning(
                f"MTF HARD VETO: {symbol} {proposed_direction} blocked. "
                f"Upper TF: {upper_direction} (conf: {upper_confidence:.0%})"
            )
            return MTFValidationResult(
                allowed=False,
                reason=f"MTF Veto: Üst TF {upper_direction} ({upper_confidence:.0%})",
                override_signal='HOLD',
                upper_tf_direction=upper_direction,
                upper_tf_confidence=upper_confidence,
                veto_level='hard'
            )
        
        elif upper_confidence >= self.SOFT_VETO_CONFIDENCE:
            # SOFT VETO - İzin ver ama uyar
            logger.info(
                f"MTF SOFT VETO: {symbol} {proposed_direction}. "
                f"Upper TF: {upper_direction} (conf: {upper_confidence:.0%})"
            )
            return MTFValidationResult(
                allowed=True,
                reason=f"MTF Uyarı: Üst TF {upper_direction} ({upper_confidence:.0%}) - dikkat",
                override_signal=None,
                upper_tf_direction=upper_direction,
                upper_tf_confidence=upper_confidence,
                veto_level='soft'
            )
        
        # Düşük confidence - izin ver
        return MTFValidationResult(
            allowed=True,
            reason=f"MTF zayıf: {upper_direction} ({upper_confidence:.0%})",
            override_signal=None,
            upper_tf_direction=upper_direction,
            upper_tf_confidence=upper_confidence,
            veto_level='none'
        )
    
    def get_confidence_penalty(self, validation_result: MTFValidationResult) -> float:
        """Soft veto durumunda confidence penalty"""
        if validation_result.veto_level == 'soft':
            return 0.15  # %15 confidence düşür
        return 0.0


# Global instance
mtf_validator = MTFValidator()


def validate_mtf_consensus(
    symbol: str, 
    proposed_direction: str, 
    mtf_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Kolay kullanım için wrapper fonksiyon.
    
    Returns:
        {
            'allowed': bool,
            'reason': str or None,
            'override_signal': 'HOLD' or None,
            'confidence_penalty': float
        }
    """
    result = mtf_validator.validate(symbol, proposed_direction, mtf_data, 0)
    return {
        'allowed': result.allowed,
        'reason': result.reason,
        'override_signal': result.override_signal,
        'confidence_penalty': mtf_validator.get_confidence_penalty(result),
        'veto_level': result.veto_level
    }
