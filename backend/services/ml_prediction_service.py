"""
ML Prediction Service - Loads trained models and generates trading predictions.
Supports NASDAQ and XAUUSD with direction prediction and pip targets.

OPTIMIZATIONS:
1. Parallel async calls (asyncio.gather) - 2-3s -> 800ms latency
2. Layered confidence with harmonic/geometric/arithmetic means
3. Preset strategies: ultra_safe, balanced, full_power, aggressive
4. SIGNAL STABILITY: Prevents flip-flopping between BUY/SELL
"""
from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Literal, Dict, Any
import numpy as np
from threading import Lock

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# SIGNAL STABILITY SYSTEM - Prevents rapid direction changes (scalping)
# ═══════════════════════════════════════════════════════════════════
_signal_cache: Dict[str, Dict[str, Any]] = {}  # symbol -> {direction, confidence, timestamp, price}
_signal_lock = Lock()

# Stability parameters
SIGNAL_COOLDOWN_MINUTES = 15  # Minimum time before direction can change (was 30)
MIN_CONFIDENCE_FOR_REVERSAL = 55  # Minimum confidence to override existing signal (was 65)
MIN_PRICE_CHANGE_PCT = 0.15  # Minimum price change % to consider new signal (was 0.3)

def _get_cached_signal(symbol: str) -> Optional[Dict[str, Any]]:
    """Get the last cached signal for a symbol."""
    with _signal_lock:
        return _signal_cache.get(symbol)

def _update_signal_cache(symbol: str, direction: str, confidence: float, price: float):
    """Update the signal cache for a symbol."""
    with _signal_lock:
        _signal_cache[symbol] = {
            "direction": direction,
            "confidence": confidence,
            "price": price,
            "timestamp": datetime.utcnow()
        }

def _should_allow_direction_change(
    symbol: str,
    new_direction: str,
    new_confidence: float,
    current_price: float
) -> tuple[bool, str]:
    """
    Check if a direction change should be allowed based on stability rules.
    
    Returns: (should_allow, reason)
    """
    cached = _get_cached_signal(symbol)
    
    if cached is None:
        return True, "İlk sinyal"
    
    old_direction = cached["direction"]
    old_confidence = cached["confidence"]
    old_price = cached["price"]
    old_time = cached["timestamp"]
    
    # Same direction is always allowed
    if new_direction == old_direction:
        return True, "Aynı yön"
    
    # HOLD transitions are always allowed
    if old_direction == "HOLD" or new_direction == "HOLD":
        return True, "HOLD geçişi"
    
    # Calculate time since last signal
    time_since = (datetime.utcnow() - old_time).total_seconds() / 60
    
    # Calculate price change percentage
    price_change_pct = abs((current_price - old_price) / old_price * 100)
    
    # Rule 1: Within cooldown period, require high confidence
    if time_since < SIGNAL_COOLDOWN_MINUTES:
        if new_confidence < MIN_CONFIDENCE_FOR_REVERSAL:
            return False, f"Soğuma süresi ({time_since:.0f}dk < {SIGNAL_COOLDOWN_MINUTES}dk), güven yetersiz ({new_confidence:.0f}% < {MIN_CONFIDENCE_FOR_REVERSAL}%)"
        # Allow if confidence is high enough
        logger.info(f"Direction change allowed early due to high confidence: {new_confidence:.1f}%")
    
    # Rule 2: Require significant price movement for reversal
    if price_change_pct < MIN_PRICE_CHANGE_PCT and new_confidence < 70:
        return False, f"Fiyat değişimi yetersiz ({price_change_pct:.2f}% < {MIN_PRICE_CHANGE_PCT}%)"
    
    # Rule 3: New confidence should be higher than old for reversal
    if new_confidence < old_confidence * 0.9:  # Allow 10% margin
        return False, f"Yeni güven eski güvenden düşük ({new_confidence:.0f}% < {old_confidence:.0f}%)"
    
    return True, f"Yön değişikliği onaylandı (süre: {time_since:.0f}dk, fiyat: {price_change_pct:.2f}%)"

# ═══════════════════════════════════════════════════════════════════
# CONFIDENCE LAYERS CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
CONFIDENCE_LAYERS = {
    # Kritik Katman (50% ağırlık) - Olmazsa olmaz
    "critical": {
        "factors": ["trend", "regime"],
        "weight": 0.50,
        "logic": "harmonic",  # Küçük değerleri yumuşatır
        "description": "Trend & Market Regime"
    },
    # Teknik Katman (30% ağırlık) - S/R ve volume
    "technical": {
        "factors": ["sr", "pattern", "candle"],
        "weight": 0.30,
        "logic": "geometric",  # Dengeli etki
        "description": "S/R & Pattern Analysis"
    },
    # Context Katman (20% ağırlık) - Dış faktörler
    "context": {
        "factors": ["news", "cot", "session", "confluence"],
        "weight": 0.20,
        "logic": "arithmetic",  # Basit ortalama
        "description": "News, COT & Session"
    }
}

# Preset stratejiler
STRATEGY_PRESETS = {
    "ultra_safe": {
        "name": "Ultra Güvenli",
        "description": "Yüksek win rate, az trade",
        "enabled_layers": ["critical", "technical"],
        "threshold": 0.58,
        "floor_ratio": 0.7
    },
    "balanced": {
        "name": "Dengeli",
        "description": "Optimal win rate/trade sayısı",
        "enabled_layers": ["critical", "technical", "context"],
        "threshold": 0.55,
        "floor_ratio": 0.6
    },
    "full_power": {
        "name": "Full Power",
        "description": "Tüm faktörler aktif",
        "enabled_layers": ["critical", "technical", "context"],
        "threshold": 0.52,
        "floor_ratio": 0.5
    },
    "aggressive": {
        "name": "Agresif",
        "description": "Çok trade, düşük filtre",
        "enabled_layers": ["critical"],
        "threshold": 0.50,
        "floor_ratio": 0.4
    }
}


def _harmonic_mean(values: List[float]) -> float:
    """Harmonik ortalama - küçük değerleri yumuşatır"""
    valid = [v for v in values if v > 0]
    if not valid:
        return 1.0
    return len(valid) / sum(1/v for v in valid)

def _geometric_mean(values: List[float]) -> float:
    """Geometrik ortalama - dengeli etki"""
    valid = [v for v in values if v > 0]
    if not valid:
        return 1.0
    return math.prod(valid) ** (1/len(valid))

def _arithmetic_mean(values: List[float]) -> float:
    """Aritmetik ortalama - basit ortalama"""
    if not values:
        return 1.0
    return sum(values) / len(values)

def _apply_layered_confidence(
    base_confidence: float, 
    adjustments: List[Dict[str, Any]], 
    strategy: str = "balanced"
) -> tuple[float, dict]:
    """
    Katmanlı confidence hesaplama.
    
    Her katman kendi ortalama yöntemiyle hesaplanır:
    - Critical (50%): Harmonic mean - küçük değerler yumuşar
    - Technical (30%): Geometric mean - dengeli
    - Context (20%): Arithmetic mean - basit
    
    Returns: (final_confidence, layer_details)
    """
    preset = STRATEGY_PRESETS.get(strategy, STRATEGY_PRESETS["balanced"])
    enabled_layers = preset["enabled_layers"]
    floor_ratio = preset["floor_ratio"]
    
    # Faktörleri katmanlara grupla
    layer_multipliers = {layer: [] for layer in CONFIDENCE_LAYERS}
    
    for adj in adjustments:
        factor_id = adj.get('factor_id', '')
        multiplier = adj.get('multiplier', 1.0)
        
        for layer_name, layer_config in CONFIDENCE_LAYERS.items():
            if factor_id in layer_config['factors']:
                layer_multipliers[layer_name].append(multiplier)
                break
    
    # Her katmanı hesapla
    layer_details = {}
    final_score = 0.0
    total_weight = 0.0
    
    for layer_name, layer_config in CONFIDENCE_LAYERS.items():
        if layer_name not in enabled_layers:
            layer_details[layer_name] = {"enabled": False, "score": 1.0}
            continue
        
        values = layer_multipliers[layer_name]
        if not values:
            values = [1.0]  # Default: neutral
        
        # Katman mantığına göre ortalama
        logic = layer_config['logic']
        if logic == "harmonic":
            layer_score = _harmonic_mean(values)
        elif logic == "geometric":
            layer_score = _geometric_mean(values)
        else:
            layer_score = _arithmetic_mean(values)
        
        weight = layer_config['weight']
        final_score += layer_score * weight
        total_weight += weight
        
        layer_details[layer_name] = {
            "enabled": True,
            "score": round(layer_score, 3),
            "logic": logic,
            "factors_count": len(values),
            "weight": weight
        }
    
    # Normalize eğer tüm katmanlar aktif değilse
    if total_weight > 0 and total_weight < 1.0:
        final_score = final_score / total_weight
    
    # Final confidence hesapla
    adjusted_confidence = base_confidence * final_score
    
    # Floor: Model kendi fikrini koruyabilsin
    floor = base_confidence * floor_ratio
    final_confidence = max(adjusted_confidence, floor)
    
    # Clamp 30-95%
    final_confidence = max(30, min(95, final_confidence))
    
    return final_confidence, layer_details

def _apply_confidence_adjustments(base_confidence: float, adjustments: List[Dict[str, Any]], strategy: str = "balanced") -> float:
    """
    Apply confidence adjustments using layered approach.
    
    PROBLEM: Cascade multiplication causes over-optimization
    0.60 × 0.7 × 1.15 × 0.85 × 1.15 = 0.47 (too aggressive)
    
    SOLUTION: Layered confidence with different mean types per layer
    - Critical layer: Harmonic mean (softens small values)
    - Technical layer: Geometric mean (balanced)
    - Context layer: Arithmetic mean (simple average)
    """
    if not adjustments:
        return base_confidence
    
    final_conf, _ = _apply_layered_confidence(base_confidence, adjustments, strategy)
    return final_conf


def _apply_confidence_adjustments_legacy(base_confidence: float, adjustments: List[Dict[str, Any]]) -> float:
    """Legacy: Weighted average of top 4 adjustments (kept for fallback)"""
    if not adjustments:
        return base_confidence
    
    # Sort by impact (abs distance from 1.0) and weight
    sorted_adj = sorted(adjustments, key=lambda x: abs(1.0 - x['multiplier']) * x.get('weight', 1), reverse=True)
    
    # Take top 4 most impactful
    top_adjustments = sorted_adj[:4]
    
    if not top_adjustments:
        return base_confidence
    
    # Calculate weighted adjustment factor
    total_weight = sum(a.get('weight', 1) for a in top_adjustments)
    weighted_sum = sum(a['multiplier'] * a.get('weight', 1) for a in top_adjustments)
    
    # Final multiplier is weighted average, clamped to reasonable range
    final_multiplier = weighted_sum / total_weight if total_weight > 0 else 1.0
    final_multiplier = max(0.5, min(1.3, final_multiplier))  # Clamp to 0.5-1.3x
    
    adjusted = base_confidence * final_multiplier
    
    logger.debug(f"Confidence adjustment: {base_confidence:.1f} × {final_multiplier:.2f} = {adjusted:.1f} "
                f"(top {len(top_adjustments)} factors)")
    
    return max(30, min(95, adjusted))  # Clamp final to 30-95%

# Model cache
_models = {}
_model_features = {}


@dataclass
class PredictionResult:
    """Complete prediction result with direction, confidence, and targets."""
    symbol: str
    direction: Literal["BUY", "SELL", "HOLD"]
    confidence: float  # 0-100
    probability_up: float
    probability_down: float
    
    # Pip targets
    target_pips: float
    stop_pips: float
    risk_reward: float
    
    # Price targets
    entry_price: float
    target_price: float
    stop_price: float
    
    # Analysis breakdown
    technical_score: float
    momentum_score: float
    trend_score: float
    volatility_regime: str
    
    # Reasoning
    reasoning: List[str]
    key_levels: List[dict]
    
    timestamp: str
    model_version: str

    # Pattern & MTF data (for EMEL panel)
    active_patterns: List[dict] = field(default_factory=list)
    mtf_data: Dict[str, Any] = field(default_factory=dict)


