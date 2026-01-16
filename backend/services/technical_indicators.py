"""
Technical Indicators Module
- EMA, RSI, ATR calculations with proper warmup periods
- Rolling MAD anomaly detection
- Robust data cleaning
"""

from __future__ import annotations
import numpy as np
from typing import Tuple, Optional


# ========== ANOMALY DETECTION (Rolling MAD) ==========

def rolling_mad(values: np.ndarray, window: int = 20) -> np.ndarray:
    """Rolling Median Absolute Deviation"""
    if len(values) < window:
        return np.zeros(len(values))
    
    mad = np.zeros(len(values))
    for i in range(window - 1, len(values)):
        window_data = values[i - window + 1:i + 1]
        median = np.median(window_data)
        mad[i] = np.median(np.abs(window_data - median))
    
    # Fill initial values
    mad[:window - 1] = mad[window - 1] if len(mad) > window - 1 else 0
    return mad


def detect_anomalies_returns(
    values: np.ndarray, 
    threshold: float = 3.0,
    window: int = 20
) -> np.ndarray:
    """
    Detect anomalies based on returns (pct change) using rolling MAD.
    Returns boolean mask where True = anomaly
    """
    if len(values) < 3:
        return np.zeros(len(values), dtype=bool)
    
    # Calculate returns
    returns = np.zeros(len(values))
    returns[1:] = (values[1:] - values[:-1]) / (values[:-1] + 1e-9)
    
    # Rolling MAD on returns
    mad = rolling_mad(returns, window)
    median_returns = np.zeros(len(returns))
    
    for i in range(window - 1, len(returns)):
        median_returns[i] = np.median(returns[i - window + 1:i + 1])
    median_returns[:window - 1] = median_returns[window - 1] if len(median_returns) > window - 1 else 0
    
    # Z-score like metric using MAD
    mad_scores = np.abs(returns - median_returns) / (mad * 1.4826 + 1e-9)  # 1.4826 for normal distribution
    
    return mad_scores > threshold


