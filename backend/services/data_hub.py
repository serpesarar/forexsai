"""
DataHub - Centralized Market Data Store with Persistent Cache
=============================================================
Single source of truth for all market data in the system.

Architecture (v2 - Persistent Cache):
  Startup:  Supabase (candle_cache) → DataHub (in-memory)
  Running:  EODHD API (delta only) → DataHub (in-memory) → persist to Supabase
  Restart:  Load from Supabase (0 API calls) → fetch only new candles

Fetch schedule (after initial seed):
  - Real-time price: every 30s per symbol (1 API call each)
  - 5m candles: every 5min, DELTA only (24 candles = ~2h)
  - 1h candles: every 5min, DELTA only (6 candles = ~6h)
  - EOD candles: every 30min, DELTA only (5 candles = ~5 days)

Derived (computed, 0 API calls):
  - 15m candles: resampled from 5m (3x)
  - 30m candles: resampled from 5m (6x)
  - 4h candles: resampled from 1h (4x)

Daily API budget (after first seed):
  Price: 3 symbols × 1 call × 2/min × 60min × 24h = 8,640 calls
  5m:    3 symbols × 1 call × 12/hour × 24h = 864 calls (delta=24 candles)
  1h:    3 symbols × 1 call × 12/hour × 24h = 864 calls (delta=6 candles)
  EOD:   3 symbols × 1 call × 2/hour × 24h = 144 calls (delta=5 candles)
  Macro: 5 symbols × 1 call × 12/hour × 24h = 1,440 calls
  TOTAL: ~11,950 / 100,000 limit (~12% usage)

  First-time seed (one-time): ~30 extra calls for full history
  Subsequent days: only delta → 93% reduction vs original design
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

import httpx
import numpy as np

from config import settings

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# TRACKED SYMBOLS
# ═══════════════════════════════════════════════════════════════
TRACKED_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]

# ═══════════════════════════════════════════════════════════════
# FETCH INTERVALS (seconds)
# ═══════════════════════════════════════════════════════════════
PRICE_INTERVAL = 5        # Fetch live price every 5 seconds (WS fallback since EODHD premium missing)
CANDLE_5M_INTERVAL = 300  # Fetch 5m candles every 5 minutes
CANDLE_30M_INTERVAL = 300 # Fetch 30m candles every 5 minutes (XAUUSD only)
CANDLE_1H_INTERVAL = 300  # Fetch 1h candles every 5 minutes
CANDLE_EOD_INTERVAL = 1800  # Fetch EOD candles every 30 minutes
MACRO_INTERVAL = 300      # Fetch macro (DXY, VIX, USDTRY) every 5 minutes

# Macro symbols
MACRO_SYMBOLS = {
    "dxy": "DXY.INDX",
    "vix": "VIX.INDX",
    "usdtry": "USDTRY",
    "eurusd": "EURUSD.FOREX",
    "vdax": "V1X.INDX",
}

# ═══════════════════════════════════════════════════════════════
# IN-MEMORY DATA STORE
# ═══════════════════════════════════════════════════════════════
_lock = Lock()

# Raw data from EODHD (fetched via API)
_prices: Dict[str, Dict[str, Any]] = {}        # symbol -> {price, timestamp}
_candles_5m: Dict[str, Dict[str, Any]] = {}     # symbol -> {candles, timestamp}
_candles_1h: Dict[str, Dict[str, Any]] = {}     # symbol -> {candles, timestamp}
_candles_eod: Dict[str, Dict[str, Any]] = {}    # symbol -> {candles, timestamp}

# Derived data (computed from raw, 0 API calls)
_candles_15m: Dict[str, Dict[str, Any]] = {}    # symbol -> {candles, timestamp}
_candles_30m: Dict[str, Dict[str, Any]] = {}    # symbol -> {candles, timestamp}
_candles_4h: Dict[str, Dict[str, Any]] = {}     # symbol -> {candles, timestamp}

# Macro data
_macro_data: Dict[str, Dict[str, Any]] = {}     # key -> {symbol, price, timestamp}

# Last fetch timestamps
_last_fetch: Dict[str, float] = {}

# Hub running flag
_hub_running = False


# ═══════════════════════════════════════════════════════════════
# SYMBOL NORMALIZATION
# ═══════════════════════════════════════════════════════════════
def _normalize_symbol(symbol: str) -> str:
    s = (symbol or "").strip()
    if not s:
        return s
    # Explicit commodity mappings - EODHD uses specific formats
    if s.upper() in ("WTI", "USOIL.FOREX", "CL"):
        return "CL"
    if s.upper() == "BRENT":
        return "BZ"
    if s.upper() == "DXY":
        return "DX-Y.NYB"
    if "." in s:
        # Keep existing dotted symbols but handle special cases
        if s.upper() == "USOIL.FOREX":
            return "CL"
        if s.upper() == "BZ.COMM":
            return "BZ"
        return s
    if s.upper() == "XAUUSD":
        return "XAUUSD.FOREX"
    if len(s) == 6 and s.isalnum():
        return f"{s}.FOREX"
    return s


# ═══════════════════════════════════════════════════════════════
# YAHOO FINANCE FALLBACK (Commodities/Forex bypassing EODHD)
# ═══════════════════════════════════════════════════════════════
def _is_us_market_open() -> bool:
    """Check if it's currently US Market Hours (09:30 - 16:00 EST/EDT, Mon-Fri)."""
    try:
        now_ny = datetime.now(zoneinfo.ZoneInfo("America/New_York"))
    except Exception:
        now_ny = datetime.utcnow() - timedelta(hours=5)
    
    if now_ny.weekday() >= 5:
        return False
    # Use fractional hours (9.5 = 09:30 AM, 16.0 = 4:00 PM)
    time_val = now_ny.hour + now_ny.minute / 60.0
    return 9.5 <= time_val <= 16.0