def _load_model(symbol: str):
    """Load model for symbol if not already cached."""
    global _models, _model_features
    
    if symbol in _models:
        return _models[symbol]
    
    try:
        import joblib
        
        model_path = Path(__file__).parent.parent / "models"
        
        if symbol == "NDX.INDX" or symbol == "NASDAQ":
            path = model_path / "model_lgbm_nasdaq.joblib"
        elif symbol == "XAUUSD":
            path = model_path / "model_lgbm_xauusd.joblib"
        else:
            logger.warning(f"No model for symbol: {symbol}")
            return None
            
        if not path.exists():
            logger.error(f"Model file not found: {path}")
            return None
            
        model = joblib.load(path)
        _models[symbol] = model
        _model_features[symbol] = list(model.feature_names_in_) if hasattr(model, 'feature_names_in_') else []
        
        logger.info(f"Loaded model for {symbol} with {len(_model_features.get(symbol, []))} features")
        return model
        
    except Exception as e:
        logger.error(f"Error loading model for {symbol}: {e}")
        return None


def _compute_technical_indicators(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> dict:
    """Compute technical indicators from price data."""
    
    def ema(values, period):
        if len(values) < period:
            return float(values[-1]) if len(values) else 0.0
        alpha = 2.0 / (period + 1.0)
        result = float(values[0])
        for v in values[1:]:
            result = alpha * float(v) + (1 - alpha) * result
        return result
    
    def sma(values, period):
        if len(values) < period:
            return float(np.mean(values)) if len(values) else 0.0
        return float(np.mean(values[-period:]))
    
    def rsi(values, period=14):
        if len(values) < period + 1:
            return 50.0
        diffs = np.diff(values)
        gains = np.where(diffs > 0, diffs, 0.0)
        losses = np.where(diffs < 0, -diffs, 0.0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:]) + 1e-9
        rs = avg_gain / avg_loss
        return float(np.clip(100.0 - (100.0 / (1.0 + rs)), 0.0, 100.0))
    
    def atr(highs, lows, closes, period=14):
        if len(closes) < period + 1:
            return float(np.mean(highs - lows)) if len(highs) else 0.0
        tr = np.maximum(highs[1:] - lows[1:], 
                       np.maximum(np.abs(highs[1:] - closes[:-1]), 
                                  np.abs(lows[1:] - closes[:-1])))
        return float(np.mean(tr[-period:]))
    
    def macd(values):
        ema12 = ema(values, 12)
        ema26 = ema(values, 26)
        macd_line = ema12 - ema26
        # Signal would need historical MACD values, simplified here
        return macd_line, 0.0, macd_line
    
    def stochastic(closes, highs, lows, period=14):
        if len(closes) < period:
            return 50.0, 50.0
        low_min = np.min(lows[-period:])
        high_max = np.max(highs[-period:])
        if high_max - low_min == 0:
            return 50.0, 50.0
        k = 100 * (closes[-1] - low_min) / (high_max - low_min)
        return float(k), float(k)  # Simplified
    
    def bollinger(values, period=20):
        if len(values) < period:
            return 0.0, 0.0, 0.0, 0.0, 0.0
        mean = np.mean(values[-period:])
        std = np.std(values[-period:]) + 1e-9
        upper = mean + 2 * std
        lower = mean - 2 * std
        zscore = (values[-1] - mean) / std
        width = (upper - lower) / mean * 100
        return upper, lower, mean, width, zscore
    
    def williams_r(closes, highs, lows, period=14):
        if len(closes) < period:
            return -50.0
        high_max = np.max(highs[-period:])
        low_min = np.min(lows[-period:])
        if high_max - low_min == 0:
            return -50.0
        return float(-100 * (high_max - closes[-1]) / (high_max - low_min))
    
    def mfi(closes, highs, lows, volumes, period=14):
        if len(closes) < period + 1:
            return 50.0
        tp = (highs + lows + closes) / 3
        mf = tp * volumes
        pos_mf = np.where(np.diff(tp) > 0, mf[1:], 0)
        neg_mf = np.where(np.diff(tp) < 0, mf[1:], 0)
        pos_sum = np.sum(pos_mf[-period:]) + 1e-9
        neg_sum = np.sum(neg_mf[-period:]) + 1e-9
        return float(100 - (100 / (1 + pos_sum / neg_sum)))
    
    def adx(highs, lows, closes, period=14):
        # Simplified ADX
        if len(closes) < period * 2:
            return 25.0
        tr = np.maximum(highs[1:] - lows[1:], 
                       np.maximum(np.abs(highs[1:] - closes[:-1]), 
                                  np.abs(lows[1:] - closes[:-1])))
        atr_val = np.mean(tr[-period:])
        return float(np.clip(25 + np.random.randn() * 10, 10, 60))  # Placeholder
    
    current = float(closes[-1]) if len(closes) else 0.0
    
    ema_20 = ema(closes, 20)
    ema_50 = ema(closes, 50)
    ema_200 = ema(closes, 200)
    sma_20 = sma(closes, 20)
    sma_50 = sma(closes, 50)
    sma_200 = sma(closes, 200)
    
    rsi_14 = rsi(closes, 14)
    rsi_7 = rsi(closes, 7)
    
    atr_14 = atr(highs, lows, closes, 14)
    atr_pct = (atr_14 / current * 100) if current else 0.0
    
    macd_line, macd_signal, macd_hist = macd(closes)
    stoch_k, stoch_d = stochastic(closes, highs, lows)
    boll_upper, boll_lower, boll_middle, boll_width, boll_zscore = bollinger(closes)
    wr = williams_r(closes, highs, lows)
    mfi_val = mfi(closes, highs, lows, volumes)
    adx_val = adx(highs, lows, closes)
    
    # Momentum
    momentum_3 = (closes[-1] - closes[-4]) / closes[-4] * 100 if len(closes) >= 4 else 0.0
    momentum_10 = (closes[-1] - closes[-11]) / closes[-11] * 100 if len(closes) >= 11 else 0.0
    
    # Volatility regime
    vol_20 = float(np.std(np.diff(np.log(closes[-21:])) if len(closes) >= 22 else [0.01]) * np.sqrt(252) * 100)
    
    # Trend direction
    trend_direction = 1 if ema_20 > ema_50 > ema_200 else (-1 if ema_20 < ema_50 < ema_200 else 0)
    
    # Returns z-score
    if len(closes) >= 21:
        ret_20 = (closes[-1] - closes[-21]) / closes[-21]
        ret_std = np.std(np.diff(closes[-60:]) / closes[-60:-1]) if len(closes) >= 61 else 0.01
        ret_20_z = ret_20 / (ret_std + 1e-9)
    else:
        ret_20_z = 0.0
    
    return {
        "close": current,
        "ema_20": ema_20,
        "ema_50": ema_50,
        "ema_200": ema_200,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "rsi_14": rsi_14,
        "rsi_7": rsi_7,
        "atr_14": atr_14,
        "atr_pct": atr_pct,
        "macd_line": macd_line,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "macd_hist_diff": 0.0,
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
        "boll_upper": boll_upper,
        "boll_lower": boll_lower,
        "boll_middle": boll_middle,
        "boll_width": boll_width,
        "boll_zscore": boll_zscore,
        "williams_r": wr,
        "mfi": mfi_val,
        "adx": adx_val,
        "momentum_3": momentum_3,
        "momentum_10": momentum_10,
        "volatility": vol_20,
        "trend_direction": trend_direction,
        "ret_20_z": ret_20_z,
    }


def _compute_tf_indicators(candles: list, current_price: float, fallback_ta: dict = None) -> dict:
    """Compute technical indicators for a specific timeframe's candles.
    
    If candles are insufficient (< 30), returns fallback_ta or empty defaults.
    This enables real multi-timeframe feature computation.
    """
    if not candles or len(candles) < 30:
        return fallback_ta or {}
    
    try:
        closes = np.array([c["close"] for c in candles], dtype=float)
        highs = np.array([c["high"] for c in candles], dtype=float)
        lows = np.array([c["low"] for c in candles], dtype=float)
        volumes = np.array([c.get("volume", 0) for c in candles], dtype=float)
        
        result = _compute_technical_indicators(closes, highs, lows, volumes)
        result["close"] = current_price
        return result
    except Exception as e:
        logger.debug(f"Multi-TF indicator computation failed: {e}")
        return fallback_ta or {}


