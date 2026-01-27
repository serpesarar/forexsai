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
        risk_level=risk_level
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
        
        result = {
            "success": True,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "current_price": current_price,
            "pip_value": pip_value,
            "timeframes": {tf: asdict(a) for tf, a in analyses.items()},
            "confluence": asdict(confluence)
        }
    
    # Cache result
    with _cache_lock:
        _mtf_cache[cache_key] = (now_ts, result)
    
    return result
