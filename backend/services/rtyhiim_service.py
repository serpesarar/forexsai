from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sys

import numpy as np
import httpx

from models.rtyhiim import RtyhiimPrediction, RtyhiimResponse, RtyhiimState
from config import settings


@dataclass
class ConsolidationResult:
    """Yatay hareket (consolidation) tespit sonucu."""
    is_consolidating: bool  # Yatay hareket var mı?
    range_high: float  # Range üst sınırı
    range_low: float  # Range alt sınırı
    range_size: float  # Range boyutu (pips/points)
    range_percent: float  # Range boyutu (% olarak)
    midpoint: float  # Range orta noktası
    current_price: float  # Anlık fiyat
    position_in_range: float  # Fiyatın range içindeki pozisyonu (0-100%)
    atr: float  # Average True Range
    volatility_ratio: float  # ATR / Range oranı
    consolidation_score: float  # Consolidation skoru (0-100)
    candles_analyzed: int  # Analiz edilen mum sayısı
    breakout_direction: Optional[str]  # Potansiyel kırılım yönü
    # Swing point based detection
    swing_highs: List[float]  # Tespit edilen tepe noktaları
    swing_lows: List[float]  # Tespit edilen dip noktaları
    swing_high_consistency: bool  # Tepeler tutarlı mı?
    swing_low_consistency: bool  # Dipler tutarlı mı?
    swing_count: int  # Toplam swing sayısı
    high_deviation: float  # Tepeler arası maksimum sapma
    low_deviation: float  # Dipler arası maksimum sapma
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _get_symbol_threshold(symbol: str) -> float:
    """
    Sembol bazlı sapma threshold'u döndür.
    XAUUSD: 3 pip ($3)
    NASDAQ: 15 point
    """
    sym = symbol.upper()
    if "XAU" in sym or "GOLD" in sym:
        return 3.0  # $3 for gold
    elif "NDX" in sym or "NASDAQ" in sym or "NAS" in sym:
        return 15.0  # 15 points for NASDAQ
    elif "EUR" in sym or "GBP" in sym or "JPY" in sym:
        return 0.0015  # 15 pips for forex
    else:
        return 10.0  # Default


def _detect_swing_points(candles: List[Dict], lookback: int = 3) -> tuple:
    """
    Swing high ve swing low noktalarını tespit et.
    
    Swing High: Sağındaki ve solundaki N mumdan daha yüksek
    Swing Low: Sağındaki ve solundaki N mumdan daha düşük
    
    Returns:
        (swing_highs, swing_lows, swing_high_indices, swing_low_indices)
    """
    swing_highs = []
    swing_lows = []
    swing_high_indices = []
    swing_low_indices = []
    
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    
    for i in range(lookback, len(candles) - lookback):
        # Swing High kontrolü
        is_swing_high = True
        for j in range(1, lookback + 1):
            if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                is_swing_high = False
                break
        
        if is_swing_high:
            swing_highs.append(highs[i])
            swing_high_indices.append(i)
        
        # Swing Low kontrolü
        is_swing_low = True
        for j in range(1, lookback + 1):
            if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                is_swing_low = False
                break
        
        if is_swing_low:
            swing_lows.append(lows[i])
            swing_low_indices.append(i)
    
    return swing_highs, swing_lows, swing_high_indices, swing_low_indices


def _check_swing_consistency(swing_points: List[float], threshold: float) -> tuple:
    """
    Swing noktalarının tutarlılığını kontrol et.
    
    Tüm noktalar arasındaki maksimum sapma threshold'dan küçükse tutarlı.
    
    Returns:
        (is_consistent, max_deviation)
    """
    if len(swing_points) < 2:
        return False, 0.0
    
    max_deviation = max(swing_points) - min(swing_points)
    is_consistent = max_deviation <= threshold
    
    return is_consistent, max_deviation


