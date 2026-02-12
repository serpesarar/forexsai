"""
Trading Engine Constants & Enums
"""
from enum import Enum, auto
from typing import Literal


class MarketRegime(Enum):
    """5 Farklı Piyasa Rejimi"""
    STRONG_TREND_UP = "strong_trend_up"
    STRONG_TREND_DOWN = "strong_trend_down"
    WEAK_TREND = "weak_trend"
    RANGE_BOUND = "range_bound"
    LOW_VOL_COMPRESSION = "low_vol_compression"
    HIGH_VOL_CHOPPY = "high_vol_choppy"
    TREND_EXHAUSTING = "trend_exhausting"


class PriceStructure(Enum):
    """Fiyat Yapısı"""
    HIGHER_HIGHS = "higher_highs"
    LOWER_LOWS = "lower_lows"
    EXPANDING_RANGE = "expanding_range"
    CONTRACTING_RANGE = "contracting_range"
    CHAOTIC = "chaotic"


class SignalState(Enum):
    """Sinyal Durumları"""
    NEUTRAL = auto()
    LONG_SETUP = auto()
    LONG_ACTIVE = auto()
    SHORT_SETUP = auto()
    SHORT_ACTIVE = auto()
    WAITING_PULLBACK = auto()
    COOLDOWN = auto()
    NO_TRADE = auto()


class SetupType(Enum):
    """Setup Türleri"""
    BREAKOUT = "breakout"
    PULLBACK = "pullback"
    REVERSAL = "reversal"
    CONTINUATION = "continuation"


# Timeframe Ağırlıkları
TIMEFRAME_WEIGHTS = {
    "1W": 0.15,
    "1D": 0.30,
    "4H": 0.30,
    "1H": 0.20,
    "15m": 0.05
}

# ADX Eşikleri
ADX_STRONG = 30
ADX_WEAK = 20

# Cooldown Süreleri (dakika)
COOLDOWN_AFTER_STOP = 240
COOLDOWN_AFTER_TARGET = 120
COOLDOWN_AFTER_INVALIDATION = 60
MIN_HOLD_TIME = 60

# TF Onay Matrisi
TF_APPROVAL_MATRIX = {
    ("UP", "UP", "UP"): ("STRONG_LONG", 1.0, "normal"),
    ("UP", "UP", "DOWN"): ("WAIT_PULLBACK", 0.5, "low"),
    ("UP", "DOWN", "UP"): ("NO_TRADE", 0.0, None),
    ("UP", "DOWN", "DOWN"): ("HEDGE_ONLY", 0.2, "very_low"),
    ("DOWN", "DOWN", "DOWN"): ("STRONG_SHORT", 1.0, "normal"),
    ("DOWN", "DOWN", "UP"): ("WAIT_PULLBACK", 0.5, "low"),
    ("DOWN", "UP", "DOWN"): ("NO_TRADE", 0.0, None),
    ("DOWN", "UP", "UP"): ("HEDGE_ONLY", 0.2, "very_low"),
    ("NEUTRAL", "UP", "UP"): ("CAUTIOUS_LONG", 0.7, "low"),
    ("NEUTRAL", "DOWN", "DOWN"): ("CAUTIOUS_SHORT", 0.7, "low"),
}

# Konfluans Kategori Ağırlıkları
CONFLUENCE_WEIGHTS = {
    "trend": 0.30,
    "momentum": 0.20,
    "structure": 0.25,
    "pattern": 0.15,
    "temporal": 0.10
}

# ═══════════════════════════════════════════════════════════════════════════════
# EKSİK #3: Minimum Signal Duration (saat)
# ═══════════════════════════════════════════════════════════════════════════════
MIN_SIGNAL_DURATION_HOURS = {
    'ultra_safe': 4,    # 4 saat minimum aynı sinyal
    'balanced': 1,      # 1 saat (was 4h - too restrictive for live dashboard)
    'full_power': 0.5,  # 30 dakika
    'aggressive': 0.25  # 15 dakika
}

# ═══════════════════════════════════════════════════════════════════════════════
# EKSİK #5: Pattern TF Önceliği
# ═══════════════════════════════════════════════════════════════════════════════
TF_PRIORITY = {
    '1W': 7, '1D': 6, '4H': 5, '1H': 4, '30m': 3, '15m': 2, '5m': 1
}

# ═══════════════════════════════════════════════════════════════════════════════
# EKSİK #10: NULL Signal Reasons
# ═══════════════════════════════════════════════════════════════════════════════
NULL_SIGNAL_REASONS = {
    'COOLDOWN': 'Sinyal değişimi için bekleme süresi',
    'MIN_DURATION': 'Minimum sinyal süresi dolmadı',
    'INSUFFICIENT_CONFIDENCE': 'Yeterli confidence yok',
    'MTF_VETO': 'Üst timeframe onay vermiyor',
    'REGIME_BLOCK': 'Piyasa rejimi uygun değil',
    'LAYER_CONFLICT': 'Katmanlar arası çelişki',
    'PATTERN_CONFLICT': 'Pattern çakışması çözülemedi',
    'PATTERN_INVALID': 'Pattern henüz tamamlanmadı',
    'LEARNING_WARNING': 'Benzer setup\'lar başarısız olmuş',
    'PORTFOLIO_RISK': 'Portföy risk limiti dolu',
    'AWAITING_CONFIRMATION': 'Entry trigger bekleniyor',
    'DAILY_LIMIT': 'Günlük trade limiti doldu',
    'CONSECUTIVE_LOSS': 'Ardışık kayıp limiti aşıldı',
    'PRICE_MOVEMENT': 'Yeterli fiyat hareketi yok'
}

# NULL Signal için retry süreleri (dakika)
NULL_RETRY_TIMES = {
    'COOLDOWN': 30,
    'MIN_DURATION': 60,
    'INSUFFICIENT_CONFIDENCE': 15,
    'MTF_VETO': 60,
    'REGIME_BLOCK': 120,
    'LAYER_CONFLICT': 30,
    'PATTERN_CONFLICT': 15,
    'PATTERN_INVALID': 15,
    'LEARNING_WARNING': 60,
    'PORTFOLIO_RISK': 240,
    'AWAITING_CONFIRMATION': 5,
    'DAILY_LIMIT': 480,
    'CONSECUTIVE_LOSS': 240,
    'PRICE_MOVEMENT': 15
}

# ═══════════════════════════════════════════════════════════════════════════════
# Adaptive Threshold Base Values
# ═══════════════════════════════════════════════════════════════════════════════
ADAPTIVE_THRESHOLD_CONFIG = {
    'base_threshold': 0.55,       # 0.65 -> 0.55 (daha fazla sinyal için)
    'low_winrate_boost': 0.10,    # Win rate < 40% ise +%10
    'high_winrate_reduce': 0.05,  # Win rate > 70% ise -%5
    'min_samples': 5,             # Minimum sample sayısı
    'lookback_days': 7            # Kaç günlük veri
}

# ═══════════════════════════════════════════════════════════════════════════════
# Portfolio Risk Config
# ═══════════════════════════════════════════════════════════════════════════════
PORTFOLIO_RISK_CONFIG = {
    'max_drawdown_pct': 10,       # %10 max DD
    'max_correlated_risk': 0.3,   # Aynı sektörde max %30 risk
    'daily_loss_limit': 3,        # Günlük max %3 kayıp
    'max_open_trades': 3,         # Max açık pozisyon
    'dd_warning_threshold': 0.8   # DD limitinin %80'inde uyarı
}