def _filter_us_hours(candles: List[Dict]) -> List[Dict]:
    """Filter candles to only include US Market Hours (09:30 - 16:00 NY Time)."""
    filtered = []
    try:
        us_tz = zoneinfo.ZoneInfo("America/New_York")
    except Exception:
        return candles

    for c in candles:
        dt_us = datetime.fromtimestamp(c["timestamp"] / 1000.0, tz=us_tz)
        if dt_us.weekday() >= 5:
            continue
        time_val = dt_us.hour + dt_us.minute / 60.0
        if 9.5 <= time_val <= 16.0:
            filtered.append(c)
    return filtered

async def _fetch_yahoo_price(yahoo_symbol: str) -> Optional[float]:
    """Fetch live price from Yahoo Finance as a precise fallback.
    
    For commodities/forex (GC=F, CL=F): No US hours filter — they trade ~23h/day.
    For stock indices: US hours filter applies.
    """
    # Commodities and forex trade nearly 24h — no US hours restriction
    is_commodity = yahoo_symbol in ("GC=F", "CL=F", "SI=F", "HG=F")
    
    if not is_commodity and not _is_us_market_open():
        # Stock indices: use last valid US-hours candle
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval=5m&range=5d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    result = resp.json()['chart']['result'][0]
                    timestamps = result.get('timestamp', [])
                    quote = result.get('indicators', {}).get('quote', [{}])[0]
                    if timestamps and quote.get('close'):
                        candles = []
                        for i in range(len(timestamps)):
                            if quote['close'][i] is not None:
                                candles.append({
                                    "timestamp": timestamps[i] * 1000,
                                    "close": float(quote['close'][i])
                                })
                        valid_candles = _filter_us_hours(candles)
                        if valid_candles:
                            return valid_candles[-1]["close"]
        except Exception:
            pass
        return None  # Keeps previous data hub cache intact

    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval=1m&range=1d"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                meta = data['chart']['result'][0]['meta']
                return float(meta['regularMarketPrice'])
    except Exception as e:
        logger.error(f"Yahoo fetch error for {yahoo_symbol}: {e}")
    return None

async def _fetch_yahoo_candles(yahoo_symbol: str, interval: str, limit: int) -> List[Dict]:
    """Fetch history from Yahoo Finance.
    
    For commodities/forex (GC=F, CL=F): No US hours filter — they trade ~23h/day.
    For stock indices: US hours filter applies to intraday data.
    """
    # Commodities and forex trade nearly 24h — no US hours restriction
    is_commodity = yahoo_symbol in ("GC=F", "CL=F", "SI=F", "HG=F")
    
    yf_interval = interval
    if interval == "1h": yf_interval = "60m"
    elif interval in ("1d", "eod"): yf_interval = "1d"
    
    yf_range = "5d"
    if yf_interval == "60m": yf_range = "1mo"
    elif yf_interval == "1d": yf_range = "2y"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval={yf_interval}&range={yf_range}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                result = resp.json()['chart']['result'][0]
                timestamps = result.get('timestamp', [])
                quote = result['indicators']['quote'][0]
                
                candles = []
                for i in range(len(timestamps)):
                    if quote['open'][i] is not None:
                        # Convert to milliseconds for standard Datahub format
                        ts_ms = timestamps[i] * 1000
                        dt_str = datetime.fromtimestamp(timestamps[i]).isoformat()
                        
                        candles.append({
                            "timestamp": ts_ms,
                            "date": dt_str,
                            "open": float(quote['open'][i]),
                            "high": float(quote['high'][i]),
                            "low": float(quote['low'][i]),
                            "close": float(quote['close'][i]),
                            "volume": float(quote.get('volume', [0])[i] or 0)
                        })
                
                # Filter out Asian/off-hours ONLY for stock indices, NOT for commodities/forex
                if not is_commodity and yf_interval in ("1m", "5m", "15m", "30m", "60m"):
                    candles = _filter_us_hours(candles)
                
                return candles[-limit:]
    except Exception as e:
        logger.error(f"Yahoo candle error for {yahoo_symbol}: {e}")
    return []


