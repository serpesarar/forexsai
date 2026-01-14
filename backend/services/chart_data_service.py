from __future__ import annotations

from datetime import datetime, timedelta
import math
import random
from typing import List

import httpx
import numpy as np

from config import settings
from models.chart import ChartCandle, SupportResistanceLevel

_TIMEFRAME_MINUTES = {
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}


async def fetch_ohlcv_data(symbol: str, timeframe: str, limit: int) -> List[ChartCandle]:
    if not settings.eodhd_api_key:
        return _generate_mock_candles(symbol, timeframe, limit)

    url = f"https://eodhistoricaldata.com/api/intraday/{symbol}"
    params = {
        "api_token": settings.eodhd_api_key,
        "interval": timeframe,
        "fmt": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return _generate_mock_candles(symbol, timeframe, limit)

    if not isinstance(payload, list):
        return _generate_mock_candles(symbol, timeframe, limit)

    candles: List[ChartCandle] = []
    for item in payload[-limit:]:
        timestamp = _parse_timestamp(item.get("datetime") or item.get("date"))
        candles.append(
            ChartCandle(
                timestamp=timestamp,
                open=float(item.get("open", 0.0)),
                high=float(item.get("high", 0.0)),
                low=float(item.get("low", 0.0)),
                close=float(item.get("close", 0.0)),
                volume=int(item.get("volume") or 0),
            )
        )

    return candles


def build_support_resistance(candles: List[ChartCandle]) -> List[SupportResistanceLevel]:
    if not candles:
        return []

    lows = np.array([candle.low for candle in candles])
    highs = np.array([candle.high for candle in candles])
    support_levels = np.quantile(lows, [0.1, 0.25])
    resistance_levels = np.quantile(highs, [0.75, 0.9])

    levels = [
        SupportResistanceLevel(type="support", price=float(level), label="Support")
        for level in support_levels
    ] + [
        SupportResistanceLevel(type="resistance", price=float(level), label="Resistance")
        for level in resistance_levels
    ]

    return levels


def _parse_timestamp(value: str | None) -> int:
    if not value:
        return int(datetime.utcnow().timestamp() * 1000)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dt = datetime.utcnow()
    return int(dt.timestamp() * 1000)


def _generate_mock_candles(symbol: str, timeframe: str, limit: int) -> List[ChartCandle]:
    minutes = _TIMEFRAME_MINUTES.get(timeframe, 5)
    now = datetime.utcnow().replace(second=0, microsecond=0)
    randomizer = random.Random(hash((symbol, timeframe)) & 0xFFFFFFFF)
    base_price = 21500.0 if "NDX" in symbol else 2000.0
    candles: List[ChartCandle] = []
    for idx in range(limit):
        timestamp = now - timedelta(minutes=(limit - idx) * minutes)
        angle = idx / 15.0
        drift = math.sin(angle) * 15
        noise = randomizer.uniform(-8, 8)
        open_price = base_price + drift + noise
        close_price = open_price + randomizer.uniform(-5, 5)
        high_price = max(open_price, close_price) + randomizer.uniform(0, 6)
        low_price = min(open_price, close_price) - randomizer.uniform(0, 6)
        volume = int(1200 + randomizer.uniform(-200, 200))
        candles.append(
            ChartCandle(
                timestamp=int(timestamp.timestamp() * 1000),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )
        )
    return candles