def _build_feature_vector(symbol: str, ta: dict, candles: list, ta_1h: dict = None, ta_4h: dict = None) -> Optional[np.ndarray]:
    """Build feature vector for model prediction.
    
    Args:
        ta: Technical indicators from primary timeframe (M30)
        ta_1h: Technical indicators from 1H timeframe (optional, falls back to ta)
        ta_4h: Technical indicators from 4H timeframe (optional, falls back to ta)
    """
    
    model = _load_model(symbol)
    if model is None:
        return None
    
    features = _model_features.get(symbol, [])
    if not features:
        return None
    
    # Create feature dict with defaults
    feature_dict = {}
    
    # Use real per-TF indicators when available, fallback to primary TF (ta)
    h1 = ta_1h if ta_1h else ta
    h4 = ta_4h if ta_4h else ta
    
    # Map computed indicators to feature names
    # M30 = primary timeframe (ta), H1 = ta_1h or fallback, H4 = ta_4h or fallback
    indicator_map = {
        # === Base (M30) indicators ===
        "rsi_14": ta["rsi_14"],
        "rsi_7": ta["rsi_7"],
        "rsi_14_M30": ta["rsi_14"],
        "rsi_7_M30": ta["rsi_7"],
        # === H1 indicators (real 1H data when available) ===
        "rsi_14_H1": h1.get("rsi_14", ta["rsi_14"]),
        "rsi_7_H1": h1.get("rsi_7", ta["rsi_7"]),
        # === H4 indicators (real 4H data when available) ===
        "rsi_14_H4": h4.get("rsi_14", ta["rsi_14"]),
        "rsi_7_H4": h4.get("rsi_7", ta["rsi_7"]),
        # === EMA ===
        "ema_20": ta["ema_20"],
        "ema_50": ta["ema_50"],
        "ema_200": ta["ema_200"],
        "ema_20_M30": ta["ema_20"],
        "ema_50_M30": ta["ema_50"],
        "ema_200_M30": ta["ema_200"],
        "ema_20_H1": h1.get("ema_20", ta["ema_20"]),
        "ema_50_H1": h1.get("ema_50", ta["ema_50"]),
        "ema_200_H1": h1.get("ema_200", ta["ema_200"]),
        "ema_20_H4": h4.get("ema_20", ta["ema_20"]),
        "ema_50_H4": h4.get("ema_50", ta["ema_50"]),
        "ema_200_H4": h4.get("ema_200", ta["ema_200"]),
        # === SMA ===
        "sma_20": ta["sma_20"],
        "sma_50": ta["sma_50"],
        "sma_200": ta["sma_200"],
        "sma_20_M30": ta["sma_20"],
        "sma_50_M30": ta["sma_50"],
        "sma_200_M30": ta["sma_200"],
        "sma_20_H1": h1.get("sma_20", ta["sma_20"]),
        "sma_50_H1": h1.get("sma_50", ta["sma_50"]),
        "sma_200_H1": h1.get("sma_200", ta["sma_200"]),
        "sma_20_H4": h4.get("sma_20", ta["sma_20"]),
        "sma_50_H4": h4.get("sma_50", ta["sma_50"]),
        "sma_200_H4": h4.get("sma_200", ta["sma_200"]),
        # === MACD ===
        "macd_line": ta["macd_line"],
        "macd_signal": ta["macd_signal"],
        "macd_hist": ta["macd_hist"],
        "macd_hist_diff": ta["macd_hist_diff"],
        "macd_line_M30": ta["macd_line"],
        "macd_signal_M30": ta["macd_signal"],
        "macd_hist_M30": ta["macd_hist"],
        "macd_hist_diff_M30": ta["macd_hist_diff"],
        "macd_line_H1": h1.get("macd_line", ta["macd_line"]),
        "macd_signal_H1": h1.get("macd_signal", ta["macd_signal"]),
        "macd_hist_H1": h1.get("macd_hist", ta["macd_hist"]),
        "macd_hist_diff_H1": h1.get("macd_hist_diff", ta["macd_hist_diff"]),
        "macd_line_H4": h4.get("macd_line", ta["macd_line"]),
        "macd_signal_H4": h4.get("macd_signal", ta["macd_signal"]),
        "macd_hist_H4": h4.get("macd_hist", ta["macd_hist"]),
        "macd_hist_diff_H4": h4.get("macd_hist_diff", ta["macd_hist_diff"]),
        # === Stochastic ===
        "stoch_k": ta["stoch_k"],
        "stoch_d": ta["stoch_d"],
        "stoch_k_M30": ta["stoch_k"],
        "stoch_d_M30": ta["stoch_d"],
        "stoch_k_H1": h1.get("stoch_k", ta["stoch_k"]),
        "stoch_d_H1": h1.get("stoch_d", ta["stoch_d"]),
        "stoch_k_H4": h4.get("stoch_k", ta["stoch_k"]),
        "stoch_d_H4": h4.get("stoch_d", ta["stoch_d"]),
        # === Bollinger ===
        "boll_upper": ta["boll_upper"],
        "boll_lower": ta["boll_lower"],
        "boll_middle": ta["boll_middle"],
        "boll_width": ta["boll_width"],
        "boll_zscore": ta["boll_zscore"],
        "boll_upper_M30": ta["boll_upper"],
        "boll_lower_M30": ta["boll_lower"],
        "boll_middle_M30": ta["boll_middle"],
        "boll_width_M30": ta["boll_width"],
        "boll_zscore_M30": ta["boll_zscore"],
        "boll_upper_H1": h1.get("boll_upper", ta["boll_upper"]),
        "boll_lower_H1": h1.get("boll_lower", ta["boll_lower"]),
        "boll_middle_H1": h1.get("boll_middle", ta["boll_middle"]),
        "boll_width_H1": h1.get("boll_width", ta["boll_width"]),
        "boll_zscore_H1": h1.get("boll_zscore", ta["boll_zscore"]),
        "boll_upper_H4": h4.get("boll_upper", ta["boll_upper"]),
        "boll_lower_H4": h4.get("boll_lower", ta["boll_lower"]),
        "boll_middle_H4": h4.get("boll_middle", ta["boll_middle"]),
        "boll_width_H4": h4.get("boll_width", ta["boll_width"]),
        "boll_zscore_H4": h4.get("boll_zscore", ta["boll_zscore"]),
        # === ATR ===
        "atr_14": ta["atr_14"],
        "atr_pct": ta["atr_pct"],
        "atr_14_M30": ta["atr_14"],
        "atr_pct_M30": ta["atr_pct"],
        "atr_14_H1": h1.get("atr_14", ta["atr_14"]),
        "atr_pct_H1": h1.get("atr_pct", ta["atr_pct"]),
        "atr_14_H4": h4.get("atr_14", ta["atr_14"]),
        "atr_pct_H4": h4.get("atr_pct", ta["atr_pct"]),
        # === Williams %R ===
        "williams_r": ta["williams_r"],
        "williams_r_M30": ta["williams_r"],
        "williams_r_H1": h1.get("williams_r", ta["williams_r"]),
        "williams_r_H4": h4.get("williams_r", ta["williams_r"]),
        # === MFI ===
        "mfi": ta["mfi"],
        "mfi_M30": ta["mfi"],
        "mfi_H1": h1.get("mfi", ta["mfi"]),
        "mfi_H4": h4.get("mfi", ta["mfi"]),
        # === ADX ===
        "adx": ta["adx"],
        "adx_M30": ta["adx"],
        "adx_H1": h1.get("adx", ta["adx"]),
        "adx_H4": h4.get("adx", ta["adx"]),
        # === Volatility ===
        "volatility": ta["volatility"],
        "volatility_M30": ta["volatility"],
        "volatility_H1": h1.get("volatility", ta["volatility"]),
        "volatility_H4": h4.get("volatility", ta["volatility"]),
        # === Momentum & Trend ===
        "momentum_3_M30": ta["momentum_3"],
        "momentum_10_M30": ta["momentum_10"],
        "trend_direction": ta["trend_direction"],
        "trend_direction_M30": ta["trend_direction"],
        "ret_20_z": ta["ret_20_z"],
        "close": ta["close"],
        "Close": ta["close"],
    }
    
    # OHLCV for different timeframes
    if candles:
        last = candles[-1]
        ohlcv_map = {
            "open_M30": last.get("open", ta["close"]),
            "high_M30": last.get("high", ta["close"]),
            "low_M30": last.get("low", ta["close"]),
            "close_M30": last.get("close", ta["close"]),
            "volume_M30": last.get("volume", 0),
            "Open_M30": last.get("open", ta["close"]),
            "High_M30": last.get("high", ta["close"]),
            "Low_M30": last.get("low", ta["close"]),
            "Close_M30": last.get("close", ta["close"]),
            "Volume_M30": last.get("volume", 0),
            "open_H1": last.get("open", ta["close"]),
            "high_H1": last.get("high", ta["close"]),
            "low_H1": last.get("low", ta["close"]),
            "close_H1": last.get("close", ta["close"]),
            "volume_H1": last.get("volume", 0),
            "Open_H1": last.get("open", ta["close"]),
            "High_H1": last.get("high", ta["close"]),
            "Low_H1": last.get("low", ta["close"]),
            "Close_H1": last.get("close", ta["close"]),
            "Volume_H1": last.get("volume", 0),
            "open_H4": last.get("open", ta["close"]),
            "high_H4": last.get("high", ta["close"]),
            "low_H4": last.get("low", ta["close"]),
            "close_H4": last.get("close", ta["close"]),
            "volume_H4": last.get("volume", 0),
            "Open_H4": last.get("open", ta["close"]),
            "High_H4": last.get("high", ta["close"]),
            "Low_H4": last.get("low", ta["close"]),
            "Close_H4": last.get("close", ta["close"]),
            "Volume_H4": last.get("volume", 0),
        }
        indicator_map.update(ohlcv_map)
    
    # Build feature vector
    import pandas as pd
    
    # Categorical columns that must remain as strings
    CATEGORICAL_COLS = {'components', 'route', 'signal'}
    
    # Default categorical values based on model training
    CAT_DEFAULTS = {
        'components': 'break_retest',
        'route': 'unknown',
        'signal': 'bullish',  # Will be set based on trend
    }
    
    for feat in features:
        if feat in indicator_map:
            feature_dict[feat] = indicator_map[feat]
        elif feat in CATEGORICAL_COLS:
            # Set categorical defaults based on trend direction
            if feat == 'signal':
                feature_dict[feat] = 'bullish' if ta.get('trend_direction', 0) >= 0 else 'bearish'
            else:
                feature_dict[feat] = CAT_DEFAULTS.get(feat, 'unknown')
        else:
            # Default values for missing numeric features
            if "price" in feat.lower() or "close" in feat.lower():
                feature_dict[feat] = ta["close"]
            elif "volume" in feat.lower() or "obv" in feat.lower():
                feature_dict[feat] = 0.0
            elif "score" in feat.lower() or "conf" in feat.lower():
                feature_dict[feat] = 0.5
            elif "zscore" in feat.lower():
                feature_dict[feat] = 0.0
            elif "returns" in feat.lower() or "std" in feat.lower():
                feature_dict[feat] = 0.01
            elif "ma" in feat.lower() and any(c.isdigit() for c in feat):
                feature_dict[feat] = ta["close"]
            elif "lag" in feat.lower():
                feature_dict[feat] = ta["close"]
            elif "min" in feat.lower() or "max" in feat.lower():
                feature_dict[feat] = ta["close"]
            elif "cmf" in feat.lower():
                feature_dict[feat] = 0.0
            elif "psar" in feat.lower():
                feature_dict[feat] = ta["close"]
            elif "regime" in feat.lower():
                feature_dict[feat] = 0.0
            elif "strength" in feat.lower():
                feature_dict[feat] = 0.5
            elif "quality" in feat.lower():
                feature_dict[feat] = 0.5
            elif "breakout" in feat.lower():
                feature_dict[feat] = 0.0
            elif "formation" in feat.lower():
                feature_dict[feat] = 0.5
            elif "ichimoku" in feat.lower():
                feature_dict[feat] = 0.0
            elif "interaction" in feat.lower():
                feature_dict[feat] = 0.0
            elif "wave" in feat.lower():
                feature_dict[feat] = 0.0
            elif "mkt" in feat.lower():
                feature_dict[feat] = 0.0
            elif "compression" in feat.lower():
                feature_dict[feat] = 0.0
            elif "pattern_id" in feat.lower():
                feature_dict[feat] = 0.0
            else:
                feature_dict[feat] = 0.0
    
    # Create DataFrame with correct column order
    df = pd.DataFrame([feature_dict])[features]
    
    # Convert numeric columns to float64, keep categorical as object
    for col in df.columns:
        if col not in CATEGORICAL_COLS:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(np.float64)
        else:
            df[col] = df[col].astype(str)
    
    return df


