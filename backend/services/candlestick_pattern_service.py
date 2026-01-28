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
