"""Data Fetcher - ALL reads go through DataHub (0 direct EODHD calls).

Every function here reads from the in-memory DataHub cache.
DataHub is the ONLY component that talks to EODHD API.
This eliminates duplicate API calls from 20+ services.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def fetch_latest_price(symbol: str) -> Optional[float]:
    """Get latest price from DataHub (0 API calls)."""
    try:
        from services.data_hub import get_price
        return get_price(symbol)
    except Exception:
        return None


async def fetch_intraday_candles(symbol: str, interval: str = "5m", limit: int = 300) -> list[dict]:
    """Get intraday candles from DataHub (0 API calls)."""
    try:
        from services.data_hub import get_candles
        return get_candles(symbol, interval, limit)
    except Exception:
        return []


async def fetch_30m_candles(symbol: str, limit: int = 300) -> list[dict]:
    """Get 30m candles from DataHub (0 API calls). DataHub resamples from 5m."""
    try:
        from services.data_hub import get_candles
        return get_candles(symbol, "30m", limit)
    except Exception:
        return []


async def fetch_ohlc_data(symbol: str, timeframe: str = "1h", limit: int = 50) -> list[dict]:
    """Get OHLC data for any timeframe from DataHub (0 API calls)."""
    try:
        from services.data_hub import get_candles
        return get_candles(symbol, timeframe, limit)
    except Exception:
        return []


async def fetch_eod_candles(symbol: str, limit: int = 300) -> list[dict]:
    """Get EOD candles from DataHub (0 API calls)."""
    try:
        from services.data_hub import get_candles
        return get_candles(symbol, "eod", limit)
    except Exception:
        return []