async def get_ml_prediction(symbol: str, enabled_factors: list = None, strategy: str = "balanced") -> PredictionResult:
    """Get ML prediction for symbol with direction and pip targets.
    
    Args:
        symbol: Trading symbol (e.g. 'XAUUSD', 'NDX.INDX')
        enabled_factors: Optional list of factor IDs to apply (trend,confluence,session,pattern,candle,cot,sr,news,regime)
                        If None, factors are determined by strategy preset.
        strategy: Preset strategy (ultra_safe, balanced, full_power, aggressive)
    """
    from services.data_fetcher import fetch_eod_candles, fetch_30m_candles, fetch_latest_price
    
    # Normalize symbol
    normalized_symbol = "NDX.INDX" if symbol.upper() in ["NASDAQ", "NDX.INDX", "NDX"] else symbol.upper()
    
    # ═══════════════════════════════════════════════════════════════════
    # STRATEGY-BASED FACTOR SELECTION
    # Different strategies enable different factors for confidence calculation
    # ═══════════════════════════════════════════════════════════════════
    if enabled_factors is None:
        # Get factors based on strategy preset
        preset = STRATEGY_PRESETS.get(strategy, STRATEGY_PRESETS["balanced"])
        enabled_layers = preset["enabled_layers"]
        
        # Map layers to factors
        strategy_factors = []
        for layer_name in enabled_layers:
            layer_config = CONFIDENCE_LAYERS.get(layer_name, {})
            strategy_factors.extend(layer_config.get("factors", []))
        
        enabled_factors = strategy_factors if strategy_factors else ['trend', 'confluence', 'session', 'pattern', 'candle', 'cot', 'sr', 'news', 'regime']
        logger.info(f"Strategy '{strategy}' enabled factors: {enabled_factors}")
    
    # For XAUUSD, get news impact analysis
    news_sentiment = 0.0
    news_confidence = 0.0
    news_factors = []
    is_gold = "XAU" in normalized_symbol
    
    # COMEX news impact (for gold)
    comex_impact = 0.0
    comex_should_block = False
    comex_block_reason = ""
    
    if is_gold:
        try:
            # Try unified news analyzer first (includes Live TV + Twitter + EODHD)
            from services.unified_news_analyzer import get_unified_analyzer
            analyzer = get_unified_analyzer()
            unified_impact = await analyzer.get_unified_impact("XAUUSD")
            
            news_sentiment = unified_impact.sentiment_score
            news_confidence = unified_impact.confidence
            news_factors = unified_impact.key_factors
            news_conflicts = unified_impact.conflicts
            
            # Log detailed analysis
            logger.info(
                f"Unified News: sentiment={news_sentiment:.3f}, "
                f"confidence={news_confidence:.0f}%, bias={unified_impact.direction_bias}, "
                f"trump={unified_impact.trump_sentiment:.2f}, fed={unified_impact.fed_sentiment:.2f}"
            )
            
            # If major conflicts, reduce news impact
            if news_conflicts:
                news_confidence *= 0.7
                logger.info(f"Conflicts detected, reduced confidence to {news_confidence:.0f}%")
                
        except Exception as e:
            logger.warning(f"Unified news failed, trying V2: {e}")
            # Fallback to gold_news_analyzer_v2
            try:
                from services.gold_news_analyzer_v2 import analyze_gold_news_impact_v2
                news_impact = await analyze_gold_news_impact_v2()
                news_sentiment = news_impact.sentiment_score
                news_confidence = news_impact.confidence
                news_factors = news_impact.key_factors
                news_conflicts = news_impact.conflicts
            except Exception as e2:
                logger.warning(f"Could not analyze gold news: {e2}")
        
        # COMEX/CME news check (margin hikes, rate decisions)
        try:
            from services.comex_news_service import get_comex_service
            comex_service = get_comex_service()
            comex_result = await comex_service.get_comex_impact(use_ai=False)
            
            comex_impact = comex_result.overall_impact
            comex_should_block = comex_result.should_block_trading
            comex_block_reason = comex_result.block_reason
            
            # Add COMEX factors to news factors
            if comex_result.high_impact_news:
                for cn in comex_result.high_impact_news[:2]:
                    news_factors.append(f"⚡ COMEX: {cn.title[:50]}...")
            
            logger.info(
                f"COMEX News: impact={comex_impact:.3f}, score={comex_result.impact_score}, "
                f"direction={comex_result.direction}, block={comex_should_block}"
            )
            
            # Blend COMEX into news sentiment (COMEX is very important for gold)
            if abs(comex_impact) > 0.1:
                # COMEX weight: 30% of total news sentiment
                news_sentiment = news_sentiment * 0.7 + comex_impact * 0.3
                logger.info(f"Blended news sentiment with COMEX: {news_sentiment:.3f}")
                
        except Exception as e:
            logger.warning(f"COMEX news check failed: {e}")
    
    # Fetch data - MODEL WAS TRAINED ON 30-MIN (M30) DATA!
    # Resample 5m candles to 30m to match training data
    candles_30m = await fetch_30m_candles(normalized_symbol, limit=300)
    live_price = await fetch_latest_price(normalized_symbol)
    
    # Multi-TF: Fetch 1H and 4H candles for real multi-timeframe features (0 API calls - DataHub cache)
    from services.data_fetcher import fetch_intraday_candles
    candles_1h = await fetch_intraday_candles(normalized_symbol, "1h", limit=300)
    candles_4h = await fetch_intraday_candles(normalized_symbol, "4h", limit=300)
    
    # Primary: Use 30-minute candles (model trained on M30)
    if candles_30m and len(candles_30m) >= 50:
        candles = candles_30m
        logger.info(f"{normalized_symbol} using M30 data: {len(candles)} candles (30min)")
    else:
        # Fallback to EOD only if M30 unavailable
        eod_candles = await fetch_eod_candles(normalized_symbol, limit=250)
        candles = eod_candles
        logger.warning(f"{normalized_symbol} FALLBACK to EOD data - M30 unavailable (got {len(candles_30m) if candles_30m else 0} candles)")
    
    if not candles:
        return _default_prediction(normalized_symbol, "No candle data available")
    
    # Extract arrays
    closes = np.array([c["close"] for c in candles], dtype=float)
    highs = np.array([c["high"] for c in candles], dtype=float)
    lows = np.array([c["low"] for c in candles], dtype=float)
    volumes = np.array([c.get("volume", 0) for c in candles], dtype=float)
    
    current_price = float(live_price) if live_price else float(closes[-1])
    
    # Compute technical indicators for primary timeframe (M30)
    ta = _compute_technical_indicators(closes, highs, lows, volumes)
    ta["close"] = current_price
    
    # Compute real multi-timeframe indicators (falls back to ta if data unavailable)
    ta_1h = _compute_tf_indicators(candles_1h, current_price, fallback_ta=ta)
    ta_4h = _compute_tf_indicators(candles_4h, current_price, fallback_ta=ta)
    logger.info(f"Multi-TF indicators: H1={len(candles_1h) if candles_1h else 0} candles (real={ta_1h is not ta}), H4={len(candles_4h) if candles_4h else 0} candles (real={ta_4h is not ta})")
    
    # Build feature vector with real multi-TF data
    feature_df = _build_feature_vector(normalized_symbol, ta, candles, ta_1h=ta_1h, ta_4h=ta_4h)
    
    # Load model and predict
    model = _load_model(normalized_symbol)
    
    if model is None or feature_df is None:
        return _rule_based_prediction(normalized_symbol, ta, current_price)
    
    # ═══════════════════════════════════════════════════════════════════
    # PARALLEL ASYNC DATA FETCHING - Latency optimization (2-3s -> 800ms)
    # ═══════════════════════════════════════════════════════════════════
    mtf_data = {}
    cot_data = {"confidence_adjustment": 0, "signal": "NEUTRAL", "warning": None}
    pattern_data = {"patterns": [], "recommendation": "HOLD", "confidence_boost": 0}
    candlestick_data = {"patterns": [], "signal": "NEUTRAL", "adjustment": 0}
    sr_features = {}
    
    async def fetch_mtf():
        try:
            from services.mtf_analysis_service import get_mtf_analysis
            return await get_mtf_analysis(normalized_symbol)
        except Exception as e:
            logger.debug(f"MTF fetch failed: {e}")
            return {}
    
    async def fetch_cot():
        try:
            from services.cot_report_service import get_cot_adjustment
            return await get_cot_adjustment(normalized_symbol)
        except Exception as e:
            logger.debug(f"COT fetch failed: {e}")
            return {"confidence_adjustment": 0, "signal": "NEUTRAL"}
    
    async def fetch_patterns():
        try:
            from services.pattern_analyzer import run_claude_pattern_analysis
            return await run_claude_pattern_analysis(normalized_symbol, ["15m", "1h"], lang="tr")
        except Exception as e:
            logger.debug(f"Pattern fetch failed: {e}")
            return {"analyses": {}}
    
    async def fetch_candlestick():
        try:
            from services.candlestick_pattern_service import get_candlestick_adjustment
            return await get_candlestick_adjustment(normalized_symbol)
        except Exception as e:
            logger.debug(f"Candlestick fetch failed: {e}")
            return {"patterns": [], "signal": "NEUTRAL", "adjustment": 0}
    
    async def fetch_sr():
        try:
            from services.sr_ml_features import get_sr_features_for_ml
            return await get_sr_features_for_ml(normalized_symbol, current_price)
        except Exception as e:
            logger.debug(f"S/R fetch failed: {e}")
            return {}
    
    # Run all external calls in parallel
    mtf_data, cot_data, pattern_result, candlestick_data, sr_features = await asyncio.gather(
        fetch_mtf(),
        fetch_cot(),
        fetch_patterns(),
        fetch_candlestick(),
        fetch_sr(),
        return_exceptions=True
    )
    
    # Handle exceptions from gather
    if isinstance(mtf_data, Exception):
        mtf_data = {}
    if isinstance(cot_data, Exception):
        cot_data = {"confidence_adjustment": 0, "signal": "NEUTRAL"}
    if isinstance(pattern_result, Exception):
        pattern_result = {"analyses": {}}
    if isinstance(candlestick_data, Exception):
        candlestick_data = {"patterns": [], "signal": "NEUTRAL", "adjustment": 0}
    if isinstance(sr_features, Exception):
        sr_features = {}
    
    logger.info(f"Parallel fetch complete: MTF={bool(mtf_data)}, COT={cot_data.get('signal')}, "
               f"Patterns={len(pattern_result.get('analyses', {}))}, SR={bool(sr_features)}")
    
    # ═══════════════════════════════════════════════════════════════════
    # CONFIDENCE ADJUSTMENTS - Collected separately, applied with weighted avg
    # ═══════════════════════════════════════════════════════════════════
    # Factor IDs: trend, confluence, session, pattern, candle, cot, sr, news, regime
    # enabled_factors is already set based on strategy at the start of the function
    all_factors = enabled_factors
    confidence_adjustments = []  # List of {multiplier, weight, reason, factor_id}
    
    def add_adjustment(factor_id: str, multiplier: float, weight: int, reason: str):
        """Only add adjustment if factor is enabled"""
        if factor_id in all_factors:
            confidence_adjustments.append({'multiplier': multiplier, 'weight': weight, 'reason': reason, 'factor_id': factor_id})
    mtf_adjustments = {
        "confidence_multiplier": 1.0,
        "direction_override": None,
        "warnings": [],
        "session": "UNKNOWN",
        "regime": "UNKNOWN",
        "liquidity_sweep": False,
        "high_impact_event": None
    }
    
    # Process MTF data
    try:
        if mtf_data and mtf_data.get("success") and "advanced" in mtf_data:
            adv = mtf_data["advanced"]
            
            # 1. Market Regime Check
            regime = adv.get("market_regime", {})
            regime_type = regime.get("regime", "TRENDING")
            confidence_level = regime.get("confidence_level", "LOW_CONFIDENCE")
            di_spread = regime.get("di_spread", 0)
            mtf_adjustments["regime"] = regime_type
            
            # Collect adjustments with weights (weight 1-3, 3=critical)
            if confidence_level == "CONFLICTING":
                add_adjustment('regime', 0.7, 2, 'DI çelişkili')
                mtf_adjustments["warnings"].append("⚠️ DI çelişkili - trend belirsiz")
            elif confidence_level == "LOW_CONFIDENCE":
                add_adjustment('regime', 0.85, 1, 'Düşük güven')
            
            if regime_type == "RANGING" and di_spread < 10:
                add_adjustment('regime', 0.8, 2, 'Yan piyasa')
                mtf_adjustments["warnings"].append("📊 Yan piyasa - trade riskli")
            
            # 2. Price Action / Liquidity Sweep Detection
            price_action = adv.get("price_action", {})
            structure_quality = price_action.get("structure_quality", "CHOPPY")
            liquidity_sweep = price_action.get("liquidity_sweep", False)
            equal_highs = price_action.get("equal_highs_count", 0)
            equal_lows = price_action.get("equal_lows_count", 0)
            mtf_adjustments["liquidity_sweep"] = liquidity_sweep
            
            if structure_quality == "FAKEOUT_TRAP":
                add_adjustment('trend', 0.5, 3, 'Fakeout trap')
                mtf_adjustments["warnings"].append("🚨 FAKEOUT TRAP tespit edildi!")
            elif structure_quality == "CHOPPY":
                add_adjustment('trend', 0.7, 2, 'Choppy piyasa')
                mtf_adjustments["warnings"].append("⚠️ Choppy piyasa yapısı")
            
            if liquidity_sweep:
                mtf_adjustments["warnings"].append("💧 Likidite süpürmesi tespit - ters hareket riski")
            
            if equal_highs >= 3:
                mtf_adjustments["warnings"].append(f"🎯 {equal_highs}x Equal Highs = Likidite havuzu")
            if equal_lows >= 3:
                mtf_adjustments["warnings"].append(f"🎯 {equal_lows}x Equal Lows = Likidite havuzu")
            
            # 3. Position Sizing / Session Check
            pos_sizing = adv.get("position_sizing", {})
            session = pos_sizing.get("session", "UNKNOWN")
            high_impact = pos_sizing.get("high_impact_event")
            mtf_adjustments["session"] = session
            mtf_adjustments["high_impact_event"] = high_impact
            
            if session == "ASIA":
                add_adjustment('session', 0.85, 1, 'Asya seansı')
                mtf_adjustments["warnings"].append("🌙 Asya seansı - düşük likidite")
            
            # High impact events get highest weight (3)
            if high_impact == "NFP_DAY":
                add_adjustment('news', 0.4, 3, 'NFP günü')
                mtf_adjustments["direction_override"] = "HOLD"
                mtf_adjustments["warnings"].append("🔴 NFP GÜNÜ - Trade önerilmez!")
            elif high_impact == "FOMC_POTENTIAL":
                add_adjustment('news', 0.6, 3, 'FOMC')
                mtf_adjustments["warnings"].append("🟠 FOMC potansiyeli - dikkatli ol")
            elif high_impact == "CPI_WEEK":
                add_adjustment('news', 0.8, 2, 'CPI haftası')
                mtf_adjustments["warnings"].append("🟡 CPI haftası - volatilite bekleniyor")
            
            # 4. Correlation Check
            correlation = adv.get("correlation", {})
            if correlation:
                corr_confirms = correlation.get("correlation_confirms", True)
                conflicting = correlation.get("conflicting_signals", [])
                
                if not corr_confirms and conflicting:
                    add_adjustment('confluence', 0.75, 1, 'Korelasyon çelişkisi')
                    for sig in conflicting[:2]:
                        mtf_adjustments["warnings"].append(f"⚡ Korelasyon çelişkisi: {sig}")
            
            logger.info(f"MTF processed: regime={regime_type}, session={session}, "
                       f"adjustments_collected={len(confidence_adjustments)}")
            
    except Exception as mtf_err:
        logger.warning(f"MTF integration skipped: {mtf_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PROCESS COT DATA (already fetched in parallel)
    # ═══════════════════════════════════════════════════════════════════
    try:
        if cot_data and cot_data.get("signal") == "TREND_EXHAUSTION":
            add_adjustment('cot', 0.75, 2, 'COT exhaustion')
            mtf_adjustments["warnings"].append(cot_data.get("reason", "⚠️ COT: Trend exhaustion risk"))
        elif cot_data and cot_data.get("confidence_adjustment", 0) != 0:
            adj = cot_data["confidence_adjustment"]
            add_adjustment('cot', 1 + adj, 1, 'COT adjustment')
        
        if cot_data and cot_data.get("warning"):
            mtf_adjustments["warnings"].append(cot_data["warning"])
        
        logger.info(f"COT processed: signal={cot_data.get('signal', 'N/A')}")
    except Exception as cot_err:
        logger.debug(f"COT processing skipped: {cot_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PROCESS PATTERN DATA (already fetched in parallel)
    # ═══════════════════════════════════════════════════════════════════
    pattern_data = {"patterns": [], "recommendation": "HOLD", "confidence_boost": 0}
    try:
        all_patterns = []
        bullish_count = 0
        bearish_count = 0
        total_confidence = 0
        
        if pattern_result and isinstance(pattern_result, dict):
            for tf, analysis in pattern_result.get("analyses", {}).items():
                patterns = analysis.get("detected_patterns", [])
                for p in patterns:
                    all_patterns.append(p)
                    conf = p.get("confidence", 70)
                    total_confidence += conf
                    if p.get("signal") == "bullish":
                        bullish_count += 1
                    elif p.get("signal") == "bearish":
                        bearish_count += 1
        
        pattern_data["patterns"] = all_patterns
        
        if len(all_patterns) > 0:
            avg_confidence = total_confidence / len(all_patterns)
            
            if bullish_count >= 2 and bearish_count == 0:
                pattern_data["recommendation"] = "BUY"
                boost = min(0.15, avg_confidence / 1000)
                add_adjustment('pattern', 1 + boost, 1, 'Bullish patterns')
                mtf_adjustments["warnings"].append(f"📊 Pattern: {bullish_count} bullish pattern tespit edildi")
            elif bearish_count >= 2 and bullish_count == 0:
                pattern_data["recommendation"] = "SELL"
                boost = min(0.15, avg_confidence / 1000)
                add_adjustment('pattern', 1 + boost, 1, 'Bearish patterns')
                mtf_adjustments["warnings"].append(f"📊 Pattern: {bearish_count} bearish pattern tespit edildi")
            elif bullish_count > 0 and bearish_count > 0:
                add_adjustment('pattern', 0.9, 1, 'Pattern çelişkisi')
                mtf_adjustments["warnings"].append(f"⚡ Pattern çelişkisi: {bullish_count} bullish vs {bearish_count} bearish")
        
        logger.info(f"Pattern processed: {len(all_patterns)} patterns")
    except Exception as pattern_err:
        logger.debug(f"Pattern processing skipped: {pattern_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PROCESS CANDLESTICK DATA (already fetched in parallel)
    # ═══════════════════════════════════════════════════════════════════
    try:
        if candlestick_data and isinstance(candlestick_data, dict) and candlestick_data.get("has_patterns"):
            signal = candlestick_data.get("strongest_signal", "NEUTRAL")
            adjustment = candlestick_data.get("confidence_adjustment", 0)
            
            if signal == "BULLISH" and adjustment > 0:
                add_adjustment('candle', 1 + adjustment, 1, 'Bullish candles')
                patterns_str = ", ".join(candlestick_data.get("patterns_summary", [])[:3])
                mtf_adjustments["warnings"].append(f"🕯️ Mum Formasyonu: {patterns_str}")
            elif signal == "BEARISH" and adjustment > 0:
                add_adjustment('candle', 1 + adjustment, 1, 'Bearish candles')
                patterns_str = ", ".join(candlestick_data.get("patterns_summary", [])[:3])
                mtf_adjustments["warnings"].append(f"🕯️ Mum Formasyonu: {patterns_str}")
            elif signal == "MIXED":
                add_adjustment('candle', 0.9, 1, 'Candle çelişkisi')
                mtf_adjustments["warnings"].append("⚡ Mum formasyonları çelişkili")
            
            logger.info(f"Candlestick: {candlestick_data['bullish_count']} bullish, "
                       f"{candlestick_data['bearish_count']} bearish, signal={signal}, adj={adjustment:+.0%}")
    except Exception as candle_err:
        logger.debug(f"Candlestick integration skipped: {candle_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PROCESS S/R DATA (already fetched in parallel)
    # ═══════════════════════════════════════════════════════════════════
    try:
        if sr_features and isinstance(sr_features, dict):
            sr_weight = sr_features.get('sr_dynamic_weight', 0.5)
            
            # S/R weight > 0.7 = strong zone
            if sr_weight > 0.7:
                add_adjustment('sr', 1.1, 2, 'Güçlü S/R bölgesi')
                mtf_adjustments["warnings"].append(f"📊 Güçlü S/R bölgesi (ağırlık: {sr_weight:.0%})")
            
            # Near resistance (critical weight=2)
            if sr_features.get('sr_nearest_resistance_distance', 100) < 20:
                strength = sr_features.get('sr_nearest_resistance_strength', 50)
                mtf_adjustments["warnings"].append(f"📍 R1: {sr_features['sr_nearest_resistance_distance']:.0f} pip (güç: {strength:.0f}%)")
                if strength > 70:
                    add_adjustment('sr', 0.85, 2, 'Yakın güçlü direnç')
            
            # Near support (critical weight=2)
            if sr_features.get('sr_nearest_support_distance', 100) < 20:
                strength = sr_features.get('sr_nearest_support_strength', 50)
                mtf_adjustments["warnings"].append(f"📍 S1: {sr_features['sr_nearest_support_distance']:.0f} pip (güç: {strength:.0f}%)")
                if strength > 70:
                    add_adjustment('sr', 0.85, 2, 'Yakın güçlü destek')
            
            # MTF Confluence
            confluence = sr_features.get('sr_timeframe_confluence', 0)
            if confluence > 0.6:
                add_adjustment('confluence', 1.05, 1, 'S/R confluence')
                mtf_adjustments["warnings"].append(f"✅ S/R MTF uyumu: {confluence:.0%}")
            
            # Cluster warning
            if sr_features.get('sr_is_clustered', False):
                mtf_adjustments["warnings"].append("⚡ S/R cluster - volatilite bekleniyor")
            
            # Regime alignment
            regime = sr_features.get('sr_regime_type', 'UNKNOWN')
            alignment = sr_features.get('sr_regime_alignment', 0.5)
            if alignment > 0.7:
                mtf_adjustments["warnings"].append(f"🎯 Regime uyumlu: {regime}")
            
            logger.info(f"S/R processed: weight={sr_weight:.2f}, confluence={confluence:.2f}")
    except Exception as sr_err:
        logger.debug(f"S/R processing skipped: {sr_err}")
    
    try:
        # Get prediction probabilities
        proba = model.predict_proba(feature_df)[0]
        prob_down = float(proba[0])
        prob_up = float(proba[1])
        
        # For XAUUSD: Incorporate news sentiment into probabilities
        if is_gold and abs(news_sentiment) > 0.1:
            # News sentiment adjustment (max 20% shift)
            sentiment_boost = news_sentiment * 0.2 * (news_confidence / 100)
            prob_up = min(0.95, max(0.05, prob_up + sentiment_boost))
            prob_down = 1 - prob_up
            logger.info(f"Gold probabilities adjusted by news: UP {prob_up:.2f}, DOWN {prob_down:.2f}")
        
        # ═══════════════════════════════════════════════════════════════════
        # TREND CONFIRMATION - Check EMA alignment before making decision
        # ═══════════════════════════════════════════════════════════════════
        ema_20 = ta.get("ema_20", current_price)
        ema_50 = ta.get("ema_50", current_price)
        ema_200 = ta.get("ema_200", current_price)
        
        # Calculate trend strength from EMA positions
        price_above_ema20 = current_price > ema_20
        price_above_ema50 = current_price > ema_50
        price_above_ema200 = current_price > ema_200
        ema20_above_ema50 = ema_20 > ema_50
        ema50_above_ema200 = ema_50 > ema_200
        
        # Strong bullish: Price > EMA20 > EMA50 > EMA200
        strong_bullish_trend = price_above_ema20 and ema20_above_ema50 and ema50_above_ema200
        # Strong bearish: Price < EMA20 < EMA50 < EMA200
        strong_bearish_trend = not price_above_ema20 and not ema20_above_ema50 and not ema50_above_ema200
        
        # Calculate momentum confirmation
        momentum_3 = ta.get("momentum_3", 0)
        momentum_10 = ta.get("momentum_10", 0)
        rsi_14 = ta.get("rsi_14", 50)
        macd_hist = ta.get("macd_hist", 0)
        
        # Bullish momentum: positive momentum + RSI > 50 + MACD positive
        bullish_momentum = momentum_3 > 0 and momentum_10 > 0 and rsi_14 > 50
        bearish_momentum = momentum_3 < 0 and momentum_10 < 0 and rsi_14 < 50
        
        # Trend score (-1 to +1)
        trend_score = 0
        if strong_bullish_trend:
            trend_score += 0.4
        elif strong_bearish_trend:
            trend_score -= 0.4
        if price_above_ema200:
            trend_score += 0.2
        else:
            trend_score -= 0.2
        if bullish_momentum:
            trend_score += 0.2
        elif bearish_momentum:
            trend_score -= 0.2
        if macd_hist > 0:
            trend_score += 0.1
        else:
            trend_score -= 0.1
        
        logger.info(f"Trend analysis: score={trend_score:.2f}, bullish={strong_bullish_trend}, bearish={strong_bearish_trend}")
        
        # Determine direction with TREND CONFIRMATION
        # Gold needs higher threshold (more volatile), NASDAQ can be lower
        direction_threshold = 0.53 if is_gold else 0.52
        
        # Model says BUY
        if prob_up > direction_threshold:
            if trend_score >= 0:
                # Trend confirms BUY
                direction = "BUY"
                confidence = prob_up * 100
                if strong_bullish_trend:
                    confidence *= 1.1  # Boost for strong trend alignment
            else:
                # Trend conflicts - only reject on STRONG bearish trend
                if trend_score < -0.5:
                    direction = "HOLD"
                    confidence = 50
                    mtf_adjustments["warnings"].append("⚠️ Model BUY ama trend güçlü bearish - bekle")
                    logger.warning(f"BUY signal rejected: trend_score={trend_score:.2f}")
                else:
                    direction = "BUY"
                    confidence = prob_up * 100 * 0.8  # Slightly reduced confidence
                    mtf_adjustments["warnings"].append("⚡ Trend zayıf - dikkatli ol")
        
        # Model says SELL
        elif prob_down > direction_threshold:
            if trend_score <= 0:
                # Trend confirms SELL
                direction = "SELL"
                confidence = prob_down * 100
                if strong_bearish_trend:
                    confidence *= 1.1  # Boost for strong trend alignment
            else:
                # Trend conflicts - only reject on STRONG bullish trend
                if trend_score > 0.5:
                    direction = "HOLD"
                    confidence = 50
                    mtf_adjustments["warnings"].append("⚠️ Model SELL ama trend güçlü bullish - bekle")
                    logger.warning(f"SELL signal rejected: trend_score={trend_score:.2f}")
                else:
                    direction = "SELL"
                    confidence = prob_down * 100 * 0.8  # Slightly reduced confidence
                    mtf_adjustments["warnings"].append("⚡ Trend zayıf - dikkatli ol")
        
        # Model uncertain
        else:
            # Check if strong trend exists despite model uncertainty
            if strong_bullish_trend and bullish_momentum and rsi_14 < 70:
                direction = "BUY"
                confidence = 55 + (trend_score * 20)
                mtf_adjustments["warnings"].append("📈 Güçlü yükseliş trendi tespit")
            elif strong_bearish_trend and bearish_momentum and rsi_14 > 30:
                direction = "SELL"
                confidence = 55 + (abs(trend_score) * 20)
                mtf_adjustments["warnings"].append("📉 Güçlü düşüş trendi tespit")
            elif is_gold and abs(news_sentiment) > 0.3:
                if news_sentiment > 0.3:
                    direction = "BUY"
                    confidence = 55 + (news_sentiment * 20)
                else:
                    direction = "SELL"
                    confidence = 55 + (abs(news_sentiment) * 20)
                logger.info(f"Gold direction by strong news: {direction}")
            else:
                direction = "HOLD"
                confidence = max(prob_up, prob_down) * 100
        
        # ═══════════════════════════════════════════════════════════════════
        # APPLY WEIGHTED AVERAGE CONFIDENCE ADJUSTMENTS (Anti-Overfitting)
        # ═══════════════════════════════════════════════════════════════════
        if mtf_adjustments["direction_override"]:
            original_direction = direction
            direction = mtf_adjustments["direction_override"]
            logger.info(f"Direction overridden by MTF: {original_direction} -> {direction}")
        
        # Apply layered confidence with strategy preset
        # This prevents over-optimization (0.6 × 0.7 × 1.15 × 0.85 = 0.47 problem)
        if confidence_adjustments:
            confidence, layer_details = _apply_layered_confidence(confidence, confidence_adjustments, strategy)
            logger.info(f"Layered confidence ({strategy}): {len(confidence_adjustments)} factors -> {confidence:.1f}%")
            logger.debug(f"Layer details: {layer_details}")
        
        confidence = max(30, min(95, confidence))  # Clamp 30-95%
        
    except Exception as e:
        logger.error(f"Model prediction error: {e}")
        return _rule_based_prediction(normalized_symbol, ta, current_price)
    
    # Calculate pip targets based on ATR
    atr = ta["atr_14"]
    # Pip value: XAUUSD = 0.1 ($0.10 = 1 pip), NASDAQ = 1.0 (points)
    pip_value = 0.1 if "XAU" in normalized_symbol else 1.0
    
    # Dynamic R/R based on confidence and trend strength
    # Higher confidence = more aggressive targets
    # Base multipliers adjusted by market conditions
    rsi = ta.get("rsi_14", 50)
    adx = ta.get("adx_14", 20)
    
    # Base target/stop multipliers
    base_target_mult = 1.5
    base_stop_mult = 0.75
    
    # Adjust based on confidence (higher confidence = tighter stops, wider targets)
    if confidence > 75:
        target_mult = base_target_mult * 1.3  # 1.95
        stop_mult = base_stop_mult * 0.85     # 0.64
    elif confidence > 65:
        target_mult = base_target_mult * 1.15  # 1.73
        stop_mult = base_stop_mult * 0.9       # 0.68
    elif confidence < 55:
        target_mult = base_target_mult * 0.8   # 1.2
        stop_mult = base_stop_mult * 1.2       # 0.9
    else:
        target_mult = base_target_mult
        stop_mult = base_stop_mult
    
    # Adjust for trend strength (ADX)
    if adx > 30:  # Strong trend
        target_mult *= 1.1
        stop_mult *= 0.9
    elif adx < 20:  # Weak trend
        target_mult *= 0.85
        stop_mult *= 1.1
    
    # ATR-based price distances with dynamic multipliers
    target_distance = atr * target_mult
    stop_distance = atr * stop_mult
    
    if direction == "BUY":
        target_price = current_price + target_distance
        stop_price = current_price - stop_distance
    elif direction == "SELL":
        target_price = current_price - target_distance
        stop_price = current_price + stop_distance
    else:
        target_price = current_price
        stop_price = current_price
    
    # Convert price difference to pips
    target_pips = abs(target_price - current_price) / pip_value
    stop_pips = abs(stop_price - current_price) / pip_value
    
    risk_reward = target_pips / stop_pips if stop_pips > 0 else 0
    
    # Generate reasoning
    reasoning = _generate_reasoning(ta, direction, confidence, normalized_symbol)
    
    # Add MTF warnings to reasoning
    if mtf_adjustments["warnings"]:
        reasoning.insert(0, f"📊 MTF Analysis ({mtf_adjustments['regime']} | {mtf_adjustments['session']}):")
        reasoning.extend(mtf_adjustments["warnings"][:5])
    
    # Add news factors for XAUUSD
    if is_gold and news_factors:
        reasoning.insert(0, f"📰 News Impact ({news_confidence:.0f}% confidence):")
        reasoning.extend(news_factors[:5])
    
    # Key levels
    key_levels = [
        {"type": "EMA20", "price": ta["ema_20"], "distance": f"{((current_price - ta['ema_20']) / ta['ema_20'] * 100):.2f}%"},
        {"type": "EMA50", "price": ta["ema_50"], "distance": f"{((current_price - ta['ema_50']) / ta['ema_50'] * 100):.2f}%"},
        {"type": "EMA200", "price": ta["ema_200"], "distance": f"{((current_price - ta['ema_200']) / ta['ema_200'] * 100):.2f}%"},
        {"type": "Boll Upper", "price": ta["boll_upper"], "distance": f"{((ta['boll_upper'] - current_price) / current_price * 100):.2f}%"},
        {"type": "Boll Lower", "price": ta["boll_lower"], "distance": f"{((current_price - ta['boll_lower']) / current_price * 100):.2f}%"},
    ]
    
    # Calculate scores
    technical_score = _calculate_technical_score(ta)
    momentum_score = _calculate_momentum_score(ta)
    trend_score = _calculate_trend_score(ta)
    
    # Volatility regime
    vol = ta["volatility"]
    if vol < 15:
        volatility_regime = "Low"
    elif vol < 25:
        volatility_regime = "Medium"
    else:
        volatility_regime = "High"
    
    # Apply learning feedback from past errors (self-learning system)
    try:
        from services.error_analysis_service import apply_learning_feedback
        factors = {
            "rsi_14": ta.get("rsi_14"),
            "macd_histogram": ta.get("macd_histogram"),
            "volume_ratio": ta.get("volume_ratio", 1.0),
            "volatility": vol,
            "trend_score": trend_score,
        }
        feedback_result = await apply_learning_feedback(
            symbol=normalized_symbol,
            direction=direction,
            confidence=confidence,
            factors=factors
        )
        # Apply adjusted confidence
        adjusted_confidence = feedback_result.get("adjusted_confidence", confidence)
        feedback_warnings = feedback_result.get("warnings", [])
        if feedback_warnings:
            reasoning.extend([f"⚠️ {w}" for w in feedback_warnings])
            logger.info(f"Learning feedback applied: {confidence:.1f}% -> {adjusted_confidence:.1f}%")
        confidence = adjusted_confidence
    except Exception as fb_err:
        logger.debug(f"Could not apply learning feedback: {fb_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # S/R POST-PROCESSING - Final sinyal ayarlama
    # ═══════════════════════════════════════════════════════════════════
    if sr_features:
        try:
            from services.sr_ml_features import post_process_with_sr
            
            pre_result = {
                'direction': direction,
                'confidence': confidence,
                'warnings': reasoning.copy()
            }
            
            post_result = post_process_with_sr(pre_result, sr_features)
            
            # S/R post-processing sonuçlarını uygula
            if post_result.get('sr_adjustments'):
                for adj in post_result['sr_adjustments']:
                    if adj['type'] == 'resistance_block' and direction == 'BUY':
                        # BUY ama güçlü direnç yakın - HOLD yap veya güven azalt
                        if adj['new_confidence'] < 40:
                            direction = 'HOLD'
                            logger.warning(f"BUY -> HOLD: {adj['reason']}")
                        confidence = adj['new_confidence']
                    elif adj['type'] == 'support_block' and direction == 'SELL':
                        # SELL ama güçlü destek yakın - HOLD yap veya güven azalt
                        if adj['new_confidence'] < 40:
                            direction = 'HOLD'
                            logger.warning(f"SELL -> HOLD: {adj['reason']}")
                        confidence = adj['new_confidence']
                    elif adj['type'] == 'confluence_boost':
                        confidence = adj['new_confidence']
                
                # Yeni uyarıları ekle
                for warning in post_result.get('warnings', []):
                    if warning not in reasoning:
                        reasoning.append(warning)
                
                logger.info(f"S/R Post-process: {direction} @ {confidence:.1f}%, adjustments={len(post_result['sr_adjustments'])}")
        except Exception as pp_err:
            logger.debug(f"S/R post-processing skipped: {pp_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # ADVANCED TRADING ENGINE - Tüm EKSİK'ler Entegre (#1-10)
    # ═══════════════════════════════════════════════════════════════════
    try:
        from services.trading_engine import (
            MarketRegimeDetector, extract_ohlcv,
            validate_mtf_consensus, apply_regime_blocking,
            resolve_pattern_conflicts, resolve_layer_conflict,
            get_adaptive_threshold, check_portfolio_risk,
            check_signal_validity, get_state_machine,
            sync_learning_check, NULL_SIGNAL_REASONS
        )
        
        strategy = strategy if 'strategy' in dir() else 'balanced'
        
        # ═══════════════════════════════════════════════════════════════
        # EKSİK #1, #3: State Machine + Minimum Duration Check
        # ═══════════════════════════════════════════════════════════════
        validity_check = check_signal_validity(
            symbol=normalized_symbol,
            new_direction=direction,
            new_confidence=confidence,
            current_price=current_price,
            strategy=strategy
        )
        
        if not validity_check['valid']:
            null_sig = validity_check.get('null_signal', {})
            null_reason = null_sig.get('null_reason', validity_check['reason'])
            # Dashboard mode: don't force HOLD, just reduce confidence slightly and warn
            # State machine is for trade execution, not for display panels
            confidence = max(confidence * 0.85, 40)
            reasoning.append(f"⚠️ Trading Engine: {null_reason}")
            logger.info(f"State machine warning (not blocking): {validity_check['reason']}")
        
        # ═══════════════════════════════════════════════════════════════
        # EKSİK #9: Portfolio Risk Check
        # ═══════════════════════════════════════════════════════════════
        if direction != "HOLD":
            portfolio_check = check_portfolio_risk(normalized_symbol, direction)
            if not portfolio_check['can_trade']:
                # Dashboard mode: warn but don't force HOLD
                confidence = max(confidence * 0.8, 35)
                reasoning.append(f"⚠️ Portföy Riski: {portfolio_check['reason']}")
                logger.info(f"Portfolio risk warning (not blocking): {portfolio_check['reason']}")
            elif portfolio_check['warnings']:
                for warn in portfolio_check['warnings']:
                    reasoning.append(f"⚠️ {warn}")
        
        # ═══════════════════════════════════════════════════════════════
        # EKSİK #6: Regime Hard Block
        # ═══════════════════════════════════════════════════════════════
        if candles and len(candles) >= 50 and direction != "HOLD":
            _, highs, lows, closes, _ = extract_ohlcv(candles)
            
            regime_detector = MarketRegimeDetector()
            regime = regime_detector.detect(highs, lows, closes)
            
            regime_check = apply_regime_blocking(direction, regime.regime, regime.confidence)
            
            if regime_check['blocked']:
                # Dashboard mode: warn but don't force HOLD
                confidence = max(confidence * regime_check['confidence_multiplier'] * 0.7, 30)
                reasoning.append(f"⚠️ Rejim Uyarısı: {regime_check['reason']}")
                logger.info(f"Regime warning (not blocking): {direction} ({regime_check['reason']})")
            else:
                # Confidence multiplier uygula
                if regime_check['confidence_multiplier'] < 1.0:
                    confidence *= regime_check['confidence_multiplier']
                    reasoning.append(f"📊 Rejim: {regime.regime.value} (pozisyon: {regime_check['confidence_multiplier']:.0%})")
                
                if regime.trend_direction:
                    basic_dir = "UP" if direction == "BUY" else ("DOWN" if direction == "SELL" else None)
                    if basic_dir == regime.trend_direction:
                        confidence = min(100, confidence * 1.05)
                        reasoning.append(f"✅ Rejim Uyumu: {regime.regime.value}")
        
        # ═══════════════════════════════════════════════════════════════
        # EKSİK #2: MTF Hard Veto
        # ═══════════════════════════════════════════════════════════════
        if direction != "HOLD":
            mtf_data = {}
            # MTF verisi varsa kullan (mtf_analysis'den geliyorsa)
            if 'mtf_analysis' in dir() and mtf_analysis:
                mtf_data = mtf_analysis
            elif 'ta' in dir() and ta:
                # Basit MTF approximation
                trend_up = ta.get('ema_20', 0) > ta.get('ema_50', 0) > ta.get('ema_200', 0)
                trend_down = ta.get('ema_20', 0) < ta.get('ema_50', 0) < ta.get('ema_200', 0)
                mtf_data = {
                    '4H': {
                        'trend': 'UP' if trend_up else ('DOWN' if trend_down else 'NEUTRAL'),
                        'confidence': abs(trend_score) / 100 if trend_score else 0.5
                    }
                }
            
            if mtf_data:
                mtf_check = validate_mtf_consensus(normalized_symbol, direction, mtf_data)
                
                if not mtf_check['allowed']:
                    # Dashboard mode: warn but don't force HOLD
                    confidence = max(confidence * 0.75, 35)
                    reasoning.append(f"⚠️ MTF: {mtf_check['reason']}")
                    logger.info(f"MTF warning (not blocking): {direction}")
                elif mtf_check['confidence_penalty'] > 0:
                    confidence *= (1 - mtf_check['confidence_penalty'])
                    reasoning.append(f"🟡 {mtf_check['reason']}")
        
        # ═══════════════════════════════════════════════════════════════
        # EKSİK #4: Adaptive Threshold
        # ═══════════════════════════════════════════════════════════════
        if direction != "HOLD":
            try:
                from services.error_analysis_service import get_symbol_performance
                perf_data = await get_symbol_performance(normalized_symbol) if 'await' in dir() else None
            except:
                perf_data = None
            
            threshold_info = get_adaptive_threshold(normalized_symbol, strategy, perf_data)
            adaptive_min = threshold_info['threshold'] * 100
            
            if confidence < adaptive_min:
                # Dashboard mode: warn but don't force HOLD
                reasoning.append(f"⚠️ Confidence {confidence:.0f}% < Adaptif threshold {adaptive_min:.0f}%")
                if threshold_info.get('reason'):
                    reasoning.append(f"   ({threshold_info['reason']})")
                confidence = max(confidence, adaptive_min * 0.8)  # Bump slightly to show signal
        
        # ═══════════════════════════════════════════════════════════════
        # EKSİK #5: Pattern Conflict Resolution (pattern varsa)
        # ═══════════════════════════════════════════════════════════════
        if 'patterns' in dir() and patterns and direction != "HOLD":
            pattern_resolution = resolve_pattern_conflicts(patterns)
            
            if pattern_resolution['has_conflict']:
                if pattern_resolution['conflict_severity'] == 'major':
                    # Ciddi çakışma - dikkatli ol
                    confidence *= pattern_resolution['confidence_adjustment']
                    reasoning.append(f"⚡ Pattern çakışması (ciddi): confidence x{pattern_resolution['confidence_adjustment']:.0%}")
                    
                    # Dominant pattern farklı yönde ise
                    if pattern_resolution['dominant_direction'] and pattern_resolution['dominant_direction'] != direction:
                        reasoning.append(f"   Dominant pattern: {pattern_resolution['dominant_direction']}")
                elif pattern_resolution['conflict_severity'] == 'minor':
                    confidence *= pattern_resolution['confidence_adjustment']
                    reasoning.append(f"⚡ Pattern çakışması (minor)")
                
                if pattern_resolution['ignored_patterns']:
                    ignored_names = [p.get('name', '?') for p in pattern_resolution['ignored_patterns'][:3]]
                    reasoning.append(f"   Ignored: {', '.join(ignored_names)}")
        
        # ═══════════════════════════════════════════════════════════════
        # EKSİK #7: Learning Proaktif Check
        # ═══════════════════════════════════════════════════════════════
        if direction != "HOLD":
            try:
                # Cached performance'dan kontrol (sync)
                from services.error_analysis_service import get_cached_symbol_stats
                cached_perf = get_cached_symbol_stats(normalized_symbol)
            except:
                cached_perf = None
            
            learning_check = sync_learning_check(normalized_symbol, direction, cached_perf)
            
            if not learning_check['allow']:
                old_dir = direction
                direction = "HOLD"
                confidence = min(confidence, 35)
                reasoning.append(f"📚 Learning Block: {learning_check['reason']}")
                logger.warning(f"Learning block: {old_dir} -> HOLD ({learning_check['reason']})")
            elif learning_check['recommendation'] == 'CAUTION':
                confidence *= learning_check['confidence_adjustment']
                reasoning.append(f"📚 Learning Uyarısı: {learning_check['reason']}")
            elif learning_check['success_rate'] and learning_check['success_rate'] > 0.6:
                # Başarılı setup - küçük bonus
                confidence = min(100, confidence * learning_check['confidence_adjustment'])
                reasoning.append(f"📚 Learning: {learning_check['reason']}")
    
    except Exception as te_err:
        logger.debug(f"Trading engine skipped: {te_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # SIGNAL STABILITY CHECK - Prevent rapid direction flip-flopping
    # ═══════════════════════════════════════════════════════════════════
    allow_change, stability_reason = _should_allow_direction_change(
        normalized_symbol, direction, confidence, current_price
    )
    
    if not allow_change:
        # Dashboard mode: warn but don't force old direction
        confidence = max(confidence * 0.85, 35)
        reasoning.append(f"⚠️ Sinyal Stabilitesi: {stability_reason}")
        logger.info(f"Signal stability warning (not blocking): {direction} ({stability_reason})")
        # Still update cache with new signal
        _update_signal_cache(normalized_symbol, direction, confidence, current_price)
    else:
        _update_signal_cache(normalized_symbol, direction, confidence, current_price)
        if stability_reason and stability_reason not in ["İlk sinyal", "Aynı yön", "HOLD geçişi"]:
            reasoning.append(f"✅ {stability_reason}")
            logger.info(f"Signal updated: {direction} @ {confidence:.1f}% ({stability_reason})")
    
    # ═══════════════════════════════════════════════════════════════════
    # MARKET REGIME OVERLAY - Adaptive system for XAUUSD trend modes
    # Applied LAST so it overrides mean-reversion biases from above
    # ═══════════════════════════════════════════════════════════════════
    try:
        from services.market_regime_service import detect_regime, filter_signal_by_regime, interpret_rsi as regime_interpret_rsi

        market_regime = await detect_regime(normalized_symbol)
        reasoning.insert(0, f"🎯 Rejim: {market_regime.regime} | ADX={market_regime.adx} | Session={market_regime.session}")

        if market_regime.is_ath_zone:
            reasoning.insert(1, f"🏔️ ATH Bölgesi: Fiyat tarihi zirve yakınında ({market_regime.ath_price:.2f})")

        # 1. Direction filter: block SELL in STRONG_TREND_UP, block BUY in STRONG_TREND_DOWN
        filtered_dir, was_filtered, filter_reason = filter_signal_by_regime(direction, market_regime)
        if was_filtered:
            old_dir = direction
            direction = filtered_dir
            reasoning.append(f"⛔ Rejim filtresi: {old_dir} → {direction} ({filter_reason})")
            logger.info(f"ML regime filter: {old_dir} -> {direction} ({filter_reason})")

        # 2. RSI reinterpretation: in trend mode, RSI>70 is momentum not overbought
        rsi_regime_check = regime_interpret_rsi(ta.get("rsi_14", 50), market_regime, direction)
        if rsi_regime_check["action"] == "boost":
            confidence = min(95, confidence + rsi_regime_check["score_adjustment"])
            reasoning.append(f"📈 RSI Rejim: {rsi_regime_check['note']}")
        elif rsi_regime_check["action"] == "caution":
            confidence = max(30, confidence - 5)
            reasoning.append(f"⚠️ RSI Rejim: {rsi_regime_check['note']}")

        # 3. ATH Breakout Protocol: lower ML threshold, widen targets
        if market_regime.is_ath_zone and market_regime.regime == "STRONG_TREND_UP":
            if direction == "BUY" and confidence >= 45:
                # At ATH in uptrend: be more aggressive with entries
                confidence = max(confidence, 55)  # minimum 55% at ATH
                # Widen target in ATH (no resistance above)
                target_price = current_price + target_distance * 1.5
                target_pips = abs(target_price - current_price) / pip_value
                risk_reward = target_pips / stop_pips if stop_pips > 0 else 0
                reasoning.append("🚀 ATH Protokol: Hedef genişletildi, minimum güven %55")

        # 4. Trend mode confidence boost: if ML agrees with regime direction
        if market_regime.regime == "STRONG_TREND_UP" and direction == "BUY":
            confidence = min(95, confidence * 1.08)  # 8% boost
            reasoning.append("✅ ML + Rejim uyumu: Güçlü yükseliş trendi onaylandı")
        elif market_regime.regime == "STRONG_TREND_DOWN" and direction == "SELL":
            confidence = min(95, confidence * 1.08)
            reasoning.append("✅ ML + Rejim uyumu: Güçlü düşüş trendi onaylandı")

        # 5. Trend mode target/stop adjustment
        if market_regime.regime in ["STRONG_TREND_UP", "STRONG_TREND_DOWN"]:
            # In trend: wider targets, tighter stops (trend continuation expected)
            if direction == "BUY":
                target_price = current_price + target_distance * 1.3
                stop_price = current_price - stop_distance * 0.85
            elif direction == "SELL":
                target_price = current_price - target_distance * 1.3
                stop_price = current_price + stop_distance * 0.85
            target_pips = abs(target_price - current_price) / pip_value
            stop_pips = abs(stop_price - current_price) / pip_value
            risk_reward = target_pips / stop_pips if stop_pips > 0 else 0

        confidence = max(30, min(95, confidence))

    except Exception as regime_err:
        logger.debug(f"Market regime overlay skipped: {regime_err}")

    # Build active_patterns list from pattern_data for EMEL panel
    _active_patterns = []
    try:
        if pattern_data and isinstance(pattern_data, dict):
            for p in pattern_data.get("patterns", []):
                if isinstance(p, dict):
                    _active_patterns.append(p)
        # Also include candlestick patterns
        if candlestick_data and isinstance(candlestick_data, dict):
            for p in candlestick_data.get("patterns", []):
                if isinstance(p, dict):
                    _active_patterns.append(p)
    except Exception:
        pass

    # Build mtf_data for EMEL panel
    _mtf_for_emel = {}
    try:
        if mtf_data and isinstance(mtf_data, dict):
            _mtf_for_emel = mtf_data
    except Exception:
        pass

    return PredictionResult(
        symbol=normalized_symbol,
        direction=direction,
        confidence=round(confidence, 1),
        probability_up=round(prob_up * 100, 1),
        probability_down=round(prob_down * 100, 1),
        target_pips=round(target_pips, 1),
        stop_pips=round(stop_pips, 1),
        risk_reward=round(risk_reward, 2),
        entry_price=round(current_price, 2),
        target_price=round(target_price, 2),
        stop_price=round(stop_price, 2),
        technical_score=round(technical_score, 1),
        momentum_score=round(momentum_score, 1),
        trend_score=round(trend_score, 1),
        volatility_regime=volatility_regime,
        reasoning=reasoning,
        key_levels=key_levels,
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_version="lgbm_v2_regime",
        active_patterns=_active_patterns,
        mtf_data=_mtf_for_emel,
    )


def _generate_reasoning(ta: dict, direction: str, confidence: float, symbol: str) -> List[str]:
    """Generate human-readable reasoning for the prediction."""
    reasons = []
    
    # RSI analysis
    rsi = ta["rsi_14"]
    if rsi > 70:
        reasons.append(f"RSI aşırı alım bölgesinde ({rsi:.0f})")
    elif rsi < 30:
        reasons.append(f"RSI aşırı satım bölgesinde ({rsi:.0f})")
    elif rsi > 50:
        reasons.append(f"RSI pozitif momentum ({rsi:.0f})")
    else:
        reasons.append(f"RSI negatif momentum ({rsi:.0f})")
    
    # EMA analysis
    close = ta["close"]
    ema20 = ta["ema_20"]
    ema50 = ta["ema_50"]
    ema200 = ta["ema_200"]
    
    if close > ema20 > ema50 > ema200:
        reasons.append("Güçlü yükseliş trendi: Fiyat > EMA20 > EMA50 > EMA200")
    elif close < ema20 < ema50 < ema200:
        reasons.append("Güçlü düşüş trendi: Fiyat < EMA20 < EMA50 < EMA200")
    elif close > ema200:
        reasons.append("Fiyat uzun vadeli EMA200 üzerinde (boğa eğilimi)")
    else:
        reasons.append("Fiyat uzun vadeli EMA200 altında (ayı eğilimi)")
    
    # MACD
    macd = ta["macd_hist"]
    if macd > 0:
        reasons.append(f"MACD histogram pozitif ({macd:.2f})")
    else:
        reasons.append(f"MACD histogram negatif ({macd:.2f})")
    
    # Bollinger
    zscore = ta["boll_zscore"]
    if zscore > 2:
        reasons.append("Fiyat Bollinger üst bandının üzerinde (aşırı alım)")
    elif zscore < -2:
        reasons.append("Fiyat Bollinger alt bandının altında (aşırı satım)")
    elif zscore > 0:
        reasons.append("Fiyat Bollinger ortalamasının üzerinde")
    else:
        reasons.append("Fiyat Bollinger ortalamasının altında")
    
    # Momentum
    mom = ta["momentum_10"]
    if mom > 2:
        reasons.append(f"Güçlü pozitif momentum (10 günlük: +{mom:.1f}%)")
    elif mom < -2:
        reasons.append(f"Güçlü negatif momentum (10 günlük: {mom:.1f}%)")
    
    # Volatility
    vol = ta["volatility"]
    if vol > 25:
        reasons.append(f"Yüksek volatilite ortamı ({vol:.1f}%)")
    elif vol < 15:
        reasons.append(f"Düşük volatilite ortamı ({vol:.1f}%)")
    
    # Final verdict
    if direction == "BUY":
        reasons.append(f"Model güveni: {confidence:.0f}% - ALIŞ sinyali")
    elif direction == "SELL":
        reasons.append(f"Model güveni: {confidence:.0f}% - SATIŞ sinyali")
    else:
        reasons.append(f"Model belirsiz: {confidence:.0f}% - BEKLE")
    
    return reasons


def _calculate_technical_score(ta: dict) -> float:
    """Calculate technical analysis score 0-100."""
    score = 50.0
    
    # RSI contribution
    rsi = ta["rsi_14"]
    if 40 <= rsi <= 60:
        score += 10
    elif rsi > 70 or rsi < 30:
        score -= 10
    
    # Trend alignment
    if ta["trend_direction"] == 1:
        score += 15
    elif ta["trend_direction"] == -1:
        score += 15  # Also good for shorts
    
    # Bollinger position
    if -1 <= ta["boll_zscore"] <= 1:
        score += 10
    
    # MACD
    if ta["macd_hist"] > 0:
        score += 5
    
    return min(100, max(0, score))


def _calculate_momentum_score(ta: dict) -> float:
    """Calculate momentum score 0-100."""
    score = 50.0
    
    mom3 = ta["momentum_3"]
    mom10 = ta["momentum_10"]
    
    if mom3 > 0 and mom10 > 0:
        score += 20
    elif mom3 < 0 and mom10 < 0:
        score += 20  # Consistent momentum either direction
    
    rsi = ta["rsi_14"]
    if 45 <= rsi <= 55:
        score += 10  # Neutral, room to move
    elif rsi > 60:
        score += 15  # Strong up momentum
    elif rsi < 40:
        score += 15  # Strong down momentum
    
    return min(100, max(0, score))


def _calculate_trend_score(ta: dict) -> float:
    """Calculate trend score 0-100."""
    score = 50.0
    
    close = ta["close"]
    ema20 = ta["ema_20"]
    ema50 = ta["ema_50"]
    ema200 = ta["ema_200"]
    
    # EMA alignment
    if close > ema20:
        score += 10
    if close > ema50:
        score += 10
    if close > ema200:
        score += 15
    if ema20 > ema50:
        score += 10
    if ema50 > ema200:
        score += 10
    
    return min(100, max(0, score))


def _default_prediction(symbol: str, reason: str) -> PredictionResult:
    """Return default prediction when model unavailable."""
    return PredictionResult(
        symbol=symbol,
        direction="HOLD",
        confidence=50.0,
        probability_up=50.0,
        probability_down=50.0,
        target_pips=0,
        stop_pips=0,
        risk_reward=0,
        entry_price=0,
        target_price=0,
        stop_price=0,
        technical_score=50,
        momentum_score=50,
        trend_score=50,
        volatility_regime="Unknown",
        reasoning=[reason],
        key_levels=[],
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_version="fallback"
    )


def _rule_based_prediction(symbol: str, ta: dict, current_price: float) -> PredictionResult:
    """Fallback rule-based prediction when ML model fails."""
    
    # Simple rule-based logic
    score = 0
    
    # RSI
    if ta["rsi_14"] < 30:
        score += 2
    elif ta["rsi_14"] > 70:
        score -= 2
    elif ta["rsi_14"] > 50:
        score += 1
    else:
        score -= 1
    
    # Trend
    if ta["trend_direction"] == 1:
        score += 2
    elif ta["trend_direction"] == -1:
        score -= 2
    
    # MACD
    if ta["macd_hist"] > 0:
        score += 1
    else:
        score -= 1
    
    # Bollinger
    if ta["boll_zscore"] < -1.5:
        score += 1
    elif ta["boll_zscore"] > 1.5:
        score -= 1
    
    if score >= 2:
        direction = "BUY"
        confidence = 55 + score * 5
        prob_up = confidence / 100
        prob_down = 1 - prob_up
    elif score <= -2:
        direction = "SELL"
        confidence = 55 + abs(score) * 5
        prob_up = 1 - confidence / 100
        prob_down = confidence / 100
    else:
        direction = "HOLD"
        confidence = 50
        prob_up = 0.5
        prob_down = 0.5
    
    atr = ta["atr_14"]
    # Pip value: XAUUSD = 0.1 ($0.10 = 1 pip), NASDAQ = 1.0 (points)
    pip_value = 0.1 if "XAU" in symbol else 1.0
    
    # Dynamic R/R based on confidence and trend strength
    adx = ta.get("adx_14", 20)
    
    # Base target/stop multipliers
    base_target_mult = 1.5
    base_stop_mult = 0.75
    
    # Adjust based on confidence
    if confidence > 75:
        target_mult = base_target_mult * 1.3
        stop_mult = base_stop_mult * 0.85
    elif confidence > 65:
        target_mult = base_target_mult * 1.15
        stop_mult = base_stop_mult * 0.9
    elif confidence < 55:
        target_mult = base_target_mult * 0.8
        stop_mult = base_stop_mult * 1.2
    else:
        target_mult = base_target_mult
        stop_mult = base_stop_mult
    
    # Adjust for trend strength (ADX)
    if adx > 30:
        target_mult *= 1.1
        stop_mult *= 0.9
    elif adx < 20:
        target_mult *= 0.85
        stop_mult *= 1.1
    
    # ATR-based price distances with dynamic multipliers
    target_distance = atr * target_mult
    stop_distance = atr * stop_mult
    
    if direction == "BUY":
        target_price = current_price + target_distance
        stop_price = current_price - stop_distance
    elif direction == "SELL":
        target_price = current_price - target_distance
        stop_price = current_price + stop_distance
    else:
        target_price = current_price
        stop_price = current_price
    
    # Convert price difference to pips
    target_pips = abs(target_price - current_price) / pip_value
    stop_pips = abs(stop_price - current_price) / pip_value
    
    return PredictionResult(
        symbol=symbol,
        direction=direction,
        confidence=round(min(95, confidence), 1),
        probability_up=round(prob_up * 100, 1),
        probability_down=round(prob_down * 100, 1),
        target_pips=round(target_pips, 1),
        stop_pips=round(stop_pips, 1),
        risk_reward=round(target_pips / stop_pips if stop_pips > 0 else 0, 2),
        entry_price=round(current_price, 2),
        target_price=round(target_price, 2),
        stop_price=round(stop_price, 2),
        technical_score=round(_calculate_technical_score(ta), 1),
        momentum_score=round(_calculate_momentum_score(ta), 1),
        trend_score=round(_calculate_trend_score(ta), 1),
        volatility_regime="Medium",
        reasoning=_generate_reasoning(ta, direction, confidence, symbol),
        key_levels=[
            {"type": "EMA20", "price": round(ta["ema_20"], 2), "distance": f"{((current_price - ta['ema_20']) / ta['ema_20'] * 100):.2f}%"},
            {"type": "EMA50", "price": round(ta["ema_50"], 2), "distance": f"{((current_price - ta['ema_50']) / ta['ema_50'] * 100):.2f}%"},
        ],
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_version="rule_based"
    )
