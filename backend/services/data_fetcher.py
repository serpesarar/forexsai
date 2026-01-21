from __future__ import annotations

from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Optional

import httpx

from config import settings


_price_cache: dict[str, tuple[float, float]] = {}  # symbol -> (ts_epoch, price)
_eod_cache: dict[str, tuple[float, list[dict]]] = {}  # symbol -> (ts_epoch, rows)
_cache_lock = Lock()


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
    - Primary: EODHD REST real-time (more reliable than websocket in local dev)
    - For XAU: fallback to goldprice.org when EODHD returns NA
    """
    if not settings.eodhd_api_key:
        return None

    key = _normalize_eodhd_symbol(symbol)
    now_ts = datetime.utcnow().timestamp()
    with _cache_lock:
        cached = _price_cache.get(key)
        if cached and now_ts - cached[0] < 30:  # 30s TTL
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
    
    # Map interval to EODHD format
    interval_map = {"1m": "1m", "5m": "5m", "15m": "5m", "1h": "1h"}
    eodhd_interval = interval_map.get(interval, "5m")
    
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
            
            return cleaned[-limit:]
    except Exception:
        return []


def _resample_to_30m(candles_5m: list[dict]) -> list[dict]:
    """
    Resample 5-minute candles to 30-minute candles.
    Groups every 6 consecutive 5m candles into one 30m candle.
    """
    if not candles_5m or len(candles_5m) < 6:
        return candles_5m
    
    result = []
    for i in range(0, len(candles_5m) - 5, 6):
        group = candles_5m[i:i+6]
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
    """
    # Fetch 6x more 5m candles to get enough 30m candles
    candles_5m = await fetch_intraday_candles(symbol, interval="5m", limit=limit * 6)
    
    if not candles_5m:
        return []
    
    candles_30m = _resample_to_30m(candles_5m)
    return candles_30m[-limit:]


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
        if cached and now_ts - cached[0] < 600:  # 10m TTL
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
