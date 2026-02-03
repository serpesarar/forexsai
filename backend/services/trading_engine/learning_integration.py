"""
EKSİK #7: Learning Proaktif Entegrasyonu
Prediction ÖNCESİ benzer setup'ların başarı oranını kontrol et
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LearningCheckResult:
    """Learning kontrolü sonucu"""
    allow: bool
    reason: Optional[str]
    recommendation: str  # 'PROCEED', 'CAUTION', 'AVOID'
    success_rate: Optional[float]
    sample_count: int
    confidence_adjustment: float  # 0.0 - 1.0


class LearningIntegration:
    """
    Learning Proaktif Entegrasyon Sistemi
    
    Kurallar:
    - Benzer setup'ların başarı oranı < 30% ise BLOCK
    - Başarı oranı 30-50% ise CAUTION + confidence düşür
    - Başarı oranı > 50% ise PROCEED
    """
    
    MIN_SUCCESS_RATE = 0.30  # Altında trade yapma
    CAUTION_SUCCESS_RATE = 0.50  # Altında dikkatli ol
    MIN_SAMPLES = 5  # Minimum sample sayısı
    
    def __init__(self):
        pass
    
    async def pre_prediction_check(
        self,
        symbol: str,
        direction: str,
        setup_type: Optional[str] = None,
        regime: Optional[str] = None,
        timeframe: str = '1H'
    ) -> LearningCheckResult:
        """
        Prediction ÖNCESİ kontrol: Bu setup geçmişte başarısız mı?
        """
        try:
            similar_setups = await self._get_similar_setups(
                symbol=symbol,
                direction=direction,
                setup_type=setup_type,
                regime=regime,
                timeframe=timeframe
            )
            
            if not similar_setups or similar_setups['count'] < self.MIN_SAMPLES:
                # Yeterli veri yok - izin ver
                return LearningCheckResult(
                    allow=True,
                    reason=f"Yeterli öğrenme verisi yok ({similar_setups.get('count', 0)} < {self.MIN_SAMPLES})",
                    recommendation='PROCEED',
                    success_rate=None,
                    sample_count=similar_setups.get('count', 0),
                    confidence_adjustment=1.0
                )
            
            success_rate = similar_setups['success_rate']
            sample_count = similar_setups['count']
            
            if success_rate < self.MIN_SUCCESS_RATE:
                # Çok düşük başarı - BLOCK
                logger.warning(
                    f"Learning BLOCK: {symbol} {direction} similar setups have "
                    f"{success_rate:.0%} success rate (n={sample_count})"
                )
                return LearningCheckResult(
                    allow=False,
                    reason=f"Benzer setup'lar başarısız ({success_rate:.0%} < {self.MIN_SUCCESS_RATE:.0%})",
                    recommendation='AVOID',
                    success_rate=success_rate,
                    sample_count=sample_count,
                    confidence_adjustment=0.0
                )
            
            if success_rate < self.CAUTION_SUCCESS_RATE:
                # Orta başarı - CAUTION
                adjustment = 0.7 + (success_rate - self.MIN_SUCCESS_RATE) * 1.5
                return LearningCheckResult(
                    allow=True,
                    reason=f"Benzer setup'lar orta başarılı ({success_rate:.0%})",
                    recommendation='CAUTION',
                    success_rate=success_rate,
                    sample_count=sample_count,
                    confidence_adjustment=adjustment
                )
            
            # Yüksek başarı - PROCEED
            adjustment = min(1.1, 0.9 + success_rate * 0.2)
            return LearningCheckResult(
                allow=True,
                reason=f"Benzer setup'lar başarılı ({success_rate:.0%})",
                recommendation='PROCEED',
                success_rate=success_rate,
                sample_count=sample_count,
                confidence_adjustment=adjustment
            )
            
        except Exception as e:
            logger.debug(f"Learning check failed: {e}")
            # Hata durumunda izin ver
            return LearningCheckResult(
                allow=True,
                reason=f"Learning kontrol hatası: {str(e)[:50]}",
                recommendation='PROCEED',
                success_rate=None,
                sample_count=0,
                confidence_adjustment=1.0
            )
    
    async def _get_similar_setups(
        self,
        symbol: str,
        direction: str,
        setup_type: Optional[str],
        regime: Optional[str],
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Learning DB'den benzer setup'ları çek.
        """
        try:
            from services.error_analysis_service import get_similar_trades
            
            result = await get_similar_trades(
                symbol=symbol,
                direction=direction,
                setup_type=setup_type,
                regime=regime,
                timeframe=timeframe,
                days=30
            )
            
            return result
            
        except ImportError:
            # error_analysis_service yoksa
            return {'count': 0, 'success_rate': 0.5}
        except Exception as e:
            logger.debug(f"Could not get similar setups: {e}")
            return {'count': 0, 'success_rate': 0.5}
    
    def sync_check(
        self,
        symbol: str,
        direction: str,
        cached_performance: Optional[Dict[str, Any]] = None
    ) -> LearningCheckResult:
        """
        Senkron versiyon - cache'den kontrol et.
        """
        if not cached_performance:
            return LearningCheckResult(
                allow=True,
                reason="Öğrenme verisi yok",
                recommendation='PROCEED',
                success_rate=None,
                sample_count=0,
                confidence_adjustment=1.0
            )
        
        success_rate = cached_performance.get('win_rate', 0.5)
        sample_count = cached_performance.get('total_trades', 0)
        
        if sample_count < self.MIN_SAMPLES:
            return LearningCheckResult(
                allow=True,
                reason=f"Yeterli veri yok ({sample_count})",
                recommendation='PROCEED',
                success_rate=success_rate,
                sample_count=sample_count,
                confidence_adjustment=1.0
            )
        
        if success_rate < self.MIN_SUCCESS_RATE:
            return LearningCheckResult(
                allow=False,
                reason=f"Düşük başarı oranı ({success_rate:.0%})",
                recommendation='AVOID',
                success_rate=success_rate,
                sample_count=sample_count,
                confidence_adjustment=0.0
            )
        
        if success_rate < self.CAUTION_SUCCESS_RATE:
            return LearningCheckResult(
                allow=True,
                reason=f"Orta başarı ({success_rate:.0%})",
                recommendation='CAUTION',
                success_rate=success_rate,
                sample_count=sample_count,
                confidence_adjustment=0.8
            )
        
        return LearningCheckResult(
            allow=True,
            reason=f"İyi başarı ({success_rate:.0%})",
            recommendation='PROCEED',
            success_rate=success_rate,
            sample_count=sample_count,
            confidence_adjustment=1.0
        )


# Global instance
learning_integration = LearningIntegration()


async def pre_prediction_learning_check(
    symbol: str,
    direction: str,
    setup_type: Optional[str] = None,
    regime: Optional[str] = None
) -> Dict[str, Any]:
    """
    Kolay kullanım için async wrapper.
    """
    result = await learning_integration.pre_prediction_check(
        symbol, direction, setup_type, regime
    )
    return {
        'allow': result.allow,
        'reason': result.reason,
        'recommendation': result.recommendation,
        'success_rate': result.success_rate,
        'sample_count': result.sample_count,
        'confidence_adjustment': result.confidence_adjustment
    }


def sync_learning_check(
    symbol: str,
    direction: str,
    cached_performance: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Kolay kullanım için sync wrapper.
    """
    result = learning_integration.sync_check(symbol, direction, cached_performance)
    return {
        'allow': result.allow,
        'reason': result.reason,
        'recommendation': result.recommendation,
        'success_rate': result.success_rate,
        'sample_count': result.sample_count,
        'confidence_adjustment': result.confidence_adjustment
    }