async def detect_consolidation(
    symbol: str,
    lookback: int = 20,
    interval: str = "1m"
) -> ConsolidationResult:
    """
    Yatay hareket (consolidation/range) tespiti.
    
    İki yöntem kullanılır:
    1. Swing Point Consistency: Tepe ve dip noktalarının belirli sapma içinde kalması
    2. Statistical: ATR, slope, range analizi
    
    Args:
        symbol: Trading sembolü
        lookback: Kontrol edilecek mum sayısı (varsayılan: 20)
        interval: Zaman dilimi (varsayılan: 1m)
    
    Returns:
        ConsolidationResult: Yatay hareket analiz sonucu
    """
    # Intraday veri çek
    candles = await fetch_intraday_candles(symbol, interval, lookback + 14)  # ATR için ekstra
    
    if not candles or len(candles) < lookback:
        return ConsolidationResult(
            is_consolidating=False,
            range_high=0, range_low=0, range_size=0, range_percent=0,
            midpoint=0, current_price=0, position_in_range=0,
            atr=0, volatility_ratio=0, consolidation_score=0,
            candles_analyzed=0, breakout_direction=None,
            swing_highs=[], swing_lows=[],
            swing_high_consistency=False, swing_low_consistency=False,
            swing_count=0, high_deviation=0, low_deviation=0
        )
    
    # Son N mumu al
    recent = candles[-lookback:]
    
    # OHLC değerlerini çıkar
    highs = [c["high"] for c in recent]
    lows = [c["low"] for c in recent]
    closes = [c["close"] for c in recent]
    
    # Range hesapla
    range_high = max(highs)
    range_low = min(lows)
    range_size = range_high - range_low
    current_price = closes[-1]
    midpoint = (range_high + range_low) / 2
    range_percent = (range_size / midpoint) * 100 if midpoint > 0 else 0
    
    # Fiyatın range içindeki pozisyonu (0-100%)
    position_in_range = ((current_price - range_low) / range_size * 100) if range_size > 0 else 50
    
    # ATR hesapla (14 periyot)
    atr = _calculate_atr_from_candles(candles, 14)
    
    # Volatility ratio
    volatility_ratio = (atr / range_size) if range_size > 0 else 0
    
    # === SWING POINT DETECTION ===
    threshold = _get_symbol_threshold(symbol)
    swing_highs, swing_lows, _, _ = _detect_swing_points(recent, lookback=2)
    
    # Swing tutarlılık kontrolü
    swing_high_consistent, high_deviation = _check_swing_consistency(swing_highs, threshold)
    swing_low_consistent, low_deviation = _check_swing_consistency(swing_lows, threshold)
    
    total_swings = len(swing_highs) + len(swing_lows)
    
    # === CONSOLIDATION KARARI ===
    # Yeni mantık: Her iki tarafta da tutarlı swing noktaları varsa ve minimum 4 swing varsa
    swing_based_consolidation = (
        swing_high_consistent and 
        swing_low_consistent and 
        total_swings >= 4
    )
    
    # Statistical score (yedek olarak)
    statistical_score = _calculate_consolidation_score(
        closes, range_size, atr, volatility_ratio, current_price, midpoint
    )
    
    # Final karar: Swing based öncelikli, statistical yedek
    if swing_based_consolidation:
        is_consolidating = True
        # Swing tutarlılığına göre score hesapla
        consolidation_score = min(100, 60 + (total_swings * 5) + (20 if high_deviation < threshold/2 else 0) + (20 if low_deviation < threshold/2 else 0))
    else:
        is_consolidating = statistical_score >= 70  # Daha yüksek threshold
        consolidation_score = statistical_score
    
    # Breakout yönü tahmini
    breakout_direction = None
    if is_consolidating:
        if position_in_range > 70:
            breakout_direction = "UP"
        elif position_in_range < 30:
            breakout_direction = "DOWN"
        else:
            breakout_direction = "NEUTRAL"
    
    return ConsolidationResult(
        is_consolidating=is_consolidating,
        range_high=round(range_high, 4),
        range_low=round(range_low, 4),
        range_size=round(range_size, 4),
        range_percent=round(range_percent, 4),
        midpoint=round(midpoint, 4),
        current_price=round(current_price, 4),
        position_in_range=round(position_in_range, 2),
        atr=round(atr, 4),
        volatility_ratio=round(volatility_ratio, 4),
        consolidation_score=round(consolidation_score, 2),
        candles_analyzed=len(recent),
        breakout_direction=breakout_direction,
        swing_highs=[round(h, 4) for h in swing_highs],
        swing_lows=[round(l, 4) for l in swing_lows],
        swing_high_consistency=swing_high_consistent,
        swing_low_consistency=swing_low_consistent,
        swing_count=total_swings,
        high_deviation=round(high_deviation, 4),
        low_deviation=round(low_deviation, 4)
    )


