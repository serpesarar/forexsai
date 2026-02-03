"""
EKSİK #9: Portfolio-Level Risk Management
Portföy bazlı risk kontrolü ve trade limitleri
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from threading import Lock
from .constants import PORTFOLIO_RISK_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class PortfolioState:
    """Portföy durumu"""
    open_trades: List[Dict[str, Any]] = field(default_factory=list)
    daily_pnl: float = 0.0
    current_drawdown: float = 0.0
    peak_equity: float = 10000.0  # Başlangıç
    current_equity: float = 10000.0
    today_trades: int = 0
    last_trade_time: Optional[datetime] = None
    daily_reset_date: Optional[datetime] = None


@dataclass
class RiskCheckResult:
    """Risk kontrol sonucu"""
    can_trade: bool
    reason: Optional[str]
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    max_position_size: float  # 0.0 - 1.0
    warnings: List[str] = field(default_factory=list)


class PortfolioRiskManager:
    """
    Portfolio Risk Management Sistemi
    
    Kontroller:
    1. Drawdown limiti (%10)
    2. Günlük kayıp limiti (%3)
    3. Korelasyon riski
    4. Max açık trade sayısı
    5. Günlük trade limiti
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or PORTFOLIO_RISK_CONFIG
        self.state = PortfolioState()
        self._lock = Lock()
    
    def can_take_new_trade(
        self,
        symbol: str,
        direction: str,
        proposed_risk_pct: float = 1.0
    ) -> RiskCheckResult:
        """
        Yeni trade alınabilir mi kontrol et.
        """
        with self._lock:
            self._check_daily_reset()
            
            warnings = []
            risk_level = 'low'
            max_position = 1.0
            
            # 1. Drawdown kontrolü
            dd_check = self._check_drawdown()
            if not dd_check['ok']:
                return RiskCheckResult(
                    can_trade=False,
                    reason=dd_check['reason'],
                    risk_level='critical',
                    max_position_size=0.0,
                    warnings=[dd_check['reason']]
                )
            if dd_check.get('warning'):
                warnings.append(dd_check['warning'])
                risk_level = 'high'
                max_position *= 0.5
            
            # 2. Günlük kayıp kontrolü
            daily_check = self._check_daily_loss()
            if not daily_check['ok']:
                return RiskCheckResult(
                    can_trade=False,
                    reason=daily_check['reason'],
                    risk_level='critical',
                    max_position_size=0.0,
                    warnings=[daily_check['reason']]
                )
            if daily_check.get('warning'):
                warnings.append(daily_check['warning'])
                if risk_level != 'high':
                    risk_level = 'medium'
                max_position *= 0.7
            
            # 3. Açık trade sayısı kontrolü
            open_check = self._check_open_trades()
            if not open_check['ok']:
                return RiskCheckResult(
                    can_trade=False,
                    reason=open_check['reason'],
                    risk_level='high',
                    max_position_size=0.0,
                    warnings=[open_check['reason']]
                )
            
            # 4. Korelasyon kontrolü
            corr_check = self._check_correlation(symbol, direction)
            if not corr_check['ok']:
                return RiskCheckResult(
                    can_trade=False,
                    reason=corr_check['reason'],
                    risk_level='medium',
                    max_position_size=0.0,
                    warnings=[corr_check['reason']]
                )
            if corr_check.get('warning'):
                warnings.append(corr_check['warning'])
                max_position *= 0.7
            
            # 5. Günlük trade limiti
            if self.state.today_trades >= 10:  # Soft limit
                warnings.append(f"Günlük trade sayısı yüksek: {self.state.today_trades}")
                max_position *= 0.8
            
            return RiskCheckResult(
                can_trade=True,
                reason=None,
                risk_level=risk_level,
                max_position_size=max_position,
                warnings=warnings
            )
    
    def _check_drawdown(self) -> Dict[str, Any]:
        """Drawdown kontrolü"""
        max_dd = self.config['max_drawdown_pct']
        warning_threshold = self.config['dd_warning_threshold']
        
        current_dd = self.state.current_drawdown
        
        if current_dd >= max_dd:
            return {
                'ok': False,
                'reason': f"Max drawdown aşıldı: {current_dd:.1f}% >= {max_dd}%"
            }
        
        if current_dd >= max_dd * warning_threshold:
            return {
                'ok': True,
                'warning': f"Drawdown uyarısı: {current_dd:.1f}% (limit: {max_dd}%)"
            }
        
        return {'ok': True}
    
    def _check_daily_loss(self) -> Dict[str, Any]:
        """Günlük kayıp kontrolü"""
        limit = self.config['daily_loss_limit']
        daily_loss_pct = -self.state.daily_pnl / self.state.current_equity * 100 if self.state.current_equity > 0 else 0
        
        if daily_loss_pct >= limit:
            return {
                'ok': False,
                'reason': f"Günlük kayıp limiti aşıldı: {daily_loss_pct:.1f}% >= {limit}%"
            }
        
        if daily_loss_pct >= limit * 0.7:
            return {
                'ok': True,
                'warning': f"Günlük kayıp uyarısı: {daily_loss_pct:.1f}% (limit: {limit}%)"
            }
        
        return {'ok': True}
    
    def _check_open_trades(self) -> Dict[str, Any]:
        """Açık trade sayısı kontrolü"""
        max_open = self.config['max_open_trades']
        current_open = len(self.state.open_trades)
        
        if current_open >= max_open:
            return {
                'ok': False,
                'reason': f"Max açık trade: {current_open} >= {max_open}"
            }
        
        return {'ok': True}
    
    def _check_correlation(self, symbol: str, direction: str) -> Dict[str, Any]:
        """Korelasyon kontrolü"""
        max_corr = self.config['max_correlated_risk']
        
        # Aynı symbol veya ilişkili sembollerde aynı yönde trade var mı?
        correlated_symbols = self._get_correlated_symbols(symbol)
        
        same_direction_count = 0
        for trade in self.state.open_trades:
            if trade['symbol'] in correlated_symbols and trade['direction'] == direction:
                same_direction_count += 1
        
        if same_direction_count >= 2:
            return {
                'ok': False,
                'reason': f"Korelasyon riski: {same_direction_count} aynı yönde ilişkili pozisyon"
            }
        
        if same_direction_count == 1:
            return {
                'ok': True,
                'warning': f"Korelasyon uyarısı: 1 ilişkili pozisyon mevcut"
            }
        
        return {'ok': True}
    
    def _get_correlated_symbols(self, symbol: str) -> List[str]:
        """İlişkili sembolleri döndür"""
        symbol_upper = symbol.upper()
        
        # Basit korelasyon grupları
        correlation_groups = [
            ['XAUUSD', 'XAGUSD', 'GOLD'],  # Precious metals
            ['NDX', 'NDX.INDX', 'NAS100', 'NASDAQ'],  # US Tech
            ['EURUSD', 'GBPUSD', 'AUDUSD'],  # USD pairs
            ['USDJPY', 'USDCHF', 'USDCAD'],  # USD strength
        ]
        
        for group in correlation_groups:
            if any(s in symbol_upper for s in group):
                return [s for s in group if s != symbol_upper] + [symbol]
        
        return [symbol]
    
    def _check_daily_reset(self):
        """Günlük reset kontrolü"""
        today = datetime.utcnow().date()
        
        if self.state.daily_reset_date != today:
            self.state.daily_pnl = 0.0
            self.state.today_trades = 0
            self.state.daily_reset_date = today
    
    def record_trade_open(self, symbol: str, direction: str, size: float, entry_price: float):
        """Trade açılışı kaydet"""
        with self._lock:
            self.state.open_trades.append({
                'symbol': symbol,
                'direction': direction,
                'size': size,
                'entry_price': entry_price,
                'open_time': datetime.utcnow()
            })
            self.state.today_trades += 1
            self.state.last_trade_time = datetime.utcnow()
    
    def record_trade_close(self, symbol: str, pnl: float):
        """Trade kapanışı kaydet"""
        with self._lock:
            # Trade'i listeden kaldır
            self.state.open_trades = [
                t for t in self.state.open_trades 
                if t['symbol'] != symbol
            ]
            
            # PnL güncelle
            self.state.daily_pnl += pnl
            self.state.current_equity += pnl
            
            # Peak equity güncelle
            if self.state.current_equity > self.state.peak_equity:
                self.state.peak_equity = self.state.current_equity
            
            # Drawdown hesapla
            if self.state.peak_equity > 0:
                self.state.current_drawdown = (
                    (self.state.peak_equity - self.state.current_equity) 
                    / self.state.peak_equity * 100
                )
    
    def get_status(self) -> Dict[str, Any]:
        """Portföy durumunu döndür"""
        with self._lock:
            return {
                'open_trades': len(self.state.open_trades),
                'daily_pnl': self.state.daily_pnl,
                'current_drawdown': self.state.current_drawdown,
                'current_equity': self.state.current_equity,
                'today_trades': self.state.today_trades
            }


# Global instance
portfolio_risk_manager = PortfolioRiskManager()


def check_portfolio_risk(
    symbol: str,
    direction: str,
    proposed_risk_pct: float = 1.0
) -> Dict[str, Any]:
    """
    Kolay kullanım için wrapper fonksiyon.
    """
    result = portfolio_risk_manager.can_take_new_trade(symbol, direction, proposed_risk_pct)
    return {
        'can_trade': result.can_trade,
        'reason': result.reason,
        'risk_level': result.risk_level,
        'max_position_size': result.max_position_size,
        'warnings': result.warnings
    }
