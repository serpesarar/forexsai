"""
Trend Analysis Engine v3.0 (Production-Ready)

Features:
- Multi-timeframe support (daily + hourly)
- Rolling MAD anomaly detection
- Weighted linear regression for channels
- Fractal pivot detection with confirmation status
- OBV volume confirmation
- Pivot-based RSI divergence
- Conflict detection with penalty
- Symbol-specific weights
- Slope deadzone for noise filtering
- Proper data warmup requirements
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from enum import Enum
import numpy as np

from services.technical_indicators import (
    calculate_ema, calculate_rsi, calculate_atr,
    calculate_rsi_series, weighted_linear_regression,
    obv_trend_confirmation, clean_ohlc_data
)
from services.analysis_cache import get_cached, set_cached
from services.data_fetcher import fetch_eod_candles, fetch_latest_price, fetch_intraday_candles


# ========== ENUMS & DATA CLASSES ==========

class TrendDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class VolatilityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PivotStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNCONFIRMED = "UNCONFIRMED"


@dataclass
class EMAMetric:
    period: int
    value: Optional[float]
    distance: Optional[float]
    distance_pct: Optional[float]
    has_data: bool = True


@dataclass
class ChannelMetric:
    upper: float
    lower: float
    width: float
    distance_to_upper: float
    distance_to_lower: float
    slope: float
    slope_normalized: float  # Slope / ATR for comparability
    r_squared: float
    is_valid: bool


@dataclass
class SupportResistance:
    price: float
    distance: float
    distance_pct: float
    strength: float
    touches: int
    status: PivotStatus = PivotStatus.CONFIRMED


@dataclass
class DivergenceSignal:
    type: Literal["BULLISH_DIV", "BEARISH_DIV", "NONE"]
    strength: float
    description: str


@dataclass
class ConflictInfo:
    has_conflict: bool
    description: str
    penalty: float


@dataclass
class TrendAnalysisResult:
    symbol: str
    current_price: float
    timestamp: str
    data_quality: float
    
    trend: str
    trend_strength: int
    confidence: int
    
    ema20: EMAMetric
    ema50: EMAMetric
    ema200: EMAMetric
    ema_alignment: str
    
    channel: ChannelMetric
    
    nearest_support: SupportResistance
    nearest_resistance: SupportResistance
    sr_levels: List[SupportResistance]
    
    atr_14: Optional[float]
    volatility_pct: Optional[float]
    volatility_level: str
    
    rsi_14: Optional[float]
    rsi_divergence: DivergenceSignal
    momentum_5d: float
    momentum_10d: float
    momentum_20d: float
    
    volume_confirmed: bool
    obv_trend: str
    
    daily_trend: Optional[str] = None
    hourly_trend: Optional[str] = None
    mtf_alignment: bool = True
    
    conflict: Optional[ConflictInfo] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [
                    asdict(item) if hasattr(item, '__dataclass_fields__') else item 
                    for item in value
                ]
            elif hasattr(value, '__dataclass_fields__'):
                result[key] = asdict(value)
            else:
                result[key] = value
        return result


# ========== SYMBOL PROFILES ==========

SYMBOL_PROFILES = {
    "NASDAQ": {
        "ema_weight": 0.25,
        "momentum_weight": 0.25,
        "sr_weight": 0.20,
        "volume_weight": 0.15,
        "channel_weight": 0.15,
        "vol_low_threshold": 0.8,
        "vol_high_threshold": 2.0,
        "slope_deadzone_multiplier": 0.001,  # ATR multiplier for slope deadzone
    },
    "XAUUSD": {
        "ema_weight": 0.30,
        "momentum_weight": 0.20,
        "sr_weight": 0.25,
        "volume_weight": 0.10,
        "channel_weight": 0.15,
        "vol_low_threshold": 0.5,
        "vol_high_threshold": 1.5,
        "slope_deadzone_multiplier": 0.0008,
    },
    "NDX.INDX": {
        "ema_weight": 0.25,
        "momentum_weight": 0.25,
        "sr_weight": 0.20,
        "volume_weight": 0.15,
        "channel_weight": 0.15,
        "vol_low_threshold": 0.8,
        "vol_high_threshold": 2.0,
        "slope_deadzone_multiplier": 0.001,
    },
}


def get_symbol_profile(symbol: str) -> dict:
    """Get symbol-specific weights and thresholds"""
    # Normalize symbol
    normalized = symbol.upper().replace(".INDX", "").replace(".FOREX", "")
    if "NDX" in normalized or "NASDAQ" in normalized:
        return SYMBOL_PROFILES["NASDAQ"]
    elif "XAU" in normalized:
        return SYMBOL_PROFILES["XAUUSD"]
    return SYMBOL_PROFILES["NASDAQ"]  # Default


# ========== PIVOT DETECTION ==========

def detect_fractal_pivots(
    highs: np.ndarray,
    lows: np.ndarray,
    left_bars: int = 5,
    right_bars: int = 5,
    include_unconfirmed: bool = False
) -> tuple[List[tuple], List[tuple]]:
    """
    Fractal pivot detection with confirmation status.
    Confirmed = has right_bars candles after pivot
    Unconfirmed = last right_bars candles (potential pivot)
    
    Returns: (pivot_highs, pivot_lows) as list of (index, price, status)
    """
    pivot_highs = []
    pivot_lows = []
    
    # Confirmed pivots (full left + right bars available)
    for i in range(left_bars, len(highs) - right_bars):
        is_pivot_high = all(
            highs[i] >= highs[i - j] for j in range(1, left_bars + 1)
        ) and all(
            highs[i] >= highs[i + j] for j in range(1, right_bars + 1)
        )
        
        if is_pivot_high:
            pivot_highs.append((i, float(highs[i]), PivotStatus.CONFIRMED))
        
        is_pivot_low = all(
            lows[i] <= lows[i - j] for j in range(1, left_bars + 1)
        ) and all(
            lows[i] <= lows[i + j] for j in range(1, right_bars + 1)
        )
        
        if is_pivot_low:
            pivot_lows.append((i, float(lows[i]), PivotStatus.CONFIRMED))
    
    # Unconfirmed pivots (last right_bars not yet formed)
    if include_unconfirmed and len(highs) > left_bars:
        for i in range(max(left_bars, len(highs) - right_bars), len(highs)):
            # Check only left bars
            if all(highs[i] >= highs[i - j] for j in range(1, min(left_bars + 1, i + 1))):
                # Also check available right bars
                right_available = len(highs) - i - 1
                if right_available == 0 or all(highs[i] >= highs[i + j] for j in range(1, right_available + 1)):
                    pivot_highs.append((i, float(highs[i]), PivotStatus.UNCONFIRMED))
            
            if all(lows[i] <= lows[i - j] for j in range(1, min(left_bars + 1, i + 1))):
                right_available = len(lows) - i - 1
                if right_available == 0 or all(lows[i] <= lows[i + j] for j in range(1, right_available + 1)):
                    pivot_lows.append((i, float(lows[i]), PivotStatus.UNCONFIRMED))
    
    return pivot_highs, pivot_lows


def cluster_sr_levels(
    pivots: List[tuple],
    current_price: float,
    tolerance_pct: float = 0.5,
    is_support: bool = True,
    only_confirmed: bool = True
) -> List[SupportResistance]:
    """Cluster pivot levels into support/resistance zones"""
    if not pivots:
        return []
    
    # Filter by confirmation status if needed
    if only_confirmed:
        pivots = [(idx, price, status) for idx, price, status in pivots if status == PivotStatus.CONFIRMED]
    
    if not pivots:
        return []
    
    # Filter by position relative to current price
    if is_support:
        filtered = [(idx, price, status) for idx, price, status in pivots if price < current_price]
    else:
        filtered = [(idx, price, status) for idx, price, status in pivots if price > current_price]
    
    if not filtered:
        return []
    
    tolerance = current_price * (tolerance_pct / 100)
    
    # Sort by price
    sorted_pivots = sorted(filtered, key=lambda x: x[1])
    
    # Cluster nearby levels
    clusters: List[List[tuple]] = []
    for pivot in sorted_pivots:
        if not clusters or abs(pivot[1] - np.mean([p[1] for p in clusters[-1]])) > tolerance:
            clusters.append([pivot])
        else:
            clusters[-1].append(pivot)
    
    # Create SR levels
    sr_list = []
    for c in clusters:
        prices = [p[1] for p in c]
        statuses = [p[2] for p in c]
        
        price = float(np.mean(prices))
        touches = len(c)
        strength = min(1.0, touches / 5.0)
        distance = price - current_price
        distance_pct = (distance / current_price) * 100
        
        # Use most confident status
        status = PivotStatus.CONFIRMED if PivotStatus.CONFIRMED in statuses else PivotStatus.UNCONFIRMED
        
        sr_list.append(SupportResistance(
            price=round(price, 2),
            distance=round(distance, 2),
            distance_pct=round(distance_pct, 2),
            strength=round(strength, 2),
            touches=touches,
            status=status
        ))
    
    # Sort by distance to current price
    sr_list.sort(key=lambda x: abs(x.distance))
    
    return sr_list[:5]  # Top 5


# ========== RSI DIVERGENCE (Pivot-Based) ==========

def detect_pivot_rsi_divergence(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    rsi_series: np.ndarray,
    lookback: int = 50
) -> DivergenceSignal:
    """
    Pivot-based RSI divergence detection.
    Compares last 2 confirmed swing highs/lows with RSI at those points.
    """
    if len(closes) < lookback or len(rsi_series) < lookback:
        return DivergenceSignal("NONE", 0.0, "Yetersiz veri")
    
    # Get recent pivots
    pivot_highs, pivot_lows = detect_fractal_pivots(
        highs[-lookback:], lows[-lookback:], 
        left_bars=3, right_bars=3, 
        include_unconfirmed=False
    )
    
    # Bearish divergence: price makes higher high, RSI makes lower high
    if len(pivot_highs) >= 2:
        # Last 2 pivot highs
        ph1_idx, ph1_price, _ = pivot_highs[-2]
        ph2_idx, ph2_price, _ = pivot_highs[-1]
        
        # Adjust indices for sliced array
        rsi_idx1 = len(rsi_series) - lookback + ph1_idx
        rsi_idx2 = len(rsi_series) - lookback + ph2_idx
        
        if 0 <= rsi_idx1 < len(rsi_series) and 0 <= rsi_idx2 < len(rsi_series):
            rsi1 = rsi_series[rsi_idx1]
            rsi2 = rsi_series[rsi_idx2]
            
            # Price higher, RSI lower = bearish divergence
            if ph2_price > ph1_price and rsi2 < rsi1 - 3:  # 3 point threshold
                strength = min(1.0, abs(rsi1 - rsi2) / 15)
                return DivergenceSignal(
                    "BEARISH_DIV",
                    round(strength, 2),
                    f"Fiyat yeni zirve ({ph2_price:.0f}), RSI düşük ({rsi2:.0f} < {rsi1:.0f})"
                )
    
    # Bullish divergence: price makes lower low, RSI makes higher low
    if len(pivot_lows) >= 2:
        pl1_idx, pl1_price, _ = pivot_lows[-2]
        pl2_idx, pl2_price, _ = pivot_lows[-1]
        
        rsi_idx1 = len(rsi_series) - lookback + pl1_idx
        rsi_idx2 = len(rsi_series) - lookback + pl2_idx
        
        if 0 <= rsi_idx1 < len(rsi_series) and 0 <= rsi_idx2 < len(rsi_series):
            rsi1 = rsi_series[rsi_idx1]
            rsi2 = rsi_series[rsi_idx2]
            
            # Price lower, RSI higher = bullish divergence
            if pl2_price < pl1_price and rsi2 > rsi1 + 3:
                strength = min(1.0, abs(rsi2 - rsi1) / 15)
                return DivergenceSignal(
                    "BULLISH_DIV",
                    round(strength, 2),
                    f"Fiyat yeni dip ({pl2_price:.0f}), RSI yüksek ({rsi2:.0f} > {rsi1:.0f})"
                )
    
    return DivergenceSignal("NONE", 0.0, "Divergence tespit edilmedi")


# ========== CONFLICT DETECTION ==========

def detect_conflicts(
    trend_strength: float,
    momentum_score: float,
    volume_confirmed: bool,
    rsi_divergence: DivergenceSignal,
    mtf_aligned: bool
) -> ConflictInfo:
    """Detect conflicts between indicators"""
    conflicts = []
    penalty = 0.0
    
    # Trend-Momentum conflict
    if trend_strength > 70 and momentum_score < 40:
        conflicts.append("Trend güçlü ama momentum zayıf")
        penalty += 0.15
    elif trend_strength < 30 and momentum_score > 60:
        conflicts.append("Trend zayıf ama momentum güçlü")
        penalty += 0.10
    
    # Volume not confirming
    if trend_strength > 60 and not volume_confirmed:
        conflicts.append("Hacim trendi onaylamıyor")
        penalty += 0.10
    
    # RSI divergence
    if rsi_divergence.type != "NONE" and rsi_divergence.strength > 0.5:
        conflicts.append(f"RSI {rsi_divergence.type.replace('_', ' ')}")
        penalty += 0.12
    
    # Multi-timeframe misalignment
    if not mtf_aligned:
        conflicts.append("Günlük ve saatlik trend uyumsuz")
        penalty += 0.08
    
    return ConflictInfo(
        has_conflict=len(conflicts) > 0,
        description="; ".join(conflicts) if conflicts else "Çelişki yok",
        penalty=min(0.40, penalty)
    )


# ========== SR SCORE CALCULATION ==========

def calculate_sr_score(
    nearest_support: SupportResistance,
    nearest_resistance: SupportResistance,
    trend_direction: TrendDirection
) -> float:
    """
    Calculate SR position score with trend-aware logic.
    - Uptrend: Being close to resistance is risky (lower score)
    - Downtrend: Being close to support is risky (lower score)
    """
    support_dist = abs(nearest_support.distance)
    resistance_dist = abs(nearest_resistance.distance)
    total_range = support_dist + resistance_dist + 0.01
    
    # Position in range (0 = at support, 1 = at resistance)
    position = support_dist / total_range
    
    if trend_direction == TrendDirection.BULLISH:
        # In uptrend: closer to support = better buying opportunity
        # closer to resistance = risk of rejection
        score = (1 - position) * 100  # Higher score when closer to support
        # Add penalty if too close to resistance (within 20% of range)
        if position > 0.8:
            score *= 0.7  # 30% penalty
    elif trend_direction == TrendDirection.BEARISH:
        # In downtrend: closer to resistance = better shorting opportunity
        # closer to support = risk of bounce
        score = position * 100  # Higher score when closer to resistance
        if position < 0.2:
            score *= 0.7
    else:
        # Neutral: middle is best
        score = (1 - abs(position - 0.5) * 2) * 100
    
    return max(0, min(100, score))


# ========== VOLATILITY LEVEL ==========

def get_volatility_level(atr_pct: float, symbol: str) -> VolatilityLevel:
    """Get volatility level with symbol-specific thresholds"""
    profile = get_symbol_profile(symbol)
    low_th = profile.get("vol_low_threshold", 1.0)
    high_th = profile.get("vol_high_threshold", 2.5)
    
    if atr_pct < low_th:
        return VolatilityLevel.LOW
    elif atr_pct > high_th:
        return VolatilityLevel.HIGH
    return VolatilityLevel.MEDIUM


# ========== MAIN ANALYSIS FUNCTION ==========

async def run_trend_analysis(
    symbol: str,
    include_hourly: bool = False
) -> TrendAnalysisResult:
    """
    Main trend analysis function.
    Computes all metrics and returns TrendAnalysisResult.
    """
    # Cache check (5 min TTL)
    cache_key = f"trend_analysis:{symbol}:{include_hourly}"
    cached = get_cached(cache_key)
    if cached:
        return cached
    
    # Fetch data
    try:
        eod_data = await fetch_eod_candles(symbol, limit=300)
        live_price = await fetch_latest_price(symbol)
    except Exception as e:
        raise ValueError(f"Veri çekilemedi: {symbol} - {str(e)}")
    
    if len(eod_data) < 50:
        raise ValueError(f"Yetersiz veri: {symbol} ({len(eod_data)} gün)")
    
    # Extract OHLCV
    opens = np.array([d["open"] for d in eod_data])
    highs = np.array([d["high"] for d in eod_data])
    lows = np.array([d["low"] for d in eod_data])
    closes = np.array([d["close"] for d in eod_data])
    volumes = np.array([d.get("volume", 0) for d in eod_data])
    
    # Clean data (rolling MAD based)
    clean_opens, clean_highs, clean_lows, clean_closes, data_quality = clean_ohlc_data(
        opens, highs, lows, closes, threshold=3.0
    )
    
    # Current price (live or last close)
    current_price = float(live_price) if live_price else float(clean_closes[-1])
    
    profile = get_symbol_profile(symbol)
    
    # ========== EMA ==========
    ema20_val = calculate_ema(clean_closes, 20)
    ema50_val = calculate_ema(clean_closes, 50) if len(clean_closes) >= 50 else None
    ema200_val = calculate_ema(clean_closes, 200) if len(clean_closes) >= 200 else None
    
    def make_ema(period: int, value: Optional[float]) -> EMAMetric:
        if value is None:
            return EMAMetric(period, None, None, None, has_data=False)
        dist = current_price - value
        dist_pct = (dist / current_price) * 100
        return EMAMetric(period, round(value, 2), round(dist, 2), round(dist_pct, 2), True)
    
    ema20 = make_ema(20, ema20_val)
    ema50 = make_ema(50, ema50_val)
    ema200 = make_ema(200, ema200_val)
    
    # EMA alignment
    if all(e.has_data for e in [ema20, ema50, ema200]):
        if ema20.value > ema50.value > ema200.value:
            ema_alignment = "BULLISH"
        elif ema20.value < ema50.value < ema200.value:
            ema_alignment = "BEARISH"
        else:
            ema_alignment = "MIXED"
    elif ema20.has_data and ema50.has_data:
        if ema20.value > ema50.value:
            ema_alignment = "BULLISH"
        elif ema20.value < ema50.value:
            ema_alignment = "BEARISH"
        else:
            ema_alignment = "MIXED"
    else:
        ema_alignment = "MIXED"
    
    # ========== ATR & VOLATILITY ==========
    atr_14 = calculate_atr(clean_highs, clean_lows, clean_closes, 14)
    if atr_14:
        volatility_pct = (atr_14 / current_price) * 100
        volatility_level = get_volatility_level(volatility_pct, symbol)
    else:
        volatility_pct = None
        volatility_level = VolatilityLevel.MEDIUM
    
    # ========== TREND CHANNEL ==========
    channel_period = 20
    slope, intercept, r_sq = weighted_linear_regression(clean_closes[-channel_period:])
    
    # Slope deadzone (normalized by ATR)
    slope_deadzone = (atr_14 or current_price * 0.01) * profile.get("slope_deadzone_multiplier", 0.001)
    slope_normalized = slope / (atr_14 + 1e-9) if atr_14 else 0
    
    # Channel bounds
    residuals = clean_closes[-channel_period:] - (slope * np.arange(channel_period) + intercept)
    std_dev = np.std(residuals)
    
    regression_end = slope * (channel_period - 1) + intercept
    channel_upper = regression_end + 2 * std_dev
    channel_lower = regression_end - 2 * std_dev
    
    channel = ChannelMetric(
        upper=round(channel_upper, 2),
        lower=round(channel_lower, 2),
        width=round(channel_upper - channel_lower, 2),
        distance_to_upper=round(channel_upper - current_price, 2),
        distance_to_lower=round(current_price - channel_lower, 2),
        slope=round(slope, 6),
        slope_normalized=round(slope_normalized, 6),
        r_squared=round(r_sq, 2),
        is_valid=r_sq > 0.6
    )
    
    # ========== SUPPORT/RESISTANCE ==========
    pivot_highs, pivot_lows = detect_fractal_pivots(
        clean_highs, clean_lows, 
        left_bars=5, right_bars=5,
        include_unconfirmed=False  # Only confirmed for SR
    )
    
    supports = cluster_sr_levels(pivot_lows, current_price, is_support=True, only_confirmed=True)
    resistances = cluster_sr_levels(pivot_highs, current_price, is_support=False, only_confirmed=True)
    
    # Nearest SR (with fallback)
    if supports:
        nearest_support = supports[0]
    else:
        fallback_price = current_price * 0.98
        nearest_support = SupportResistance(
            round(fallback_price, 2), round(fallback_price - current_price, 2),
            -2.0, 0.3, 0, PivotStatus.UNCONFIRMED
        )
    
    if resistances:
        nearest_resistance = resistances[0]
    else:
        fallback_price = current_price * 1.02
        nearest_resistance = SupportResistance(
            round(fallback_price, 2), round(fallback_price - current_price, 2),
            2.0, 0.3, 0, PivotStatus.UNCONFIRMED
        )
    
    # ========== MOMENTUM ==========
    def momentum(period: int) -> float:
        if len(clean_closes) < period:
            return 0.0
        return ((clean_closes[-1] - clean_closes[-period]) / clean_closes[-period]) * 100
    
    mom_5d = momentum(5)
    mom_10d = momentum(10)
    mom_20d = momentum(20)
    
    # ========== RSI ==========
    rsi_14 = calculate_rsi(clean_closes, 14)
    rsi_series = calculate_rsi_series(clean_closes, 14)
    
    # Pivot-based divergence
    rsi_divergence = detect_pivot_rsi_divergence(
        clean_highs, clean_lows, clean_closes, rsi_series, lookback=50
    )
    
    # ========== VOLUME CONFIRMATION ==========
    volume_confirmed, obv_trend_str = obv_trend_confirmation(clean_closes, volumes)
    obv_trend = obv_trend_str
    
    # ========== TREND DIRECTION ==========
    bullish_signals = 0
    bearish_signals = 0
    
    # EMA alignment (weight: 2)
    if ema_alignment == "BULLISH":
        bullish_signals += 2
    elif ema_alignment == "BEARISH":
        bearish_signals += 2
    
    # Price vs EMA20 (weight: 1)
    if ema20.has_data and current_price > ema20.value:
        bullish_signals += 1
    elif ema20.has_data:
        bearish_signals += 1
    
    # Slope with deadzone (weight: 1)
    if abs(slope) > slope_deadzone:
        if slope > 0:
            bullish_signals += 1
        else:
            bearish_signals += 1
    # Else: neutral, no signal
    
    # Momentum (weight: 1)
    if mom_20d > 2:
        bullish_signals += 1
    elif mom_20d < -2:
        bearish_signals += 1
    
    # RSI (weight: 1)
    if rsi_14 and rsi_14 > 55:
        bullish_signals += 1
    elif rsi_14 and rsi_14 < 45:
        bearish_signals += 1
    
    # Determine trend
    if bullish_signals > bearish_signals + 2:
        trend = TrendDirection.BULLISH
    elif bearish_signals > bullish_signals + 2:
        trend = TrendDirection.BEARISH
    else:
        trend = TrendDirection.NEUTRAL
    
    # ========== MULTI-TIMEFRAME (if enabled) ==========
    daily_trend = trend
    hourly_trend = None
    mtf_alignment = True
    
    if include_hourly:
        try:
            hourly_data = await fetch_intraday_candles(symbol, interval="1h", limit=100)
            if len(hourly_data) >= 20:
                h_closes = np.array([d["close"] for d in hourly_data])
                h_ema20 = calculate_ema(h_closes, 20)
                h_mom = ((h_closes[-1] - h_closes[-10]) / h_closes[-10]) * 100 if len(h_closes) >= 10 else 0
                
                if h_ema20 and h_closes[-1] > h_ema20 and h_mom > 0.5:
                    hourly_trend = TrendDirection.BULLISH.value
                elif h_ema20 and h_closes[-1] < h_ema20 and h_mom < -0.5:
                    hourly_trend = TrendDirection.BEARISH.value
                else:
                    hourly_trend = TrendDirection.NEUTRAL.value
                
                mtf_alignment = (trend.value == hourly_trend) or hourly_trend == TrendDirection.NEUTRAL.value
        except:
            hourly_trend = None
            mtf_alignment = True
    
    # ========== TREND STRENGTH (0-100) ==========
    # EMA score
    ema_score = 50
    if ema_alignment == "BULLISH":
        ema_score = 70 + min(30, abs(ema20.distance_pct or 0) * 10)
    elif ema_alignment == "BEARISH":
        ema_score = 30 - min(30, abs(ema20.distance_pct or 0) * 10)
    ema_score = max(0, min(100, ema_score))
    
    # Momentum score
    momentum_score = 50 + max(-50, min(50, mom_20d * 10))
    momentum_score = max(0, min(100, momentum_score))
    
    # SR score (trend-aware)
    sr_score = calculate_sr_score(nearest_support, nearest_resistance, trend)
    
    # Channel score (clamped)
    if channel.is_valid and channel.width > 0:
        channel_position = (current_price - channel.lower) / channel.width
        channel_position = max(0, min(1, channel_position))  # Clamp 0-1
        channel_score = channel_position * 100
    else:
        channel_score = 50
    channel_score = max(0, min(100, channel_score))
    
    # Volume score
    volume_score = 70 if volume_confirmed else 40
    
    # Weighted trend strength
    trend_strength = int(
        ema_score * profile["ema_weight"] +
        momentum_score * profile["momentum_weight"] +
        sr_score * profile["sr_weight"] +
        volume_score * profile["volume_weight"] +
        channel_score * profile["channel_weight"]
    )
    trend_strength = max(0, min(100, trend_strength))
    
    # ========== CONFLICT DETECTION ==========
    conflict = detect_conflicts(
        trend_strength, momentum_score, volume_confirmed, 
        rsi_divergence, mtf_alignment
    )
    
    # ========== FINAL CONFIDENCE ==========
    confidence = int(trend_strength * data_quality * (1 - conflict.penalty))
    confidence = max(0, min(100, confidence))
    
    # ========== BUILD RESULT ==========
    result = TrendAnalysisResult(
        symbol=symbol,
        current_price=round(current_price, 2),
        timestamp=datetime.utcnow().isoformat() + "Z",
        data_quality=round(data_quality, 2),
        
        trend=trend.value,
        trend_strength=trend_strength,
        confidence=confidence,
        
        ema20=ema20,
        ema50=ema50,
        ema200=ema200,
        ema_alignment=ema_alignment,
        
        channel=channel,
        
        nearest_support=nearest_support,
        nearest_resistance=nearest_resistance,
        sr_levels=supports[:3] + resistances[:3],
        
        atr_14=round(atr_14, 2) if atr_14 else None,
        volatility_pct=round(volatility_pct, 2) if volatility_pct else None,
        volatility_level=volatility_level.value,
        
        rsi_14=round(rsi_14, 1) if rsi_14 else None,
        rsi_divergence=rsi_divergence,
        momentum_5d=round(mom_5d, 2),
        momentum_10d=round(mom_10d, 2),
        momentum_20d=round(mom_20d, 2),
        
        volume_confirmed=volume_confirmed,
        obv_trend=obv_trend,
        
        daily_trend=daily_trend.value,
        hourly_trend=hourly_trend,
        mtf_alignment=mtf_alignment,
        
        conflict=conflict
    )
    
    # Cache result (5 min TTL)
    set_cached(cache_key, result, ttl=300)
    
    return result


# ========== SIMPLE WRAPPER FOR API ==========

async def get_trend_analysis_dict(symbol: str, include_hourly: bool = False) -> dict:
    """Wrapper that returns dict for API response"""
    result = await run_trend_analysis(symbol, include_hourly)
    return result.to_dict()