# ═══════════════════════════════════════════════════════════════
# EODHD API FETCHERS (only called by DataHub pump)
# ═══════════════════════════════════════════════════════════════
async def _fetch_price_from_api(symbol: str) -> Optional[float]:
    """Fetch real-time price. Intercepts Commodities for Yahoo, else EODHD."""
    eod_symbol = _normalize_symbol(symbol)
    
    # --- YAHOO FINANCE FALLBACK ---
    if eod_symbol == "CL": # USOil / WTI
        return await _fetch_yahoo_price("CL=F")
    if eod_symbol in ("XAUUSD.FOREX", "XAUUSD"): # Gold
        return await _fetch_yahoo_price("GC=F")

    if not settings.eodhd_api_key:
        return None
    eod_symbol = _normalize_symbol(symbol)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://eodhistoricaldata.com/api/real-time/{eod_symbol}",
                params={"api_token": settings.eodhd_api_key, "fmt": "json"},
            )
            if resp.status_code == 402:
                return None  # Quota exceeded
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and data:
                data = data[0]
            if isinstance(data, dict):
                # Prioritize real-time keys over 'close' which may be stale after-hours
                # 'last' and 'price' are more likely to be actual current quotes
                # Fallback chain: last → price → close → value → previousClose
                for key in ("last", "price", "close", "value"):
                    if key in data and data[key] is not None:
                        val = data[key]
                        # Skip "NA", "N/A", empty strings, or other non-numeric values
                        if isinstance(val, str):
                            val_stripped = val.strip().upper()
                            if val_stripped in ("NA", "N/A", "", "NULL", "NONE"):
                                continue
                        try:
                            return float(val)
                        except (TypeError, ValueError):
                            continue
                # Final fallback: previousClose (useful when market is closed)
                if "previousClose" in data and data["previousClose"] is not None:
                    val = data["previousClose"]
                    if isinstance(val, str):
                        val_stripped = val.strip().upper()
                        if val_stripped not in ("NA", "N/A", "", "NULL", "NONE"):
                            try:
                                return float(val)
                            except (TypeError, ValueError):
                                pass
                    else:
                        try:
                            return float(val)
                        except (TypeError, ValueError):
                            pass
    except Exception as e:
        logger.debug(f"Price fetch failed for {symbol}: {e}")
    return None


