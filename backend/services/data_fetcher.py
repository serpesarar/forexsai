from __future__ import annotations

from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Optional

import httpx

from config import settings
from services.api_cache import api_cache, APICache


_price_cache: dict[str, tuple[float, float]] = {}  # symbol -> (ts_epoch, price)
_eod_cache: dict[str, tuple[float, list[dict]]] = {}  # symbol -> (ts_epoch, rows)
_intraday_cache: dict[str, tuple[float, list[dict]]] = {}  # symbol:interval -> (ts, rows)
_cache_lock = Lock()

# Cache TTLs optimized for 100K daily API call limit
# Each intraday/real-time request = 5 API calls on EODHD
PRICE_TTL = 60       # 60s - real-time price (1 API call each)
INTRADAY_TTL = 300   # 5 min - intraday candles (5 API calls each)
EOD_TTL = 1800       # 30 min - daily candles (5 API calls each)


def _normalize_eodhd_symbol(symbol: str) -> str:
    s = (symbol or "").strip()
    if not s:
        return s
    if "." in s:
        return s
    if s.upper() == "XAUUSD":
        return "XAUUSD.FOREX"
    if len(s) == 6 and s.isalnum():
        return f"{s}.FOREX"
    return s


def _extract_price(payload: Any) -> Optional[float]:
    if payload is None:
        return None
    if isinstance(payload, list) and payload:
        return _extract_price(payload[0])
    if not isinstance(payload, dict):
        return None
    for key in ("close", "price", "last", "value", "previousClose"):
        if key in payload and payload[key] is not None:
            try:
                return float(payload[key])
            except (TypeError, ValueError):
                continue
    return None


async def fetch_latest_price(symbol: str) -> Optional[float]:
    """
    Live price fetch.
    Primary: DataHub (updated every 5s, 0 API calls)
    Fallback: Direct EODHD API (only during startup before DataHub populates)
    """
    # Try DataHub first (0 API calls)
    try:
        from services.data_hub import get_price
        hub_price = get_price(symbol)
        if hub_price is not None:
            return hub_price
    except ImportError:
        pass
    
    if not settings.eodhd_api_key:
        return None

    key = _normalize_eodhd_symbol(symbol)
    now_ts = datetime.utcnow().timestamp()
    with _cache_lock:
        cached = _price_cache.get(key)
        if cached and now_ts - cached[0] < PRICE_TTL:
            return cached[1]

    is_xau = (symbol or "").upper().startswith("XAU")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            eod_symbol = _normalize_eodhd_symbol(symbol)
            url = f"https://eodhistoricaldata.com/api/real-time/{eod_symbol}"
            resp = await client.get(url, params={"api_token": settings.eodhd_api_key, "fmt": "json"})
            # Quota exceeded -> serve stale cache if available
            if resp.status_code == 402:
                with _cache_lock:
                    cached = _price_cache.get(key)
                    return cached[1] if cached else None
            resp.raise_for_status()
            price = _extract_price(resp.json())
            if price is not None:
                with _cache_lock:
                    _price_cache[key] = (now_ts, float(price))
                return price

            if is_xau:
                gp = await client.get("https://data-asg.goldprice.org/dbXRates/USD")
                gp.raise_for_status()
                gp_payload = gp.json()
                items = gp_payload.get("items") if isinstance(gp_payload, dict) else None
                if isinstance(items, list) and items:
                    xau_price = items[0].get("xauPrice")
                    if xau_price is not None:
                        with _cache_lock:
                            _price_cache[key] = (now_ts, float(xau_price))
                        return float(xau_price)
            return None
    except Exception:
        # Serve stale cache on transient failures
        with _cache_lock:
            cached = _price_cache.get(key)
            return cached[1] if cached else None


