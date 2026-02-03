# FOREXSAI KOD ANALİZİ - DETAYLI RAPOR
> Bu rapor otomatik olarak repo içinden üretildi. Büyük dosyaların TAM içerikleri fenced code blokları içinde verilmiştir.

## 1. Proje Yapısı Tespiti
- **Toplam Python dosyası sayısı (virtualenv hariç):** `92`

### Dizin Ağacı (özet)
```
/backend
  - .dockerignore
  - .env
  - .env.example
  - Dockerfile
  - __init__.py
  - config.py
  - fvg_detector.py
  - main.py
  - order_block_detector.py
  - railway.toml
  - requirements.txt
  - routers/
    - __init__.py
    - ai_analysis.py
    - auth.py
    - chart_data.py
    - claude_news.py
    - claude_patterns.py
    - claude_sentiment.py
    - data.py
    - earnings.py
    - fvg.py
    - learning.py
    - live_news.py
    - mtf_analysis.py
    - nasdaq.py
    - news.py
    - order_blocks.py
    - pattern_engine.py
    - prediction.py
    - rtyhiim.py
    - ta.py
    - xauusd.py
  - database/
    - __init__.py
    - schema.sql
    - supabase_client.py
    - migrations/
      - 004_failure_analyses.sql
      - 005_news_cache.sql
      - 006_membership_system.sql
      - 006_membership_system_v2.sql
      - 007_live_data_cache.sql
      - 008_security_fixes.sql
      - 009_security_warnings_fix.sql
  - models/
    - %80nasdaq_meta_lgb_v2.pkl
    - chart.py
    - model_lgbm_nasdaq.joblib
    - model_lgbm_xauusd.joblib
    - nasdaq.py
    - news.py
    - order_blocks.py
    - responses.py
    - rtyhiim.py
    - xau_meta_dir_lgbm_v2.pkl
    - xauusd.py
  - services/
    - adaptive_tp_sl.py
    - analysis_cache.py
    - api_cache.py
    - auth_service.py
    - background_scheduler.py
    - candlestick_pattern_service.py
    - chart_data_service.py
    - claude_news_analyzer.py
    - claude_signal_analyzer.py
    - comex_news_service.py
    - cot_report_service.py
    - data_fetcher.py
    - detailed_ai_analysis_service.py
    - earnings_service.py
    - email_service.py
    - error_analysis_service.py
    - gold_news_analyzer.py
    - gold_news_analyzer_v2.py
    - learning_analyzer.py
    - live_news_monitor.py
    - marketaux_service.py
    - ml_prediction_service.py
    - ml_service.py
    - mtf_analysis_service.py
    - news_fetcher.py
    - order_block_service.py
    - outcome_tracker.py
    - pattern_analyzer.py
    - pattern_engine_runner.py
    - prediction_logger.py
    - rtyhiim_service.py
    - sentiment_analyzer.py
    - slippage_monitor.py
    - sr_ml_features.py
    - ta_service.py
    - target_config.py
    - technical_indicators.py
    - translation_service.py
    - trend_analyzer.py
    - twitter_monitor.py
    - unified_news_analyzer.py
    - trading_engine/
      - __init__.py
      - confluence_engine.py
      - constants.py
      - decision_layers.py
      - helpers.py
      - mtf_analyzer.py
      - regime_detector.py
      - signal_state_machine.py
/frontend
  - .gitignore
  - netlify.toml
  - next-env.d.ts
  - next.config.js
  - package-lock.json
  - package.json
  - postcss.config.js
  - railway.toml
  - tailwind.config.ts
  - tsconfig.json
  - tsconfig.tsbuildinfo
  - vitest.config.ts
  - vitest.setup.ts
  - messages/
    - en.json
    - en_backup.json
    - tr.json
    - tr_backup.json
  - contexts/
    - DashboardEditContext.tsx
  - app/
    - globals.css
    - layout.tsx
    - page-new.tsx
    - page.tsx
    - page.tsx.backup
    - providers.tsx
  - tests/
    - orderBlockPanel.test.tsx
  - components/
    - AdaptiveTPSLPanel.tsx
    - AdvancedAnalysisPanel.tsx
    - AdvancedChart.tsx
    - COMEXNewsPanel.tsx
    - CandlestickChart.tsx
    - CandlestickPatternPanel.tsx
    - ChartControls.tsx
    - ChartLegend.tsx
    - ChartOverlays.tsx
    - CircularChart.tsx
    - CircularProgress.tsx
    - ClaudeAnalysisPanel.tsx
    - ClaudeNewsAnalysisPanel.tsx
    - ClaudePatternPanel.tsx
    - CumulativeChart.tsx
    - DashboardCard.tsx
    - DetailPanel.tsx
    - DetailedAnalysisPanel.tsx
    - DraggableDashboard.tsx
    - GuidePanel.tsx
    - IndicatorChart.tsx
    - InfoTooltip.tsx
    - InlineCandles.tsx
    - InstitutionalDataPanel.tsx
    - LanguageSwitcher.tsx
    - LearningDashboardPanel.tsx
    - LiveChartPanel.tsx
    - MLFactorPanel.tsx
    - MLPredictionPanel.tsx
    - MetricCard.tsx
    - NasdaqPanel.tsx
    - NewsCard.tsx
    - NewsFeed.tsx
    - NewsFilters.tsx
    - OrderBlockChart.tsx
    - OrderBlockPanel.tsx
    - OrderBlockPanelSimple.tsx
    - OrderBlockSettings.tsx
    - OrderBlockSignals.tsx
    - PatternEnginePanel.tsx
    - PatternEngineV2.tsx
    - PredictionHistoryTable.tsx
    - PremiumHeader.tsx
    - ProFeatureGate.tsx
    - RTYHIIMDetectorPanel.tsx
    - RhythmDetectorSimple.tsx
    - SentimentPanel.tsx
    - StrategyPerformancePanel.tsx
    - TradingBackground.tsx
    - TradingCalendar.tsx
    - TradingChart.tsx
    - TradingChartWrapper.tsx
    - UserMenu.tsx
    - XauusdPanel.tsx
    - useChartData.ts
    - useNews.ts
  - public/
    - android-chrome-192x192.png
    - android-chrome-512x512.png
    - apple-touch-icon.png
    - bu.png
    - favicon-16x16.png
    - favicon-32x32.png
    - favicon.ico
    - googledfa8b432a65e21f0.html
    - logo.png
    - site.webmanifest
    - uploaded_media_1769901018868.png
  - hooks/
    - useCachedDashboardData.ts
    - useLivePrices.ts
    - useMTFAnalysis.ts
  - lib/
    - api.ts
    - claudeAnalysisStore.ts
    - i18n.tsx
    - store.ts
    - utils.ts
```

### Ana servis dosyaları (backend/services)
- `adaptive_tp_sl.py`
- `analysis_cache.py`
- `api_cache.py`
- `auth_service.py`
- `background_scheduler.py`
- `candlestick_pattern_service.py`
- `chart_data_service.py`
- `claude_news_analyzer.py`
- `claude_signal_analyzer.py`
- `comex_news_service.py`
- `cot_report_service.py`
- `data_fetcher.py`
- `detailed_ai_analysis_service.py`
- `earnings_service.py`
- `email_service.py`
- `error_analysis_service.py`
- `gold_news_analyzer.py`
- `gold_news_analyzer_v2.py`
- `learning_analyzer.py`
- `live_news_monitor.py`
- `marketaux_service.py`
- `ml_prediction_service.py`
- `ml_service.py`
- `mtf_analysis_service.py`
- `news_fetcher.py`
- `order_block_service.py`
- `outcome_tracker.py`
- `pattern_analyzer.py`
- `pattern_engine_runner.py`
- `prediction_logger.py`
- `rtyhiim_service.py`
- `sentiment_analyzer.py`
- `slippage_monitor.py`
- `sr_ml_features.py`
- `ta_service.py`
- `target_config.py`
- `technical_indicators.py`
- `translation_service.py`
- `trend_analyzer.py`
- `twitter_monitor.py`
- `unified_news_analyzer.py`

### Router/endpoint dosyaları (backend/routers)
- `__init__.py`
- `ai_analysis.py`
- `auth.py`
- `chart_data.py`
- `claude_news.py`
- `claude_patterns.py`
- `claude_sentiment.py`
- `data.py`
- `earnings.py`
- `fvg.py`
- `learning.py`
- `live_news.py`
- `mtf_analysis.py`
- `nasdaq.py`
- `news.py`
- `order_blocks.py`
- `pattern_engine.py`
- `prediction.py`
- `rtyhiim.py`
- `ta.py`
- `xauusd.py`

## 2. Kritik Dosya İçerikleri

## A. ML Prediction Service

