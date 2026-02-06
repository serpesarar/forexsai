"""
Market Data Service
Provides unified OHLCV data access for panel analysis (EMEL/PULSE).
Wraps data_fetcher functions with consistent interface.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from services.data_fetcher import fetch_ohlc_data, fetch_intraday_candles, fetch_eod_candles

logger = logging.getLogger(__name__)


# Timeframe mapping for API calls
TIMEFRAME_MAP = {
    # Intraday
    "M1": ("1m", 1),
    "M5": ("5m", 5),
    "M15": ("15m", 15),
    "M30": ("30m", 30),
    "1M": ("1m", 1),
    "5M": ("5m", 5),
    "15M": ("15m", 15),
    "30M": ("30m", 30),
    # Hourly
    "H1": ("1h", 60),
    "1H": ("1h", 60),
    "H4": ("4h", 240),
    "4H": ("4h", 240),
    # Daily
    "D1": ("1d", 1440),
    "1D": ("1d", 1440),
}


async def get_ohlcv_data(
    symbol: str,
    timeframe: str = "1H",
    limit: int = 250
) -> Optional[List[Dict[str, Any]]]:
    """
    Get OHLCV data for any timeframe.
    
    Args:
        symbol: Trading symbol (e.g., "NDX.INDX", "XAUUSD")
        timeframe: M1, M5, M15, M30, H1, H4, D1 (case insensitive)
        limit: Number of candles to fetch
    
    Returns:
        List of dicts with keys: open, high, low, close, volume
        Or None if data fetch fails
    """
    try:
        tf_upper = timeframe.upper()
        
        # Get the normalized timeframe
        if tf_upper in TIMEFRAME_MAP:
            normalized_tf, _ = TIMEFRAME_MAP[tf_upper]
        else:
            # Default to 1h if unknown
            normalized_tf = "1h"
            logger.warning(f"Unknown timeframe {timeframe}, defaulting to 1h")
        
        # Fetch data using the existing data_fetcher
        candles = await fetch_ohlc_data(symbol, normalized_tf, limit)
        
        if not candles:
            logger.warning(f"No OHLCV data returned for {symbol} {timeframe}")
            return None
        
        # Ensure consistent format
        result = []
        for c in candles:
            result.append({
                "open": float(c.get("open", 0)),
                "high": float(c.get("high", 0)),
                "low": float(c.get("low", 0)),
                "close": float(c.get("close", 0)),
                "volume": float(c.get("volume", 0)),
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching OHLCV data for {symbol} {timeframe}: {e}")
        return None


async def get_latest_candle(symbol: str, timeframe: str = "1H") -> Optional[Dict[str, Any]]:
    """Get only the latest candle for quick checks."""
    data = await get_ohlcv_data(symbol, timeframe, limit=1)
    return data[0] if data else None