async def fetch_intraday_candles(symbol: str, interval: str = "5m", limit: int = 300) -> list[dict]:
    """
    Fetch intraday OHLC candles from EODHD (requires paid plan).
    
    Args:
        symbol: Trading symbol
        interval: Time interval - "1m", "5m", or "1h"
        limit: Number of candles to return
    
    Returns list of dicts with keys: timestamp, open, high, low, close, volume
    """
    if not settings.eodhd_api_key:
        return []
    
    eod_symbol = _normalize_eodhd_symbol(symbol)
    cache_key = f"{eod_symbol}:{interval}"
    now_ts = datetime.utcnow().timestamp()
    
    # Check cache first (5 min TTL - each call costs 5 API calls)
    with _cache_lock:
        cached = _intraday_cache.get(cache_key)
        if cached and now_ts - cached[0] < INTRADAY_TTL:
            return cached[1][-limit:]
    
    # Map interval to EODHD format (EODHD only supports: 1m, 5m, 1h)
    interval_lower = interval.lower()
    interval_map = {
        "1m": "1m", "m1": "1m",
        "5m": "5m", "m5": "5m",
        "15m": "5m", "m15": "5m",
        "30m": "5m", "m30": "5m",
        "1h": "1h", "h1": "1h", "60m": "1h",
        "4h": "1h", "h4": "1h",
    }
    eodhd_interval = interval_map.get(interval_lower, "5m")
    
    url = f"https://eodhistoricaldata.com/api/intraday/{eod_symbol}"
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                url,
                params={
                    "api_token": settings.eodhd_api_key,
                    "fmt": "json",
                    "interval": eodhd_interval,
                },
            )
            if resp.status_code == 402:
                return []
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list):
                return []
            
            cleaned = []
            for row in data:
                if not isinstance(row, dict):
                    continue
                if row.get("close") is None:
                    continue
                # Convert datetime to timestamp
                dt_str = row.get("datetime", "")
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    ts = int(dt.timestamp() * 1000)
                except:
                    ts = 0
                
                cleaned.append({
                    "timestamp": ts,
                    "date": dt_str,
                    "open": float(row.get("open") or 0.0),
                    "high": float(row.get("high") or 0.0),
                    "low": float(row.get("low") or 0.0),
                    "close": float(row.get("close") or 0.0),
                    "volume": float(row.get("volume") or 0.0),
                })
            
            # Cache the result
            with _cache_lock:
                _intraday_cache[cache_key] = (now_ts, cleaned)
            
            return cleaned[-limit:]
    except Exception:
        # Return stale cache on error
        with _cache_lock:
            cached = _intraday_cache.get(cache_key)
            return cached[1][-limit:] if cached else []


def _resample_to_30m(candles_1m: list[dict]) -> list[dict]:
    """
    Resample 1-minute candles to 30-minute candles.
    Groups every 30 consecutive 1m candles into one 30m candle.
    """
    if not candles_1m or len(candles_1m) < 30:
        return []
    
    result = []
    for i in range(0, len(candles_1m) - 29, 30):
        group = candles_1m[i:i+30]
        candle_30m = {
            "timestamp": group[0]["timestamp"],
            "date": group[0].get("date", ""),
            "open": group[0]["open"],
            "high": max(c["high"] for c in group),
            "low": min(c["low"] for c in group),
            "close": group[-1]["close"],
            "volume": sum(c.get("volume", 0) for c in group),
        }
        result.append(candle_30m)
    
    return result


async def fetch_30m_candles(symbol: str, limit: int = 300) -> list[dict]:
    """
    Fetch 30-minute candles by resampling 5-minute data from EODHD.
    Model was trained on M30 data, so this is the correct timeframe.
    Uses 5m data (EODHD supports 5m) and resamples 6×5m = 30m.
    Much more efficient than using 1m data (saves ~5x API calls).
    """
    # Use 5m interval and resample to 30m (6 × 5m = 30m)
    candles_5m = await fetch_intraday_candles(symbol, interval="5m", limit=limit * 7)
    
    if not candles_5m:
        return []
    
    candles_30m = _resample_candles(candles_5m, 6)
    return candles_30m[-limit:]