async def _fetch_candles_from_api(symbol: str, interval: str, limit: int = 500) -> List[Dict]:
    """Fetch intraday candles. Intercepts Commodities for Yahoo, else EODHD."""
    eod_symbol = _normalize_symbol(symbol)
    
    # --- YAHOO FINANCE FALLBACK ---
    if eod_symbol == "CL":
        return await _fetch_yahoo_candles("CL=F", interval, limit)
    if eod_symbol in ("XAUUSD.FOREX", "XAUUSD"):
        return await _fetch_yahoo_candles("GC=F", interval, limit)

    if not settings.eodhd_api_key:
        return []
    
    # Calculate how far back we need to go based on interval and limit
    # EODHD requires 'from' param for historical intraday data
    # Use CONSERVATIVE (stock market) estimates so we always fetch enough days
    import math
    candles_per_day = {"1m": 390, "5m": 78, "15m": 26, "30m": 13, "1h": 7}.get(interval, 78)
    trading_days_needed = math.ceil(limit / max(candles_per_day, 1))
    # Buffer for weekends/holidays (×2 to be safe)
    calendar_days = max(int(trading_days_needed * 2) + 7, 14)
    from_ts = int((datetime.utcnow() - timedelta(days=calendar_days)).timestamp())
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://eodhistoricaldata.com/api/intraday/{eod_symbol}",
                params={
                    "api_token": settings.eodhd_api_key,
                    "fmt": "json",
                    "interval": interval,
                    "from": from_ts,
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
                if not isinstance(row, dict) or row.get("close") is None:
                    continue
                dt_str = row.get("datetime", "")
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    ts = int(dt.timestamp() * 1000)
                except Exception:
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
            logger.info(f"[DataHub] Fetched {len(cleaned)} {interval} candles for {symbol} (requested {limit}, from {calendar_days}d ago)")
            return cleaned  # Return ALL candles — _merge_candles handles dedup & limit
    except Exception as e:
        logger.debug(f"Candle fetch failed for {symbol} {interval}: {e}")
    return []


async def _fetch_eod_from_api(symbol: str, limit: int = 300) -> List[Dict]:
    """Fetch EOD candles. Intercepts Commodities for Yahoo, else EODHD."""
    eod_symbol = _normalize_symbol(symbol)
    
    # --- YAHOO FINANCE FALLBACK ---
    if eod_symbol == "CL":
        return await _fetch_yahoo_candles("CL=F", "1d", limit)
    if eod_symbol in ("XAUUSD.FOREX", "XAUUSD"):
        return await _fetch_yahoo_candles("GC=F", "1d", limit)

    if not settings.eodhd_api_key:
        return []
    from_date = (datetime.utcnow() - timedelta(days=max(30, limit * 2))).date().isoformat()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://eodhistoricaldata.com/api/eod/{eod_symbol}",
                params={
                    "api_token": settings.eodhd_api_key,
                    "fmt": "json",
                    "period": "d",
                    "from": from_date,
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
                if not isinstance(row, dict) or row.get("close") is None:
                    continue
                cleaned.append({
                    "date": row.get("date"),
                    "open": float(row.get("open") or 0.0),
                    "high": float(row.get("high") or 0.0),
                    "low": float(row.get("low") or 0.0),
                    "close": float(row.get("close") or 0.0),
                    "volume": float(row.get("volume") or 0.0),
                })
            return cleaned[-limit:]
    except Exception as e:
        logger.debug(f"EOD fetch failed for {symbol}: {e}")
    return []


# ═══════════════════════════════════════════════════════════════
# RESAMPLE LOGIC (0 API calls - pure computation)
# ═══════════════════════════════════════════════════════════════
def _resample(candles: List[Dict], period: int) -> List[Dict]:
    """Resample candles to larger timeframe. E.g., 5m×3=15m, 5m×6=30m, 1h×4=4h."""
    if not candles or len(candles) < period:
        return []
    result = []
    for i in range(0, len(candles) - period + 1, period):
        group = candles[i:i + period]
        if not group:
            continue
        result.append({
            "timestamp": group[0].get("timestamp", 0),
            "date": group[0].get("date", ""),
            "open": group[0].get("open", 0),
            "high": max(c.get("high", 0) for c in group),
            "low": min(c.get("low", float("inf")) for c in group),
            "close": group[-1].get("close", 0),
            "volume": sum(c.get("volume", 0) for c in group),
        })
    return result


def _rebuild_derived(symbol: str):
    """Rebuild derived timeframes from raw data.
    
    NDX.INDX: 5m→15m, 5m→30m, 1h(fetched)→4h
    XAUUSD:   5m→15m, 30m(fetched)→1h→4h  (30m also from 5m if not fetched)
    """
    now = datetime.utcnow().timestamp()
    
    raw_5m = _candles_5m.get(symbol, {}).get("candles", [])
    if raw_5m:
        # 15m = 5m × 3 (always)
        _candles_15m[symbol] = {"candles": _resample(raw_5m, 3), "timestamp": now}
        
        # 30m: use directly-fetched 30m if available, otherwise derive from 5m
        if symbol not in _30M_DIRECT_SYMBOLS:
            _candles_30m[symbol] = {"candles": _resample(raw_5m, 6), "timestamp": now}
    
    # For symbols with direct 30m fetch: derive 1h and 4h from 30m
    if symbol in _30M_DIRECT_SYMBOLS:
        raw_30m = _candles_30m.get(symbol, {}).get("candles", [])
        if raw_30m:
            derived_1h = _resample(raw_30m, 2)  # 1h = 30m × 2
            if derived_1h:
                _candles_1h[symbol] = {"candles": derived_1h, "timestamp": now}
            derived_4h = _resample(raw_30m, 8)  # 4h = 30m × 8
            if derived_4h:
                _candles_4h[symbol] = {"candles": derived_4h, "timestamp": now}
    else:
        # NDX: 4h = 1h × 4
        raw_1h = _candles_1h.get(symbol, {}).get("candles", [])
        if raw_1h:
            _candles_4h[symbol] = {"candles": _resample(raw_1h, 4), "timestamp": now}


# ═══════════════════════════════════════════════════════════════
# DATA PUMP (background loop)
# ═══════════════════════════════════════════════════════════════
def _should_fetch(key: str, interval: float) -> bool:
    now = datetime.utcnow().timestamp()
    last = _last_fetch.get(key, 0)
    return (now - last) >= interval


def _mark_fetched(key: str):
    _last_fetch[key] = datetime.utcnow().timestamp()


# Track whether initial seed has been done (first fetch = full, subsequent = delta)
_initial_seed_done: Dict[str, bool] = {}

# Delta fetch limits (much smaller than full seed)
DELTA_LIMIT_5M = 24       # ~2 hours of 5m candles
DELTA_LIMIT_30M = 12      # ~6 hours of 30m candles
DELTA_LIMIT_1H = 6        # ~6 hours of 1h candles
DELTA_LIMIT_EOD = 5       # ~5 days of EOD candles

# Full seed limits — sized so EMA200 works on ALL derived timeframes:
#   5m:  1500 → 15m=500, 30m=250
#   30m: 1600 → 1h=800, 4h=200 (XAUUSD: 30m fetched directly)
#   1h:  800  → 4h=200 (NDX: fetched directly)
#   EOD: 365  → EMA200 with full year of data
FULL_SEED_LIMIT_5M = 1500   # ~5.2 days of 5m candles
FULL_SEED_LIMIT_30M = 1600  # ~54 days of 30m candles (XAUUSD max 1h limit capacity)
FULL_SEED_LIMIT_1H = 800    # ~114 days of 1h candles
FULL_SEED_LIMIT_EOD = 365   # ~1 year of daily candles

# EODHD interval support varies by symbol:
#   XAUUSD.FOREX: supports 1m, 15m, 30m (NOT 5m, 1h)
#   NDX.INDX:     supports 5m, 1h
#   GDAXI.INDX:   supports 5m, 1h (same as NDX)
# Strategy for XAUUSD: fetch 1m→5m, fetch 30m directly→1h/4h
# Strategy for DAX: same as NDX (5m fetched, 1h fetched, derive 15m/30m/4h)
_1M_ONLY_SYMBOLS = {"XAUUSD"}   # 5m = resample from 1m
_30M_DIRECT_SYMBOLS = {"XAUUSD"}  # 1h/4h = resample from 30m


_persist_timestamps: Dict[str, float] = {}   # "symbol:tf" → last persist epoch
_persist_counts: Dict[str, int] = {}         # "symbol:tf" → candle count at last persist
PERSIST_INTERVAL = 900                       # 15 minutes between Supabase writes


def _persist_async(symbol: str, timeframe: str, candles: List[Dict]):
    """Persist candles to Supabase — throttled to every 15 min & delta-only."""
    key = f"{symbol}:{timeframe}"
    now = time.time()

    # Throttle: skip if last persist was < 15 min ago
    last_ts = _persist_timestamps.get(key, 0)
    if now - last_ts < PERSIST_INTERVAL:
        return

    # Delta check: skip if candle count unchanged (same data)
    count = len(candles) if candles else 0
    if count == _persist_counts.get(key, -1) and count > 0:
        return

    try:
        from services.candle_cache_store import persist_candles
        persisted = persist_candles(symbol, timeframe, candles)
        _persist_timestamps[key] = now
        _persist_counts[key] = count
    except Exception as e:
        logger.debug(f"Persist failed for {symbol}/{timeframe}: {e}")


def _merge_candles(existing: List[Dict], new_candles: List[Dict], limit: int) -> List[Dict]:
    """Merge new candles into existing, deduplicate by timestamp, keep latest `limit`."""
    if not new_candles:
        return existing
    if not existing:
        return new_candles[-limit:]
    
    # Build a dict keyed by timestamp for dedup
    merged = {}
    for c in existing:
        key = c.get("timestamp") or c.get("date", "")
        if key:
            merged[key] = c
    for c in new_candles:
        key = c.get("timestamp") or c.get("date", "")
        if key:
            merged[key] = c  # New data overwrites old
    
    # Sort by timestamp ascending and trim
    result = sorted(merged.values(), key=lambda x: x.get("timestamp", 0) or 0)
    return result[-limit:]


async def _pump_cycle():
    """One pump cycle: fetch what's due, rebuild derived data."""
    now_ts = datetime.utcnow().timestamp()
    
    for symbol in TRACKED_SYMBOLS:
        seed_key = symbol
        is_seeded = _initial_seed_done.get(seed_key, False)
        
        # ── Price (every 30s) ──
        if _should_fetch(f"price:{symbol}", PRICE_INTERVAL):
            price = await _fetch_price_from_api(symbol)
            if price is not None:
                with _lock:
                    _prices[symbol] = {"price": price, "timestamp": now_ts}
                _mark_fetched(f"price:{symbol}")
                try:
                    from services.ws_manager import manager
                    await manager.broadcast(symbol, {
                        "type": "price_update",
                        "symbol": symbol,
                        "price": price,
                        "timestamp": now_ts
                    })
                except Exception as e:
                    logger.debug(f"[DataHub] Instant price broadcast failed for {symbol}: {e}")
        
        # ── 5m candles (every 5min) ──
        if _should_fetch(f"5m:{symbol}", CANDLE_5M_INTERVAL):
            is_seed = not is_seeded
            
            if symbol in _1M_ONLY_SYMBOLS:
                # XAUUSD.FOREX only supports 1m interval — fetch 1m, resample to 5m
                raw_limit = (FULL_SEED_LIMIT_5M * 5) if is_seed else (DELTA_LIMIT_5M * 5)
                raw_1m = await _fetch_candles_from_api(symbol, "1m", limit=raw_limit)
                candles = _resample(raw_1m, 5) if raw_1m else []
                logger.info(f"[DataHub] {symbol}: fetched {len(raw_1m)} 1m → resampled to {len(candles)} 5m candles")
            else:
                fetch_limit = FULL_SEED_LIMIT_5M if is_seed else DELTA_LIMIT_5M
                candles = await _fetch_candles_from_api(symbol, "5m", limit=fetch_limit)
            
            if candles:
                with _lock:
                    existing = (_candles_5m.get(symbol) or {}).get("candles", [])
                    merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_5M)
                    _candles_5m[symbol] = {"candles": merged, "timestamp": now_ts}
                    _rebuild_derived(symbol)
                _mark_fetched(f"5m:{symbol}")
                _persist_async(symbol, "5m", merged if is_seed else candles)
        
        # ── 30m candles (XAUUSD only — EODHD supports 30m directly) ──
        if symbol in _30M_DIRECT_SYMBOLS and _should_fetch(f"30m:{symbol}", CANDLE_30M_INTERVAL):
            is_seed = not is_seeded
            fetch_limit = FULL_SEED_LIMIT_30M if is_seed else DELTA_LIMIT_30M
            candles = await _fetch_candles_from_api(symbol, "30m", limit=fetch_limit)
            if candles:
                with _lock:
                    existing = (_candles_30m.get(symbol) or {}).get("candles", [])
                    merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_30M)
                    _candles_30m[symbol] = {"candles": merged, "timestamp": now_ts}
                    _rebuild_derived(symbol)  # This will derive 1h and 4h from 30m
                _mark_fetched(f"30m:{symbol}")
                _persist_async(symbol, "30m", merged if is_seed else candles)
                logger.info(f"[DataHub] {symbol}: fetched {len(candles)} 30m candles → 1h={len(_candles_1h.get(symbol, {}).get('candles', []))}, 4h={len(_candles_4h.get(symbol, {}).get('candles', []))}")
        
        # ── 1h candles (every 5min) ──
        if _should_fetch(f"1h:{symbol}", CANDLE_1H_INTERVAL):
            is_seed = not is_seeded
            
            if symbol in _30M_DIRECT_SYMBOLS:
                # 1h is derived from 30m in _rebuild_derived — just mark as fetched
                _mark_fetched(f"1h:{symbol}")
            else:
                fetch_limit = FULL_SEED_LIMIT_1H if is_seed else DELTA_LIMIT_1H
                candles = await _fetch_candles_from_api(symbol, "1h", limit=fetch_limit)
                if candles:
                    with _lock:
                        existing = (_candles_1h.get(symbol) or {}).get("candles", [])
                        merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_1H)
                        _candles_1h[symbol] = {"candles": merged, "timestamp": now_ts}
                        _rebuild_derived(symbol)
                    _mark_fetched(f"1h:{symbol}")
                    _persist_async(symbol, "1h", merged if is_seed else candles)
        
        # ── EOD candles (every 30min) ──
        if _should_fetch(f"eod:{symbol}", CANDLE_EOD_INTERVAL):
            is_seed = not is_seeded
            fetch_limit = FULL_SEED_LIMIT_EOD if is_seed else DELTA_LIMIT_EOD
            candles = await _fetch_eod_from_api(symbol, limit=fetch_limit)
            if candles:
                with _lock:
                    existing = (_candles_eod.get(symbol) or {}).get("candles", [])
                    merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_EOD)
                    _candles_eod[symbol] = {"candles": merged, "timestamp": now_ts}
                _mark_fetched(f"eod:{symbol}")
                _persist_async(symbol, "eod", merged if is_seed else candles)
        
        # Mark as seeded ONLY if we actually got data (avoid marking on 402/empty)
        if not is_seeded:
            has_5m = bool((_candles_5m.get(symbol) or {}).get("candles"))
            has_1h = bool((_candles_1h.get(symbol) or {}).get("candles"))
            has_eod = bool((_candles_eod.get(symbol) or {}).get("candles"))
            if has_5m or has_1h or has_eod:
                _initial_seed_done[seed_key] = True
                logger.info(f"[DataHub] {symbol} seeded: 5m={has_5m}, 1h={has_1h}, eod={has_eod}")
    
    # ── Macro data (every 5min) ──
    if _should_fetch("macro", MACRO_INTERVAL):
        for key, sym in MACRO_SYMBOLS.items():
            price = await _fetch_price_from_api(sym)
            if price is not None:
                with _lock:
                    _macro_data[key] = {"symbol": sym, "price": price, "timestamp": now_ts}
        _mark_fetched("macro")


