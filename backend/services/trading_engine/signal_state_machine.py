"""
Signal State Machine - Sinyal Durumları ve Geçişler
Zorunlu bekleme süreleri ve state yönetimi

EKSİK #1, #3, #10 entegrasyonu:
- State lifecycle (NEUTRAL -> PENDING -> CONFIRMED -> ACTIVE -> CLOSED)
- Minimum signal duration kontrolü
- NULL signal detaylı sebepleri
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional, Any, Tuple
from .constants import (
    SignalState, SetupType,
    COOLDOWN_AFTER_STOP, COOLDOWN_AFTER_TARGET, 
    COOLDOWN_AFTER_INVALIDATION, MIN_HOLD_TIME,
    MIN_SIGNAL_DURATION_HOURS, NULL_SIGNAL_REASONS, NULL_RETRY_TIMES
)


@dataclass
class SetupSignal:
    """Trade Setup Sinyali"""
    setup_type: SetupType
    direction: str
    entry_zone: Tuple[float, float]
    stop_loss: float
    targets: List[float]
    invalidation: float
    quality_score: float
    timeframe_source: str
    confluence_factors: List[str]
    requires_breakout: bool = False
    min_hold_bars: int = 4


@dataclass
class TradingSystemState:
    """Trading Sistemi Durumu"""
    current_state: SignalState
    active_setup: Optional[SetupSignal]
    last_signal_time: Optional[datetime]
    last_signal_direction: Optional[str]
    last_signal_price: Optional[float]
    cooldown_until: Optional[datetime]
    consecutive_losses: int
    daily_trades: int
    state_history: List[Dict[str, Any]] = field(default_factory=list)


class SignalStateMachine:
    """
    Sinyal State Machine
    
    Zorunlu Bekleme Süreleri:
    - Stop sonrası: 4 saat
    - Target sonrası: 2 saat
    - Invalid sonrası: 1 saat
    - Minimum tutma: 1 saat
    """
    
    def __init__(self):
        self.state = TradingSystemState(
            current_state=SignalState.NEUTRAL,
            active_setup=None,
            last_signal_time=None,
            last_signal_direction=None,
            last_signal_price=None,
            cooldown_until=None,
            consecutive_losses=0,
            daily_trades=0
        )
        self._lock = Lock()
    
    def get_state(self) -> TradingSystemState:
        """Mevcut durumu döndür"""
        with self._lock:
            return self.state
    
    def can_trade(self) -> Tuple[bool, str]:
        """Trade yapılabilir mi?"""
        with self._lock:
            now = datetime.utcnow()
            
            # Cooldown check
            if self.state.cooldown_until and now < self.state.cooldown_until:
                remaining = (self.state.cooldown_until - now).seconds // 60
                return False, f"Bekleme: {remaining}dk kaldı"
            
            # Consecutive loss check
            if self.state.consecutive_losses >= 3:
                return False, "3 ardışık kayıp - bugün stop"
            
            # Daily limit
            if self.state.daily_trades >= 5:
                return False, "Günlük limit (5) doldu"
            
            # Reset cooldown if expired
            if self.state.cooldown_until and now >= self.state.cooldown_until:
                self.state.cooldown_until = None
                self.state.current_state = SignalState.NEUTRAL
            
            return True, "Trade yapılabilir"
    
    def can_change_direction(self, new_direction: str, new_confidence: float, current_price: float) -> Tuple[bool, str]:
        """Yön değiştirilebilir mi?"""
        with self._lock:
            if not self.state.last_signal_time:
                return True, "İlk sinyal"
            
            if self.state.last_signal_direction == new_direction:
                return True, "Aynı yön"
            
            # Time since last signal
            time_since = (datetime.utcnow() - self.state.last_signal_time).seconds / 60
            
            # Cooldown period check (relaxed for responsive dashboard)
            if time_since < 15:  # 15 dakika minimum (was 30)
                if new_confidence < 55:
                    return False, f"Soğuma süresi ({time_since:.0f}dk < 15dk), güven yetersiz"
            
            # Price change check (relaxed)
            if self.state.last_signal_price:
                price_change_pct = abs(current_price - self.state.last_signal_price) / self.state.last_signal_price * 100
                if price_change_pct < 0.15 and new_confidence < 60:
                    return False, f"Fiyat değişimi yetersiz ({price_change_pct:.2f}%)"
            
            return True, f"Yön değişikliği onaylandı ({time_since:.0f}dk)"
    
    def transition_to_setup(self, setup: SetupSignal) -> bool:
        """Setup durumuna geç"""
        with self._lock:
            if self.state.current_state not in [SignalState.NEUTRAL, SignalState.WAITING_PULLBACK]:
                return False
            
            self.state.current_state = SignalState.LONG_SETUP if setup.direction == "LONG" else SignalState.SHORT_SETUP
            self.state.active_setup = setup
            self._log(f"Setup: {setup.direction} {setup.setup_type.value}")
            return True
    
    def transition_to_active(self, entry_price: float) -> bool:
        """Aktif pozisyona geç"""
        with self._lock:
            if self.state.current_state not in [SignalState.LONG_SETUP, SignalState.SHORT_SETUP]:
                return False
            
            direction = "LONG" if self.state.current_state == SignalState.LONG_SETUP else "SHORT"
            self.state.current_state = SignalState.LONG_ACTIVE if direction == "LONG" else SignalState.SHORT_ACTIVE
            self.state.last_signal_time = datetime.utcnow()
            self.state.last_signal_direction = direction
            self.state.last_signal_price = entry_price
            self.state.daily_trades += 1
            
            self._log(f"Pozisyon açıldı: {direction} @ {entry_price}")
            return True
    
    def transition_to_closed(self, reason: str, is_win: bool) -> bool:
        """Pozisyon kapat"""
        with self._lock:
            if self.state.current_state not in [SignalState.LONG_ACTIVE, SignalState.SHORT_ACTIVE]:
                return False
            
            # Cooldown
            if "stop" in reason.lower():
                cooldown = COOLDOWN_AFTER_STOP
                self.state.consecutive_losses += 1
            elif "target" in reason.lower():
                cooldown = COOLDOWN_AFTER_TARGET
                self.state.consecutive_losses = 0
            else:
                cooldown = COOLDOWN_AFTER_INVALIDATION
            
            self.state.cooldown_until = datetime.utcnow() + timedelta(minutes=cooldown)
            self.state.current_state = SignalState.COOLDOWN
            self.state.active_setup = None
            
            self._log(f"Kapandı: {reason}, {'kazanç' if is_win else 'kayıp'}")
            return True
    
    def reset_to_neutral(self):
        """Neutral'a dön"""
        with self._lock:
            self.state.current_state = SignalState.NEUTRAL
            self.state.active_setup = None
    
    def reset_daily(self):
        """Günlük reset"""
        with self._lock:
            self.state.daily_trades = 0
            self.state.consecutive_losses = 0
    
    def _log(self, message: str):
        """State history log"""
        self.state.state_history.append({
            "time": datetime.utcnow().isoformat(),
            "state": self.state.current_state.name,
            "message": message
        })
        # Keep last 50
        if len(self.state.state_history) > 50:
            self.state.state_history = self.state.state_history[-50:]
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # EKSİK #3: Minimum Signal Duration
    # ═══════════════════════════════════════════════════════════════════════════════
    def check_minimum_signal_duration(
        self, 
        symbol: str, 
        strategy: str = 'balanced'
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Minimum sinyal süresi kontrolü.
        
        Returns:
            (can_proceed, reason, retry_minutes)
        """
        with self._lock:
            if not self.state.last_signal_time:
                return True, None, None
            
            min_hours = MIN_SIGNAL_DURATION_HOURS.get(strategy, 4)
            elapsed = (datetime.utcnow() - self.state.last_signal_time).total_seconds() / 3600
            
            if elapsed < min_hours:
                remaining_hours = min_hours - elapsed
                remaining_mins = int(remaining_hours * 60)
                reason = f"Minimum süre: {elapsed:.1f}h < {min_hours}h ({remaining_mins}dk kaldı)"
                return False, reason, remaining_mins
            
            return True, None, None
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # EKSİK #10: NULL Signal Generation
    # ═══════════════════════════════════════════════════════════════════════════════
    def generate_null_signal(
        self, 
        reason_code: str, 
        details: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detaylı NULL signal üret.
        
        reason_code: NULL_SIGNAL_REASONS key'lerinden biri
        """
        reason_text = NULL_SIGNAL_REASONS.get(reason_code, 'Bilinmeyen sebep')
        retry_minutes = NULL_RETRY_TIMES.get(reason_code, 30)
        
        return {
            'signal': 'HOLD',
            'null_reason_code': reason_code,
            'null_reason': reason_text,
            'null_details': details,
            'retry_after_minutes': retry_minutes,
            'current_state': self.state.current_state.name,
            'last_signal_direction': self.state.last_signal_direction,
            'last_signal_time': self.state.last_signal_time.isoformat() if self.state.last_signal_time else None
        }
    
    def get_full_status(self) -> Dict[str, Any]:
        """Tam durum bilgisi döndür"""
        with self._lock:
            return {
                'current_state': self.state.current_state.name,
                'active_setup': {
                    'direction': self.state.active_setup.direction,
                    'type': self.state.active_setup.setup_type.value,
                    'quality': self.state.active_setup.quality_score
                } if self.state.active_setup else None,
                'last_signal': {
                    'direction': self.state.last_signal_direction,
                    'price': self.state.last_signal_price,
                    'time': self.state.last_signal_time.isoformat() if self.state.last_signal_time else None
                },
                'cooldown_until': self.state.cooldown_until.isoformat() if self.state.cooldown_until else None,
                'consecutive_losses': self.state.consecutive_losses,
                'daily_trades': self.state.daily_trades,
                'can_trade': self.can_trade()[0]
            }


# Global instance for singleton access
_global_state_machine: Optional['SignalStateMachine'] = None
_global_lock = Lock()


def get_state_machine() -> SignalStateMachine:
    """Global state machine instance al"""
    global _global_state_machine
    with _global_lock:
        if _global_state_machine is None:
            _global_state_machine = SignalStateMachine()
        return _global_state_machine


def check_signal_validity(
    symbol: str,
    new_direction: str,
    new_confidence: float,
    current_price: float,
    strategy: str = 'balanced'
) -> Dict[str, Any]:
    """
    Yeni sinyal geçerli mi kontrol et.
    Tüm state machine kontrollerini birleştirir.
    
    Returns:
        {
            'valid': bool,
            'reason': str or None,
            'null_signal': dict or None (HOLD sinyali detayları)
        }
    """
    sm = get_state_machine()
    
    # 1. Trade yapılabilir mi?
    can_trade, trade_reason = sm.can_trade()
    if not can_trade:
        null_code = 'COOLDOWN' if 'Bekleme' in trade_reason else (
            'CONSECUTIVE_LOSS' if 'ardışık' in trade_reason else 'DAILY_LIMIT'
        )
        return {
            'valid': False,
            'reason': trade_reason,
            'null_signal': sm.generate_null_signal(null_code, trade_reason)
        }
    
    # 2. Minimum duration kontrolü
    can_proceed, duration_reason, retry_mins = sm.check_minimum_signal_duration(symbol, strategy)
    if not can_proceed:
        return {
            'valid': False,
            'reason': duration_reason,
            'null_signal': sm.generate_null_signal('MIN_DURATION', duration_reason)
        }
    
    # 3. Yön değişikliği kontrolü
    can_change, change_reason = sm.can_change_direction(new_direction, new_confidence, current_price)
    if not can_change:
        null_code = 'COOLDOWN' if 'Soğuma' in change_reason else 'PRICE_MOVEMENT'
        return {
            'valid': False,
            'reason': change_reason,
            'null_signal': sm.generate_null_signal(null_code, change_reason)
        }
    
    return {
        'valid': True,
        'reason': change_reason if change_reason else 'OK',
        'null_signal': None
    }
