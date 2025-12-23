from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass
class Candle:
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class OrderBlock:
    index: int
    type: str
    zone_low: float
    zone_high: float
    score: float
    displacement: float
    has_choch: bool
    has_bos: bool
    has_fvg: bool
    fib_level: float
    volume_ratio: float
    test_count: int
    is_valid: bool


@dataclass
class OrderBlockSignal:
    order_block_index: int
    has_signal: bool
    entry_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confidence: float


@dataclass
class OrderBlockConfig:
    fractal_period: int = 2
    min_displacement_atr: float = 1.0
    min_score: float = 50.0
    zone_type: str = "wick"
    max_tests: int = 2


class OrderBlockDetector:
    """Detect order blocks and entry signals using simplified SMC logic."""

    def __init__(self, config: OrderBlockConfig | None = None) -> None:
        self.config = config or OrderBlockConfig()

    def detect(self, candles: List[Candle]) -> List[OrderBlock]:
        if len(candles) < 50:
            return []
        swings_high, swings_low = self._swings(candles)
        atr = self._atr(candles, period=14)
        order_blocks: List[OrderBlock] = []
        for idx in sorted(swings_high + swings_low):
            candle = candles[idx]
            is_bullish = idx in swings_low
            zone_low, zone_high = self._zone_from_candle(candle, is_bullish)
            displacement = self._displacement(candles, idx, atr)
            has_choch = displacement >= self.config.min_displacement_atr
            has_bos = has_choch and self._bos(candles, idx, is_bullish)
            has_fvg = self._fvg(candles, idx)
            fib_level = 0.618 if idx % 2 == 0 else 0.786
            volume_ratio = self._volume_ratio(candles, idx)
            test_count = self._test_count(candles, zone_low, zone_high, idx)
            score = self._score(displacement, has_choch, has_bos, has_fvg, volume_ratio)
            is_valid = score >= self.config.min_score and test_count <= self.config.max_tests
            order_blocks.append(
                OrderBlock(
                    index=idx,
                    type="bullish" if is_bullish else "bearish",
                    zone_low=zone_low,
                    zone_high=zone_high,
                    score=score,
                    displacement=displacement,
                    has_choch=has_choch,
                    has_bos=has_bos,
                    has_fvg=has_fvg,
                    fib_level=fib_level,
                    volume_ratio=volume_ratio,
                    test_count=test_count,
                    is_valid=is_valid,
                )
            )
        return order_blocks

    def detect_entry(self, candles: List[Candle], order_block: OrderBlock) -> Optional[OrderBlockSignal]:
        if not candles:
            return None
        current = candles[-1].close
        inside = order_block.zone_low <= current <= order_block.zone_high
        if not inside:
            return None
        entry_type = "rejection" if order_block.type == "bearish" else "touch"
        stop_loss = order_block.zone_high if order_block.type == "bearish" else order_block.zone_low
        take_profit = current - (order_block.zone_high - order_block.zone_low) * 2
        if order_block.type == "bullish":
            take_profit = current + (order_block.zone_high - order_block.zone_low) * 2
        risk = abs(current - stop_loss) + 1e-6
        reward = abs(take_profit - current)
        risk_reward = reward / risk
        confidence = min(0.95, 0.5 + order_block.score / 200)
        return OrderBlockSignal(
            order_block_index=order_block.index,
            has_signal=True,
            entry_type=entry_type,
            entry_price=current,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward=risk_reward,
            confidence=confidence,
        )

    def _swings(self, candles: List[Candle]) -> tuple[List[int], List[int]]:
        highs = np.array([c.high for c in candles])
        lows = np.array([c.low for c in candles])
        period = self.config.fractal_period
        swings_high = []
        swings_low = []
        for i in range(period, len(candles) - period):
            if highs[i] == np.max(highs[i - period : i + period + 1]):
                swings_high.append(i)
            if lows[i] == np.min(lows[i - period : i + period + 1]):
                swings_low.append(i)
        return swings_high, swings_low

    def _zone_from_candle(self, candle: Candle, bullish: bool) -> tuple[float, float]:
        if self.config.zone_type == "body":
            low = min(candle.open, candle.close)
            high = max(candle.open, candle.close)
        else:
            low = candle.low
            high = candle.high
        return (low, high) if bullish else (low, high)

    def _atr(self, candles: List[Candle], period: int) -> float:
        if len(candles) < period + 1:
            return 0.0
        ranges = []
        for i in range(1, len(candles)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i - 1].close
            ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
        return float(np.mean(ranges[-period:]))

    def _displacement(self, candles: List[Candle], index: int, atr: float) -> float:
        if atr <= 0:
            return 0.0
        start = max(0, index - 3)
        end = min(len(candles), index + 4)
        segment = candles[start:end]
        move = max(c.high for c in segment) - min(c.low for c in segment)
        return float(move / atr)

    def _bos(self, candles: List[Candle], index: int, bullish: bool) -> bool:
        lookback = candles[max(0, index - 10) : index]
        if not lookback:
            return False
        highs = [c.high for c in lookback]
        lows = [c.low for c in lookback]
        if bullish:
            return candles[index].close > max(highs)
        return candles[index].close < min(lows)

    def _fvg(self, candles: List[Candle], index: int) -> bool:
        if index < 2:
            return False
        return candles[index - 2].high < candles[index].low or candles[index - 2].low > candles[index].high

    def _volume_ratio(self, candles: List[Candle], index: int) -> float:
        volumes = np.array([c.volume for c in candles])
        avg = np.mean(volumes[max(0, index - 20) : index + 1])
        return float(volumes[index] / avg) if avg > 0 else 1.0

    def _test_count(self, candles: List[Candle], zone_low: float, zone_high: float, index: int) -> int:
        count = 0
        for candle in candles[index + 1 :]:
            if zone_low <= candle.low <= zone_high or zone_low <= candle.high <= zone_high:
                count += 1
        return count

    def _score(self, displacement: float, has_choch: bool, has_bos: bool, has_fvg: bool, volume_ratio: float) -> float:
        score = 40.0
        score += min(30.0, displacement * 10.0)
        score += 10.0 if has_choch else 0.0
        score += 10.0 if has_bos else 0.0
        score += 5.0 if has_fvg else 0.0
        score += min(5.0, (volume_ratio - 1.0) * 5.0)
        return float(max(0.0, min(100.0, score)))