def _load_from_persistent_cache():
    """Load historical candles from Supabase into memory on startup."""
    try:
        from services.candle_cache_store import load_candles
    except Exception as e:
        logger.warning(f"Candle cache store not available: {e}")
        return
    
    now_ts = datetime.utcnow().timestamp()
    loaded_any = False
    
    for symbol in TRACKED_SYMBOLS:
        # Load 5m candles
        cached_5m = load_candles(symbol, "5m", limit=FULL_SEED_LIMIT_5M)
        if cached_5m:
            with _lock:
                _candles_5m[symbol] = {"candles": cached_5m, "timestamp": now_ts}
                _rebuild_derived(symbol)
            loaded_any = True
            logger.info(f"[DataHub] Loaded {len(cached_5m)} cached 5m candles for {symbol}")
        
        # Load 30m candles (XAUUSD: fetched directly from EODHD)
        cached_30m = load_candles(symbol, "30m", limit=FULL_SEED_LIMIT_30M)
        if cached_30m:
            with _lock:
                _candles_30m[symbol] = {"candles": cached_30m, "timestamp": now_ts}
                _rebuild_derived(symbol)
            loaded_any = True
            logger.info(f"[DataHub] Loaded {len(cached_30m)} cached 30m candles for {symbol}")
        
        # Load 1h candles
        cached_1h = load_candles(symbol, "1h", limit=FULL_SEED_LIMIT_1H)
        if cached_1h:
            with _lock:
                _candles_1h[symbol] = {"candles": cached_1h, "timestamp": now_ts}
                _rebuild_derived(symbol)
            loaded_any = True
            logger.info(f"[DataHub] Loaded {len(cached_1h)} cached 1h candles for {symbol}")
        
        # Load EOD candles
        cached_eod = load_candles(symbol, "eod", limit=FULL_SEED_LIMIT_EOD)
        if cached_eod:
            with _lock:
                _candles_eod[symbol] = {"candles": cached_eod, "timestamp": now_ts}
            loaded_any = True
            logger.info(f"[DataHub] Loaded {len(cached_eod)} cached EOD candles for {symbol}")
        
        # If we loaded cached data, check if we have ENOUGH data to skip full seed
        # Fix for user issue: "only 166 candles" -> force full seed if cache is thin
        has_enough_5m = bool(cached_5m and len(cached_5m) >= FULL_SEED_LIMIT_5M * 0.5)
        has_enough_30m = bool(cached_30m and len(cached_30m) >= FULL_SEED_LIMIT_30M * 0.5)
        has_enough_1h = bool(cached_1h and len(cached_1h) >= FULL_SEED_LIMIT_1H * 0.5)
        
        # XAUUSD relies on 30m, NDX on 5m/1h
        is_enough = has_enough_5m or has_enough_30m or has_enough_1h
        
        if is_enough:
            _initial_seed_done[symbol] = True
            logger.info(f"[DataHub] Cache sufficient for {symbol} (skipping full seed)")
        else:
            _initial_seed_done[symbol] = False
            logger.info(f"[DataHub] Cache INSUFFICIENT for {symbol} (forcing full seed on next pump)")
    
    if loaded_any:
        logger.info("[DataHub] Persistent cache loaded — will only fetch delta from EODHD")
    else:
        logger.info("[DataHub] No persistent cache found — will do full seed from EODHD")


