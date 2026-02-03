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
