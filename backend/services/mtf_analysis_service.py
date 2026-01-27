"""
Multi-Timeframe Technical Analysis Service
==========================================
Provides comprehensive technical analysis across multiple timeframes:
- M1, M5, M15, M30, H1, H4, D1
- ATR-based dynamic thresholds
- Bollinger Bands
- Volume analysis
- MTF Confluence scoring
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Literal, Optional, Dict, Any
from threading import Lock
import numpy as np

from services.data_fetcher import fetch_eod_candles, fetch_intraday_candles, fetch_latest_price


# Cache for MTF analysis results
_mtf_cache: Dict[str, tuple[float, dict]] = {}  # key -> (timestamp, data)
_cache_lock = Lock()
CACHE_TTL_SECONDS = 30


Timeframe = Literal["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
Trend = Literal["BULLISH", "BEARISH", "NEUTRAL"]
Signal = Literal["STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"]


@dataclass
class EMAData:
    ema20: float
    ema50: float
    ema200: float
    ema20_distance: float  # pips from current price
    ema50_distance: float
    ema200_distance: float
    price_above_ema20: bool
    price_above_ema50: bool
    price_above_ema200: bool


@dataclass
class BollingerBands:
    upper: float
    middle: float  # SMA20
    lower: float
    bandwidth: float  # (upper - lower) / middle
    percent_b: float  # (price - lower) / (upper - lower)
    squeeze: bool  # bandwidth < 0.1 indicates low volatility


@dataclass
class ATRData:
    atr14: float
    atr_percent: float  # ATR as % of price
    volatility_level: Literal["LOW", "NORMAL", "HIGH", "EXTREME"]
    dynamic_sl_pips: float  # Suggested SL based on ATR
    dynamic_tp_pips: float  # Suggested TP based on ATR


@dataclass
class VolumeAnalysis:
    current_volume: float
    avg_volume_20: float
    volume_ratio: float  # current / avg
    volume_trend: Literal["INCREASING", "DECREASING", "STABLE"]
    volume_confirmation: bool  # True if volume supports price movement


@dataclass
class SupportResistance:
    price: float
    kind: Literal["support", "resistance"]
    strength: float  # 0-1
    distance_pips: float
    touches: int


@dataclass
class TimeframeAnalysis:
    timeframe: Timeframe
    current_price: float
    trend: Trend
    signal: Signal
    confidence: float  # 0-100
    
    ema: EMAData
    bollinger: BollingerBands
    atr: ATRData
    volume: VolumeAnalysis
    
    rsi14: float
    macd_signal: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    
    supports: List[SupportResistance]
    resistances: List[SupportResistance]
    
    # Dynamic thresholds based on ATR
    max_pip_threshold: float


@dataclass
class MarketRegime:
    """Market regime detection using ADX + DI + Correlation"""
    regime: Literal["TRENDING", "RANGING", "VOLATILE"]
    adx: float  # Average Directional Index (0-100)
    plus_di: float  # +DI (Bullish pressure)
    minus_di: float  # -DI (Bearish pressure)
    trend_strength: Literal["WEAK", "MODERATE", "STRONG", "VERY_STRONG"]
    trend_direction: Optional[Trend]
    di_spread: float  # |+DI - -DI| - trend confirmation
    confidence_level: Literal["HIGH_CONFIDENCE", "LOW_CONFIDENCE", "CONFLICTING"]  # Based on DI spread
    regime_quality: float  # 0-100 quality score


@dataclass
class PriceAction:
    """Price action and market structure analysis with liquidity detection"""
    structure: Literal["HH_HL", "LL_LH", "RANGING", "CHOPPY"]  # Higher Highs/Lows or Lower
    swing_highs: List[float]
    swing_lows: List[float]
    last_swing_high: float
    last_swing_low: float
    break_of_structure: bool  # Recent BOS detected
    change_of_character: bool  # CHoCH detected
    liquidity_sweep: bool  # Fakeout trap detected
    equal_highs_count: int  # Liquidity pool indicator (3+ = strong)
    equal_lows_count: int  # Liquidity pool indicator
    structure_quality: Literal["VALID_BREAKOUT", "FAKEOUT_TRAP", "CHOPPY", "AWAITING_CONFIRMATION"]


@dataclass
class VolumeProfile:
    """Volume Profile analysis - institutional grade with HVN S/R"""
    poc: float  # Point of Control - highest volume price
    value_area_high: float  # Upper boundary of 70% volume
    value_area_low: float  # Lower boundary of 70% volume
    high_volume_nodes: List[float]  # Significant volume levels (TRUE S/R)
    low_volume_nodes: List[float]  # Gaps in volume - easy to pass
    hvn_resistances: List[float]  # HVN with price rejection = real resistance
    hvn_supports: List[float]  # HVN with price rejection = real support
    poc_is_relevant: bool  # Is current price near POC?


@dataclass  
class PivotPoints:
    """Fibonacci Pivot Points for S/R (more accurate than classic)"""
    pivot: float  # Central pivot
    r1: float  # Resistance 1 (0.382 Fib)
    r2: float  # Resistance 2 (0.618 Fib) - STRONGEST
    r3: float  # Resistance 3 (1.0 Fib)
    s1: float  # Support 1 (0.382 Fib)
    s2: float  # Support 2 (0.618 Fib) - STRONGEST
    s3: float  # Support 3 (1.0 Fib)
    timeframe: Literal["DAILY", "WEEKLY"]
    pivot_type: Literal["FIBONACCI", "CLASSIC", "CAMARILLA"]


@dataclass
class CorrelationData:
    """Multi-asset correlation analysis with weighted confluence"""
    dxy_correlation: float  # Dollar Index correlation (-0.85 for XAUUSD)
    dxy_trend: Trend
    dxy_strength: float  # 0-100 signal strength
    vix_level: float  # Volatility Index
    vix_regime: Literal["LOW", "NORMAL", "HIGH", "EXTREME"]
    bond_yield_trend: Trend  # US10Y
    bond_yield_level: float  # Current yield %
    spx_trend: Trend  # S&P 500 trend (risk-on/off)
    correlation_confirms: bool  # Does correlation support signal?
    confluence_score: float  # -1.0 to 1.0 weighted score
    conflicting_signals: List[str]  # Which assets conflict?


@dataclass
class PositionSizing:
    """Volatility-adjusted position sizing with correlation risk"""
    recommended_risk_percent: float  # % of account to risk (dynamic)
    base_risk_percent: float  # Before adjustments
    volatility_adjustment: float  # Multiplier based on ATR
    correlation_adjustment: float  # Reduction for correlated positions
    stop_loss_pips: float
    take_profit_pips: float
    risk_reward_ratio: float
    position_size_lots: float  # For $10,000 account
    max_loss_usd: float
    potential_profit_usd: float
    session: Literal["ASIA", "LONDON", "NEW_YORK", "OVERLAP"]
    session_volatility: Literal["LOW", "NORMAL", "HIGH", "EXTREME"]
    high_impact_event: Optional[str]  # NFP, FED, CPI etc.


@dataclass
class MTFConfluence:
    overall_signal: Signal
    overall_confidence: float
    bullish_count: int
    bearish_count: int
    neutral_count: int
    
    strongest_timeframe: Timeframe
    weakest_timeframe: Timeframe
    
    alignment_score: float  # 0-100, how aligned are all timeframes
    
    recommendation: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    
    # New fields
    market_regime: Optional[MarketRegime]
    price_action: Optional[PriceAction]
    volume_profile: Optional[VolumeProfile]
    pivot_points: Optional[PivotPoints]
    correlation: Optional[CorrelationData]
    position_sizing: Optional[PositionSizing]


def _get_pip_value(symbol: str) -> float:
    """Get pip value for symbol"""
    symbol_upper = (symbol or "").upper()
    if "XAU" in symbol_upper:
        return 0.1
    elif "NDX" in symbol_upper or "NAS" in symbol_upper:
        return 1.0
    elif "JPY" in symbol_upper:
        return 0.01
    else:
        return 0.0001


def _ema(values: np.ndarray, period: int) -> float:
    """Calculate Exponential Moving Average"""
    if len(values) < period:
        return float(values[-1]) if len(values) else 0.0
    alpha = 2.0 / (period + 1.0)
    ema = float(values[0])
    for v in values[1:]:
        ema = alpha * float(v) + (1 - alpha) * ema
    return float(ema)


def _sma(values: np.ndarray, period: int) -> float:
    """Calculate Simple Moving Average"""
    if len(values) < period:
        return float(np.mean(values)) if len(values) else 0.0
    return float(np.mean(values[-period:]))


def _rsi(values: np.ndarray, period: int = 14) -> float:
    """Calculate Relative Strength Index"""
    if len(values) < period + 1:
        return 50.0
    diffs = np.diff(values)
    gains = np.where(diffs > 0, diffs, 0.0)
    losses = np.where(diffs < 0, -diffs, 0.0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:]) + 1e-9
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return float(np.clip(rsi, 0.0, 100.0))


def _atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """Calculate Average True Range"""
    if len(closes) < period + 1:
        return float(np.mean(highs - lows)) if len(highs) else 0.0
    
    tr_list = []
    for i in range(1, len(closes)):
        high_low = highs[i] - lows[i]
        high_close = abs(highs[i] - closes[i-1])
        low_close = abs(lows[i] - closes[i-1])
        tr = max(high_low, high_close, low_close)
        tr_list.append(tr)
    
    if len(tr_list) < period:
        return float(np.mean(tr_list)) if tr_list else 0.0
    
    return float(np.mean(tr_list[-period:]))


def _bollinger_bands(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> tuple[float, float, float]:
    """Calculate Bollinger Bands: upper, middle, lower"""
    if len(closes) < period:
        if len(closes) == 0:
            return 0.0, 0.0, 0.0
        mean = float(np.mean(closes))
        return mean, mean, mean
    
    recent = closes[-period:]
    middle = float(np.mean(recent))
    std = float(np.std(recent))
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    
    return upper, middle, lower


def _adx(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> tuple[float, float, float]:
    """
    Calculate Average Directional Index (ADX) with +DI and -DI.
    Returns: (adx, plus_di, minus_di)
    """
    if len(closes) < period + 1:
        return 25.0, 50.0, 50.0  # Neutral defaults
    
    # Calculate True Range and Directional Movement
    tr_list = []
    plus_dm_list = []
    minus_dm_list = []
    
    for i in range(1, len(closes)):
        high_low = highs[i] - lows[i]
        high_close = abs(highs[i] - closes[i-1])
        low_close = abs(lows[i] - closes[i-1])
        tr = max(high_low, high_close, low_close)
        tr_list.append(tr)
        
        # +DM and -DM
        up_move = highs[i] - highs[i-1]
        down_move = lows[i-1] - lows[i]
        
        plus_dm = up_move if (up_move > down_move and up_move > 0) else 0
        minus_dm = down_move if (down_move > up_move and down_move > 0) else 0
        
        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)
    
    if len(tr_list) < period:
        return 25.0, 50.0, 50.0
    
    # Smoothed averages
    tr_smooth = float(np.mean(tr_list[-period:]))
    plus_dm_smooth = float(np.mean(plus_dm_list[-period:]))
    minus_dm_smooth = float(np.mean(minus_dm_list[-period:]))
    
    # +DI and -DI
    plus_di = (plus_dm_smooth / tr_smooth * 100) if tr_smooth > 0 else 50
    minus_di = (minus_dm_smooth / tr_smooth * 100) if tr_smooth > 0 else 50
    
    # DX and ADX
    di_sum = plus_di + minus_di
    dx = abs(plus_di - minus_di) / di_sum * 100 if di_sum > 0 else 0
    
    # Simple ADX (average of recent DX values)
    adx = dx  # Simplified - for full ADX would need smoothing
    
    return float(adx), float(plus_di), float(minus_di)


def _detect_market_regime(
    highs: np.ndarray, 
    lows: np.ndarray, 
    closes: np.ndarray,
    atr: float
) -> MarketRegime:
    """
    Detect market regime using ADX + DI spread.
    
    Critical fix: ADX alone doesn't show direction, need DI spread confirmation.
    ADX=50 with +DI≈-DI means SIDE MARKET, not strong trend!
    """
    adx, plus_di, minus_di = _adx(highs, lows, closes, 14)
    
    # DI spread - the key to TRUE trend detection
    di_spread = abs(plus_di - minus_di)
    
    # Determine trend strength based on BOTH ADX and DI spread
    if adx < 20:
        trend_strength = "WEAK"
        regime = "RANGING"
    elif adx < 30:
        trend_strength = "MODERATE" if di_spread > 10 else "WEAK"
        regime = "TRENDING" if di_spread > 10 else "RANGING"
    elif adx < 50:
        trend_strength = "STRONG" if di_spread > 15 else "MODERATE"
        regime = "TRENDING" if di_spread > 10 else "RANGING"
    else:
        trend_strength = "VERY_STRONG" if di_spread > 20 else "STRONG"
        regime = "TRENDING" if di_spread > 15 else "RANGING"
    
    # Check for high volatility (ATR spike)
    historical_atr = _atr(highs[:-20], lows[:-20], closes[:-20], 14) if len(closes) > 34 else atr
    if historical_atr > 0 and atr / historical_atr > 2.0:
        regime = "VOLATILE"
    
    # Trend direction based on DI
    trend_direction: Optional[Trend] = None
    if regime == "TRENDING" and di_spread > 5:
        if plus_di > minus_di:
            trend_direction = "BULLISH"
        else:
            trend_direction = "BEARISH"
    
    # Confidence level based on DI spread
    if di_spread > 20 and adx > 30:
        confidence_level = "HIGH_CONFIDENCE"
    elif di_spread > 10 and adx > 20:
        confidence_level = "LOW_CONFIDENCE"
    else:
        confidence_level = "CONFLICTING"
    
    # Regime quality score (0-100)
    regime_quality = min(100, (adx * 0.5) + (di_spread * 2.5))
    
    return MarketRegime(
        regime=regime,
        adx=round(adx, 2),
        plus_di=round(plus_di, 2),
        minus_di=round(minus_di, 2),
        trend_strength=trend_strength,
        trend_direction=trend_direction,
        di_spread=round(di_spread, 2),
        confidence_level=confidence_level,
        regime_quality=round(regime_quality, 1)
    )


def _detect_price_action(
    highs: np.ndarray, 
    lows: np.ndarray, 
    closes: np.ndarray
) -> PriceAction:
    """
    Detect market structure with liquidity sweep and equal highs/lows detection.
    
    Critical: BOS alone doesn't confirm breakout - need to check for fakeout traps.
    Equal highs/lows (3+) indicate liquidity pools where market makers hunt stops.
    """
    if len(closes) < 20:
        return PriceAction(
            structure="CHOPPY",
            swing_highs=[],
            swing_lows=[],
            last_swing_high=float(highs[-1]) if len(highs) else 0,
            last_swing_low=float(lows[-1]) if len(lows) else 0,
            break_of_structure=False,
            change_of_character=False,
            liquidity_sweep=False,
            equal_highs_count=0,
            equal_lows_count=0,
            structure_quality="CHOPPY"
        )
    
    # Find swing highs and lows (fractal method)
    swing_highs = []
    swing_lows = []
    swing_high_indices = []
    swing_low_indices = []
    period = 3
    
    for i in range(period, len(closes) - period):
        if highs[i] == max(highs[i-period:i+period+1]):
            swing_highs.append(float(highs[i]))
            swing_high_indices.append(i)
        if lows[i] == min(lows[i-period:i+period+1]):
            swing_lows.append(float(lows[i]))
            swing_low_indices.append(i)
    
    # Get last 5 swings for better analysis
    recent_highs = swing_highs[-5:] if len(swing_highs) >= 5 else swing_highs
    recent_lows = swing_lows[-5:] if len(swing_lows) >= 5 else swing_lows
    
    # Equal highs/lows detection (liquidity pools)
    atr = float(np.mean(highs[-14:] - lows[-14:])) if len(highs) >= 14 else 1.0
    tolerance = atr * 0.3  # Within 30% of ATR = "equal"
    
    equal_highs_count = 0
    equal_lows_count = 0
    
    if len(recent_highs) >= 2:
        for i in range(len(recent_highs)):
            for j in range(i+1, len(recent_highs)):
                if abs(recent_highs[i] - recent_highs[j]) < tolerance:
                    equal_highs_count += 1
    
    if len(recent_lows) >= 2:
        for i in range(len(recent_lows)):
            for j in range(i+1, len(recent_lows)):
                if abs(recent_lows[i] - recent_lows[j]) < tolerance:
                    equal_lows_count += 1
    
    # Determine structure
    structure = "CHOPPY"
    bos = False
    choch = False
    liquidity_sweep = False
    
    if len(recent_highs) >= 2 and len(recent_lows) >= 2:
        hh = all(recent_highs[i] < recent_highs[i+1] for i in range(len(recent_highs)-1))
        hl = all(recent_lows[i] < recent_lows[i+1] for i in range(len(recent_lows)-1))
        lh = all(recent_highs[i] > recent_highs[i+1] for i in range(len(recent_highs)-1))
        ll = all(recent_lows[i] > recent_lows[i+1] for i in range(len(recent_lows)-1))
        
        if hh and hl:
            structure = "HH_HL"
        elif lh and ll:
            structure = "LL_LH"
        else:
            structure = "RANGING"
        
        # Break of Structure detection
        current_price = float(closes[-1])
        prev_close = float(closes[-2]) if len(closes) >= 2 else current_price
        
        if len(recent_lows) >= 2:
            if current_price < recent_lows[-2]:
                bos = True
                if structure == "HH_HL":
                    choch = True
                # Liquidity sweep: broke level but came back
                if prev_close > recent_lows[-2] and current_price > recent_lows[-2] * 0.998:
                    liquidity_sweep = True
        
        if len(recent_highs) >= 2:
            if current_price > recent_highs[-2]:
                bos = True
                if structure == "LL_LH":
                    choch = True
                # Liquidity sweep: broke level but came back
                if prev_close < recent_highs[-2] and current_price < recent_highs[-2] * 1.002:
                    liquidity_sweep = True
    
    # Structure quality assessment
    if bos and not choch and not liquidity_sweep and equal_highs_count < 3 and equal_lows_count < 3:
        structure_quality = "VALID_BREAKOUT"
    elif bos and liquidity_sweep:
        structure_quality = "FAKEOUT_TRAP"
    elif equal_highs_count >= 3 or equal_lows_count >= 3:
        structure_quality = "AWAITING_CONFIRMATION"  # Liquidity pool nearby
    elif structure == "CHOPPY" or structure == "RANGING":
        structure_quality = "CHOPPY"
    else:
        structure_quality = "AWAITING_CONFIRMATION"
    
    return PriceAction(
        structure=structure,
        swing_highs=recent_highs[-3:],
        swing_lows=recent_lows[-3:],
        last_swing_high=recent_highs[-1] if recent_highs else float(highs[-1]),
        last_swing_low=recent_lows[-1] if recent_lows else float(lows[-1]),
        break_of_structure=bos,
        change_of_character=choch,
        liquidity_sweep=liquidity_sweep,
        equal_highs_count=equal_highs_count,
        equal_lows_count=equal_lows_count,
        structure_quality=structure_quality
    )


def _calculate_volume_profile(
    closes: np.ndarray, 
    highs: np.ndarray,
    lows: np.ndarray,
    volumes: np.ndarray, 
    num_bins: int = 20
) -> VolumeProfile:
    """
    Calculate Volume Profile with HVN-based S/R detection.
    
    Critical: POC is NOT resistance. HVN with price rejection = TRUE S/R.
    """
    current_price = float(closes[-1]) if len(closes) else 0
    
    if len(closes) < 20 or len(volumes) < 20:
        return VolumeProfile(
            poc=current_price,
            value_area_high=current_price,
            value_area_low=current_price,
            high_volume_nodes=[],
            low_volume_nodes=[],
            hvn_resistances=[],
            hvn_supports=[],
            poc_is_relevant=False
        )
    
    price_min = float(np.min(lows))
    price_max = float(np.max(highs))
    bin_size = (price_max - price_min) / num_bins if price_max > price_min else 1
    
    # Create bins with rejection tracking
    volume_by_price = {}
    rejection_count = {}  # Track price rejections
    
    for i in range(len(closes)):
        bin_idx = int((closes[i] - price_min) / bin_size) if bin_size > 0 else 0
        bin_idx = min(bin_idx, num_bins - 1)
        bin_price = price_min + (bin_idx + 0.5) * bin_size
        
        if bin_price not in volume_by_price:
            volume_by_price[bin_price] = 0
            rejection_count[bin_price] = 0
        volume_by_price[bin_price] += volumes[i]
        
        # Check for rejection (wick) at this level
        upper_wick = highs[i] - max(closes[i], closes[i-1] if i > 0 else closes[i])
        lower_wick = min(closes[i], closes[i-1] if i > 0 else closes[i]) - lows[i]
        avg_body = abs(closes[i] - (closes[i-1] if i > 0 else closes[i]))
        
        if upper_wick > avg_body * 1.5:  # Rejection from above
            rejection_count[bin_price] += 1
        if lower_wick > avg_body * 1.5:  # Rejection from below
            rejection_count[bin_price] += 1
    
    if not volume_by_price:
        return VolumeProfile(
            poc=current_price, value_area_high=current_price, value_area_low=current_price,
            high_volume_nodes=[], low_volume_nodes=[], hvn_resistances=[], hvn_supports=[],
            poc_is_relevant=False
        )
    
    # POC: highest volume price
    poc = max(volume_by_price.keys(), key=lambda k: volume_by_price[k])
    
    # Value Area: 70% of total volume
    total_volume = sum(volume_by_price.values())
    sorted_bins = sorted(volume_by_price.items(), key=lambda x: x[1], reverse=True)
    
    running_volume = 0
    value_area_prices = []
    for price, vol in sorted_bins:
        running_volume += vol
        value_area_prices.append(price)
        if running_volume >= total_volume * 0.7:
            break
    
    value_area_high = max(value_area_prices) if value_area_prices else poc
    value_area_low = min(value_area_prices) if value_area_prices else poc
    
    # High/Low volume nodes
    avg_volume = total_volume / len(volume_by_price)
    high_volume_nodes = [p for p, v in volume_by_price.items() if v > avg_volume * 1.5]
    low_volume_nodes = [p for p, v in volume_by_price.items() if v < avg_volume * 0.5]
    
    # HVN with rejections = TRUE S/R levels
    hvn_resistances = []
    hvn_supports = []
    
    for hvn in high_volume_nodes:
        if rejection_count.get(hvn, 0) >= 2:  # At least 2 rejections
            if hvn > current_price:
                hvn_resistances.append(hvn)
            else:
                hvn_supports.append(hvn)
    
    # Is POC relevant? (price within 1% of POC)
    atr = float(np.mean(highs[-14:] - lows[-14:])) if len(highs) >= 14 else bin_size
    poc_is_relevant = abs(current_price - poc) < atr * 0.5
    
    return VolumeProfile(
        poc=round(poc, 5),
        value_area_high=round(value_area_high, 5),
        value_area_low=round(value_area_low, 5),
        high_volume_nodes=[round(p, 5) for p in sorted(high_volume_nodes)[:5]],
        low_volume_nodes=[round(p, 5) for p in sorted(low_volume_nodes)[:5]],
        hvn_resistances=[round(p, 5) for p in sorted(hvn_resistances)[:3]],
        hvn_supports=[round(p, 5) for p in sorted(hvn_supports, reverse=True)[:3]],
        poc_is_relevant=poc_is_relevant
    )


def _calculate_pivot_points(
    high: float, 
    low: float, 
    close: float,
    timeframe: Literal["DAILY", "WEEKLY"] = "DAILY",
    pivot_type: Literal["FIBONACCI", "CLASSIC", "CAMARILLA"] = "FIBONACCI"
) -> PivotPoints:
    """
    Calculate Fibonacci pivot points (more accurate for XAUUSD/NASDAQ).
    
    Fibonacci pivots use 0.382, 0.618, 1.0 ratios instead of classic formula.
    R2/S2 at 0.618 are the STRONGEST levels.
    """
    pivot = (high + low + close) / 3
    range_hl = high - low
    
    if pivot_type == "FIBONACCI":
        # Fibonacci Pivots - stronger for volatile instruments
        r1 = pivot + (range_hl * 0.382)
        r2 = pivot + (range_hl * 0.618)  # STRONGEST resistance
        r3 = pivot + (range_hl * 1.000)
        
        s1 = pivot - (range_hl * 0.382)
        s2 = pivot - (range_hl * 0.618)  # STRONGEST support
        s3 = pivot - (range_hl * 1.000)
    elif pivot_type == "CAMARILLA":
        # Camarilla - good for intraday
        r1 = close + (range_hl * 1.1 / 12)
        r2 = close + (range_hl * 1.1 / 6)
        r3 = close + (range_hl * 1.1 / 4)
        
        s1 = close - (range_hl * 1.1 / 12)
        s2 = close - (range_hl * 1.1 / 6)
        s3 = close - (range_hl * 1.1 / 4)
    else:  # CLASSIC
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + range_hl
        s2 = pivot - range_hl
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
    
    return PivotPoints(
        pivot=round(pivot, 5),
        r1=round(r1, 5),
        r2=round(r2, 5),
        r3=round(r3, 5),
        s1=round(s1, 5),
        s2=round(s2, 5),
        s3=round(s3, 5),
        timeframe=timeframe,
        pivot_type=pivot_type
    )


def _get_current_session() -> tuple[Literal["ASIA", "LONDON", "NEW_YORK", "OVERLAP"], Literal["LOW", "NORMAL", "HIGH", "EXTREME"]]:
    """Determine current trading session and expected volatility"""
    from datetime import datetime
    utc_hour = datetime.utcnow().hour
    
    # Session hours (UTC)
    # Asia: 22:00 - 07:00 UTC
    # London: 07:00 - 16:00 UTC
    # New York: 12:00 - 21:00 UTC
    # Overlap (London+NY): 12:00 - 16:00 UTC
    
    if 12 <= utc_hour < 16:
        return "OVERLAP", "EXTREME"  # Highest volatility
    elif 12 <= utc_hour < 21:
        return "NEW_YORK", "HIGH"
    elif 7 <= utc_hour < 16:
        return "LONDON", "HIGH"
    else:
        return "ASIA", "LOW"


def _check_high_impact_event() -> Optional[str]:
    """Check for high impact economic events (simplified)"""
    from datetime import datetime
    today = datetime.utcnow()
    day_of_week = today.weekday()  # 0=Monday
    day_of_month = today.day
    
    # First Friday of month = NFP
    if day_of_week == 4 and day_of_month <= 7:
        return "NFP_DAY"
    
    # FOMC typically 3rd Wednesday (simplified check)
    if day_of_week == 2 and 15 <= day_of_month <= 21:
        return "FOMC_POTENTIAL"
    
    # CPI typically 10th-15th of month
    if 10 <= day_of_month <= 15:
        return "CPI_WEEK"
    
    return None


def _calculate_position_sizing(
    signal_confidence: float,
    atr_pips: float,
    pip_value: float,
    current_price: float = 0,
    account_size: float = 10000,
    base_risk_percent: float = 2.0,
    has_correlated_position: bool = False
) -> PositionSizing:
    """
    Calculate volatility and session-adjusted position sizing.
    
    Key adjustments:
    - High volatility (ATR spike) = reduce risk
    - Asia session = reduce risk (low liquidity)
    - NFP/Fed days = reduce risk significantly
    - Correlated positions = reduce risk
    """
    # Get session info
    session, session_volatility = _get_current_session()
    high_impact_event = _check_high_impact_event()
    
    # Base risk from confidence
    if signal_confidence >= 80:
        risk_percent = base_risk_percent
    elif signal_confidence >= 60:
        risk_percent = base_risk_percent * 0.75
    elif signal_confidence >= 40:
        risk_percent = base_risk_percent * 0.5
    else:
        risk_percent = base_risk_percent * 0.25
    
    # Volatility adjustment
    vol_pct = (atr_pips * pip_value / current_price * 100) if current_price > 0 else 1.0
    if vol_pct > 2.5:
        volatility_adjustment = 0.5  # Cut risk in half
    elif vol_pct > 1.5:
        volatility_adjustment = 0.75
    elif vol_pct < 0.5:
        volatility_adjustment = 1.25  # Can increase slightly in low vol
    else:
        volatility_adjustment = 1.0
    
    # Session adjustment
    if session == "ASIA":
        volatility_adjustment *= 0.6  # Low liquidity = higher slippage risk
    elif session == "OVERLAP":
        volatility_adjustment *= 0.9  # High volatility but good liquidity
    
    # High impact event adjustment
    if high_impact_event == "NFP_DAY":
        volatility_adjustment *= 0.3  # Very risky
    elif high_impact_event == "FOMC_POTENTIAL":
        volatility_adjustment *= 0.5
    elif high_impact_event == "CPI_WEEK":
        volatility_adjustment *= 0.7
    
    # Correlation adjustment
    correlation_adjustment = 0.6 if has_correlated_position else 1.0
    
    # Final risk calculation
    final_risk = risk_percent * volatility_adjustment * correlation_adjustment
    final_risk = max(0.25, min(3.0, final_risk))  # Clamp between 0.25% and 3%
    
    # SL/TP based on ATR
    stop_loss_pips = atr_pips * 1.5
    take_profit_pips = atr_pips * 2.5  # 1:1.67 R:R minimum
    risk_reward = take_profit_pips / stop_loss_pips if stop_loss_pips > 0 else 1.0
    
    # Position size calculation
    risk_amount = account_size * (final_risk / 100)
    pip_value_per_lot = 10 if pip_value == 0.1 else 1
    position_size_lots = risk_amount / (stop_loss_pips * pip_value_per_lot) if stop_loss_pips > 0 else 0.01
    
    max_loss = risk_amount
    potential_profit = max_loss * risk_reward
    
    return PositionSizing(
        recommended_risk_percent=round(final_risk, 2),
        base_risk_percent=round(risk_percent, 2),
        volatility_adjustment=round(volatility_adjustment, 2),
        correlation_adjustment=round(correlation_adjustment, 2),
        stop_loss_pips=round(stop_loss_pips, 1),
        take_profit_pips=round(take_profit_pips, 1),
        risk_reward_ratio=round(risk_reward, 2),
        position_size_lots=round(min(position_size_lots, 1.0), 2),
        max_loss_usd=round(max_loss, 2),
        potential_profit_usd=round(potential_profit, 2),
        session=session,
        session_volatility=session_volatility,
        high_impact_event=high_impact_event
    )


def _macd(closes: np.ndarray) -> tuple[float, float, str]:
    """Calculate MACD: macd_line, signal_line, crossover_signal"""
    if len(closes) < 26:
        return 0.0, 0.0, "NEUTRAL"
    
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd_line = ema12 - ema26
    
    # Calculate signal line (EMA9 of MACD)
    if len(closes) >= 35:
        macd_values = []
        for i in range(26, len(closes)):
            e12 = _ema(closes[:i+1], 12)
            e26 = _ema(closes[:i+1], 26)
            macd_values.append(e12 - e26)
        signal_line = _ema(np.array(macd_values), 9) if len(macd_values) >= 9 else macd_line
    else:
        signal_line = macd_line
    
    if macd_line > signal_line and macd_line > 0:
        signal = "BULLISH"
    elif macd_line < signal_line and macd_line < 0:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"
    
    return macd_line, signal_line, signal


def _detect_swing_levels(
    highs: np.ndarray, 
    lows: np.ndarray, 
    closes: np.ndarray, 
    current_price: float,
    pip_value: float
) -> tuple[List[SupportResistance], List[SupportResistance]]:
    """Detect support and resistance levels from swing points"""
    if len(closes) < 30:
        return [], []
    
    supports = []
    resistances = []
    period = 3
    
    # Find swing highs and lows
    swing_highs = []
    swing_lows = []
    
    for i in range(period, len(closes) - period):
        # Swing high
        if highs[i] == max(highs[i-period:i+period+1]):
            swing_highs.append(float(highs[i]))
        # Swing low
        if lows[i] == min(lows[i-period:i+period+1]):
            swing_lows.append(float(lows[i]))
    
    # Cluster similar levels
    def cluster_levels(levels: List[float], kind: str, tol: float) -> List[SupportResistance]:
        if not levels:
            return []
        levels_sorted = sorted(levels)
        clusters = []
        for lv in levels_sorted:
            if not clusters or abs(lv - np.mean(clusters[-1])) > tol:
                clusters.append([lv])
            else:
                clusters[-1].append(lv)
        
        result = []
        for c in clusters:
            price = float(np.mean(c))
            touches = len(c)
            strength = min(1.0, touches / 5.0)
            distance = (current_price - price) / pip_value
            result.append(SupportResistance(
                price=round(price, 5),
                kind=kind,
                strength=strength,
                distance_pips=round(distance, 1),
                touches=touches
            ))
        return result
    
    tol = current_price * 0.003  # 0.3% tolerance
    
    supports = cluster_levels(
        [l for l in swing_lows if l <= current_price], 
        "support", 
        tol
    )
    resistances = cluster_levels(
        [h for h in swing_highs if h >= current_price], 
        "resistance", 
        tol
    )
    
    # Sort by distance and take nearest 3
    supports = sorted(supports, key=lambda x: abs(x.distance_pips))[:3]
    resistances = sorted(resistances, key=lambda x: abs(x.distance_pips))[:3]
    
    return supports, resistances


def _calculate_signal(
    trend: Trend,
    rsi: float,
    macd_signal: str,
    price_above_ema20: bool,
    price_above_ema50: bool,
    price_above_ema200: bool,
    volume_confirmation: bool,
    percent_b: float
) -> tuple[Signal, float]:
    """Calculate trading signal and confidence based on multiple indicators"""
    
    score = 0
    max_score = 8
    
    # Trend (+2 for strong trend)
    if trend == "BULLISH":
        score += 2
    elif trend == "BEARISH":
        score -= 2
    
    # EMA alignment (+1 each)
    if price_above_ema20:
        score += 1
    else:
        score -= 1
    if price_above_ema50:
        score += 1
    else:
        score -= 1
    if price_above_ema200:
        score += 1
    else:
        score -= 1
    
    # RSI
    if rsi > 70:
        score -= 1  # Overbought
    elif rsi < 30:
        score += 1  # Oversold (potential reversal)
    elif rsi > 50:
        score += 0.5
    else:
        score -= 0.5
    
    # MACD
    if macd_signal == "BULLISH":
        score += 1
    elif macd_signal == "BEARISH":
        score -= 1
    
    # Bollinger %B
    if percent_b > 0.8:
        score -= 0.5  # Near upper band
    elif percent_b < 0.2:
        score += 0.5  # Near lower band
    
    # Volume confirmation bonus
    if volume_confirmation:
        score = score * 1.1 if score > 0 else score * 0.9
    
    # Normalize to signal
    normalized = score / max_score
    
    if normalized >= 0.6:
        signal = "STRONG_BUY"
        confidence = 70 + (normalized * 30)
    elif normalized >= 0.2:
        signal = "BUY"
        confidence = 50 + (normalized * 40)
    elif normalized <= -0.6:
        signal = "STRONG_SELL"
        confidence = 70 + (abs(normalized) * 30)
    elif normalized <= -0.2:
        signal = "SELL"
        confidence = 50 + (abs(normalized) * 40)
    else:
        signal = "NEUTRAL"
        confidence = 30 + (abs(normalized) * 20)
    
    return signal, min(100, max(0, confidence))


def _get_volatility_level(atr_percent: float) -> Literal["LOW", "NORMAL", "HIGH", "EXTREME"]:
    """Determine volatility level from ATR percentage"""
    if atr_percent < 0.5:
        return "LOW"
    elif atr_percent < 1.5:
        return "NORMAL"
    elif atr_percent < 3.0:
        return "HIGH"
    else:
        return "EXTREME"


def _analyze_timeframe(
    symbol: str,
    timeframe: Timeframe,
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    volumes: np.ndarray,
    current_price: float,
    pip_value: float
) -> TimeframeAnalysis:
    """Analyze a single timeframe"""
    
    # EMA calculations
    ema20 = _ema(closes, 20)
    ema50 = _ema(closes, 50)
    ema200 = _ema(closes, 200)
    
    ema20_dist = (current_price - ema20) / pip_value
    ema50_dist = (current_price - ema50) / pip_value
    ema200_dist = (current_price - ema200) / pip_value
    
    ema_data = EMAData(
        ema20=round(ema20, 5),
        ema50=round(ema50, 5),
        ema200=round(ema200, 5),
        ema20_distance=round(ema20_dist, 1),
        ema50_distance=round(ema50_dist, 1),
        ema200_distance=round(ema200_dist, 1),
        price_above_ema20=current_price > ema20,
        price_above_ema50=current_price > ema50,
        price_above_ema200=current_price > ema200
    )
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = _bollinger_bands(closes)
    bb_width = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0
    bb_percent_b = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
    
    bollinger = BollingerBands(
        upper=round(bb_upper, 5),
        middle=round(bb_middle, 5),
        lower=round(bb_lower, 5),
        bandwidth=round(bb_width, 4),
        percent_b=round(bb_percent_b, 4),
        squeeze=bb_width < 0.02
    )
    
    # ATR
    atr14 = _atr(highs, lows, closes, 14)
    atr_percent = (atr14 / current_price) * 100 if current_price > 0 else 0
    vol_level = _get_volatility_level(atr_percent)
    
    # Dynamic SL/TP based on ATR (1.5x ATR for SL, 2x ATR for TP)
    atr_pips = atr14 / pip_value
    
    atr_data = ATRData(
        atr14=round(atr14, 5),
        atr_percent=round(atr_percent, 4),
        volatility_level=vol_level,
        dynamic_sl_pips=round(atr_pips * 1.5, 1),
        dynamic_tp_pips=round(atr_pips * 2.0, 1)
    )
    
    # Volume analysis
    avg_vol = _sma(volumes, 20) if len(volumes) >= 20 else float(np.mean(volumes)) if len(volumes) else 0
    current_vol = float(volumes[-1]) if len(volumes) else 0
    vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0
    
    # Volume trend (compare last 5 to previous 5)
    if len(volumes) >= 10:
        recent_vol = float(np.mean(volumes[-5:]))
        prev_vol = float(np.mean(volumes[-10:-5]))
        if recent_vol > prev_vol * 1.2:
            vol_trend = "INCREASING"
        elif recent_vol < prev_vol * 0.8:
            vol_trend = "DECREASING"
        else:
            vol_trend = "STABLE"
    else:
        vol_trend = "STABLE"
    
    # Volume confirmation: high volume on trend direction
    price_change = closes[-1] - closes[-2] if len(closes) >= 2 else 0
    vol_confirms = (vol_ratio > 1.2 and price_change > 0) or (vol_ratio > 1.2 and price_change < 0)
    
    volume_data = VolumeAnalysis(
        current_volume=round(current_vol, 2),
        avg_volume_20=round(avg_vol, 2),
        volume_ratio=round(vol_ratio, 2),
        volume_trend=vol_trend,
        volume_confirmation=vol_confirms
    )
    
    # RSI
    rsi14 = _rsi(closes, 14)
    
    # MACD
    _, _, macd_signal = _macd(closes)
    
    # Trend determination
    if current_price > ema20 > ema50 > ema200:
        trend = "BULLISH"
    elif current_price < ema20 < ema50 < ema200:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"
    
    # Support/Resistance
    supports, resistances = _detect_swing_levels(highs, lows, closes, current_price, pip_value)
    
    # Calculate signal
    signal, confidence = _calculate_signal(
        trend, rsi14, macd_signal,
        ema_data.price_above_ema20,
        ema_data.price_above_ema50,
        ema_data.price_above_ema200,
        vol_confirms,
        bb_percent_b
    )
    
    # Dynamic max pip threshold based on ATR
    # Use 3x ATR as the "significant move" threshold
    max_pip_threshold = round(atr_pips * 3, 1)
    
    return TimeframeAnalysis(
        timeframe=timeframe,
        current_price=round(current_price, 5),
        trend=trend,
        signal=signal,
        confidence=round(confidence, 1),
        ema=ema_data,
        bollinger=bollinger,
        atr=atr_data,
        volume=volume_data,
        rsi14=round(rsi14, 2),
        macd_signal=macd_signal,
        supports=supports,
        resistances=resistances,
        max_pip_threshold=max_pip_threshold
    )


def _calculate_mtf_confluence(analyses: Dict[Timeframe, TimeframeAnalysis]) -> MTFConfluence:
    """Calculate Multi-Timeframe Confluence score"""
    
    bullish = 0
    bearish = 0
    neutral = 0
    
    signal_weights = {
        "STRONG_BUY": 2,
        "BUY": 1,
        "NEUTRAL": 0,
        "SELL": -1,
        "STRONG_SELL": -2
    }
    
    timeframe_weights = {
        "M1": 0.5,
        "M5": 0.75,
        "M15": 1.0,
        "M30": 1.25,
        "H1": 1.5,
        "H4": 2.0,
        "D1": 2.5
    }
    
    weighted_score = 0
    total_weight = 0
    confidence_sum = 0
    
    strongest_tf = None
    strongest_conf = 0
    weakest_tf = None
    weakest_conf = 100
    
    for tf, analysis in analyses.items():
        weight = timeframe_weights.get(tf, 1.0)
        signal_score = signal_weights.get(analysis.signal, 0)
        
        weighted_score += signal_score * weight * (analysis.confidence / 100)
        total_weight += weight
        confidence_sum += analysis.confidence
        
        if analysis.signal in ["STRONG_BUY", "BUY"]:
            bullish += 1
        elif analysis.signal in ["STRONG_SELL", "SELL"]:
            bearish += 1
        else:
            neutral += 1
        
        if analysis.confidence > strongest_conf:
            strongest_conf = analysis.confidence
            strongest_tf = tf
        if analysis.confidence < weakest_conf:
            weakest_conf = analysis.confidence
            weakest_tf = tf
    
    # Normalize score
    if total_weight > 0:
        normalized_score = weighted_score / total_weight
    else:
        normalized_score = 0
    
    # Determine overall signal
    if normalized_score >= 0.6:
        overall_signal = "STRONG_BUY"
    elif normalized_score >= 0.2:
        overall_signal = "BUY"
    elif normalized_score <= -0.6:
        overall_signal = "STRONG_SELL"
    elif normalized_score <= -0.2:
        overall_signal = "SELL"
    else:
        overall_signal = "NEUTRAL"
    
    # Calculate alignment score (how unanimous are the signals)
    total_tf = len(analyses)
    max_alignment = max(bullish, bearish, neutral)
    alignment_score = (max_alignment / total_tf) * 100 if total_tf > 0 else 0
    
    # Overall confidence
    overall_confidence = (confidence_sum / total_tf) * (alignment_score / 100) if total_tf > 0 else 0
    
    # Risk level
    if alignment_score >= 80 and overall_confidence >= 70:
        risk_level = "LOW"
    elif alignment_score >= 50:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
    
    # Recommendation
    if overall_signal == "STRONG_BUY" and risk_level == "LOW":
        recommendation = "High-confidence BUY setup. All timeframes aligned bullish."
    elif overall_signal == "STRONG_SELL" and risk_level == "LOW":
        recommendation = "High-confidence SELL setup. All timeframes aligned bearish."
    elif overall_signal in ["BUY", "STRONG_BUY"]:
        recommendation = f"Bullish bias with {bullish}/{total_tf} timeframes supporting. Consider entry on pullback."
    elif overall_signal in ["SELL", "STRONG_SELL"]:
        recommendation = f"Bearish bias with {bearish}/{total_tf} timeframes supporting. Consider entry on rally."
    else:
        recommendation = "Mixed signals across timeframes. Wait for clearer setup or trade with reduced size."
    
    return MTFConfluence(
        overall_signal=overall_signal,
        overall_confidence=round(overall_confidence, 1),
        bullish_count=bullish,
        bearish_count=bearish,
        neutral_count=neutral,
        strongest_timeframe=strongest_tf or "M15",
        weakest_timeframe=weakest_tf or "M15",
        alignment_score=round(alignment_score, 1),
        recommendation=recommendation,
        risk_level=risk_level,
        market_regime=None,  # Will be set by caller
        price_action=None,
        volume_profile=None,
        pivot_points=None,
        correlation=None,
        position_sizing=None
    )


async def get_mtf_analysis(symbol: str, timeframe: Optional[Timeframe] = None) -> dict:
    """
    Get Multi-Timeframe Analysis for a symbol.
    
    If timeframe is specified, returns detailed analysis for that timeframe.
    If timeframe is None, returns analysis for all timeframes + MTF confluence.
    """
    
    cache_key = f"{symbol}:{timeframe or 'all'}"
    now_ts = datetime.utcnow().timestamp()
    
    # Check cache
    with _cache_lock:
        cached = _mtf_cache.get(cache_key)
        if cached and now_ts - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]
    
    pip_value = _get_pip_value(symbol)
    current_price = await fetch_latest_price(symbol)
    
    if current_price is None:
        return {"success": False, "error": "Could not fetch current price"}
    
    # Fetch daily candles for higher timeframes
    eod_candles = await fetch_eod_candles(symbol, limit=250)
    
    if not eod_candles:
        return {"success": False, "error": "Could not fetch OHLCV data"}
    
    # Convert to numpy arrays
    closes = np.array([c["close"] for c in eod_candles], dtype=float)
    highs = np.array([c.get("high", c["close"]) for c in eod_candles], dtype=float)
    lows = np.array([c.get("low", c["close"]) for c in eod_candles], dtype=float)
    volumes = np.array([c.get("volume", 0) for c in eod_candles], dtype=float)
    
    # For intraday, we'll simulate by using different lookback periods on daily data
    # In production, you'd fetch actual intraday data from your data provider
    
    timeframe_configs = {
        "M1": {"lookback": 20, "multiplier": 0.2},
        "M5": {"lookback": 30, "multiplier": 0.5},
        "M15": {"lookback": 50, "multiplier": 1.0},
        "M30": {"lookback": 75, "multiplier": 1.5},
        "H1": {"lookback": 100, "multiplier": 2.0},
        "H4": {"lookback": 150, "multiplier": 4.0},
        "D1": {"lookback": 220, "multiplier": 1.0},
    }
    
    if timeframe:
        # Single timeframe analysis
        config = timeframe_configs.get(timeframe, timeframe_configs["M15"])
        lookback = min(config["lookback"], len(closes))
        
        analysis = _analyze_timeframe(
            symbol, timeframe,
            closes[-lookback:],
            highs[-lookback:],
            lows[-lookback:],
            volumes[-lookback:],
            current_price,
            pip_value
        )
        
        result = {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": asdict(analysis)
        }
    else:
        # All timeframes + MTF confluence
        analyses = {}
        for tf, config in timeframe_configs.items():
            lookback = min(config["lookback"], len(closes))
            analyses[tf] = _analyze_timeframe(
                symbol, tf,
                closes[-lookback:],
                highs[-lookback:],
                lows[-lookback:],
                volumes[-lookback:],
                current_price,
                pip_value
            )
        
        confluence = _calculate_mtf_confluence(analyses)
        
        # Calculate advanced analysis components
        atr14 = _atr(highs, lows, closes, 14)
        atr_pips = atr14 / pip_value
        
        # Market Regime (ADX-based)
        market_regime = _detect_market_regime(highs, lows, closes, atr14)
        
        # Price Action Structure (HH/HL pattern)
        price_action = _detect_price_action(highs, lows, closes)
        
        # Volume Profile (POC, Value Area, HVN S/R)
        volume_profile = _calculate_volume_profile(closes, highs, lows, volumes)
        
        # Pivot Points (Fibonacci - from yesterday's OHLC)
        if len(highs) >= 2:
            pivot_points = _calculate_pivot_points(
                float(highs[-2]), 
                float(lows[-2]), 
                float(closes[-2]),
                "DAILY",
                "FIBONACCI"  # Use Fibonacci pivots for XAUUSD/NASDAQ
            )
        else:
            pivot_points = _calculate_pivot_points(current_price, current_price, current_price, "DAILY", "FIBONACCI")
        
        # Position Sizing (with volatility and session adjustments)
        position_sizing = _calculate_position_sizing(
            confluence.overall_confidence,
            atr_pips,
            pip_value,
            current_price,
            10000,  # Default account size
            2.0,    # Base risk percent
            False   # No correlated position check yet
        )
        
        # Update confluence with advanced data
        confluence.market_regime = market_regime
        confluence.price_action = price_action
        confluence.volume_profile = volume_profile
        confluence.pivot_points = pivot_points
        confluence.position_sizing = position_sizing
        
        # Multi-asset correlation analysis
        correlation_data = None
        if "XAU" in symbol.upper() or "NDX" in symbol.upper() or "NAS" in symbol.upper():
            try:
                # Weights for correlation scoring
                correlation_weights = {
                    "DXY": 0.35,   # Strongest for Gold
                    "VIX": 0.25,   # Risk sentiment
                    "US10Y": 0.20, # Bond yields
                    "SPX": 0.20    # Risk-on/off
                }
                
                confluence_score = 0.0
                conflicting_signals = []
                
                # DXY analysis (negative correlation with Gold)
                dxy_trend = "NEUTRAL"
                dxy_strength = 50.0
                try:
                    from services.ta_service import compute_ta_snapshot
                    dxy_data = await compute_ta_snapshot("DXY.INDX")
                    dxy_trend = dxy_data.get("trend", "NEUTRAL")
                    dxy_strength = dxy_data.get("confidence", 50)
                except Exception:
                    pass
                
                # DXY check: Gold bullish needs DXY bearish
                if "XAU" in symbol.upper():
                    if confluence.overall_signal in ["BUY", "STRONG_BUY"]:
                        if dxy_trend == "BEARISH":
                            confluence_score += correlation_weights["DXY"]
                        elif dxy_trend == "BULLISH":
                            confluence_score -= correlation_weights["DXY"]
                            conflicting_signals.append("DXY_BULLISH")
                    elif confluence.overall_signal in ["SELL", "STRONG_SELL"]:
                        if dxy_trend == "BULLISH":
                            confluence_score += correlation_weights["DXY"]
                        elif dxy_trend == "BEARISH":
                            confluence_score -= correlation_weights["DXY"]
                            conflicting_signals.append("DXY_BEARISH")
                
                # VIX analysis
                vix_price = 20.0
                try:
                    vix_data = await compute_ta_snapshot("VIX.INDX")
                    vix_price = vix_data.get("current_price", 20)
                except Exception:
                    pass
                
                vix_regime = "LOW" if vix_price < 15 else "NORMAL" if vix_price < 25 else "HIGH" if vix_price < 35 else "EXTREME"
                
                # High VIX = risk-off = Gold bullish usually
                if vix_regime in ["HIGH", "EXTREME"]:
                    if confluence.overall_signal in ["BUY", "STRONG_BUY"]:
                        confluence_score += correlation_weights["VIX"] * 0.5
                    else:
                        conflicting_signals.append("VIX_HIGH_BUT_BEARISH")
                
                # Determine if correlation confirms
                correlation_confirms = confluence_score > 0.3 and len(conflicting_signals) == 0
                
                correlation_data = CorrelationData(
                    dxy_correlation=-0.85 if "XAU" in symbol.upper() else -0.3,
                    dxy_trend=dxy_trend,
                    dxy_strength=dxy_strength,
                    vix_level=vix_price,
                    vix_regime=vix_regime,
                    bond_yield_trend="NEUTRAL",  # Would need US10Y data feed
                    bond_yield_level=4.5,  # Placeholder
                    spx_trend="NEUTRAL",  # Would need SPX data
                    correlation_confirms=correlation_confirms,
                    confluence_score=round(confluence_score, 2),
                    conflicting_signals=conflicting_signals
                )
                confluence.correlation = correlation_data
            except Exception:
                pass  # Correlation data optional
        
        result = {
            "success": True,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "current_price": current_price,
            "pip_value": pip_value,
            "timeframes": {tf: asdict(a) for tf, a in analyses.items()},
            "confluence": asdict(confluence),
            "advanced": {
                "market_regime": asdict(market_regime),
                "price_action": asdict(price_action),
                "volume_profile": asdict(volume_profile),
                "pivot_points": asdict(pivot_points),
                "position_sizing": asdict(position_sizing),
                "correlation": asdict(correlation_data) if correlation_data else None
            }
        }
    
    # Cache result
    with _cache_lock:
        _mtf_cache[cache_key] = (now_ts, result)
    
    return result