async def start_data_hub():
    """Start the DataHub background pump."""
    global _hub_running
    if _hub_running:
        logger.warning("DataHub already running")
        return
    
    _hub_running = True
    logger.info("DataHub started - centralized market data pump")
    
    # ── Step 1: Load from persistent cache (Supabase) ──
    _load_from_persistent_cache()
    
    # ── Step 2: Reset fetch timestamps to trigger immediate delta fetch ──
    for symbol in TRACKED_SYMBOLS:
        _last_fetch[f"price:{symbol}"] = 0
        _last_fetch[f"5m:{symbol}"] = 0
        _last_fetch[f"30m:{symbol}"] = 0
        _last_fetch[f"1h:{symbol}"] = 0
        _last_fetch[f"eod:{symbol}"] = 0
    _last_fetch["macro"] = 0
    
    while _hub_running:
        try:
            await _pump_cycle()
        except Exception as e:
            logger.error(f"DataHub pump error: {e}")
        await asyncio.sleep(1)  # Check every 1s, but fetches respect their intervals


def force_reseed():
    """Force a full re-seed by clearing ALL in-memory data and seed flags."""
    global _initial_seed_done
    _initial_seed_done = {}
    with _lock:
        for symbol in TRACKED_SYMBOLS:
            # Clear all candle caches so merge starts fresh
            _candles_5m.pop(symbol, None)
            _candles_15m.pop(symbol, None)
            _candles_30m.pop(symbol, None)
            _candles_1h.pop(symbol, None)
            _candles_4h.pop(symbol, None)
            _candles_eod.pop(symbol, None)
            # Reset fetch timestamps to trigger immediate fetch
            _last_fetch[f"price:{symbol}"] = 0
            _last_fetch[f"5m:{symbol}"] = 0
            _last_fetch[f"30m:{symbol}"] = 0
            _last_fetch[f"1h:{symbol}"] = 0
            _last_fetch[f"eod:{symbol}"] = 0
    _last_fetch["macro"] = 0
    logger.info("[DataHub] Force re-seed: cleared all in-memory caches and seed flags")
    return {"status": "ok", "message": "All caches cleared — full re-seed on next pump cycle"}