def _calculate_atr_from_candles(candles: List[Dict], period: int = 14) -> float:
    """ATR hesapla."""
    if len(candles) < period + 1:
        return 0.0
    
    tr_values = []
    for i in range(1, min(len(candles), period + 1)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i - 1]["close"]
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        tr_values.append(tr)
    
    return sum(tr_values) / len(tr_values) if tr_values else 0.0


def _calculate_consolidation_score(
    closes: List[float],
    range_size: float,
    atr: float,
    volatility_ratio: float,
    current_price: float,
    midpoint: float
) -> float:
    """
    Consolidation skoru hesapla (0-100).
    
    Yüksek skor = Güçlü yatay hareket
    """
    score = 0.0
    
    # 1. Range/ATR oranı (max 30 puan)
    # ATR'nin range'e oranı düşükse consolidation güçlü
    if range_size > 0 and atr > 0:
        atr_ratio = atr / range_size
        if atr_ratio < 0.3:
            score += 30
        elif atr_ratio < 0.5:
            score += 20
        elif atr_ratio < 0.7:
            score += 10
    
    # 2. Fiyat ortaya yakınlık (max 20 puan)
    if range_size > 0:
        distance_from_mid = abs(current_price - midpoint) / (range_size / 2)
        if distance_from_mid < 0.3:
            score += 20
        elif distance_from_mid < 0.5:
            score += 15
        elif distance_from_mid < 0.7:
            score += 10
    
    # 3. Trend düzlüğü (max 30 puan)
    if len(closes) >= 5:
        # Linear regression slope
        x = np.arange(len(closes))
        slope, _ = np.polyfit(x, closes, 1)
        slope_pct = abs(slope / np.mean(closes)) * 100
        
        if slope_pct < 0.01:  # Çok düz
            score += 30
        elif slope_pct < 0.05:
            score += 20
        elif slope_pct < 0.1:
            score += 10
    
    # 4. Range boyutu kontrolü (max 20 puan)
    # Çok dar range = güçlü consolidation
    range_pct = (range_size / current_price) * 100 if current_price > 0 else 0
    if range_pct < 0.5:
        score += 20
    elif range_pct < 1.0:
        score += 15
    elif range_pct < 2.0:
        score += 10
    
    return min(100.0, score)


async def fetch_intraday_candles(symbol: str, interval: str = "1m", limit: int = 100) -> List[Dict]:
    """Intraday mum verisi çek."""
    if not settings.eodhd_api_key:
        return []
    
    # Symbol normalizasyonu
    if symbol.upper() == "XAUUSD":
        eod_symbol = "XAUUSD.FOREX"
    elif symbol.upper() in ("NDX.INDX", "NASDAQ", "NDX"):
        eod_symbol = "NDX.INDX"
    else:
        eod_symbol = symbol
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"https://eodhistoricaldata.com/api/intraday/{eod_symbol}"
            resp = await client.get(url, params={
                "api_token": settings.eodhd_api_key,
                "fmt": "json",
                "interval": interval
            })
            
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list):
                    candles = []
                    for d in data[-limit:]:
                        candles.append({
                            "timestamp": d.get("timestamp", 0),
                            "open": float(d.get("open", 0)),
                            "high": float(d.get("high", 0)),
                            "low": float(d.get("low", 0)),
                            "close": float(d.get("close", 0)),
                            "volume": float(d.get("volume", 0))
                        })
                    return candles
    except Exception:
        pass
    
    return []


async def fetch_live_prices(symbol: str, limit: int = 600) -> List[float]:
    """Fetch live intraday prices for rhythm detection."""
    if not settings.eodhd_api_key:
        return []
    
    # Normalize symbol for EODHD
    if symbol.upper() == "XAUUSD":
        eod_symbol = "XAUUSD.FOREX"
    elif symbol.upper() in ("NDX.INDX", "NASDAQ", "NDX"):
        eod_symbol = "NDX.INDX"
    else:
        eod_symbol = symbol
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Try intraday data first
            url = f"https://eodhistoricaldata.com/api/intraday/{eod_symbol}"
            resp = await client.get(url, params={
                "api_token": settings.eodhd_api_key,
                "fmt": "json",
                "interval": "1m"
            })
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list):
                    prices = [float(d.get("close", d.get("price", 0))) for d in data[-limit:]]
                    if prices and len(prices) > 50:
                        return prices
            
            # Fallback to EOD data
            url = f"https://eodhistoricaldata.com/api/eod/{eod_symbol}"
            resp = await client.get(url, params={
                "api_token": settings.eodhd_api_key,
                "fmt": "json",
                "period": "d",
                "order": "d"
            })
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list):
                    prices = [float(d.get("close", 0)) for d in reversed(data[:limit])]
                    if prices:
                        return prices
    except Exception:
        pass
    return []