def clean_ohlc_data(
    opens: np.ndarray,
    highs: np.ndarray, 
    lows: np.ndarray,
    closes: np.ndarray,
    threshold: float = 3.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """
    Clean OHLC data using return-based anomaly detection.
    Uses winsorization (clamp to median ± k*MAD) instead of replacement.
    Returns: (clean_opens, clean_highs, clean_lows, clean_closes, quality_score)
    """
    if len(closes) < 5:
        return opens.copy(), highs.copy(), lows.copy(), closes.copy(), 1.0
    
    # Detect anomalies on closes
    anomalies = detect_anomalies_returns(closes, threshold)
    anomaly_count = np.sum(anomalies)
    
    # Winsorize anomalies
    clean_closes = closes.copy()
    clean_highs = highs.copy()
    clean_lows = lows.copy()
    clean_opens = opens.copy()
    
    if anomaly_count > 0:
        # Calculate bounds using rolling median ± k*MAD
        window = 20
        for i in range(len(closes)):
            if anomalies[i] and i > 0:
                start = max(0, i - window)
                local_median = np.median(closes[start:i])
                local_mad = np.median(np.abs(closes[start:i] - local_median)) * 1.4826
                
                upper_bound = local_median + threshold * local_mad
                lower_bound = local_median - threshold * local_mad
                
                # Clamp values
                clean_closes[i] = np.clip(closes[i], lower_bound, upper_bound)
                clean_highs[i] = np.clip(highs[i], lower_bound, upper_bound * 1.02)
                clean_lows[i] = np.clip(lows[i], lower_bound * 0.98, upper_bound)
                clean_opens[i] = np.clip(opens[i], lower_bound, upper_bound)
    
    # Quality score
    quality = max(0.5, 1.0 - (anomaly_count / len(closes)) * 2)
    
    return clean_opens, clean_highs, clean_lows, clean_closes, quality


# ========== EMA ==========

def calculate_ema(values: np.ndarray, period: int) -> Optional[float]:
    """
    Calculate EMA with proper warmup period.
    Returns None if insufficient data.
    """
    min_required = period
    if len(values) < min_required:
        return None
    
    alpha = 2.0 / (period + 1.0)
    ema = float(values[0])
    
    for v in values[1:]:
        ema = alpha * float(v) + (1 - alpha) * ema
    
    return float(ema)


def calculate_ema_series(values: np.ndarray, period: int) -> np.ndarray:
    """Calculate full EMA series"""
    if len(values) < period:
        return np.full(len(values), np.nan)
    
    alpha = 2.0 / (period + 1.0)
    ema = np.zeros(len(values))
    ema[0] = values[0]
    
    for i in range(1, len(values)):
        ema[i] = alpha * values[i] + (1 - alpha) * ema[i - 1]
    
    return ema


# ========== RSI ==========

def calculate_rsi(values: np.ndarray, period: int = 14) -> Optional[float]:
    """
    Calculate RSI with proper warmup.
    Returns None if insufficient data.
    """
    min_required = period + 1
    if len(values) < min_required:
        return None
    
    diffs = np.diff(values)
    gains = np.where(diffs > 0, diffs, 0.0)
    losses = np.where(diffs < 0, -diffs, 0.0)
    
    # Use Wilder's smoothing (EMA-like)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    if avg_loss < 1e-9:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    return float(np.clip(rsi, 0.0, 100.0))


def calculate_rsi_series(values: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate full RSI series"""
    if len(values) < period + 1:
        return np.full(len(values), 50.0)
    
    rsi_series = np.zeros(len(values))
    rsi_series[:period] = 50.0
    
    diffs = np.diff(values)
    gains = np.where(diffs > 0, diffs, 0.0)
    losses = np.where(diffs < 0, -diffs, 0.0)
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    for i in range(period, len(values)):
        if i > period:
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        
        if avg_loss < 1e-9:
            rsi_series[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_series[i] = 100.0 - (100.0 / (1.0 + rs))
    
    return np.clip(rsi_series, 0.0, 100.0)


# ========== ATR ==========

def calculate_atr(
    highs: np.ndarray, 
    lows: np.ndarray, 
    closes: np.ndarray, 
    period: int = 14
) -> Optional[float]:
    """
    Calculate ATR (Average True Range) with proper warmup.
    Returns None if insufficient data.
    """
    min_required = period + 1
    if len(closes) < min_required:
        return None
    
    # True Range
    tr = np.zeros(len(closes))
    tr[0] = highs[0] - lows[0]
    
    for i in range(1, len(closes)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)
    
    # Wilder's smoothing for ATR
    atr = np.mean(tr[:period])
    for i in range(period, len(tr)):
        atr = (atr * (period - 1) + tr[i]) / period
    
    return float(atr)


# ========== WEIGHTED LINEAR REGRESSION ==========

def weighted_linear_regression(
    values: np.ndarray,
    smoothing_factor: float = 0.1
) -> Tuple[float, float, float]:
    """
    Weighted linear regression - recent data gets more weight.
    Returns: (slope, intercept, r_squared)
    """
    n = len(values)
    if n < 5:
        return 0.0, float(values[-1]) if len(values) else 0.0, 0.0
    
    x = np.arange(n, dtype=float)
    y = values.astype(float)
    
    # Exponential weights (recent = higher)
    weights = np.exp(np.arange(n) * smoothing_factor)
    weights /= weights.sum()
    
    # Weighted means
    x_mean = np.sum(x * weights)
    y_mean = np.sum(y * weights)
    
    # Weighted covariance and variance
    cov_xy = np.sum(weights * (x - x_mean) * (y - y_mean))
    var_x = np.sum(weights * (x - x_mean) ** 2)
    
    if var_x < 1e-9:
        return 0.0, y_mean, 0.0
    
    slope = cov_xy / var_x
    intercept = y_mean - slope * x_mean
    
    # R-squared
    y_pred = slope * x + intercept
    ss_res = np.sum(weights * (y - y_pred) ** 2)
    ss_tot = np.sum(weights * (y - y_mean) ** 2)
    
    r_squared = 1 - (ss_res / (ss_tot + 1e-9)) if ss_tot > 1e-9 else 0.0
    r_squared = max(0.0, min(1.0, r_squared))
    
    return float(slope), float(intercept), float(r_squared)


# ========== OBV (On-Balance Volume) ==========

def calculate_obv(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """Calculate On-Balance Volume series"""
    if len(closes) != len(volumes) or len(closes) < 2:
        return np.array([0.0])
    
    obv = np.zeros(len(closes))
    
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv[i] = obv[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            obv[i] = obv[i - 1] - volumes[i]
        else:
            obv[i] = obv[i - 1]
    
    return obv


def obv_trend_confirmation(
    closes: np.ndarray,
    volumes: np.ndarray,
    period: int = 20
) -> Tuple[bool, str]:
    """
    Check if OBV confirms price trend.
    Returns: (is_confirmed, obv_trend_direction)
    """
    if len(closes) < period or len(volumes) < period:
        return True, "NEUTRAL"
    
    obv = calculate_obv(closes[-period:], volumes[-period:])
    
    # Linear regression on both
    x = np.arange(period)
    obv_slope = np.polyfit(x, obv, 1)[0]
    price_slope = np.polyfit(x, closes[-period:], 1)[0]
    
    # Same direction?
    confirmed = (obv_slope * price_slope) > 0
    
    if obv_slope > 0:
        direction = "BULLISH"
    elif obv_slope < 0:
        direction = "BEARISH"
    else:
        direction = "NEUTRAL"
    
    return confirmed, direction