def stop_data_hub():
    """Stop the DataHub."""
    global _hub_running
    _hub_running = False
    logger.info("DataHub stopped")


# ═══════════════════════════════════════════════════════════════
# PUBLIC READ API (used by all services - 0 API calls)
# ═══════════════════════════════════════════════════════════════
def get_price(symbol: str) -> Optional[float]:
    """Get latest cached price for a symbol. Returns None if not yet fetched."""
    with _lock:
        data = _prices.get(symbol)
        if data:
            return data["price"]
        # Try normalized
        for key, val in _prices.items():
            if key.upper().startswith(symbol.upper().split(".")[0]):
                return val["price"]
    return None


def get_candles(symbol: str, timeframe: str, limit: int = 300) -> List[Dict]:
    """
    Get cached candles for any timeframe. Returns empty list if not yet fetched.
    
    Supported timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d/eod
    Also accepts: M1, M5, M15, M30, H1, H4, D1
    """
    tf = timeframe.lower().strip()
    
    # Normalize timeframe aliases
    tf_map = {
        "m1": "1m", "m5": "5m", "m15": "15m", "m30": "30m",
        "h1": "1h", "h4": "4h", "d1": "eod", "1d": "eod", "daily": "eod",
    }
    tf = tf_map.get(tf, tf)
    
    store_map = {
        "5m": _candles_5m,
        "15m": _candles_15m,
        "30m": _candles_30m,
        "1h": _candles_1h,
        "4h": _candles_4h,
        "eod": _candles_eod,
    }
    
    store = store_map.get(tf)
    if store is None:
        # 1m not stored - would need separate fetch
        return []
    
    with _lock:
        data = store.get(symbol, {}).get("candles", [])
        if not data:
            # Try to find by partial symbol match
            for key, val in store.items():
                if key.upper().startswith(symbol.upper().split(".")[0]):
                    data = val.get("candles", [])
                    break
    
    if not data:
        return []
    
    # Filter out zero-volume candles (market closed periods / placeholder candles)
    # This prevents chart gaps and horizontal lines in the frontend
    filtered = [c for c in data if c.get("volume", 0) > 0]
    
    # If filtering removes everything (shouldn't happen with valid data), return original
    if not filtered and data:
        return data[-limit:]
    
    return filtered[-limit:]