def run_rtyhiim_detector(symbol: str, timeframe: str) -> Dict[str, object]:
    """Run the RTYHIIM detector using the shared rhythm detector logic (sync wrapper)."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context, use sync fallback
            state = _run_rhythm_engine_sync(symbol)
        else:
            state = loop.run_until_complete(_run_rhythm_engine_async(symbol))
    except RuntimeError:
        state = _run_rhythm_engine_sync(symbol)
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "state": state,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


async def run_rtyhiim_detector_async(symbol: str, timeframe: str) -> Dict[str, object]:
    """Run the RTYHIIM detector using live data (async version)."""
    state = await _run_rhythm_engine_async(symbol)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "state": state,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


async def _run_rhythm_engine_async(symbol: str) -> Dict[str, object]:
    """Async version that fetches live prices."""
    detector = _build_detector()
    
    # Fetch live prices
    prices = await fetch_live_prices(symbol, 600)
    if not prices or len(prices) < 50:
        # Fallback to generated prices if live data unavailable
        prices = _generate_prices(600).tolist()
    
    for idx, price in enumerate(prices):
        detector.add_tick(float(price), timestamp=float(idx))
    
    rhythm_state = detector.detect_wave_pattern()
    decision = detector.should_trade()

    return _build_state_response(rhythm_state, decision, len(prices) > 50 and prices[0] != prices[-1])


def _run_rhythm_engine_sync(symbol: str) -> Dict[str, object]:
    """Sync version for use when already in async context."""
    detector = _build_detector()
    prices = _generate_prices(600)
    
    for idx, price in enumerate(prices):
        detector.add_tick(float(price), timestamp=float(idx))
    
    rhythm_state = detector.detect_wave_pattern()
    decision = detector.should_trade()

    return _build_state_response(rhythm_state, decision, False)


def _build_state_response(rhythm_state: dict, decision: dict, is_live: bool) -> Dict[str, object]:
    """Build the state response from rhythm detection results."""
    predictions = []
    for horizon in ("30s", "60s", "120s"):
        value = rhythm_state.get("predictions", {}).get(horizon)
        if value is None:
            continue
        predictions.append(
            {
                "horizon": horizon,
                "value": float(value),
                "confidence": float(rhythm_state.get("confidence", 0.0)),
            }
        )

    return RtyhiimState(
        pattern_type=str(rhythm_state.get("pattern_type")),
        dominant_period_s=float(rhythm_state.get("dominant_period_s", 0.0)),
        confidence=float(rhythm_state.get("confidence", 0.0)),
        regularity=float(rhythm_state.get("regularity", 0.0)),
        phase=float(rhythm_state.get("phase", 0.0)),
        amplitude=float(rhythm_state.get("amplitude", 0.0)),
        should_trade=bool(decision.get("should_trade")),
        direction=str(decision.get("direction")),
        predictions=[RtyhiimPrediction(**item) for item in predictions],
    ).dict()


def _build_detector():
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    try:
        from rhythm_detector_v2 import RhythmDetector, RhythmConfig

        return RhythmDetector(
            RhythmConfig(
                window_seconds=settings.rtyhiim_window_seconds,
                tick_rate_hz=settings.rtyhiim_tick_rate_hz,
                min_period_s=settings.rtyhiim_min_period_s,
                max_period_s=settings.rtyhiim_max_period_s,
            )
        )
    except Exception:
        from rhythm_detector import RhythmDetector, RhythmConfig

        return RhythmDetector(
            RhythmConfig(
                window_seconds=settings.rtyhiim_window_seconds,
                tick_rate_hz=settings.rtyhiim_tick_rate_hz,
                min_period_s=settings.rtyhiim_min_period_s,
                max_period_s=settings.rtyhiim_max_period_s,
            )
        )


def _generate_prices(length: int) -> np.ndarray:
    t = np.arange(length)
    return 100 + np.sin(2 * np.pi * (1 / 60) * t) + np.random.normal(scale=0.3, size=length)
