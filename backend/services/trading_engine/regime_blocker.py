"""
EKSİK #6: Regime Hard Block
Piyasa rejimine göre sinyal tamamen engelleme
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .constants import MarketRegime

logger = logging.getLogger(__name__)


@dataclass
class RegimeBlockResult:
    """Regime blocking sonucu"""
    blocked: bool
    new_direction: Optional[str]
    reason: Optional[str]
    regime: MarketRegime
    allowed_directions: list
    confidence_multiplier: float  # 0.0 - 1.0


class RegimeBlocker:
    """
    Regime-Based Hard Blocking Sistemi
    
    Kurallar:
    - STRONG_TREND_UP'da SELL yasak
    - STRONG_TREND_DOWN'da BUY yasak  
    - HIGH_VOL_CHOPPY'de her şey yasak
    - TREND_EXHAUSTING'de counter-trend izinli ama dikkatli
    """
    
    # Regime bazlı izin verilen yönler
    REGIME_ALLOWED_DIRECTIONS = {
        MarketRegime.STRONG_TREND_UP: ['BUY', 'LONG'],
        MarketRegime.STRONG_TREND_DOWN: ['SELL', 'SHORT'],
        MarketRegime.WEAK_TREND: ['BUY', 'SELL', 'LONG', 'SHORT'],  # Her iki yön ama dikkatli
        MarketRegime.RANGE_BOUND: ['BUY', 'SELL', 'LONG', 'SHORT'],  # Mean reversion
        MarketRegime.LOW_VOL_COMPRESSION: [],  # Bekle
        MarketRegime.HIGH_VOL_CHOPPY: [],  # Hiçbir şey
        MarketRegime.TREND_EXHAUSTING: ['BUY', 'SELL', 'LONG', 'SHORT'],  # Reversal mümkün
    }
    
    # Regime bazlı confidence çarpanları
    REGIME_CONFIDENCE_MULTIPLIER = {
        MarketRegime.STRONG_TREND_UP: 1.0,
        MarketRegime.STRONG_TREND_DOWN: 1.0,
        MarketRegime.WEAK_TREND: 0.7,
        MarketRegime.RANGE_BOUND: 0.8,
        MarketRegime.LOW_VOL_COMPRESSION: 0.5,
        MarketRegime.HIGH_VOL_CHOPPY: 0.0,
        MarketRegime.TREND_EXHAUSTING: 0.6,
    }
    
    def __init__(self):
        pass
    
    def check_blocking(
        self,
        direction: str,  # "BUY" veya "SELL"
        regime: MarketRegime,
        regime_confidence: float = 0.5
    ) -> RegimeBlockResult:
        """
        Regime'e göre sinyal blocking kontrolü.
        """
        allowed = self.REGIME_ALLOWED_DIRECTIONS.get(regime, [])
        multiplier = self.REGIME_CONFIDENCE_MULTIPLIER.get(regime, 0.5)
        
        # Direction normalize et
        dir_normalized = direction.upper()
        
        # HIGH_VOL_CHOPPY - Her şey yasak
        if regime == MarketRegime.HIGH_VOL_CHOPPY:
            logger.warning(f"REGIME BLOCK: HIGH_VOL_CHOPPY - tüm trading durduruldu")
            return RegimeBlockResult(
                blocked=True,
                new_direction='HOLD',
                reason='HIGH_VOL_CHOPPY: Kaotik piyasa, trading tehlikeli',
                regime=regime,
                allowed_directions=[],
                confidence_multiplier=0.0
            )
        
        # LOW_VOL_COMPRESSION - Bekle
        if regime == MarketRegime.LOW_VOL_COMPRESSION:
            logger.info(f"REGIME BLOCK: LOW_VOL_COMPRESSION - breakout bekle")
            return RegimeBlockResult(
                blocked=True,
                new_direction='HOLD',
                reason='LOW_VOL_COMPRESSION: Volatilite sıkışması, breakout bekle',
                regime=regime,
                allowed_directions=[],
                confidence_multiplier=0.5
            )
        
        # STRONG_TREND_UP'da SELL yasak
        if regime == MarketRegime.STRONG_TREND_UP:
            if dir_normalized in ['SELL', 'SHORT']:
                logger.warning(f"REGIME BLOCK: STRONG_TREND_UP - {direction} blocked")
                return RegimeBlockResult(
                    blocked=True,
                    new_direction='HOLD',
                    reason='STRONG_TREND_UP: Counter-trend SELL yasak',
                    regime=regime,
                    allowed_directions=['BUY', 'LONG'],
                    confidence_multiplier=0.3
                )
        
        # STRONG_TREND_DOWN'da BUY yasak
        if regime == MarketRegime.STRONG_TREND_DOWN:
            if dir_normalized in ['BUY', 'LONG']:
                logger.warning(f"REGIME BLOCK: STRONG_TREND_DOWN - {direction} blocked")
                return RegimeBlockResult(
                    blocked=True,
                    new_direction='HOLD',
                    reason='STRONG_TREND_DOWN: Counter-trend BUY yasak',
                    regime=regime,
                    allowed_directions=['SELL', 'SHORT'],
                    confidence_multiplier=0.3
                )
        
        # TREND_EXHAUSTING - dikkatli izin
        if regime == MarketRegime.TREND_EXHAUSTING:
            return RegimeBlockResult(
                blocked=False,
                new_direction=None,
                reason='TREND_EXHAUSTING: Dikkatli trade, trend yoruluyor olabilir',
                regime=regime,
                allowed_directions=allowed,
                confidence_multiplier=0.6
            )
        
        # WEAK_TREND ve RANGE_BOUND - izin ver ama dikkatli
        if regime in [MarketRegime.WEAK_TREND, MarketRegime.RANGE_BOUND]:
            return RegimeBlockResult(
                blocked=False,
                new_direction=None,
                reason=f'{regime.value}: Trade izinli ama düşük pozisyon',
                regime=regime,
                allowed_directions=allowed,
                confidence_multiplier=multiplier
            )
        
        # Default - izin ver
        return RegimeBlockResult(
            blocked=False,
            new_direction=None,
            reason=None,
            regime=regime,
            allowed_directions=allowed,
            confidence_multiplier=multiplier
        )


# Global instance
regime_blocker = RegimeBlocker()


def apply_regime_blocking(
    direction: str, 
    regime: MarketRegime,
    regime_confidence: float = 0.5
) -> Dict[str, Any]:
    """
    Kolay kullanım için wrapper fonksiyon.
    
    Returns:
        {
            'blocked': bool,
            'new_direction': 'HOLD' or None,
            'reason': str or None,
            'confidence_multiplier': float
        }
    """
    result = regime_blocker.check_blocking(direction, regime, regime_confidence)
    return {
        'blocked': result.blocked,
        'new_direction': result.new_direction,
        'reason': result.reason,
        'confidence_multiplier': result.confidence_multiplier,
        'allowed_directions': result.allowed_directions
    }