def get_macro() -> Dict[str, Any]:
    """Get cached macro data (DXY, VIX, USDTRY)."""
    with _lock:
        return {k: {"symbol": v.get("symbol"), "price": v.get("price")} for k, v in _macro_data.items()}


def _get_volume_stats(symbol: str, store: Dict) -> Dict:
    """Get volume statistics for a symbol's candle store."""
    candles = store.get(symbol, {}).get("candles", [])
    if not candles:
        return {"count": 0, "total_volume": 0, "avg_volume": 0, "sample": []}
    
    volumes = [c.get("volume", 0) for c in candles[-20:]]  # Son 20 mum
    return {
        "count": len(candles),
        "total_volume": sum(volumes),
        "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
        "sample": volumes[-5:] if len(volumes) >= 5 else volumes,
    }


def get_hub_status() -> Dict[str, Any]:
    """Get DataHub status for debugging."""
    with _lock:
        # Get latest candle timestamps for each symbol to detect stale data
        price_staleness = {}
        for s in TRACKED_SYMBOLS:
            latest_ts = None
            # Try to get most recent timestamp from available candles
            for store in [_candles_5m, _candles_1h, _candles_30m, _candles_eod]:
                candles = store.get(s, {}).get("candles", [])
                if candles:
                    last_candle = candles[-1]
                    candle_ts = last_candle.get("timestamp") or last_candle.get("date")
                    if candle_ts:
                        latest_ts = candle_ts
                        break
            
            # Calculate staleness
            if latest_ts:
                if isinstance(latest_ts, (int, float)):
                    # Unix timestamp in milliseconds
                    hours_old = (datetime.utcnow().timestamp() - latest_ts/1000) / 3600
                else:
                    # ISO date string
                    try:
                        dt = datetime.fromisoformat(str(latest_ts).replace('Z', '+00:00'))
                        hours_old = (datetime.utcnow() - dt.replace(tzinfo=None)).total_seconds() / 3600
                    except:
                        hours_old = None
                
                price_staleness[s] = {
                    "latest_candle": latest_ts,
                    "hours_old": round(hours_old, 1) if hours_old else None,
                    "stale": hours_old > 2 if hours_old else True
                }
        
        # Volume stats for debugging
        volume_stats = {}
        for s in TRACKED_SYMBOLS:
            volume_stats[s] = {
                "5m": _get_volume_stats(s, _candles_5m),
                "15m": _get_volume_stats(s, _candles_15m),
                "30m": _get_volume_stats(s, _candles_30m),
                "1h": _get_volume_stats(s, _candles_1h),
                "4h": _get_volume_stats(s, _candles_4h),
                "eod": _get_volume_stats(s, _candles_eod),
            }
        
        status = {
            "running": _hub_running,
            "symbols": TRACKED_SYMBOLS,
            "prices": {s: _prices.get(s, {}).get("price") for s in TRACKED_SYMBOLS},
            "price_staleness": price_staleness,
            "candles_5m": {s: len(_candles_5m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_15m": {s: len(_candles_15m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_30m": {s: len(_candles_30m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_1h": {s: len(_candles_1h.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_4h": {s: len(_candles_4h.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_eod": {s: len(_candles_eod.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "volume_stats": volume_stats,  # Hacim istatistikleri eklendi
            "macro": {k: v.get("price") for k, v in _macro_data.items()},
            "last_fetch": {k: datetime.fromtimestamp(v).isoformat() for k, v in _last_fetch.items()},
            "seeded_from_cache": dict(_initial_seed_done),
        }
    # Add persistent cache stats
    try:
        from services.candle_cache_store import get_cache_stats
        status["persistent_cache"] = get_cache_stats()
    except Exception:
        status["persistent_cache"] = {"available": False}
    return status
