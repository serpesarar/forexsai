from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import numpy as np
import httpx

from models.rtyhiim import RtyhiimPrediction, RtyhiimResponse, RtyhiimState
from config import settings


@dataclass
class ConsolidationResult:
    """Yatay hareket (consolidation) tespit sonucu."""
    is_consolidating: bool
    range_high: float
    range_low: float
    range_size: float
    range_percent: float
    midpoint: float
    current_price: float
    position_in_range: float
    atr: float
    volatility_ratio: float
    consolidation_score: float
    candles_analyzed: int
    breakout_direction: Optional[str]
    swing_highs: List[float]
    swing_lows: List[float]
    swing_high_consistency: bool
    swing_low_consistency: bool
    swing_count: int
    high_deviation: float
    low_deviation: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _get_symbol_threshold(symbol: str) -> float:
    sym = symbol.upper()
    if "XAU" in sym or "GOLD" in sym:
        return 3.0
    if "NDX" in sym or "NASDAQ" in sym or "NAS" in sym:
        return 15.0
    if "EUR" in sym or "GBP" in sym or "JPY" in sym:
        return 0.0015
    return 10.0


def _detect_swing_points(candles: List[Dict[str, Any]], lookback: int = 3):
    swing_highs: List[float] = []
    swing_lows: List[float] = []
    swing_high_indices: List[int] = []
    swing_low_indices: List[int] = []
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    for i in range(lookback, len(candles) - lookback):
        is_swing_high = True
        for j in range(1, lookback + 1):
            if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                is_swing_high = False
                break
        if is_swing_high:
            swing_highs.append(highs[i])
            swing_high_indices.append(i)

        is_swing_low = True
        for j in range(1, lookback + 1):
            if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                is_swing_low = False
                break
        if is_swing_low:
            swing_lows.append(lows[i])
            swing_low_indices.append(i)

    return swing_highs, swing_lows, swing_high_indices, swing_low_indices


def _check_swing_consistency(swing_points: List[float], threshold: float):
    if len(swing_points) < 2:
        return False, 0.0
    max_deviation = max(swing_points) - min(swing_points)
    return max_deviation <= threshold, max_deviation


