"""
Signal State Machine - Sinyal Durumları ve Geçişler
Zorunlu bekleme süreleri ve state yönetimi
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional, Any, Tuple
from .constants import (
    SignalState, SetupType,
    COOLDOWN_AFTER_STOP, COOLDOWN_AFTER_TARGET, 
    COOLDOWN_AFTER_INVALIDATION, MIN_HOLD_TIME
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
            
            # Cooldown period check
            if time_since < 30:  # 30 dakika minimum
                if new_confidence < 65:
                    return False, f"Soğuma süresi ({time_since:.0f}dk < 30dk), güven yetersiz"
            
            # Price change check
            if self.state.last_signal_price:
                price_change_pct = abs(current_price - self.state.last_signal_price) / self.state.last_signal_price * 100
                if price_change_pct < 0.3 and new_confidence < 70:
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