## DOSYA ADI: backend/services/ml_prediction_service.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
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
from dataclasses import dataclass
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
SIGNAL_COOLDOWN_MINUTES = 30  # Minimum time before direction can change
MIN_CONFIDENCE_FOR_REVERSAL = 65  # Minimum confidence to override existing signal
MIN_PRICE_CHANGE_PCT = 0.3  # Minimum price change % to consider new signal

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
    # ADVANCED TRADING ENGINE - 5 Katmanlı Karar Sistemi
    # ═══════════════════════════════════════════════════════════════════
    try:
        from services.trading_engine import (
            MarketRegimeDetector, ConfluenceEngine, 
            LayeredDecisionMaker, extract_ohlcv
        )
        from services.trading_engine.mtf_analyzer import TimeframeAnalysis
        from services.trading_engine.constants import PriceStructure
        
        # Rejim tespiti (candle verisi varsa)
        if candles and len(candles) >= 50:
            _, highs, lows, closes, _ = extract_ohlcv(candles)
            
            regime_detector = MarketRegimeDetector()
            regime = regime_detector.detect(highs, lows, closes)
            
            # Rejim bazlı karar
            if regime.position_size_multiplier == 0:
                # HIGH_VOL_CHOPPY - TİCARET YAPMA
                direction = "HOLD"
                confidence = min(confidence, 40)
                reasoning.append(f"🚫 Rejim: {regime.regime.value} - Trade önerilmez")
                reasoning.extend(regime.reasoning)
            elif regime.trend_direction:
                # Trend var - counter-trend kontrolü
                basic_dir = "LONG" if direction == "BUY" else ("SHORT" if direction == "SELL" else None)
                if basic_dir and basic_dir != regime.trend_direction and not regime.counter_trend_allowed:
                    # Counter-trend yasak
                    old_dir = direction
                    direction = "HOLD"
                    confidence = min(confidence, 45)
                    reasoning.append(f"⚠️ Counter-trend: {old_dir} vs Rejim {regime.trend_direction}")
                else:
                    # Trend uyumlu - confidence boost
                    if basic_dir == regime.trend_direction:
                        confidence = min(100, confidence * 1.1)
                        reasoning.append(f"✅ Rejim Uyumu: {regime.regime.value} ({regime.trend_direction})")
            
            # Pozisyon boyut çarpanı
            if regime.position_size_multiplier < 1.0:
                reasoning.append(f"📊 Pozisyon: {regime.position_size_multiplier:.0%} (rejim ayarı)")
    except Exception as te_err:
        logger.debug(f"Trading engine skipped: {te_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # SIGNAL STABILITY CHECK - Prevent rapid direction flip-flopping
    # ═══════════════════════════════════════════════════════════════════
    allow_change, stability_reason = _should_allow_direction_change(
        normalized_symbol, direction, confidence, current_price
    )
    
    if not allow_change:
        cached = _get_cached_signal(normalized_symbol)
        if cached:
            old_direction = cached["direction"]
            logger.warning(f"Signal stability: {direction} -> {old_direction} ({stability_reason})")
            reasoning.append(f"⚡ Sinyal Stabilitesi: {stability_reason}")
            direction = old_direction
            confidence = min(confidence, cached["confidence"] + 5)
    else:
        _update_signal_cache(normalized_symbol, direction, confidence, current_price)
        if stability_reason and stability_reason not in ["İlk sinyal", "Aynı yön", "HOLD geçişi"]:
            reasoning.append(f"✅ {stability_reason}")
            logger.info(f"Signal updated: {direction} @ {confidence:.1f}% ({stability_reason})")
    
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

```


## B. Stabilite/Cooldown

## DOSYA ADI: backend/services/signal_stability.py

### BULUNDU: Hayır

### TAM İÇERİK:
```
Dosya bulunamadı
```


## DOSYA ADI: backend/services/cooldown_manager.py

### BULUNDU: Hayır

### TAM İÇERİK:
```
Dosya bulunamadı
```


## DOSYA ADI: backend/services/ml_prediction_service.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
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
from dataclasses import dataclass
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
SIGNAL_COOLDOWN_MINUTES = 30  # Minimum time before direction can change
MIN_CONFIDENCE_FOR_REVERSAL = 65  # Minimum confidence to override existing signal
MIN_PRICE_CHANGE_PCT = 0.3  # Minimum price change % to consider new signal

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
    # ADVANCED TRADING ENGINE - 5 Katmanlı Karar Sistemi
    # ═══════════════════════════════════════════════════════════════════
    try:
        from services.trading_engine import (
            MarketRegimeDetector, ConfluenceEngine, 
            LayeredDecisionMaker, extract_ohlcv
        )
        from services.trading_engine.mtf_analyzer import TimeframeAnalysis
        from services.trading_engine.constants import PriceStructure
        
        # Rejim tespiti (candle verisi varsa)
        if candles and len(candles) >= 50:
            _, highs, lows, closes, _ = extract_ohlcv(candles)
            
            regime_detector = MarketRegimeDetector()
            regime = regime_detector.detect(highs, lows, closes)
            
            # Rejim bazlı karar
            if regime.position_size_multiplier == 0:
                # HIGH_VOL_CHOPPY - TİCARET YAPMA
                direction = "HOLD"
                confidence = min(confidence, 40)
                reasoning.append(f"🚫 Rejim: {regime.regime.value} - Trade önerilmez")
                reasoning.extend(regime.reasoning)
            elif regime.trend_direction:
                # Trend var - counter-trend kontrolü
                basic_dir = "LONG" if direction == "BUY" else ("SHORT" if direction == "SELL" else None)
                if basic_dir and basic_dir != regime.trend_direction and not regime.counter_trend_allowed:
                    # Counter-trend yasak
                    old_dir = direction
                    direction = "HOLD"
                    confidence = min(confidence, 45)
                    reasoning.append(f"⚠️ Counter-trend: {old_dir} vs Rejim {regime.trend_direction}")
                else:
                    # Trend uyumlu - confidence boost
                    if basic_dir == regime.trend_direction:
                        confidence = min(100, confidence * 1.1)
                        reasoning.append(f"✅ Rejim Uyumu: {regime.regime.value} ({regime.trend_direction})")
            
            # Pozisyon boyut çarpanı
            if regime.position_size_multiplier < 1.0:
                reasoning.append(f"📊 Pozisyon: {regime.position_size_multiplier:.0%} (rejim ayarı)")
    except Exception as te_err:
        logger.debug(f"Trading engine skipped: {te_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # SIGNAL STABILITY CHECK - Prevent rapid direction flip-flopping
    # ═══════════════════════════════════════════════════════════════════
    allow_change, stability_reason = _should_allow_direction_change(
        normalized_symbol, direction, confidence, current_price
    )
    
    if not allow_change:
        cached = _get_cached_signal(normalized_symbol)
        if cached:
            old_direction = cached["direction"]
            logger.warning(f"Signal stability: {direction} -> {old_direction} ({stability_reason})")
            reasoning.append(f"⚡ Sinyal Stabilitesi: {stability_reason}")
            direction = old_direction
            confidence = min(confidence, cached["confidence"] + 5)
    else:
        _update_signal_cache(normalized_symbol, direction, confidence, current_price)
        if stability_reason and stability_reason not in ["İlk sinyal", "Aynı yön", "HOLD geçişi"]:
            reasoning.append(f"✅ {stability_reason}")
            logger.info(f"Signal updated: {direction} @ {confidence:.1f}% ({stability_reason})")
    
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

```


## C. Layer Aggregator

## DOSYA ADI: backend/services/layer_aggregator.py

### BULUNDU: Hayır

### TAM İÇERİK:
```
Dosya bulunamadı
```


## DOSYA ADI: backend/services/ml_prediction_service.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
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
from dataclasses import dataclass
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
SIGNAL_COOLDOWN_MINUTES = 30  # Minimum time before direction can change
MIN_CONFIDENCE_FOR_REVERSAL = 65  # Minimum confidence to override existing signal
MIN_PRICE_CHANGE_PCT = 0.3  # Minimum price change % to consider new signal

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
    # ADVANCED TRADING ENGINE - 5 Katmanlı Karar Sistemi
    # ═══════════════════════════════════════════════════════════════════
    try:
        from services.trading_engine import (
            MarketRegimeDetector, ConfluenceEngine, 
            LayeredDecisionMaker, extract_ohlcv
        )
        from services.trading_engine.mtf_analyzer import TimeframeAnalysis
        from services.trading_engine.constants import PriceStructure
        
        # Rejim tespiti (candle verisi varsa)
        if candles and len(candles) >= 50:
            _, highs, lows, closes, _ = extract_ohlcv(candles)
            
            regime_detector = MarketRegimeDetector()
            regime = regime_detector.detect(highs, lows, closes)
            
            # Rejim bazlı karar
            if regime.position_size_multiplier == 0:
                # HIGH_VOL_CHOPPY - TİCARET YAPMA
                direction = "HOLD"
                confidence = min(confidence, 40)
                reasoning.append(f"🚫 Rejim: {regime.regime.value} - Trade önerilmez")
                reasoning.extend(regime.reasoning)
            elif regime.trend_direction:
                # Trend var - counter-trend kontrolü
                basic_dir = "LONG" if direction == "BUY" else ("SHORT" if direction == "SELL" else None)
                if basic_dir and basic_dir != regime.trend_direction and not regime.counter_trend_allowed:
                    # Counter-trend yasak
                    old_dir = direction
                    direction = "HOLD"
                    confidence = min(confidence, 45)
                    reasoning.append(f"⚠️ Counter-trend: {old_dir} vs Rejim {regime.trend_direction}")
                else:
                    # Trend uyumlu - confidence boost
                    if basic_dir == regime.trend_direction:
                        confidence = min(100, confidence * 1.1)
                        reasoning.append(f"✅ Rejim Uyumu: {regime.regime.value} ({regime.trend_direction})")
            
            # Pozisyon boyut çarpanı
            if regime.position_size_multiplier < 1.0:
                reasoning.append(f"📊 Pozisyon: {regime.position_size_multiplier:.0%} (rejim ayarı)")
    except Exception as te_err:
        logger.debug(f"Trading engine skipped: {te_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # SIGNAL STABILITY CHECK - Prevent rapid direction flip-flopping
    # ═══════════════════════════════════════════════════════════════════
    allow_change, stability_reason = _should_allow_direction_change(
        normalized_symbol, direction, confidence, current_price
    )
    
    if not allow_change:
        cached = _get_cached_signal(normalized_symbol)
        if cached:
            old_direction = cached["direction"]
            logger.warning(f"Signal stability: {direction} -> {old_direction} ({stability_reason})")
            reasoning.append(f"⚡ Sinyal Stabilitesi: {stability_reason}")
            direction = old_direction
            confidence = min(confidence, cached["confidence"] + 5)
    else:
        _update_signal_cache(normalized_symbol, direction, confidence, current_price)
        if stability_reason and stability_reason not in ["İlk sinyal", "Aynı yön", "HOLD geçişi"]:
            reasoning.append(f"✅ {stability_reason}")
            logger.info(f"Signal updated: {direction} @ {confidence:.1f}% ({stability_reason})")
    
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

```


## D. Pattern Engine

## DOSYA ADI: backend/services/pattern_engine.py

### BULUNDU: Hayır

### TAM İÇERİK:
```
Dosya bulunamadı
```


## DOSYA ADI: backend/services/pattern_engine_runner.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import httpx

from config import settings


def _path_exists(path: str) -> bool:
    return Path(path).expanduser().exists()


def run_pattern_engine(last_n: int, select_top: float, output_selected_only: bool) -> dict:
    """
    Non-mock, deterministic "pattern engine" based on live EOD candles.
    Note: Intraday is not available on some EODHD plans; we use daily candles.
    """
    model_ok = _path_exists(settings.pattern_engine_path)
    status = None if model_ok else f"Runtime not found: {settings.pattern_engine_path}"

    # Pull recent daily candles for NDX.INDX
    symbol = "NDX.INDX"
    now = datetime.utcnow()
    from_date = (now - timedelta(days=400)).date().isoformat()

    closes: List[float] = []
    try:
        r = httpx.get(
            f"https://eodhistoricaldata.com/api/eod/{symbol}",
            params={"api_token": settings.eodhd_api_key, "fmt": "json", "period": "d", "from": from_date},
            timeout=15.0,
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict) and row.get("close") is not None:
                    closes.append(float(row["close"]))
    except Exception:
        closes = []

    def _ret(window: int) -> float:
        if len(closes) < window + 1:
            return 0.0
        return (closes[-1] - closes[-1 - window]) / max(1e-9, closes[-1 - window])

    def _vol(window: int) -> float:
        if len(closes) < window + 1:
            return 0.0
        series = closes[-window:]
        mean = sum(series) / len(series)
        var = sum((x - mean) ** 2 for x in series) / max(1, len(series) - 1)
        return var ** 0.5 / max(1e-9, mean)

    r5 = _ret(5)
    r20 = _ret(20)
    vol20 = _vol(20)
    direction = "UP" if r5 >= 0 else "DOWN"

    # Deterministic candidates derived from live series
    base_patterns = [
        ("momentum_5d", "BUY" if r5 > 0 else "SELL", min(0.95, 0.55 + abs(r5) * 5)),
        ("momentum_20d", "BUY" if r20 > 0 else "SELL", min(0.95, 0.55 + abs(r20) * 3)),
        ("volatility_break", "HOLD" if vol20 < 0.01 else ("BUY" if r5 > 0 else "SELL"), min(0.9, 0.55 + vol20 * 10)),
        ("mean_reversion", "BUY" if r5 < -0.01 else ("SELL" if r5 > 0.01 else "HOLD"), min(0.9, 0.55 + abs(r5) * 4)),
    ]

    patterns: List[dict] = []
    trade_thr = 0.65
    for idx, (pid, route, p_success) in enumerate(base_patterns[: min(10, last_n)]):
        timestamp = (now - timedelta(minutes=idx * 15)).isoformat() + "Z"
        patterns.append(
            {
                "timestamp": timestamp,
                "pattern_id": pid,
                "route": route,
                "p_success": round(float(p_success), 2),
                "trade_ok": float(p_success) >= trade_thr,
                "trade_thr": trade_thr,
                "expected_next": direction if route != "HOLD" else "SIDEWAYS",
                "stage": "DETECTED",
            }
        )

    selected_count = int(last_n * select_top)
    if output_selected_only:
        patterns = [p for p in patterns if p["trade_ok"]]

    return {
        "patterns": patterns,
        "total_candidates": last_n,
        "selected_count": selected_count,
        "selection_threshold": trade_thr,
        "model_status": status,
    }

```


## DOSYA ADI: backend/routers/pattern_engine.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
from fastapi import APIRouter
from pydantic import BaseModel

from models.responses import PatternEngineResponse
from services.pattern_engine_runner import run_pattern_engine

router = APIRouter(prefix="/api/run", tags=["pattern_engine"])


class PatternEngineRequest(BaseModel):
    last_n: int = 500
    select_top: float = 0.3
    output_selected_only: bool = True


@router.post("/pattern-engine", response_model=PatternEngineResponse)
async def run_engine(payload: PatternEngineRequest) -> PatternEngineResponse:
    result = run_pattern_engine(
        last_n=payload.last_n,
        select_top=payload.select_top,
        output_selected_only=payload.output_selected_only,
    )
    return PatternEngineResponse(**result)

```


## DOSYA ADI: backend/services/pattern_analyzer.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
from __future__ import annotations

from datetime import datetime
from typing import Dict

from config import settings
import json
import httpx

from services.data_fetcher import fetch_latest_price
from services.data_fetcher import fetch_eod_candles


async def _run_single_timeframe(symbol: str, timeframe: str, lang: str, current_price_value: float, series_json: str) -> dict:
    language_line = (
        "Write all human-readable strings in Turkish."
        if (lang or "en").lower().startswith("tr")
        else "Write all human-readable strings in English."
    )
    prompt = f"""
You are a technical analyst. Return STRICT JSON only (no markdown) in this schema:
{{
  "detected_patterns": [{{"pattern_name": string, "pattern_source": string, "completion_percentage": integer, "signal":"bullish"|"bearish"|"neutral", "entry": number, "stop_loss": number, "target": number, "confidence": number, "reasoning": string}}],
  "summary": string,
  "recommendation": "BUY"|"SELL"|"HOLD"
}}

Instrument: {symbol}
Timeframe: {timeframe}
Live last price (may be 0 if unavailable): {current_price_value}

Price series (last 100 candles, JSON list of {{d,c}} where c=close):
{series_json}

Use this data to infer key patterns. Keep strings concise and JSON-valid.
{language_line}
""".strip()

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 700,
                "temperature": 0.2,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        text = ""
        for block in data.get("content", []) or []:
            if block.get("type") == "text":
                text = block.get("text", "")
                break
        return json.loads(text)


async def run_claude_pattern_analysis(symbol: str, timeframes: list[str], lang: str = "en") -> dict:
    current_price = await fetch_latest_price(symbol)
    current_price_value = float(current_price) if current_price is not None else 0.0
    eod = await fetch_eod_candles(symbol, limit=100)
    series = [{"d": r.get("date"), "c": r.get("close")} for r in eod]
    series_json = json.dumps(series, ensure_ascii=False)

    if not settings.anthropic_api_key:
        # Minimal fallback without hallucinating hardcoded prices
        analyses: Dict[str, dict] = {}
        for timeframe in timeframes:
            analyses[timeframe] = {
                "detected_patterns": [],
                "summary": f"{timeframe} timeframe pattern analysis unavailable (ANTHROPIC_API_KEY missing).",
                "recommendation": "HOLD",
            }
        return {
            "analyses": analyses,
            "current_price": current_price_value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_status": "ANTHROPIC_API_KEY missing",
        }

    try:
        analyses: Dict[str, dict] = {}
        # Call Claude per timeframe to avoid large JSON responses that can break parsing.
        for tf in timeframes:
            try:
                one = await _run_single_timeframe(
                    symbol=symbol,
                    timeframe=tf,
                    lang=lang,
                    current_price_value=current_price_value,
                    series_json=series_json,
                )
                analyses[tf] = {
                    "detected_patterns": one.get("detected_patterns", []) or [],
                    "summary": one.get("summary", "") or "",
                    "recommendation": one.get("recommendation", "HOLD") or "HOLD",
                }
            except Exception as e:
                analyses[tf] = {
                    "detected_patterns": [],
                    "summary": f"{tf} timeframe pattern analysis failed: {e}",
                    "recommendation": "HOLD",
                }
        return {
            "analyses": analyses,
            "current_price": current_price_value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_status": None,
        }
    except Exception as e:
        analyses: Dict[str, dict] = {}
        for timeframe in timeframes:
            analyses[timeframe] = {
                "detected_patterns": [],
                "summary": f"{timeframe} timeframe pattern analysis failed: {e}",
                "recommendation": "HOLD",
            }
        return {
            "analyses": analyses,
            "current_price": current_price_value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_status": "Claude request failed",
        }

```


## DOSYA ADI: backend/services/candlestick_pattern_service.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
"""
Candlestick Pattern Detection Service
=====================================
Detects classic Japanese candlestick patterns across multiple timeframes.
Integrates with ML model for enhanced prediction confidence.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Pattern definitions with explanations
PATTERN_INFO = {
    # Bullish Reversal Patterns
    "BULLISH_ENGULFING": {
        "name": "Bullish Engulfing",
        "name_tr": "Yutan Boğa Formasyonu",
        "signal": "bullish",
        "strength": 3,
        "description": "Previous red candle is completely engulfed by a larger green candle. Strong reversal signal.",
        "description_tr": "Önceki kırmızı mum, daha büyük yeşil mum tarafından tamamen yutulur. Güçlü dönüş sinyali.",
        "action": "Look for LONG entry after confirmation",
        "action_tr": "Onay sonrası LONG giriş ara"
    },
    "HAMMER": {
        "name": "Hammer",
        "name_tr": "Çekiç",
        "signal": "bullish",
        "strength": 2,
        "description": "Small body at top, long lower wick (2x body). Shows buyers rejected lower prices.",
        "description_tr": "Üstte küçük gövde, uzun alt fitil (gövdenin 2 katı). Alıcıların düşük fiyatları reddettiğini gösterir.",
        "action": "Potential bottom reversal - wait for green confirmation candle",
        "action_tr": "Potansiyel dip dönüşü - yeşil onay mumu bekle"
    },
    "INVERTED_HAMMER": {
        "name": "Inverted Hammer",
        "name_tr": "Ters Çekiç",
        "signal": "bullish",
        "strength": 2,
        "description": "Small body at bottom, long upper wick. Appears at downtrend end.",
        "description_tr": "Altta küçük gövde, uzun üst fitil. Düşüş trendi sonunda görülür.",
        "action": "Wait for bullish confirmation before entry",
        "action_tr": "Giriş öncesi boğa onayı bekle"
    },
    "MORNING_STAR": {
        "name": "Morning Star",
        "name_tr": "Sabah Yıldızı",
        "signal": "bullish",
        "strength": 3,
        "description": "3-candle pattern: big red, small body (star), big green. Strong reversal.",
        "description_tr": "3 mumlu formasyon: büyük kırmızı, küçük gövde (yıldız), büyük yeşil. Güçlü dönüş.",
        "action": "Strong BUY signal - enter on star close or green candle",
        "action_tr": "Güçlü AL sinyali - yıldız kapanışında veya yeşil mumda gir"
    },
    "BULLISH_HARAMI": {
        "name": "Bullish Harami",
        "name_tr": "Boğa Harami",
        "signal": "bullish",
        "strength": 2,
        "description": "Small green candle contained within previous large red candle body.",
        "description_tr": "Küçük yeşil mum, önceki büyük kırmızı mumun gövdesi içinde kalır.",
        "action": "Potential reversal - needs confirmation",
        "action_tr": "Potansiyel dönüş - onay gerekli"
    },
    "PIERCING_LINE": {
        "name": "Piercing Line",
        "name_tr": "Delici Çizgi",
        "signal": "bullish",
        "strength": 2,
        "description": "Green candle opens below previous red low, closes above its midpoint.",
        "description_tr": "Yeşil mum önceki kırmızının altında açılır, ortasının üstünde kapanır.",
        "action": "Bullish reversal signal at support levels",
        "action_tr": "Destek seviyelerinde boğa dönüş sinyali"
    },
    "THREE_WHITE_SOLDIERS": {
        "name": "Three White Soldiers",
        "name_tr": "Üç Beyaz Asker",
        "signal": "bullish",
        "strength": 3,
        "description": "Three consecutive green candles with higher closes. Strong uptrend start.",
        "description_tr": "Üst üste üç yeşil mum, her biri daha yüksek kapanış. Güçlü yükseliş başlangıcı.",
        "action": "Strong bullish momentum - trend following entry",
        "action_tr": "Güçlü boğa momentumu - trend takip girişi"
    },
    "DRAGONFLY_DOJI": {
        "name": "Dragonfly Doji",
        "name_tr": "Yusufçuk Doji",
        "signal": "bullish",
        "strength": 2,
        "description": "Open=Close at top, long lower wick. Strong rejection of lower prices.",
        "description_tr": "Açılış=Kapanış üstte, uzun alt fitil. Düşük fiyatların güçlü reddi.",
        "action": "Bullish at support - potential reversal",
        "action_tr": "Destekte boğa - potansiyel dönüş"
    },
    
    # Bearish Reversal Patterns
    "BEARISH_ENGULFING": {
        "name": "Bearish Engulfing",
        "name_tr": "Yutan Ayı Formasyonu",
        "signal": "bearish",
        "strength": 3,
        "description": "Previous green candle is completely engulfed by a larger red candle. Strong reversal.",
        "description_tr": "Önceki yeşil mum, daha büyük kırmızı mum tarafından tamamen yutulur. Güçlü dönüş.",
        "action": "Look for SHORT entry after confirmation",
        "action_tr": "Onay sonrası SHORT giriş ara"
    },
    "HANGING_MAN": {
        "name": "Hanging Man",
        "name_tr": "Asılan Adam",
        "signal": "bearish",
        "strength": 2,
        "description": "Hammer shape but at uptrend top. Warning of potential reversal.",
        "description_tr": "Çekiç şekli ama yükseliş tepesinde. Potansiyel dönüş uyarısı.",
        "action": "Bearish warning - wait for red confirmation",
        "action_tr": "Ayı uyarısı - kırmızı onay bekle"
    },
    "SHOOTING_STAR": {
        "name": "Shooting Star",
        "name_tr": "Kayan Yıldız",
        "signal": "bearish",
        "strength": 2,
        "description": "Small body at bottom, long upper wick at uptrend top. Rejection of higher prices.",
        "description_tr": "Altta küçük gövde, yükseliş tepesinde uzun üst fitil. Yüksek fiyatların reddi.",
        "action": "Potential top - SHORT on confirmation",
        "action_tr": "Potansiyel tepe - onayda SHORT"
    },
    "EVENING_STAR": {
        "name": "Evening Star",
        "name_tr": "Akşam Yıldızı",
        "signal": "bearish",
        "strength": 3,
        "description": "3-candle pattern: big green, small body (star), big red. Strong reversal.",
        "description_tr": "3 mumlu formasyon: büyük yeşil, küçük gövde (yıldız), büyük kırmızı. Güçlü dönüş.",
        "action": "Strong SELL signal - enter on red candle",
        "action_tr": "Güçlü SAT sinyali - kırmızı mumda gir"
    },
    "BEARISH_HARAMI": {
        "name": "Bearish Harami",
        "name_tr": "Ayı Harami",
        "signal": "bearish",
        "strength": 2,
        "description": "Small red candle contained within previous large green candle body.",
        "description_tr": "Küçük kırmızı mum, önceki büyük yeşil mumun gövdesi içinde kalır.",
        "action": "Potential reversal - needs confirmation",
        "action_tr": "Potansiyel dönüş - onay gerekli"
    },
    "DARK_CLOUD_COVER": {
        "name": "Dark Cloud Cover",
        "name_tr": "Kara Bulut Örtüsü",
        "signal": "bearish",
        "strength": 2,
        "description": "Red candle opens above previous green high, closes below its midpoint.",
        "description_tr": "Kırmızı mum önceki yeşilin üstünde açılır, ortasının altında kapanır.",
        "action": "Bearish reversal at resistance levels",
        "action_tr": "Direnç seviyelerinde ayı dönüşü"
    },
    "THREE_BLACK_CROWS": {
        "name": "Three Black Crows",
        "name_tr": "Üç Kara Karga",
        "signal": "bearish",
        "strength": 3,
        "description": "Three consecutive red candles with lower closes. Strong downtrend start.",
        "description_tr": "Üst üste üç kırmızı mum, her biri daha düşük kapanış. Güçlü düşüş başlangıcı.",
        "action": "Strong bearish momentum - avoid longs",
        "action_tr": "Güçlü ayı momentumu - long'lardan kaçın"
    },
    "GRAVESTONE_DOJI": {
        "name": "Gravestone Doji",
        "name_tr": "Mezar Taşı Doji",
        "signal": "bearish",
        "strength": 2,
        "description": "Open=Close at bottom, long upper wick. Strong rejection of higher prices.",
        "description_tr": "Açılış=Kapanış altta, uzun üst fitil. Yüksek fiyatların güçlü reddi.",
        "action": "Bearish at resistance - potential reversal",
        "action_tr": "Dirençte ayı - potansiyel dönüş"
    },
    
    # Neutral/Continuation Patterns
    "DOJI": {
        "name": "Doji",
        "name_tr": "Doji",
        "signal": "neutral",
        "strength": 1,
        "description": "Open equals close - market indecision. Watch for next candle direction.",
        "description_tr": "Açılış kapanışa eşit - piyasa kararsızlığı. Sonraki mum yönünü izle.",
        "action": "Wait for confirmation - indecision signal",
        "action_tr": "Onay bekle - kararsızlık sinyali"
    },
    "SPINNING_TOP": {
        "name": "Spinning Top",
        "name_tr": "Dönen Tepe",
        "signal": "neutral",
        "strength": 1,
        "description": "Small body with upper and lower wicks. Indecision in the market.",
        "description_tr": "Üst ve alt fitilli küçük gövde. Piyasada kararsızlık.",
        "action": "No clear direction - wait for breakout",
        "action_tr": "Net yön yok - kırılım bekle"
    },
    "MARUBOZU_BULLISH": {
        "name": "Bullish Marubozu",
        "name_tr": "Boğa Marubozu",
        "signal": "bullish",
        "strength": 2,
        "description": "Long green candle with no wicks. Strong buying pressure.",
        "description_tr": "Fitilsiz uzun yeşil mum. Güçlü alım baskısı.",
        "action": "Strong bullish momentum - trend continuation",
        "action_tr": "Güçlü boğa momentumu - trend devamı"
    },
    "MARUBOZU_BEARISH": {
        "name": "Bearish Marubozu",
        "name_tr": "Ayı Marubozu",
        "signal": "bearish",
        "strength": 2,
        "description": "Long red candle with no wicks. Strong selling pressure.",
        "description_tr": "Fitilsiz uzun kırmızı mum. Güçlü satış baskısı.",
        "action": "Strong bearish momentum - trend continuation",
        "action_tr": "Güçlü ayı momentumu - trend devamı"
    },
}


@dataclass
class CandlestickPattern:
    pattern_id: str
    name: str
    name_tr: str
    signal: Literal["bullish", "bearish", "neutral"]
    strength: int  # 1-3
    description: str
    description_tr: str
    action: str
    action_tr: str
    timeframe: str
    candle_index: int  # Index of the pattern in the data
    confidence: float  # 0-100


def detect_patterns_manual(
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    timeframe: str = "1H"
) -> List[CandlestickPattern]:
    """
    Manual candlestick pattern detection without TA-Lib dependency.
    Detects patterns in the last 5 candles.
    """
    patterns: List[CandlestickPattern] = []
    
    if len(closes) < 5:
        return patterns
    
    # Helper functions
    def body_size(i: int) -> float:
        return abs(closes[i] - opens[i])
    
    def is_bullish(i: int) -> bool:
        return closes[i] > opens[i]
    
    def is_bearish(i: int) -> bool:
        return closes[i] < opens[i]
    
    def upper_wick(i: int) -> float:
        return highs[i] - max(opens[i], closes[i])
    
    def lower_wick(i: int) -> float:
        return min(opens[i], closes[i]) - lows[i]
    
    def is_doji(i: int) -> bool:
        body = body_size(i)
        total_range = highs[i] - lows[i]
        return total_range > 0 and body / total_range < 0.1
    
    def is_small_body(i: int) -> bool:
        body = body_size(i)
        total_range = highs[i] - lows[i]
        return total_range > 0 and body / total_range < 0.3
    
    def avg_body_size(start: int, end: int) -> float:
        bodies = [body_size(i) for i in range(start, end)]
        return np.mean(bodies) if bodies else 0
    
    # Check last 3 candles for patterns
    i = len(closes) - 1  # Current candle
    avg_body = avg_body_size(max(0, i-10), i)
    
    # ============ BULLISH PATTERNS ============
    
    # Bullish Engulfing
    if i >= 1 and is_bearish(i-1) and is_bullish(i):
        if opens[i] <= closes[i-1] and closes[i] >= opens[i-1]:
            if body_size(i) > body_size(i-1) * 1.1:
                patterns.append(_create_pattern("BULLISH_ENGULFING", timeframe, i, 85))
    
    # Hammer
    if i >= 0:
        body = body_size(i)
        lower = lower_wick(i)
        upper = upper_wick(i)
        if body > 0 and lower >= body * 2 and upper < body * 0.5:
            patterns.append(_create_pattern("HAMMER", timeframe, i, 75))
    
    # Inverted Hammer
    if i >= 0:
        body = body_size(i)
        lower = lower_wick(i)
        upper = upper_wick(i)
        if body > 0 and upper >= body * 2 and lower < body * 0.5:
            patterns.append(_create_pattern("INVERTED_HAMMER", timeframe, i, 70))
    
    # Morning Star (3 candle)
    if i >= 2:
        if is_bearish(i-2) and body_size(i-2) > avg_body * 0.8:
            if is_small_body(i-1):
                if is_bullish(i) and body_size(i) > avg_body * 0.8:
                    if closes[i] > (opens[i-2] + closes[i-2]) / 2:
                        patterns.append(_create_pattern("MORNING_STAR", timeframe, i, 90))
    
    # Bullish Harami
    if i >= 1 and is_bearish(i-1) and is_bullish(i):
        if opens[i] > closes[i-1] and closes[i] < opens[i-1]:
            if body_size(i) < body_size(i-1) * 0.6:
                patterns.append(_create_pattern("BULLISH_HARAMI", timeframe, i, 70))
    
    # Piercing Line
    if i >= 1 and is_bearish(i-1) and is_bullish(i):
        mid_prev = (opens[i-1] + closes[i-1]) / 2
        if opens[i] < closes[i-1] and closes[i] > mid_prev and closes[i] < opens[i-1]:
            patterns.append(_create_pattern("PIERCING_LINE", timeframe, i, 75))
    
    # Three White Soldiers
    if i >= 2:
        if all(is_bullish(i-j) for j in range(3)):
            if closes[i] > closes[i-1] > closes[i-2]:
                if all(body_size(i-j) > avg_body * 0.5 for j in range(3)):
                    patterns.append(_create_pattern("THREE_WHITE_SOLDIERS", timeframe, i, 85))
    
    # Dragonfly Doji
    if i >= 0:
        if is_doji(i) and lower_wick(i) > (highs[i] - lows[i]) * 0.6:
            if upper_wick(i) < (highs[i] - lows[i]) * 0.1:
                patterns.append(_create_pattern("DRAGONFLY_DOJI", timeframe, i, 75))
    
    # ============ BEARISH PATTERNS ============
    
    # Bearish Engulfing
    if i >= 1 and is_bullish(i-1) and is_bearish(i):
        if opens[i] >= closes[i-1] and closes[i] <= opens[i-1]:
            if body_size(i) > body_size(i-1) * 1.1:
                patterns.append(_create_pattern("BEARISH_ENGULFING", timeframe, i, 85))
    
    # Hanging Man (Hammer at top)
    if i >= 0:
        body = body_size(i)
        lower = lower_wick(i)
        upper = upper_wick(i)
        # Need to check if we're at a high - simplified check
        if body > 0 and lower >= body * 2 and upper < body * 0.5:
            # Check if price has been rising
            if i >= 5 and closes[i] > closes[i-5]:
                patterns.append(_create_pattern("HANGING_MAN", timeframe, i, 70))
    
    # Shooting Star
    if i >= 0:
        body = body_size(i)
        lower = lower_wick(i)
        upper = upper_wick(i)
        if body > 0 and upper >= body * 2 and lower < body * 0.5:
            # Check if price has been rising
            if i >= 5 and closes[i] > closes[i-5]:
                patterns.append(_create_pattern("SHOOTING_STAR", timeframe, i, 80))
    
    # Evening Star (3 candle)
    if i >= 2:
        if is_bullish(i-2) and body_size(i-2) > avg_body * 0.8:
            if is_small_body(i-1):
                if is_bearish(i) and body_size(i) > avg_body * 0.8:
                    if closes[i] < (opens[i-2] + closes[i-2]) / 2:
                        patterns.append(_create_pattern("EVENING_STAR", timeframe, i, 90))
    
    # Bearish Harami
    if i >= 1 and is_bullish(i-1) and is_bearish(i):
        if opens[i] < closes[i-1] and closes[i] > opens[i-1]:
            if body_size(i) < body_size(i-1) * 0.6:
                patterns.append(_create_pattern("BEARISH_HARAMI", timeframe, i, 70))
    
    # Dark Cloud Cover
    if i >= 1 and is_bullish(i-1) and is_bearish(i):
        mid_prev = (opens[i-1] + closes[i-1]) / 2
        if opens[i] > closes[i-1] and closes[i] < mid_prev and closes[i] > opens[i-1]:
            patterns.append(_create_pattern("DARK_CLOUD_COVER", timeframe, i, 75))
    
    # Three Black Crows
    if i >= 2:
        if all(is_bearish(i-j) for j in range(3)):
            if closes[i] < closes[i-1] < closes[i-2]:
                if all(body_size(i-j) > avg_body * 0.5 for j in range(3)):
                    patterns.append(_create_pattern("THREE_BLACK_CROWS", timeframe, i, 85))
    
    # Gravestone Doji
    if i >= 0:
        if is_doji(i) and upper_wick(i) > (highs[i] - lows[i]) * 0.6:
            if lower_wick(i) < (highs[i] - lows[i]) * 0.1:
                patterns.append(_create_pattern("GRAVESTONE_DOJI", timeframe, i, 75))
    
    # ============ NEUTRAL PATTERNS ============
    
    # Doji
    if i >= 0 and is_doji(i):
        # Don't add if already detected as dragonfly or gravestone
        existing_ids = [p.pattern_id for p in patterns]
        if "DRAGONFLY_DOJI" not in existing_ids and "GRAVESTONE_DOJI" not in existing_ids:
            patterns.append(_create_pattern("DOJI", timeframe, i, 60))
    
    # Spinning Top
    if i >= 0:
        body = body_size(i)
        total = highs[i] - lows[i]
        upper = upper_wick(i)
        lower = lower_wick(i)
        if total > 0 and 0.1 < body / total < 0.3:
            if upper > body * 0.5 and lower > body * 0.5:
                patterns.append(_create_pattern("SPINNING_TOP", timeframe, i, 55))
    
    # Marubozu (no wicks)
    if i >= 0:
        body = body_size(i)
        total = highs[i] - lows[i]
        upper = upper_wick(i)
        lower = lower_wick(i)
        if total > 0 and body / total > 0.9:
            if is_bullish(i):
                patterns.append(_create_pattern("MARUBOZU_BULLISH", timeframe, i, 80))
            else:
                patterns.append(_create_pattern("MARUBOZU_BEARISH", timeframe, i, 80))
    
    return patterns


def _create_pattern(pattern_id: str, timeframe: str, candle_index: int, confidence: float) -> CandlestickPattern:
    """Helper to create a CandlestickPattern from pattern info."""
    info = PATTERN_INFO.get(pattern_id, {})
    return CandlestickPattern(
        pattern_id=pattern_id,
        name=info.get("name", pattern_id),
        name_tr=info.get("name_tr", pattern_id),
        signal=info.get("signal", "neutral"),
        strength=info.get("strength", 1),
        description=info.get("description", ""),
        description_tr=info.get("description_tr", ""),
        action=info.get("action", ""),
        action_tr=info.get("action_tr", ""),
        timeframe=timeframe,
        candle_index=candle_index,
        confidence=confidence
    )


async def detect_candlestick_patterns(
    symbol: str,
    timeframes: List[str] = ["15m", "30m", "1h", "4h"]
) -> Dict:
    """
    Detect candlestick patterns across multiple timeframes.
    
    Args:
        symbol: Trading symbol (e.g., "XAUUSD", "NAS100")
        timeframes: List of timeframes to analyze
    
    Returns:
        Dictionary with patterns per timeframe and summary
    """
    from services.data_fetcher import fetch_ohlc_data
    
    result = {
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "timeframes": {},
        "all_patterns": [],
        "bullish_count": 0,
        "bearish_count": 0,
        "neutral_count": 0,
        "strongest_signal": None,
        "ml_adjustment": 0,
    }
    
    all_patterns = []
    
    for tf in timeframes:
        try:
            # Fetch OHLC data for this timeframe
            ohlc = await fetch_ohlc_data(symbol, timeframe=tf, limit=50)
            
            if not ohlc or len(ohlc) < 5:
                result["timeframes"][tf] = {"patterns": [], "error": "Insufficient data"}
                continue
            
            opens = np.array([c.get("open", c.get("o", 0)) for c in ohlc], dtype=float)
            highs = np.array([c.get("high", c.get("h", 0)) for c in ohlc], dtype=float)
            lows = np.array([c.get("low", c.get("l", 0)) for c in ohlc], dtype=float)
            closes = np.array([c.get("close", c.get("c", 0)) for c in ohlc], dtype=float)
            
            # Detect patterns
            patterns = detect_patterns_manual(opens, highs, lows, closes, tf)
            
            result["timeframes"][tf] = {
                "patterns": [
                    {
                        "id": p.pattern_id,
                        "name": p.name,
                        "name_tr": p.name_tr,
                        "signal": p.signal,
                        "strength": p.strength,
                        "description": p.description,
                        "description_tr": p.description_tr,
                        "action": p.action,
                        "action_tr": p.action_tr,
                        "confidence": p.confidence,
                    }
                    for p in patterns
                ],
                "count": len(patterns),
            }
            
            all_patterns.extend(patterns)
            
        except Exception as e:
            logger.error(f"Error detecting patterns for {tf}: {e}")
            result["timeframes"][tf] = {"patterns": [], "error": str(e)}
    
    # Summarize all patterns
    result["all_patterns"] = [
        {
            "id": p.pattern_id,
            "name": p.name,
            "name_tr": p.name_tr,
            "signal": p.signal,
            "strength": p.strength,
            "timeframe": p.timeframe,
            "confidence": p.confidence,
            "description_tr": p.description_tr,
            "action_tr": p.action_tr,
        }
        for p in all_patterns
    ]
    
    # Count signals
    for p in all_patterns:
        if p.signal == "bullish":
            result["bullish_count"] += 1
        elif p.signal == "bearish":
            result["bearish_count"] += 1
        else:
            result["neutral_count"] += 1
    
    # Determine strongest signal for ML
    if result["bullish_count"] > result["bearish_count"] and result["bullish_count"] >= 2:
        result["strongest_signal"] = "BULLISH"
        # Calculate ML adjustment based on pattern strength and count
        strength_sum = sum(p.strength for p in all_patterns if p.signal == "bullish")
        result["ml_adjustment"] = min(0.20, strength_sum * 0.03)  # Max +20%
    elif result["bearish_count"] > result["bullish_count"] and result["bearish_count"] >= 2:
        result["strongest_signal"] = "BEARISH"
        strength_sum = sum(p.strength for p in all_patterns if p.signal == "bearish")
        result["ml_adjustment"] = min(0.20, strength_sum * 0.03)  # Max +20%
    elif result["bullish_count"] > 0 and result["bearish_count"] > 0:
        result["strongest_signal"] = "MIXED"
        result["ml_adjustment"] = -0.10  # Reduce confidence for mixed signals
    else:
        result["strongest_signal"] = "NEUTRAL"
        result["ml_adjustment"] = 0
    
    logger.info(f"Candlestick patterns for {symbol}: {result['bullish_count']} bullish, "
                f"{result['bearish_count']} bearish, signal={result['strongest_signal']}")
    
    return result


async def get_candlestick_adjustment(symbol: str) -> Dict:
    """
    Get candlestick pattern adjustment for ML model.
    Returns a simplified dict for ML integration.
    """
    try:
        result = await detect_candlestick_patterns(symbol)
        return {
            "has_patterns": len(result["all_patterns"]) > 0,
            "bullish_count": result["bullish_count"],
            "bearish_count": result["bearish_count"],
            "strongest_signal": result["strongest_signal"],
            "confidence_adjustment": result["ml_adjustment"],
            "patterns_summary": [
                f"{p['name_tr']} ({p['timeframe']})" 
                for p in result["all_patterns"][:5]  # Top 5
            ],
        }
    except Exception as e:
        logger.error(f"Candlestick adjustment error: {e}")
        return {
            "has_patterns": False,
            "bullish_count": 0,
            "bearish_count": 0,
            "strongest_signal": "NEUTRAL",
            "confidence_adjustment": 0,
            "patterns_summary": [],
        }

```


## E. Strategy Selector

## DOSYA ADI: backend/services/strategy_selector.py

### BULUNDU: Hayır

### TAM İÇERİK:
```
Dosya bulunamadı
```


## DOSYA ADI: backend/services/ml_prediction_service.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
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
from dataclasses import dataclass
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
SIGNAL_COOLDOWN_MINUTES = 30  # Minimum time before direction can change
MIN_CONFIDENCE_FOR_REVERSAL = 65  # Minimum confidence to override existing signal
MIN_PRICE_CHANGE_PCT = 0.3  # Minimum price change % to consider new signal

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
    # ADVANCED TRADING ENGINE - 5 Katmanlı Karar Sistemi
    # ═══════════════════════════════════════════════════════════════════
    try:
        from services.trading_engine import (
            MarketRegimeDetector, ConfluenceEngine, 
            LayeredDecisionMaker, extract_ohlcv
        )
        from services.trading_engine.mtf_analyzer import TimeframeAnalysis
        from services.trading_engine.constants import PriceStructure
        
        # Rejim tespiti (candle verisi varsa)
        if candles and len(candles) >= 50:
            _, highs, lows, closes, _ = extract_ohlcv(candles)
            
            regime_detector = MarketRegimeDetector()
            regime = regime_detector.detect(highs, lows, closes)
            
            # Rejim bazlı karar
            if regime.position_size_multiplier == 0:
                # HIGH_VOL_CHOPPY - TİCARET YAPMA
                direction = "HOLD"
                confidence = min(confidence, 40)
                reasoning.append(f"🚫 Rejim: {regime.regime.value} - Trade önerilmez")
                reasoning.extend(regime.reasoning)
            elif regime.trend_direction:
                # Trend var - counter-trend kontrolü
                basic_dir = "LONG" if direction == "BUY" else ("SHORT" if direction == "SELL" else None)
                if basic_dir and basic_dir != regime.trend_direction and not regime.counter_trend_allowed:
                    # Counter-trend yasak
                    old_dir = direction
                    direction = "HOLD"
                    confidence = min(confidence, 45)
                    reasoning.append(f"⚠️ Counter-trend: {old_dir} vs Rejim {regime.trend_direction}")
                else:
                    # Trend uyumlu - confidence boost
                    if basic_dir == regime.trend_direction:
                        confidence = min(100, confidence * 1.1)
                        reasoning.append(f"✅ Rejim Uyumu: {regime.regime.value} ({regime.trend_direction})")
            
            # Pozisyon boyut çarpanı
            if regime.position_size_multiplier < 1.0:
                reasoning.append(f"📊 Pozisyon: {regime.position_size_multiplier:.0%} (rejim ayarı)")
    except Exception as te_err:
        logger.debug(f"Trading engine skipped: {te_err}")
    
    # ═══════════════════════════════════════════════════════════════════
    # SIGNAL STABILITY CHECK - Prevent rapid direction flip-flopping
    # ═══════════════════════════════════════════════════════════════════
    allow_change, stability_reason = _should_allow_direction_change(
        normalized_symbol, direction, confidence, current_price
    )
    
    if not allow_change:
        cached = _get_cached_signal(normalized_symbol)
        if cached:
            old_direction = cached["direction"]
            logger.warning(f"Signal stability: {direction} -> {old_direction} ({stability_reason})")
            reasoning.append(f"⚡ Sinyal Stabilitesi: {stability_reason}")
            direction = old_direction
            confidence = min(confidence, cached["confidence"] + 5)
    else:
        _update_signal_cache(normalized_symbol, direction, confidence, current_price)
        if stability_reason and stability_reason not in ["İlk sinyal", "Aynı yön", "HOLD geçişi"]:
            reasoning.append(f"✅ {stability_reason}")
            logger.info(f"Signal updated: {direction} @ {confidence:.1f}% ({stability_reason})")
    
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

```


## F. Config/Settings

## DOSYA ADI: backend/config.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    nasdaq_model_path: str = Field(
        default="~/Desktop/nasdaq/models/",
        env="NASDAQ_MODEL_PATH",
    )
    xauusd_model_path: str = Field(
        default="~/Desktop/xauusddata/models/",
        env="XAUUSD_MODEL_PATH",
    )
    pattern_engine_path: str = Field(
        default="~/Desktop/video/pattern_engine_runtime.py",
        env="PATTERN_ENGINE_PATH",
    )
    claude_patterns_path: str = Field(
        default="~/Desktop/trading-pattern-system/",
        env="CLAUDE_PATTERNS_PATH",
    )
    anthropic_api_key: str | None = Field(default=None, env="ANTHROPIC_API_KEY")
    eodhd_api_key: str | None = Field(default=None, env="EODHD_API_KEY")
    marketaux_api_key: str | None = Field(default=None, env="MARKETAUX_API_KEY")
    groq_api_key: str | None = Field(default=None, env="GROQ_API_KEY")
    xai_api_key: str | None = Field(default=None, env="XAI_API_KEY")
    x_bearer_token: str | None = Field(default=None, env="X_BEARER_TOKEN")
    marketaux_base_url: str = Field(
        default="https://api.marketaux.com/v1/news/all",
        env="MARKETAUX_BASE_URL",
    )
    supabase_url: str | None = Field(default=None, env="SUPABASE_URL")
    supabase_key: str | None = Field(default=None, env="SUPABASE_KEY")
    resend_api_key: str | None = Field(default=None, env="RESEND_API_KEY")
    ob_fractal_period: int = Field(default=2, env="OB_FRACTAL_PERIOD")
    ob_min_displacement_atr: float = Field(default=1.0, env="OB_MIN_DISPLACEMENT_ATR")
    ob_min_score: float = Field(default=50.0, env="OB_MIN_SCORE")
    ob_zone_type: str = Field(default="wick", env="OB_ZONE_TYPE")
    ob_max_tests: int = Field(default=2, env="OB_MAX_TESTS")
    rtyhiim_window_seconds: int = Field(default=600, env="RTYHIIM_WINDOW_SECONDS")
    rtyhiim_tick_rate_hz: float = Field(default=1.0, env="RTYHIIM_TICK_RATE_HZ")
    rtyhiim_min_period_s: float = Field(default=8.0, env="RTYHIIM_MIN_PERIOD_S")
    rtyhiim_max_period_s: float = Field(default=240.0, env="RTYHIIM_MAX_PERIOD_S")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()

```


## DOSYA ADI: backend/settings.py

### BULUNDU: Hayır

### TAM İÇERİK:
```
Dosya bulunamadı
```


## G. Market Regime

## DOSYA ADI: backend/services/market_regime.py

### BULUNDU: Hayır

### TAM İÇERİK:
```
Dosya bulunamadı
```


## DOSYA ADI: backend/services/mtf_analysis_service.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
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
    
    # Timeframe to data source mapping
    timeframe_data_map = {
        "M1": "1m",
        "M5": "5m",
        "M15": "15m",
        "M30": "30m",
        "H1": "1h",
        "H4": "4h",
        "D1": "1d",
    }
    
    timeframe_configs = {
        "M1": {"lookback": 50, "candles": 100},
        "M5": {"lookback": 50, "candles": 100},
        "M15": {"lookback": 50, "candles": 100},
        "M30": {"lookback": 50, "candles": 100},
        "H1": {"lookback": 100, "candles": 200},
        "H4": {"lookback": 100, "candles": 200},
        "D1": {"lookback": 220, "candles": 250},
    }
    
    async def fetch_tf_candles(tf: str) -> tuple:
        """Fetch candles for a specific timeframe"""
        from services.data_fetcher import fetch_ohlc_data, fetch_30m_candles
        
        data_tf = timeframe_data_map.get(tf, "1h")
        config = timeframe_configs.get(tf, timeframe_configs["H1"])
        
        candles = None
        
        try:
            # Try fetching specific timeframe data
            if tf in ["M15", "M30"]:
                # Use 30m candles for M15/M30 (more reliable)
                candles = await fetch_30m_candles(symbol, limit=config["candles"])
            elif tf in ["H1", "H4"]:
                candles = await fetch_ohlc_data(symbol, data_tf, config["candles"])
            else:
                candles = await fetch_ohlc_data(symbol, data_tf, config["candles"])
        except Exception as e:
            logger.warning(f"Failed to fetch {tf} data: {e}")
        
        if not candles or len(candles) < 20:
            # Fallback to EOD data with appropriate scaling
            try:
                eod_candles = await fetch_eod_candles(symbol, limit=config["candles"])
                if eod_candles:
                    candles = eod_candles
                    logger.info(f"Using EOD fallback for {tf}: {len(candles)} candles")
            except Exception as e:
                logger.warning(f"EOD fallback failed for {tf}: {e}")
        
        if not candles or len(candles) < 20:
            return None, None, None, None
            
        closes = np.array([c["close"] for c in candles], dtype=float)
        highs = np.array([c.get("high", c["close"]) for c in candles], dtype=float)
        lows = np.array([c.get("low", c["close"]) for c in candles], dtype=float)
        volumes = np.array([c.get("volume", 0) for c in candles], dtype=float)
        
        return closes, highs, lows, volumes
    
    if timeframe:
        # Single timeframe analysis
        closes, highs, lows, volumes = await fetch_tf_candles(timeframe)
        
        if closes is None or len(closes) < 20:
            return {"success": False, "error": f"Could not fetch data for {timeframe}"}
        
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
        
        # Fetch data for each timeframe
        for tf, config in timeframe_configs.items():
            tf_closes, tf_highs, tf_lows, tf_volumes = await fetch_tf_candles(tf)
            
            if tf_closes is None or len(tf_closes) < 20:
                continue
                
            lookback = min(config["lookback"], len(tf_closes))
            analyses[tf] = _analyze_timeframe(
                symbol, tf,
                tf_closes[-lookback:],
                tf_highs[-lookback:],
                tf_lows[-lookback:],
                tf_volumes[-lookback:],
                current_price,
                pip_value
            )
        
        if not analyses:
            return {"success": False, "error": "Could not fetch data for any timeframe"}
        
        confluence = _calculate_mtf_confluence(analyses)
        
        # Use H1 data for advanced components (fallback to first available)
        h1_closes, h1_highs, h1_lows, h1_volumes = await fetch_tf_candles("H1")
        if h1_closes is None:
            h1_closes, h1_highs, h1_lows, h1_volumes = await fetch_tf_candles("D1")
        
        if h1_closes is None:
            closes = highs = lows = volumes = np.array([current_price])
        else:
            closes, highs, lows, volumes = h1_closes, h1_highs, h1_lows, h1_volumes
        
        # Calculate advanced analysis components
        atr14 = _atr(highs, lows, closes, 14) if len(closes) > 14 else 0.0
        atr_pips = atr14 / pip_value if atr14 > 0 else 0.0
        
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

```


## DOSYA ADI: backend/services/trading_engine/regime_detector.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
"""
Market Regime Detector
5 farklı piyasa rejimi tespiti
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from .constants import MarketRegime, PriceStructure, ADX_STRONG, ADX_WEAK
from .helpers import adx, atr, find_swing_points, analyze_price_structure


@dataclass
class RegimeAnalysis:
    """Piyasa Rejimi Analizi"""
    regime: MarketRegime
    adx: float
    adx_trend: str
    price_structure: PriceStructure
    volatility_percentile: float
    trend_direction: Optional[str]
    confidence: float
    strategy_recommendation: str
    counter_trend_allowed: bool
    position_size_multiplier: float
    reasoning: List[str] = field(default_factory=list)


class MarketRegimeDetector:
    """
    Piyasa Rejimi Tespiti - ADX + Price Structure
    
    Rejimler:
    1. STRONG_TREND_UP/DOWN - ADX>30, güçlü yapı
    2. WEAK_TREND - ADX 20-30
    3. RANGE_BOUND - ADX<20, yatay
    4. LOW_VOL_COMPRESSION - Düşük vol, patlama yakın
    5. HIGH_VOL_CHOPPY - Kaotik, trade yapma
    6. TREND_EXHAUSTING - Trend bitiyor
    """
    
    def detect(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> RegimeAnalysis:
        """Piyasa rejimini tespit et"""
        
        # ADX hesapla
        adx_val, plus_di, minus_di = adx(highs, lows, closes, 14)
        
        # Kısa dönem ADX
        adx_short, _, _ = adx(highs[-30:], lows[-30:], closes[-30:], 7) if len(closes) > 30 else (adx_val, 0, 0)
        adx_trend = "rising" if adx_short > adx_val else ("falling" if adx_short < adx_val * 0.9 else "flat")
        
        # Volatilite percentile
        atr_val = atr(highs, lows, closes, 14)
        atr_history = []
        for i in range(30, len(closes), 10):
            atr_history.append(atr(highs[max(0,i-14):i], lows[max(0,i-14):i], closes[max(0,i-14):i], 14))
        vol_percentile = (sum(1 for a in atr_history if a < atr_val) / len(atr_history) * 100) if atr_history else 50
        
        # Price structure
        swing_highs, swing_lows = find_swing_points(highs, lows, 5)
        price_structure = analyze_price_structure(swing_highs, swing_lows)
        
        # Rejim belirleme
        reasoning = []
        
        if adx_val > ADX_STRONG:
            if adx_trend == "rising":
                if price_structure == PriceStructure.HIGHER_HIGHS:
                    regime = MarketRegime.STRONG_TREND_UP
                    trend_dir = "UP"
                    reasoning.append(f"ADX={adx_val:.1f} güçlü, yükseliyor, HH+HL yapısı")
                elif price_structure == PriceStructure.LOWER_LOWS:
                    regime = MarketRegime.STRONG_TREND_DOWN
                    trend_dir = "DOWN"
                    reasoning.append(f"ADX={adx_val:.1f} güçlü, yükseliyor, LH+LL yapısı")
                else:
                    regime = MarketRegime.WEAK_TREND
                    trend_dir = "UP" if plus_di > minus_di else "DOWN"
                    reasoning.append(f"ADX güçlü ama yapı belirsiz")
            else:
                regime = MarketRegime.TREND_EXHAUSTING
                trend_dir = "UP" if plus_di > minus_di else "DOWN"
                reasoning.append(f"ADX={adx_val:.1f} düşüyor, trend yoruluyor")
        
        elif adx_val < ADX_WEAK:
            if vol_percentile < 30:
                regime = MarketRegime.LOW_VOL_COMPRESSION
                trend_dir = None
                reasoning.append(f"ADX={adx_val:.1f} düşük, volatilite %{vol_percentile:.0f} - sıkışma")
            else:
                regime = MarketRegime.RANGE_BOUND
                trend_dir = None
                reasoning.append(f"ADX={adx_val:.1f} düşük, yatay piyasa")
        
        else:
            if vol_percentile > 70:
                regime = MarketRegime.HIGH_VOL_CHOPPY
                trend_dir = None
                reasoning.append(f"Orta ADX={adx_val:.1f} ama yüksek vol - choppy")
            else:
                regime = MarketRegime.WEAK_TREND
                trend_dir = "UP" if plus_di > minus_di else "DOWN"
                reasoning.append(f"ADX={adx_val:.1f} orta, zayıf trend")
        
        # Strateji önerisi
        strategy_map = {
            MarketRegime.STRONG_TREND_UP: ("Trend takibi LONG, pullback entry", False, 1.0),
            MarketRegime.STRONG_TREND_DOWN: ("Trend takibi SHORT, pullback entry", False, 1.0),
            MarketRegime.WEAK_TREND: ("Temkinli, küçük pozisyon", True, 0.5),
            MarketRegime.TREND_EXHAUSTING: ("Dikkatli ol, diverjans ara", True, 0.3),
            MarketRegime.RANGE_BOUND: ("Mean reversion, range extreme", True, 0.5),
            MarketRegime.LOW_VOL_COMPRESSION: ("Breakout bekle", False, 0.7),
            MarketRegime.HIGH_VOL_CHOPPY: ("TİCARET YAPMA", False, 0.0),
        }
        
        strategy, counter_allowed, size_mult = strategy_map.get(regime, ("Belirsiz", False, 0.3))
        
        # Confidence
        di_spread = abs(plus_di - minus_di)
        confidence = min(100, adx_val * 0.5 + di_spread * 2)
        
        return RegimeAnalysis(
            regime=regime,
            adx=round(adx_val, 1),
            adx_trend=adx_trend,
            price_structure=price_structure,
            volatility_percentile=round(vol_percentile, 1),
            trend_direction=trend_dir,
            confidence=round(confidence, 1),
            strategy_recommendation=strategy,
            counter_trend_allowed=counter_allowed,
            position_size_multiplier=size_mult,
            reasoning=reasoning
        )

```


## H. API/Dashboard Router

## DOSYA ADI: backend/routers/prediction.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
"""
API Router for ML Predictions
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/prediction", tags=["prediction"])


class KeyLevel(BaseModel):
    type: str
    price: float
    distance: str


class PredictionResponse(BaseModel):
    symbol: str
    direction: str
    confidence: float
    probability_up: float
    probability_down: float
    target_pips: float
    stop_pips: float
    risk_reward: float
    entry_price: float
    target_price: float
    stop_price: float
    technical_score: float
    momentum_score: float
    trend_score: float
    volatility_regime: str
    reasoning: List[str]
    key_levels: List[KeyLevel]
    timestamp: str
    model_version: str


@router.get("/{symbol}", response_model=PredictionResponse)
async def get_prediction(
    symbol: str,
    enabled_factors: Optional[str] = Query(
        default=None,
        description="Comma-separated list of enabled factor IDs (trend,confluence,session,pattern,candle,cot,sr,news,regime)"
    ),
    strategy: Optional[str] = Query(
        default="balanced",
        description="Preset strategy: ultra_safe, balanced, full_power, aggressive"
    ),
    log_to_db: bool = Query(
        default=False,
        description="Log this prediction to database for learning"
    )
):
    """
    Get ML prediction for a symbol.
    
    Returns direction (BUY/SELL/HOLD), confidence, pip targets, and analysis.
    - enabled_factors: Filter which confidence factors are applied
    - strategy: Preset layer configuration (ultra_safe, balanced, full_power, aggressive)
    - log_to_db: If true, logs prediction to database for learning system
    """
    from services.ml_prediction_service import get_ml_prediction
    
    # Parse enabled factors if provided
    factor_list = None
    if enabled_factors:
        factor_list = [f.strip() for f in enabled_factors.split(",") if f.strip()]
    
    # Validate strategy
    valid_strategies = ["ultra_safe", "balanced", "full_power", "aggressive"]
    if strategy not in valid_strategies:
        strategy = "balanced"
    
    result = await get_ml_prediction(symbol, enabled_factors=factor_list, strategy=strategy)
    
    # Log to database if requested (for learning system)
    if log_to_db:
        try:
            from services.prediction_logger import log_prediction
            from database.supabase_client import is_db_available
            
            if is_db_available():
                context = {
                    "symbol": symbol,
                    "ml_prediction": {
                        "direction": result.direction,
                        "confidence": result.confidence,
                        "probability_up": result.probability_up,
                        "probability_down": result.probability_down,
                        "entry_price": result.entry_price,
                        "target_price": result.target_price,
                        "stop_price": result.stop_price,
                    },
                    "ta": {},
                    "distances": {},
                    "volume": {},
                    "trend_channel": {},
                    "macro": {},
                    "news": {},
                }
                analysis = {
                    "final_decision": result.direction,
                    "confidence": result.confidence,
                    "model_used": result.model_version,
                }
                await log_prediction(
                    symbol=symbol,
                    context=context,
                    analysis=analysis,
                    timeframe="1d",
                    strategy=strategy
                )
        except Exception as e:
            import logging
            logging.warning(f"Failed to log prediction: {e}")
    
    return PredictionResponse(
        symbol=result.symbol,
        direction=result.direction,
        confidence=result.confidence,
        probability_up=result.probability_up,
        probability_down=result.probability_down,
        target_pips=result.target_pips,
        stop_pips=result.stop_pips,
        risk_reward=result.risk_reward,
        entry_price=result.entry_price,
        target_price=result.target_price,
        stop_price=result.stop_price,
        technical_score=result.technical_score,
        momentum_score=result.momentum_score,
        trend_score=result.trend_score,
        volatility_regime=result.volatility_regime,
        reasoning=result.reasoning,
        key_levels=[KeyLevel(**kl) for kl in result.key_levels],
        timestamp=result.timestamp,
        model_version=result.model_version
    )


@router.get("/", response_model=List[PredictionResponse])
async def get_all_predictions():
    """Get predictions for both NASDAQ and XAUUSD."""
    from services.ml_prediction_service import get_ml_prediction
    
    nasdaq = await get_ml_prediction("NDX.INDX")
    xauusd = await get_ml_prediction("XAUUSD")
    
    results = []
    for result in [nasdaq, xauusd]:
        results.append(PredictionResponse(
            symbol=result.symbol,
            direction=result.direction,
            confidence=result.confidence,
            probability_up=result.probability_up,
            probability_down=result.probability_down,
            target_pips=result.target_pips,
            stop_pips=result.stop_pips,
            risk_reward=result.risk_reward,
            entry_price=result.entry_price,
            target_price=result.target_price,
            stop_price=result.stop_price,
            technical_score=result.technical_score,
            momentum_score=result.momentum_score,
            trend_score=result.trend_score,
            volatility_regime=result.volatility_regime,
            reasoning=result.reasoning,
            key_levels=[KeyLevel(**kl) for kl in result.key_levels],
            timestamp=result.timestamp,
            model_version=result.model_version
        ))
    
    return results

```


## DOSYA ADI: backend/routers/nasdaq.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
from fastapi import APIRouter

from models.responses import SignalResponse
from services.ml_service import run_nasdaq_signal_async

router = APIRouter(prefix="/api/run", tags=["nasdaq"])


@router.post("/nasdaq", response_model=SignalResponse)
async def run_nasdaq() -> SignalResponse:
    """
    Run NASDAQ trend analysis using real-time data and trend_analyzer.
    Returns signal, confidence, reasoning, and metrics.
    """
    result = await run_nasdaq_signal_async()
    return SignalResponse(
        signal=result.signal,
        confidence=result.confidence,
        reasoning=result.reasoning,
        metrics=result.metrics,
        timestamp=result.timestamp,
        model_status=result.model_status,
    )

```


## DOSYA ADI: backend/routers/xauusd.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
from fastapi import APIRouter
from typing import List, Dict

from models.responses import SignalResponse
from services.ml_service import run_xauusd_signal_async
from services.gold_news_analyzer_v2 import analyze_gold_news_impact_v2
from pydantic import BaseModel

router = APIRouter(prefix="/api/run", tags=["xauusd"])


class GoldNewsResponse(BaseModel):
    """V2 Gold News Impact Response"""
    sentiment_score: float
    confidence: float
    impact_level: str
    direction_bias: str
    key_factors: List[str]
    news_count: int
    high_impact_events: List[dict]
    # V2 additions
    conflicts: List[str] = []
    time_to_expiry_minutes: int = 60
    source_breakdown: Dict[str, int] = {}
    validation_status: str = "pending"


@router.post("/xauusd", response_model=SignalResponse)
async def run_xauusd() -> SignalResponse:
    """
    Run XAUUSD trend analysis using real-time data and trend_analyzer.
    Returns signal, confidence, reasoning, and metrics.
    """
    result = await run_xauusd_signal_async()
    return SignalResponse(
        signal=result.signal,
        confidence=result.confidence,
        reasoning=result.reasoning,
        metrics=result.metrics,
        timestamp=result.timestamp,
        model_status=result.model_status,
    )


@router.get("/gold-news-impact", response_model=GoldNewsResponse)
async def get_gold_news_impact() -> GoldNewsResponse:
    """
    Analyze news impact on gold prices (XAUUSD) - V2 Advanced Analysis.
    
    Features:
    - Context-aware NLP with negation detection
    - Source reliability weighting (Reuters > Zerohedge)
    - Time decay (30 min half-life)
    - Dynamic event-based impact levels
    - Conflict detection for mixed signals
    
    Gold is heavily influenced by:
    - Interest rate decisions (Fed, ECB)
    - Inflation data (CPI, PPI)
    - Geopolitical events (wars, tensions)
    - USD strength/weakness
    - Real yields
    """
    impact = await analyze_gold_news_impact_v2()
    return GoldNewsResponse(
        sentiment_score=impact.sentiment_score,
        confidence=impact.confidence,
        impact_level=impact.impact_level,
        direction_bias=impact.direction_bias,
        key_factors=impact.key_factors,
        news_count=impact.news_count,
        high_impact_events=impact.high_impact_events,
        conflicts=impact.conflicts,
        time_to_expiry_minutes=impact.time_to_expiry_minutes,
        source_breakdown=impact.source_breakdown,
        validation_status=impact.validation_status,
    )

```


## DOSYA ADI: backend/main.py

### BULUNDU: Evet

### TAM İÇERİK:
```python
from datetime import datetime
import time
import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

# Load .env file - try multiple locations
env_paths = [
    Path(__file__).parent / ".env",  # backend/.env
    Path(__file__).parent.parent / ".env",  # project root/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Trading Dashboard API", version="0.1.0")

# CORS - allow all origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple health check first
@app.get("/api/health")
async def health_check():
    return {"ok": True, "status": "running"}

@app.get("/")
async def root():
    return {"message": "AI Trading Dashboard API", "status": "ok"}

ROUTERS_LOADED = False
IMPORT_ERROR = None

# Try to import routers with error handling
try:
    from models.responses import HealthResponse, RunAllResponse
    from routers import (
        nasdaq,
        xauusd,
        pattern_engine,
        claude_patterns,
        claude_sentiment,
        order_blocks,
        rtyhiim,
        news,
        ta,
        data,
        prediction,
        ai_analysis,
        learning,
        fvg,
        claude_news,
        auth,
        live_news,
        mtf_analysis,
        earnings,
    )
    from services.data_fetcher import fetch_latest_price
    from services.ml_service import run_nasdaq_signal, run_xauusd_signal
    from services.pattern_engine_runner import run_pattern_engine
    from services.pattern_analyzer import run_claude_pattern_analysis
    from services.sentiment_analyzer import run_claude_sentiment
    from services.rtyhiim_service import run_rtyhiim_detector
    from services.order_block_service import service as order_block_service
    from order_block_detector import OrderBlockConfig

    app.include_router(nasdaq.router)
    app.include_router(xauusd.router)
    app.include_router(pattern_engine.router)
    app.include_router(claude_patterns.router)
    app.include_router(claude_sentiment.router)
    app.include_router(order_blocks.router)
    app.include_router(rtyhiim.router)
    app.include_router(news.router)
    app.include_router(ta.router)
    app.include_router(data.router)
    app.include_router(prediction.router)
    app.include_router(ai_analysis.router)
    app.include_router(learning.router)
    app.include_router(fvg.router)
    app.include_router(claude_news.router)
    app.include_router(auth.router)
    app.include_router(live_news.router)
    app.include_router(mtf_analysis.router)
    app.include_router(earnings.router)
    
    ROUTERS_LOADED = True
except Exception as e:
    ROUTERS_LOADED = False
    IMPORT_ERROR = str(e)
    IMPORT_TRACEBACK = traceback.format_exc()
    print(f"ERROR loading routers: {e}", file=sys.stderr)
    print(IMPORT_TRACEBACK, file=sys.stderr)

@app.get("/api/debug")
async def debug_info():
    from config import settings
    return {
        "routers_loaded": ROUTERS_LOADED,
        "import_error": IMPORT_ERROR if not ROUTERS_LOADED else None,
        "env_vars_os": {
            "EODHD_API_KEY": "set" if os.getenv("EODHD_API_KEY") else "not set",
            "ANTHROPIC_API_KEY": "set" if os.getenv("ANTHROPIC_API_KEY") else "not set",
            "SUPABASE_URL": "set" if os.getenv("SUPABASE_URL") else "not set",
            "SUPABASE_KEY": "set" if os.getenv("SUPABASE_KEY") else "not set",
            "SUPABASE_ANON_KEY": "set" if os.getenv("SUPABASE_ANON_KEY") else "not set",
        },
        "settings_config": {
            "anthropic_api_key": "set" if settings.anthropic_api_key else "not set",
            "eodhd_api_key": "set" if settings.eodhd_api_key else "not set",
        }
    }


@app.get("/api/debug/ml-model/{symbol}")
async def debug_ml_model(symbol: str):
    """Debug ML model loading and prediction for a symbol."""
    from pathlib import Path
    result = {"symbol": symbol, "errors": [], "info": []}
    
    # Check model file
    model_path = Path(__file__).parent / "models"
    result["model_dir"] = str(model_path)
    result["model_dir_exists"] = model_path.exists()
    
    if symbol.upper() in ["NASDAQ", "NDX.INDX", "NDX"]:
        model_file = model_path / "model_lgbm_nasdaq.joblib"
    elif symbol.upper() == "XAUUSD":
        model_file = model_path / "model_lgbm_xauusd.joblib"
    else:
        model_file = None
    
    if model_file:
        result["model_file"] = str(model_file)
        result["model_file_exists"] = model_file.exists()
        
        if model_file.exists():
            try:
                import joblib
                model = joblib.load(model_file)
                result["model_loaded"] = True
                result["model_type"] = str(type(model))
                if hasattr(model, 'feature_names_in_'):
                    features = list(model.feature_names_in_)
                    result["feature_count"] = len(features)
                    result["features_sample"] = features[:20]
                else:
                    result["errors"].append("Model has no feature_names_in_")
            except Exception as e:
                result["model_loaded"] = False
                result["errors"].append(f"Model load error: {str(e)}")
    
    # Check data fetching
    try:
        from services.data_fetcher import fetch_30m_candles, fetch_latest_price, fetch_eod_candles
        normalized = "NDX.INDX" if symbol.upper() in ["NASDAQ", "NDX.INDX", "NDX"] else symbol.upper()
        
        candles_30m = await fetch_30m_candles(normalized, limit=50)
        result["candles_30m_count"] = len(candles_30m) if candles_30m else 0
        
        candles_eod = await fetch_eod_candles(normalized, limit=50)
        result["candles_eod_count"] = len(candles_eod) if candles_eod else 0
        
        price = await fetch_latest_price(normalized)
        result["latest_price"] = price
        
        if not candles_30m or len(candles_30m) < 50:
            result["info"].append(f"M30 candles: {len(candles_30m) if candles_30m else 0}")
        if not candles_eod or len(candles_eod) < 50:
            result["errors"].append(f"Insufficient EOD candles: {len(candles_eod) if candles_eod else 0}")
    except Exception as e:
        result["errors"].append(f"Data fetch error: {str(e)}")
    
    return result


@app.get("/api/debug/news-test")
async def debug_news_test():
    """Test news API sources."""
    import httpx
    from config import settings
    
    result = {"eodhd_news": None, "marketaux_news": None}
    
    # Test EODHD News API
    if settings.eodhd_api_key:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(
                    "https://eodhistoricaldata.com/api/news",
                    params={
                        "api_token": settings.eodhd_api_key,
                        "s": "GOLD,GLD.US,DXY.INDX",
                        "limit": 5,
                        "fmt": "json",
                    },
                )
                result["eodhd_status"] = resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    result["eodhd_news"] = [{"title": n.get("title", "")[:80], "date": n.get("date", "")} for n in (data or [])[:3]]
                else:
                    result["eodhd_error"] = resp.text[:200]
        except Exception as e:
            result["eodhd_error"] = str(e)
    
    # Test MarketAux
    if settings.marketaux_api_key:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    settings.marketaux_base_url,
                    params={
                        "api_token": settings.marketaux_api_key,
                        "symbols": "XAUUSD,GOLD",
                        "limit": 5,
                        "language": "en",
                    },
                )
                result["marketaux_status"] = resp.status_code
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    result["marketaux_news"] = [{"title": n.get("title", "")[:80], "published": n.get("published_at", "")} for n in (data or [])[:3]]
                else:
                    result["marketaux_error"] = resp.text[:200]
        except Exception as e:
            result["marketaux_error"] = str(e)
    
    return result


@app.get("/api/debug/intraday-test/{symbol}")
async def debug_intraday_test(symbol: str):
    """Test EODHD intraday API directly."""
    import httpx
    from config import settings
    
    result = {"symbol": symbol, "tests": []}
    
    # Normalize symbol
    if symbol.upper() == "XAUUSD":
        test_symbols = ["XAUUSD.FOREX", "XAU.FOREX", "XAUUSD", "GC.COMEX"]
    else:
        test_symbols = [symbol]
    
    for test_sym in test_symbols:
        test_result = {"symbol": test_sym}
        url = f"https://eodhistoricaldata.com/api/intraday/{test_sym}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Use 1m for forex (EODHD only provides 1m for forex)
                interval = "1m" if ".FOREX" in test_sym.upper() else "5m"
                resp = await client.get(
                    url,
                    params={
                        "api_token": settings.eodhd_api_key,
                        "fmt": "json",
                        "interval": interval,
                    },
                )
                test_result["status_code"] = resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        test_result["count"] = len(data)
                        if data:
                            test_result["sample"] = data[-1]
                    else:
                        test_result["response_type"] = str(type(data))
                        test_result["response_preview"] = str(data)[:200]
                else:
                    test_result["error"] = resp.text[:200]
        except Exception as e:
            test_result["exception"] = str(e)
        
        result["tests"].append(test_result)
    
    return result


# ═══════════════════════════════════════════════════════════════════
# SLIPPAGE & COT API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/slippage/stats")
async def get_slippage_stats():
    """Get slippage statistics and current position multiplier."""
    try:
        from services.slippage_monitor import get_slippage_stats, get_position_multiplier
        stats = await get_slippage_stats()
        return {
            "success": True,
            "data": {
                "average_slippage": stats.average_slippage,
                "max_slippage": stats.max_slippage,
                "min_slippage": stats.min_slippage,
                "favorable_count": stats.favorable_count,
                "unfavorable_count": stats.unfavorable_count,
                "total_trades": stats.total_trades,
                "position_multiplier": stats.position_multiplier,
                "high_slippage_mode": stats.high_slippage_mode,
                "last_10_trades": stats.last_10_trades,
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/slippage/log")
async def log_execution(data: dict):
    """Log a trade execution for slippage tracking."""
    try:
        from services.slippage_monitor import handle_execution_webhook
        result = await handle_execution_webhook(data)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/cot/summary")
async def get_cot_summary():
    """Get COT report summary for all tracked symbols."""
    try:
        from services.cot_report_service import get_cot_summary
        summary = await get_cot_summary()
        return {"success": True, "data": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/cot/{symbol}")
async def get_cot_data(symbol: str):
    """Get COT report data for a specific symbol."""
    try:
        from services.cot_report_service import fetch_cot_data
        from dataclasses import asdict
        cot = await fetch_cot_data(symbol)
        return {"success": True, "data": asdict(cot)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/candlestick-patterns/{symbol}")
async def get_candlestick_patterns(symbol: str):
    """
    Get candlestick patterns for a symbol across M15, M30, H1, H4 timeframes.
    Returns detected patterns with explanations in Turkish.
    """
    try:
        from services.candlestick_pattern_service import detect_candlestick_patterns
        result = await detect_candlestick_patterns(symbol, ["15m", "30m", "1h", "4h"])
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Startup event - start background scheduler
@app.on_event("startup")
async def startup_event():
    try:
        from services.background_scheduler import start_scheduler
        start_scheduler()
        print("Background scheduler started")
    except Exception as e:
        print(f"Failed to start scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from services.background_scheduler import stop_scheduler
        stop_scheduler()
        print("Background scheduler stopped")
    except Exception as e:
        print(f"Error stopping scheduler: {e}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

```


## 3. Kod Analizi (Check-list Yanıtları)
Bu bölümde koddan gözlemlenen durumlar özetlenmiştir. Detay ve kaynak kod yukarıdaki bölümlerde yer alır.

### ML Prediction Service
- Cooldown/Stabilite kontrolü: **Evet** (memory cache + 30dk cooldown)
- Minimum confidence kontrolü: **Evet** (preset threshold + reversal için min confidence)
- Fiyat hareketi threshold: **Evet** (`MIN_PRICE_CHANGE_PCT`)
- Yön değişikliği için ek onay: **Evet** (cooldown + confidence + price move + old_confidence kıyas)
- State machine (PENDING→CONFIRMED→ACTIVE): **Kısmi** (Signal stability cache var; yeni trading_engine içinde state machine var)

### Layer Aggregator
- 3 katman ağırlıkları: **50/30/20** (CONFIDENCE_LAYERS)
- Harmonic/Geometric/Arithmetic mean: **Var**
- Katman çelişki çözümü: **Sınırlı** (floor_ratio ile tabanlama var; explicit conflict resolver yok)

### Regime-based filtering
- Rejim tespiti: **Var** (`mtf_analysis_service.py` + `trading_engine/regime_detector.py`)
- Trend piyasasında counter-trend engelleme: **Var** (ml_prediction_service entegrasyonu)


## 4. Son Değişiklikler (Git)
### Son 5 commit
```
0fa6ad4 Add Advanced Trading Engine - MTF analysis, regime detection, confluence scoring, 5-layer decision system
13b9f87 Fix strategy-performance endpoint - complete rewrite with proper structure
5bac43e Fix strategy-performance indentation and simplify logic
5246d81 Optimize strategy-performance - batch outcome query instead of N+1
ccc671e Fix strategy-performance 500 error - separate outcome queries

```

### Son committe değişen dosyalar
```
0fa6ad4628772129d9aeb5c75a43d689be56971a Add Advanced Trading Engine - MTF analysis, regime detection, confluence scoring, 5-layer decision system
backend/services/ml_prediction_service.py
backend/services/trading_engine/__init__.py
backend/services/trading_engine/confluence_engine.py
backend/services/trading_engine/constants.py
backend/services/trading_engine/decision_layers.py
backend/services/trading_engine/helpers.py
backend/services/trading_engine/mtf_analyzer.py
backend/services/trading_engine/regime_detector.py
backend/services/trading_engine/signal_state_machine.py

```

## 5. Eksikler (Var/Yok)
- **Regime-based filtering**: VAR (trading_engine entegrasyonu)
- **Multi-timeframe consensus**: KISMİ (mtf_analysis_service var; trading_engine MTF iskeleti var ama her TF tam kullanılmıyor)
- **Layer conflict resolution**: KISMİ (floor_ratio var; explicit conflict resolver yok)
- **Learning-integrated prediction**: VAR (apply_learning_feedback)
- **Adaptive cooldown**: YOK (cooldown sabit; adaptif değil)
- **Pattern prioritization**: KISMİ (pattern servisleri var; TF önceliği sınırlı)
- **State machine (PENDING→CONFIRMED→ACTIVE)**: VAR (trading_engine/signal_state_machine var; ancak execution gerçek trade sistemine bağlı değil)
- **Position tracking (mevcut pozisyon)**: YOK (DB/portfolio entegrasyonu yok; state memory temelli)

## 6. Genel Değerlendirme
| Kriter | Durum | Açıklama |
|:---|:---|:---|
| Sinyal Stabilitesi | İyi | 30dk cooldown + reversal koşulları + cache |
| Multi-TF Uyumu | Orta | `mtf_analysis_service` güçlü; trading_engine tarafında henüz tüm TF’ler tam entegre değil |
| Katman Entegrasyonu | İyi | 50/30/20 layer sistemi mevcut |
| Pattern Çakışma Çözümü | Orta | Pattern servisleri var; TF önceliği ve conflict resolution sınırlı |
| Regime Farkındalığı | Var | ADX+structure rejim + counter-trend blok |
| Learning Entegrasyonu | Var | `apply_learning_feedback` ile confidence ayarı |

### Önerilen Öncelikli Değişiklikler
1. **Adaptive cooldown**: rejim/volatiliteye göre cooldown dinamikleştir (örn. ATR percentile / ADX trend)
2. **Gerçek MTF consensus**: Weekly+Daily+4H zorunlu onay matrisi (1W verisi eklenmeli)
3. **Layer conflict resolver**: Critical vs Technical zıt ise “WAIT/NO_TRADE” state’i üret
4. **Position tracking**: açık pozisyonu DB’de tut ve state machine’i onunla senkronla