def _calculate_atr_from_candles(candles: List[Dict[str, Any]], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0.0
    tr_values: List[float] = []
    for i in range(1, min(len(candles), period + 1)):
        high = float(candles[i]["high"])
        low = float(candles[i]["low"])
        prev_close = float(candles[i - 1]["close"])
        tr_values.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    return sum(tr_values) / len(tr_values) if tr_values else 0.0


def _calculate_consolidation_score(
    closes: List[float],
    range_size: float,
    atr: float,
    volatility_ratio: float,
    current_price: float,
    midpoint: float,
) -> float:
    score = 0.0
    if range_size > 0 and atr > 0:
        atr_ratio = atr / range_size
        if atr_ratio < 0.3:
            score += 30
        elif atr_ratio < 0.5:
            score += 20
        elif atr_ratio < 0.7:
            score += 10

    if range_size > 0:
        distance_from_mid = abs(current_price - midpoint) / (range_size / 2)
        if distance_from_mid < 0.3:
            score += 20
        elif distance_from_mid < 0.5:
            score += 15
        elif distance_from_mid < 0.7:
            score += 10

    if len(closes) >= 5:
        x = np.arange(len(closes))
        slope, _ = np.polyfit(x, closes, 1)
        slope_pct = abs(float(slope) / float(np.mean(closes))) * 100
        if slope_pct < 0.01:
            score += 30
        elif slope_pct < 0.05:
            score += 20
        elif slope_pct < 0.1:
            score += 10

    range_pct = (range_size / current_price) * 100 if current_price > 0 else 0
    if range_pct < 0.5:
        score += 20
    elif range_pct < 1.0:
        score += 15
    elif range_pct < 2.0:
        score += 10
    return min(100.0, score)


async def fetch_intraday_candles(symbol: str, interval: str = "1m", limit: int = 100) -> List[Dict[str, Any]]:
    from services.data_fetcher import fetch_intraday_candles as _central_fetch
    return await _central_fetch(symbol, interval=interval, limit=limit)


async def fetch_live_prices(symbol: str, limit: int = 600) -> List[float]:
    from services.data_fetcher import fetch_intraday_candles as _central_fetch
    candles = await _central_fetch(symbol, interval="5m", limit=limit)
    if candles:
        return [float(c.get("close", 0)) for c in candles[-limit:]]

    from services.data_fetcher import fetch_eod_candles
    eod = await fetch_eod_candles(symbol, limit=limit)
    if eod:
        return [float(c.get("close", 0)) for c in eod[-limit:]]
    return []


async def detect_consolidation(symbol: str, lookback: int = 20, interval: str = "1m") -> ConsolidationResult:
    candles = await fetch_intraday_candles(symbol, interval, lookback + 14)
    if not candles or len(candles) < lookback:
        return ConsolidationResult(
            is_consolidating=False,
            range_high=0,
            range_low=0,
            range_size=0,
            range_percent=0,
            midpoint=0,
            current_price=0,
            position_in_range=0,
            atr=0,
            volatility_ratio=0,
            consolidation_score=0,
            candles_analyzed=0,
            breakout_direction=None,
            swing_highs=[],
            swing_lows=[],
            swing_high_consistency=False,
            swing_low_consistency=False,
            swing_count=0,
            high_deviation=0,
            low_deviation=0,
        )

    recent = candles[-lookback:]
    highs = [float(c["high"]) for c in recent]
    lows = [float(c["low"]) for c in recent]
    closes = [float(c["close"]) for c in recent]
    range_high = max(highs)
    range_low = min(lows)
    range_size = range_high - range_low
    current_price = closes[-1]
    midpoint = (range_high + range_low) / 2
    range_percent = (range_size / midpoint) * 100 if midpoint > 0 else 0
    position_in_range = ((current_price - range_low) / range_size * 100) if range_size > 0 else 50
    atr = _calculate_atr_from_candles(candles, 14)
    volatility_ratio = (atr / range_size) if range_size > 0 else 0

    threshold = _get_symbol_threshold(symbol)
    swing_highs, swing_lows, _, _ = _detect_swing_points(recent, lookback=2)
    swing_high_consistent, high_deviation = _check_swing_consistency(swing_highs, threshold)
    swing_low_consistent, low_deviation = _check_swing_consistency(swing_lows, threshold)
    total_swings = len(swing_highs) + len(swing_lows)
    swing_based_consolidation = swing_high_consistent and swing_low_consistent and total_swings >= 4
    statistical_score = _calculate_consolidation_score(closes, range_size, atr, volatility_ratio, current_price, midpoint)

    if swing_based_consolidation:
        is_consolidating = True
        consolidation_score = min(
            100,
            60 + (total_swings * 5) + (20 if high_deviation < threshold / 2 else 0) + (20 if low_deviation < threshold / 2 else 0),
        )
    else:
        is_consolidating = statistical_score >= 70
        consolidation_score = statistical_score

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
        low_deviation=round(low_deviation, 4),
    )


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
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


async def run_rtyhiim_detector_async(symbol: str, timeframe: str) -> Dict[str, object]:
    """Run the RTYHIIM detector using live data (async version)."""
    state = await _run_rhythm_engine_async(symbol)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "state": state,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


async def _run_rhythm_engine_async(symbol: str) -> Dict[str, object]:
    """Async version that fetches live prices."""
    detector = _build_detector()

    prices = await fetch_live_prices(symbol, 600)
    if not prices or len(prices) < 50:
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
    # rhythm_detector_v2 lives at the app root (backend/), so it ships with the
    # deploy and is importable directly. rhythm_detector is a thin re-export shim.
    from rhythm_detector_v2 import RhythmDetector, RhythmConfig

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
