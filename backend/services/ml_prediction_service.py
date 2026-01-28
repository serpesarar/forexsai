"""
ML Prediction Service - Loads trained models and generates trading predictions.
Supports NASDAQ and XAUUSD with direction prediction and pip targets.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Literal
import numpy as np

logger = logging.getLogger(__name__)

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


def _build_feature_vector(symbol: str, ta: dict, candles: list) -> Optional[np.ndarray]:
    """Build feature vector for model prediction."""
    
    model = _load_model(symbol)
    if model is None:
        return None
    
    features = _model_features.get(symbol, [])
    if not features:
        return None
    
    # Create feature dict with defaults
    feature_dict = {}
    
    # Map computed indicators to feature names
    indicator_map = {
        "rsi_14": ta["rsi_14"],
        "rsi_7": ta["rsi_7"],
        "rsi_14_M30": ta["rsi_14"],
        "rsi_7_M30": ta["rsi_7"],
        "rsi_14_H1": ta["rsi_14"],
        "rsi_7_H1": ta["rsi_7"],
        "rsi_14_H4": ta["rsi_14"],
        "rsi_7_H4": ta["rsi_7"],
        "ema_20": ta["ema_20"],
        "ema_50": ta["ema_50"],
        "ema_200": ta["ema_200"],
        "ema_20_M30": ta["ema_20"],
        "ema_50_M30": ta["ema_50"],
        "ema_200_M30": ta["ema_200"],
        "ema_20_H1": ta["ema_20"],
        "ema_50_H1": ta["ema_50"],
        "ema_200_H1": ta["ema_200"],
        "ema_20_H4": ta["ema_20"],
        "ema_50_H4": ta["ema_50"],
        "ema_200_H4": ta["ema_200"],
        "sma_20": ta["sma_20"],
        "sma_50": ta["sma_50"],
        "sma_200": ta["sma_200"],
        "sma_20_M30": ta["sma_20"],
        "sma_50_M30": ta["sma_50"],
        "sma_200_M30": ta["sma_200"],
        "sma_20_H1": ta["sma_20"],
        "sma_50_H1": ta["sma_50"],
        "sma_200_H1": ta["sma_200"],
        "sma_20_H4": ta["sma_20"],
        "sma_50_H4": ta["sma_50"],
        "sma_200_H4": ta["sma_200"],
        "macd_line": ta["macd_line"],
        "macd_signal": ta["macd_signal"],
        "macd_hist": ta["macd_hist"],
        "macd_hist_diff": ta["macd_hist_diff"],
        "macd_line_M30": ta["macd_line"],
        "macd_signal_M30": ta["macd_signal"],
        "macd_hist_M30": ta["macd_hist"],
        "macd_hist_diff_M30": ta["macd_hist_diff"],
        "macd_line_H1": ta["macd_line"],
        "macd_signal_H1": ta["macd_signal"],
        "macd_hist_H1": ta["macd_hist"],
        "macd_hist_diff_H1": ta["macd_hist_diff"],
        "macd_line_H4": ta["macd_line"],
        "macd_signal_H4": ta["macd_signal"],
        "macd_hist_H4": ta["macd_hist"],
        "macd_hist_diff_H4": ta["macd_hist_diff"],
        "stoch_k": ta["stoch_k"],
        "stoch_d": ta["stoch_d"],
        "stoch_k_M30": ta["stoch_k"],
        "stoch_d_M30": ta["stoch_d"],
        "stoch_k_H1": ta["stoch_k"],
        "stoch_d_H1": ta["stoch_d"],
        "stoch_k_H4": ta["stoch_k"],
        "stoch_d_H4": ta["stoch_d"],
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
        "boll_upper_H1": ta["boll_upper"],
        "boll_lower_H1": ta["boll_lower"],
        "boll_middle_H1": ta["boll_middle"],
        "boll_width_H1": ta["boll_width"],
        "boll_zscore_H1": ta["boll_zscore"],
        "boll_upper_H4": ta["boll_upper"],
        "boll_lower_H4": ta["boll_lower"],
        "boll_middle_H4": ta["boll_middle"],
        "boll_width_H4": ta["boll_width"],
        "boll_zscore_H4": ta["boll_zscore"],
        "atr_14": ta["atr_14"],
        "atr_pct": ta["atr_pct"],
        "atr_14_M30": ta["atr_14"],
        "atr_pct_M30": ta["atr_pct"],
        "atr_14_H1": ta["atr_14"],
        "atr_pct_H1": ta["atr_pct"],
        "atr_14_H4": ta["atr_14"],
        "atr_pct_H4": ta["atr_pct"],
        "williams_r": ta["williams_r"],
        "williams_r_M30": ta["williams_r"],
        "williams_r_H1": ta["williams_r"],
        "williams_r_H4": ta["williams_r"],
        "mfi": ta["mfi"],
        "mfi_M30": ta["mfi"],
        "mfi_H1": ta["mfi"],
        "mfi_H4": ta["mfi"],
        "adx": ta["adx"],
        "adx_M30": ta["adx"],
        "adx_H1": ta["adx"],
        "adx_H4": ta["adx"],
        "volatility": ta["volatility"],
        "volatility_M30": ta["volatility"],
        "volatility_H1": ta["volatility"],
        "volatility_H4": ta["volatility"],
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


async def get_ml_prediction(symbol: str) -> PredictionResult:
    """Get ML prediction for symbol with direction and pip targets."""
    from services.data_fetcher import fetch_eod_candles, fetch_30m_candles, fetch_latest_price
    
    # Normalize symbol
    normalized_symbol = "NDX.INDX" if symbol.upper() in ["NASDAQ", "NDX.INDX", "NDX"] else symbol.upper()
    
    # For XAUUSD, get news impact analysis
    news_sentiment = 0.0
    news_confidence = 0.0
    news_factors = []
    is_gold = "XAU" in normalized_symbol
    
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
    
    # Fetch data - MODEL WAS TRAINED ON 30-MIN (M30) DATA!
    # Resample 5m candles to 30m to match training data
    candles_30m = await fetch_30m_candles(normalized_symbol, limit=300)
    live_price = await fetch_latest_price(normalized_symbol)
    
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
    
    # Compute technical indicators
    ta = _compute_technical_indicators(closes, highs, lows, volumes)
    ta["close"] = current_price
    
    # Build feature vector
    feature_df = _build_feature_vector(normalized_symbol, ta, candles)
    
    # Load model and predict
    model = _load_model(normalized_symbol)
    
    if model is None or feature_df is None:
        return _rule_based_prediction(normalized_symbol, ta, current_price)
    
    # ═══════════════════════════════════════════════════════════════════
    # MTF ADVANCED DATA INTEGRATION - Professional Trading Enhancements
    # ═══════════════════════════════════════════════════════════════════
    mtf_adjustments = {
        "confidence_multiplier": 1.0,
        "direction_override": None,
        "warnings": [],
        "session": "UNKNOWN",
        "regime": "UNKNOWN",
        "liquidity_sweep": False,
        "high_impact_event": None
    }
    
    try:
        from services.mtf_analysis_service import get_mtf_analysis
        mtf_data = await get_mtf_analysis(normalized_symbol)
        
        if mtf_data.get("success") and "advanced" in mtf_data:
            adv = mtf_data["advanced"]
            
            # 1. Market Regime Check
            regime = adv.get("market_regime", {})
            regime_type = regime.get("regime", "TRENDING")
            confidence_level = regime.get("confidence_level", "LOW_CONFIDENCE")
            di_spread = regime.get("di_spread", 0)
            mtf_adjustments["regime"] = regime_type
            
            if confidence_level == "CONFLICTING":
                mtf_adjustments["confidence_multiplier"] *= 0.7
                mtf_adjustments["warnings"].append("⚠️ DI çelişkili - trend belirsiz")
            elif confidence_level == "LOW_CONFIDENCE":
                mtf_adjustments["confidence_multiplier"] *= 0.85
            
            if regime_type == "RANGING" and di_spread < 10:
                mtf_adjustments["confidence_multiplier"] *= 0.8
                mtf_adjustments["warnings"].append("📊 Yan piyasa - trade riskli")
            
            # 2. Price Action / Liquidity Sweep Detection
            price_action = adv.get("price_action", {})
            structure_quality = price_action.get("structure_quality", "CHOPPY")
            liquidity_sweep = price_action.get("liquidity_sweep", False)
            equal_highs = price_action.get("equal_highs_count", 0)
            equal_lows = price_action.get("equal_lows_count", 0)
            mtf_adjustments["liquidity_sweep"] = liquidity_sweep
            
            if structure_quality == "FAKEOUT_TRAP":
                mtf_adjustments["confidence_multiplier"] *= 0.5
                mtf_adjustments["warnings"].append("🚨 FAKEOUT TRAP tespit edildi!")
            elif structure_quality == "CHOPPY":
                mtf_adjustments["confidence_multiplier"] *= 0.7
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
            session_vol = pos_sizing.get("session_volatility", "NORMAL")
            high_impact = pos_sizing.get("high_impact_event")
            vol_adj = pos_sizing.get("volatility_adjustment", 1.0)
            mtf_adjustments["session"] = session
            mtf_adjustments["high_impact_event"] = high_impact
            
            if session == "ASIA":
                mtf_adjustments["confidence_multiplier"] *= 0.85
                mtf_adjustments["warnings"].append("🌙 Asya seansı - düşük likidite")
            
            if high_impact == "NFP_DAY":
                mtf_adjustments["confidence_multiplier"] *= 0.4
                mtf_adjustments["direction_override"] = "HOLD"
                mtf_adjustments["warnings"].append("🔴 NFP GÜNÜ - Trade önerilmez!")
            elif high_impact == "FOMC_POTENTIAL":
                mtf_adjustments["confidence_multiplier"] *= 0.6
                mtf_adjustments["warnings"].append("🟠 FOMC potansiyeli - dikkatli ol")
            elif high_impact == "CPI_WEEK":
                mtf_adjustments["confidence_multiplier"] *= 0.8
                mtf_adjustments["warnings"].append("🟡 CPI haftası - volatilite bekleniyor")
            
            # 4. Correlation Check
            correlation = adv.get("correlation", {})
            if correlation:
                corr_confirms = correlation.get("correlation_confirms", True)
                conflicting = correlation.get("conflicting_signals", [])
                
                if not corr_confirms and conflicting:
                    mtf_adjustments["confidence_multiplier"] *= 0.75
                    for sig in conflicting[:2]:
                        mtf_adjustments["warnings"].append(f"⚡ Korelasyon çelişkisi: {sig}")
            
            logger.info(f"MTF adjustments applied: mult={mtf_adjustments['confidence_multiplier']:.2f}, "
                       f"regime={regime_type}, session={session}, warnings={len(mtf_adjustments['warnings'])}")
            
    except Exception as mtf_err:
        logger.warning(f"MTF integration skipped: {mtf_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # SLIPPAGE MONITOR INTEGRATION
    # ═══════════════════════════════════════════════════════════════════
    slippage_data = {"position_multiplier": 1.0, "warning": None, "confidence_penalty": 0}
    try:
        from services.slippage_monitor import get_slippage_adjustment
        slippage_data = await get_slippage_adjustment()
        
        if slippage_data.get("high_slippage_mode"):
            mtf_adjustments["warnings"].append(slippage_data.get("warning", "⚠️ High slippage detected"))
            logger.info(f"Slippage adjustment: multiplier={slippage_data['position_multiplier']}, penalty={slippage_data['confidence_penalty']}%")
    except Exception as slip_err:
        logger.debug(f"Slippage monitor skipped: {slip_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # COT REPORT INTEGRATION (Institutional Positioning)
    # ═══════════════════════════════════════════════════════════════════
    cot_data = {"confidence_adjustment": 0, "signal": "NEUTRAL", "warning": None}
    try:
        from services.cot_report_service import get_cot_adjustment
        cot_data = await get_cot_adjustment(normalized_symbol)
        
        if cot_data.get("signal") == "TREND_EXHAUSTION":
            # Speculators overcrowded - reduce confidence significantly
            mtf_adjustments["confidence_multiplier"] *= 0.75
            mtf_adjustments["warnings"].append(cot_data.get("reason", "⚠️ COT: Trend exhaustion risk"))
        elif cot_data.get("confidence_adjustment", 0) != 0:
            # Apply COT adjustment
            adj = cot_data["confidence_adjustment"]
            if adj > 0:
                mtf_adjustments["confidence_multiplier"] *= (1 + adj)
            else:
                mtf_adjustments["confidence_multiplier"] *= (1 + adj)
        
        if cot_data.get("warning"):
            mtf_adjustments["warnings"].append(cot_data["warning"])
        
        logger.info(f"COT adjustment: signal={cot_data['signal']}, adj={cot_data['confidence_adjustment']:+.0%}, spec_long={cot_data.get('spec_long_percent', 50):.0f}%")
    except Exception as cot_err:
        logger.debug(f"COT integration skipped: {cot_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PATTERN ENGINE INTEGRATION
    # ═══════════════════════════════════════════════════════════════════
    pattern_data = {"patterns": [], "recommendation": "HOLD", "confidence_boost": 0}
    try:
        from services.pattern_analyzer import run_claude_pattern_analysis
        pattern_result = await run_claude_pattern_analysis(normalized_symbol, ["15m", "1h"], lang="tr")
        
        all_patterns = []
        bullish_count = 0
        bearish_count = 0
        total_confidence = 0
        
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
        
        # Apply pattern-based adjustments
        if len(all_patterns) > 0:
            avg_confidence = total_confidence / len(all_patterns)
            
            # Strong bullish/bearish pattern consensus boosts confidence
            if bullish_count >= 2 and bearish_count == 0:
                pattern_data["recommendation"] = "BUY"
                pattern_data["confidence_boost"] = min(0.15, avg_confidence / 1000)
                mtf_adjustments["confidence_multiplier"] *= (1 + pattern_data["confidence_boost"])
                mtf_adjustments["warnings"].append(f"📊 Pattern: {bullish_count} bullish pattern tespit edildi")
            elif bearish_count >= 2 and bullish_count == 0:
                pattern_data["recommendation"] = "SELL"
                pattern_data["confidence_boost"] = min(0.15, avg_confidence / 1000)
                mtf_adjustments["confidence_multiplier"] *= (1 + pattern_data["confidence_boost"])
                mtf_adjustments["warnings"].append(f"📊 Pattern: {bearish_count} bearish pattern tespit edildi")
            elif bullish_count > 0 and bearish_count > 0:
                # Mixed signals - reduce confidence
                mtf_adjustments["confidence_multiplier"] *= 0.9
                mtf_adjustments["warnings"].append(f"⚡ Pattern çelişkisi: {bullish_count} bullish vs {bearish_count} bearish")
        
        logger.info(f"Pattern Engine: {len(all_patterns)} patterns, bullish={bullish_count}, bearish={bearish_count}")
    except Exception as pattern_err:
        logger.debug(f"Pattern Engine integration skipped: {pattern_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # CANDLESTICK PATTERN INTEGRATION (M15, M30, H1, H4)
    # ═══════════════════════════════════════════════════════════════════
    candlestick_data = {"patterns": [], "signal": "NEUTRAL", "adjustment": 0}
    try:
        from services.candlestick_pattern_service import get_candlestick_adjustment
        candlestick_data = await get_candlestick_adjustment(normalized_symbol)
        
        if candlestick_data.get("has_patterns"):
            signal = candlestick_data.get("strongest_signal", "NEUTRAL")
            adjustment = candlestick_data.get("confidence_adjustment", 0)
            
            if signal == "BULLISH" and adjustment > 0:
                mtf_adjustments["confidence_multiplier"] *= (1 + adjustment)
                patterns_str = ", ".join(candlestick_data.get("patterns_summary", [])[:3])
                mtf_adjustments["warnings"].append(f"🕯️ Mum Formasyonu: {patterns_str}")
            elif signal == "BEARISH" and adjustment > 0:
                mtf_adjustments["confidence_multiplier"] *= (1 + adjustment)
                patterns_str = ", ".join(candlestick_data.get("patterns_summary", [])[:3])
                mtf_adjustments["warnings"].append(f"🕯️ Mum Formasyonu: {patterns_str}")
            elif signal == "MIXED":
                mtf_adjustments["confidence_multiplier"] *= 0.9
                mtf_adjustments["warnings"].append("⚡ Mum formasyonları çelişkili")
            
            logger.info(f"Candlestick: {candlestick_data['bullish_count']} bullish, "
                       f"{candlestick_data['bearish_count']} bearish, signal={signal}, adj={adjustment:+.0%}")
    except Exception as candle_err:
        logger.debug(f"Candlestick integration skipped: {candle_err}")
    
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
        # Higher thresholds + trend must align
        direction_threshold = 0.55 if is_gold else 0.55
        
        # Model says BUY
        if prob_up > direction_threshold:
            if trend_score >= 0:
                # Trend confirms BUY
                direction = "BUY"
                confidence = prob_up * 100
                if strong_bullish_trend:
                    confidence *= 1.1  # Boost for strong trend alignment
            else:
                # Trend conflicts - reduce confidence or switch to HOLD
                if trend_score < -0.3:
                    direction = "HOLD"
                    confidence = 50
                    mtf_adjustments["warnings"].append("⚠️ Model BUY ama trend bearish - bekle")
                    logger.warning(f"BUY signal rejected: trend_score={trend_score:.2f}")
                else:
                    direction = "BUY"
                    confidence = prob_up * 100 * 0.7  # Reduced confidence
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
                # Trend conflicts - reduce confidence or switch to HOLD
                if trend_score > 0.3:
                    direction = "HOLD"
                    confidence = 50
                    mtf_adjustments["warnings"].append("⚠️ Model SELL ama trend bullish - bekle")
                    logger.warning(f"SELL signal rejected: trend_score={trend_score:.2f}")
                else:
                    direction = "SELL"
                    confidence = prob_down * 100 * 0.7  # Reduced confidence
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
        # APPLY MTF ADJUSTMENTS TO FINAL DECISION
        # ═══════════════════════════════════════════════════════════════════
        if mtf_adjustments["direction_override"]:
            original_direction = direction
            direction = mtf_adjustments["direction_override"]
            logger.info(f"Direction overridden by MTF: {original_direction} -> {direction}")
        
        # Apply confidence multiplier from MTF analysis
        confidence = confidence * mtf_adjustments["confidence_multiplier"]
        confidence = max(25, min(95, confidence))  # Clamp 25-95%
        
    except Exception as e:
        logger.error(f"Model prediction error: {e}")
        return _rule_based_prediction(normalized_symbol, ta, current_price)
    
    # Calculate pip targets based on ATR
    atr = ta["atr_14"]
    # Pip value: XAUUSD = 0.01 (100 pips = $1), NASDAQ = 1.0 (points)
    pip_value = 0.01 if "XAU" in normalized_symbol else 1.0
    
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
        model_version="lgbm_v2"
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
    # Pip value: XAUUSD = 0.01 (100 pips = $1), NASDAQ = 1.0 (points)
    pip_value = 0.01 if "XAU" in symbol else 1.0
    
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