async def fetch_ohlc_data(symbol: str, timeframe: str = "1h", limit: int = 50) -> list[dict]:
    """
    Fetch OHLC data for any timeframe.
    Primary: DataHub (pre-fetched & resampled, 0 API calls)
    Fallback: Direct EODHD API (only during startup)
    
    Args:
        symbol: Trading symbol
        timeframe: "5m", "15m", "30m", "1h", "4h", "1d"
        limit: Number of candles to return
    
    Returns list of dicts with keys: open, high, low, close, volume
    """
    # Try DataHub first (0 API calls)
    try:
        from services.data_hub import get_candles
        hub_candles = get_candles(symbol, timeframe, limit)
        if hub_candles:
            return hub_candles
    except ImportError:
        pass
    
    # Fallback to direct API (only during startup before DataHub populates)
    tf_lower = timeframe.lower()
    
    # For daily, use EOD data
    if tf_lower in ["1d", "d", "daily"]:
        return await fetch_eod_candles(symbol, limit)
    
    # For M1, fetch 1m directly
    if tf_lower in ["1m", "m1"]:
        return await fetch_intraday_candles(symbol, interval="1m", limit=limit)
    
    # For M5, fetch 5m directly
    if tf_lower in ["5m", "m5"]:
        return await fetch_intraday_candles(symbol, interval="5m", limit=limit)
    
    # For 15m, fetch 5m and resample to 15m (EODHD doesn't support 15m)
    if tf_lower in ["15m", "m15"]:
        candles_5m = await fetch_intraday_candles(symbol, interval="5m", limit=limit * 4)
        if not candles_5m:
            return []
        return _resample_candles(candles_5m, 3)[-limit:]  # 5m x 3 = 15m
    
    # For 30m, resample from 5m
    if tf_lower in ["30m", "m30"]:
        candles_5m = await fetch_intraday_candles(symbol, interval="5m", limit=limit * 7)
        if not candles_5m:
            return []
        return _resample_candles(candles_5m, 6)[-limit:]  # 5m x 6 = 30m
    
    # For 1H, try 1h directly first, fallback to resample
    if tf_lower in ["1h", "h1", "60m"]:
        candles_1h = await fetch_intraday_candles(symbol, interval="1h", limit=limit)
        if candles_1h:
            return candles_1h
        # Fallback: resample from 5m
        candles_5m = await fetch_intraday_candles(symbol, interval="5m", limit=limit * 13)
        if not candles_5m:
            return []
        return _resample_candles(candles_5m, 12)[-limit:]  # 5m x 12 = 1h
    
    # For 4H, resample from 1h
    if tf_lower in ["4h", "h4", "240m"]:
        candles_1h = await fetch_intraday_candles(symbol, interval="1h", limit=limit * 5)
        if not candles_1h:
            return []
        return _resample_candles(candles_1h, 4)[-limit:]  # 1h x 4 = 4h
    
    # Default: return 1h data
    return await fetch_intraday_candles(symbol, interval="1h", limit=limit)



def _resample_candles(candles: list[dict], period: int) -> list[dict]:
    """
    Resample candles to a larger timeframe.
    
    Args:
        candles: List of OHLC candles
        period: Number of candles to group
    
    Returns resampled candles
    """
    if not candles or len(candles) < period:
        return []
    
    result = []
    for i in range(0, len(candles) - period + 1, period):
        group = candles[i:i+period]
        if not group:
            continue
        resampled = {
            "timestamp": group[0].get("timestamp", 0),
            "date": group[0].get("date", ""),
            "open": group[0].get("open", 0),
            "high": max(c.get("high", 0) for c in group),
            "low": min(c.get("low", float('inf')) for c in group),
            "close": group[-1].get("close", 0),
            "volume": sum(c.get("volume", 0) for c in group),
        }
        result.append(resampled)
    
    return result


async def fetch_eod_candles(symbol: str, limit: int = 300) -> list[dict]:
    """
    Fetch end-of-day OHLC candles from EODHD (available on free plans).
    Returns list of dicts with keys: date, open, high, low, close, volume
    """
    if not settings.eodhd_api_key:
        return []

    eod_symbol = _normalize_eodhd_symbol(symbol)
    now_ts = datetime.utcnow().timestamp()
    with _cache_lock:
        cached = _eod_cache.get(eod_symbol)
        if cached and now_ts - cached[0] < EOD_TTL:  # 30m TTL
            return cached[1][-limit:]
    # Pull a bit more than needed in case of holidays/weekends; then slice.
    from_date = (datetime.utcnow() - timedelta(days=max(30, limit * 2))).date().isoformat()
    url = f"https://eodhistoricaldata.com/api/eod/{eod_symbol}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                url,
                params={
                    "api_token": settings.eodhd_api_key,
                    "fmt": "json",
                    "period": "d",
                    "from": from_date,
                },
            )
            if resp.status_code == 402:
                with _cache_lock:
                    cached = _eod_cache.get(eod_symbol)
                    return cached[1][-limit:] if cached else []
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list):
                return []
            # Keep only required keys and last N
            cleaned = []
            for row in data:
                if not isinstance(row, dict):
                    continue
                if row.get("close") is None:
                    continue
                cleaned.append(
                    {
                        "date": row.get("date"),
                        "open": float(row.get("open") or 0.0),
                        "high": float(row.get("high") or 0.0),
                        "low": float(row.get("low") or 0.0),
                        "close": float(row.get("close") or 0.0),
                        "volume": float(row.get("volume") or 0.0),
                    }
                )
            with _cache_lock:
                _eod_cache[eod_symbol] = (now_ts, cleaned)
            return cleaned[-limit:]
    except Exception:
        with _cache_lock:
            cached = _eod_cache.get(eod_symbol)
            return cached[1][-limit:] if cached else []
