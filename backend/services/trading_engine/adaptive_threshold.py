"""
EKSİK #4: Adaptif Threshold
Son performansa göre dinamik confidence threshold
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from .constants import ADAPTIVE_THRESHOLD_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ThresholdResult:
    """Threshold hesaplama sonucu"""
    threshold: float
    base_threshold: float
    adjustment: float
    reason: str
    win_rate: Optional[float]
    sample_count: int


class AdaptiveThresholdManager:
    """
    Adaptif Threshold Sistemi
    
    Kurallar:
    - Win rate < 40% -> Threshold +%10 (daha seçici)
    - Win rate > 70% -> Threshold -%5 (biraz toleranslı)
    - Yeterli sample yoksa base threshold kullan
    """
    
    def __init__(self):
        self.config = ADAPTIVE_THRESHOLD_CONFIG
        self._performance_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_threshold(
        self,
        symbol: str,
        strategy: str,
        performance_data: Optional[Dict[str, Any]] = None
    ) -> ThresholdResult:
        """
        Symbol ve strategy için adaptif threshold hesapla.
        
        performance_data format:
        {
            'win_rate': float (0-1),
            'total_trades': int,
            'recent_wins': int,
            'recent_losses': int
        }
        """
        base = self.config['base_threshold']
        min_samples = self.config['min_samples']
        
        # Strategy bazlı base adjustment
        strategy_adjustments = {
            'ultra_safe': 0.05,      # +%5 daha yüksek threshold
            'balanced': 0.0,
            'full_power': -0.03,     # -%3 daha düşük
            'aggressive': -0.05      # -%5 daha düşük
        }
        
        strategy_adj = strategy_adjustments.get(strategy, 0)
        base_with_strategy = base + strategy_adj
        
        # Performance verisi yoksa base döndür
        if not performance_data:
            return ThresholdResult(
                threshold=base_with_strategy,
                base_threshold=base,
                adjustment=strategy_adj,
                reason=f"Base threshold ({strategy})",
                win_rate=None,
                sample_count=0
            )
        
        win_rate = performance_data.get('win_rate', 0.5)
        total_trades = performance_data.get('total_trades', 0)
        
        # Yeterli sample yoksa
        if total_trades < min_samples:
            return ThresholdResult(
                threshold=base_with_strategy,
                base_threshold=base,
                adjustment=strategy_adj,
                reason=f"Yetersiz sample ({total_trades} < {min_samples})",
                win_rate=win_rate,
                sample_count=total_trades
            )
        
        # Win rate'e göre adjustment
        performance_adj = 0.0
        reason = ""
        
        if win_rate < 0.40:
            # Düşük başarı - daha seçici ol
            performance_adj = self.config['low_winrate_boost']
            reason = f"Düşük win rate ({win_rate:.0%}) - threshold artırıldı"
            logger.info(f"Adaptive threshold: {symbol} win_rate={win_rate:.0%}, boosting threshold by {performance_adj:.0%}")
        
        elif win_rate > 0.70:
            # Yüksek başarı - biraz toleranslı
            performance_adj = -self.config['high_winrate_reduce']
            reason = f"Yüksek win rate ({win_rate:.0%}) - threshold düşürüldü"
        
        else:
            reason = f"Normal win rate ({win_rate:.0%})"
        
        total_adj = strategy_adj + performance_adj
        final_threshold = base + total_adj
        
        # Sınırla (min 0.50, max 0.85)
        final_threshold = max(0.50, min(0.85, final_threshold))
        
        return ThresholdResult(
            threshold=final_threshold,
            base_threshold=base,
            adjustment=total_adj,
            reason=reason,
            win_rate=win_rate,
            sample_count=total_trades
        )
    
    def update_performance_cache(
        self,
        symbol: str,
        is_win: bool,
        timestamp: Optional[datetime] = None
    ):
        """Performance cache'i güncelle"""
        if symbol not in self._performance_cache:
            self._performance_cache[symbol] = {
                'wins': 0,
                'losses': 0,
                'history': []
            }
        
        cache = self._performance_cache[symbol]
        ts = timestamp or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        if is_win:
            cache['wins'] += 1
        else:
            cache['losses'] += 1
        
        cache['history'].append({
            'time': ts,
            'win': is_win
        })
        
        # Son 7 günü tut
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.config['lookback_days'])
        cache['history'] = [h for h in cache['history'] if h['time'] > cutoff]
    
    def get_cached_performance(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Cache'den performance al"""
        if symbol not in self._performance_cache:
            return None
        
        cache = self._performance_cache[symbol]
        history = cache.get('history', [])
        
        if not history:
            return None
        
        wins = sum(1 for h in history if h['win'])
        losses = len(history) - wins
        
        return {
            'win_rate': wins / len(history) if history else 0.5,
            'total_trades': len(history),
            'recent_wins': wins,
            'recent_losses': losses
        }


# Global instance
adaptive_threshold_manager = AdaptiveThresholdManager()


def get_adaptive_threshold(
    symbol: str,
    strategy: str,
    performance_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Kolay kullanım için wrapper fonksiyon.
    """
    result = adaptive_threshold_manager.get_threshold(symbol, strategy, performance_data)
    return {
        'threshold': result.threshold,
        'base_threshold': result.base_threshold,
        'adjustment': result.adjustment,
        'reason': result.reason,
        'win_rate': result.win_rate,
        'sample_count': result.sample_count
    }


async def get_threshold_with_learning(symbol: str, strategy: str) -> Dict[str, Any]:
    """
    Learning DB'den performance çekip threshold hesapla.
    """
    try:
        from services.error_analysis_service import get_recent_performance
        perf_data = await get_recent_performance(symbol, days=7)
        return get_adaptive_threshold(symbol, strategy, perf_data)
    except Exception as e:
        logger.debug(f"Could not get learning performance: {e}")
        return get_adaptive_threshold(symbol, strategy, None)
