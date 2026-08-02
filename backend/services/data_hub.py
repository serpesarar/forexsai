"""
DataHub - Centralized Market Data Store
========================================
Single source of truth for all market data in the system.

Default mode: mt5_redis (MT5 Bridge → Redis → DataHub)
  All price and OHLCV data flows exclusively from the MT5 bridge.
  No external market-data vendor API is used for price/candle data.

Architecture (mt5_redis mode):
  Startup:  Supabase (candle_cache) → DataHub (in-memory)
  Running:  MT5 Bridge → Redis pub/sub + streams → ingest_live_price / ingest_candle
  Persist:  DataHub (in-memory) → Supabase candle_cache (every 15 min)
  Restart:  Load from Supabase (0 MT5 wait) → live updates resume automatically

MT5 streams consumed:
  mt5:tick       → ingest_live_price (real-time bid/ask/last)
  mt5:bar:5m     → ingest_candle("5m")  → rebuild 15m / 30m + XAUUSD 1h/4h
  mt5:bar:1h     → ingest_candle("1h")  → rebuild 4h (NDX/DAX/USOIL)
  mt5:bar:1d     → ingest_candle("eod")

Derived (0 API calls — pure resample):
  NDX/DAX/USOIL: 5m→15m, 5m→30m, 5m→1h, 1h→4h
  XAUUSD:        5m→15m, 5m→30m, 30m→1h, 30m→4h

Macro data (DXY, VIX, USDTRY, EURUSD — context only, not trading data):
  Fetched from yfinance (see macro_data_service), independent of this module.

Other modes (set MARKET_DATA_SOURCE env var):
  hybrid    → MT5 primary; Yahoo Finance fallback for commodities when MT5 is stale
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, Deque, List, Optional, Tuple

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

# REFERENCE-ONLY symbols: ingested for CONTEXT (price/candles) but NOT tradable —
# no signal generation, no scheduler, no model routing touches them. QQQ.US (a
# NASDAQ-100 ETF that trades the US premarket, unlike the NDX cash index) gives
# the bias debate engine a live premarket read when NDX cash is closed.
REFERENCE_SYMBOLS = {"QQQ.US"}

# ═══════════════════════════════════════════════════════════════
# FETCH INTERVALS (seconds)
# ═══════════════════════════════════════════════════════════════
PRICE_INTERVAL = 5        # Fetch live price every 5 seconds (WS fallback since upstream premium missing)
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

# Raw data from upstream (fetched via API)
_prices: Dict[str, Dict[str, Any]] = {}        # symbol -> {price, timestamp}
_candles_1m: Dict[str, Dict[str, Any]] = {}     # symbol -> {candles, timestamp} — MT5 Redis / XAUUSD
_candles_5m: Dict[str, Dict[str, Any]] = {}     # symbol -> {candles, timestamp}
_candles_1h: Dict[str, Dict[str, Any]] = {}     # symbol -> {candles, timestamp}
_candles_eod: Dict[str, Dict[str, Any]] = {}    # symbol -> {candles, timestamp}

# Derived data (computed from raw, 0 API calls)
_candles_20m: Dict[str, Dict[str, Any]] = {}    # symbol -> {candles, timestamp}
_candles_15m: Dict[str, Dict[str, Any]] = {}    # symbol -> {candles, timestamp}
_candles_30m: Dict[str, Dict[str, Any]] = {}    # symbol -> {candles, timestamp}
_candles_4h: Dict[str, Dict[str, Any]] = {}     # symbol -> {candles, timestamp}

# Macro data
_macro_data: Dict[str, Dict[str, Any]] = {}     # key -> {symbol, price, timestamp}

# Real-time tick history — bounded ring buffer per symbol, fed by ingest_live_price.
# Used ONLY to synthesize sub-minute (e.g. 15s) bars for the rhythm detector. The
# MT5 tick pub/sub overwrites _prices with the latest tick; this buffer additionally
# retains the recent tick *series* so we can resample below the 1m/5m floor. Bounded
# by count (memory-safe); stale ticks age out naturally when the window slides.
_TICK_BUFFER_MAXLEN = 24000     # ~ enough for 600 × 15s bars even at heavy tick flow
_tick_buffer: Dict[str, Deque[Tuple[float, float]]] = {}   # symbol -> deque[(ts_seconds, price)]

# Last fetch timestamps
_last_fetch: Dict[str, float] = {}

# Hub running flag
_hub_running = False

# ── Hybrid-mode MT5 freshness thresholds ─────────────────────────────────────
# If MT5 has pushed data more recently than these thresholds, skip the upstream
# poll so that stale upstream data cannot overwrite correct live MT5 prices/candles.
MT5_PRICE_FRESHNESS_THRESHOLD = 120    # 2 min — skip upstream price if MT5 is fresher
MT5_CANDLES_FRESHNESS_THRESHOLD = 900  # 15 min — skip upstream candle fetch if MT5 is fresher

# ── Persistent-cache staleness gate ──────────────────────────────────────────
# If the most recent candle in a Supabase cache is older than this threshold,
# skip that cache entry entirely (force fresh API seed instead of using stale data).
MAX_CACHE_AGE_HOURS = 96  # 4 days — covers a long holiday weekend

# ═══════════════════════════════════════════════════════════════
# CANDLE CLOSE EVENT SYSTEM
# ═══════════════════════════════════════════════════════════════
# Tracks the latest candle timestamp per symbol/timeframe to detect new closes
_last_candle_ts: Dict[str, int] = {}  # "symbol:timeframe" -> last candle timestamp (ms)

# Registered callbacks: timeframe -> list of async callables(symbol, timeframe)
_candle_close_callbacks: Dict[str, List] = {}


def on_candle_close(timeframe: str):
    """Decorator to register a callback for candle close events.
    Usage:
        @on_candle_close("5m")
        async def handle_5m_close(symbol: str, timeframe: str): ...
    """
    def decorator(func):
        _candle_close_callbacks.setdefault(timeframe, []).append(func)
        logger.info(f"[DataHub] Registered candle close callback: {func.__name__} for {timeframe}")
        return func
    return decorator


def register_candle_close_callback(timeframe: str, func):
    """Programmatic registration of candle close callbacks."""
    _candle_close_callbacks.setdefault(timeframe, []).append(func)
    logger.info(f"[DataHub] Registered candle close callback: {func.__name__} for {timeframe}")


async def _fire_candle_close_events(symbol: str, timeframe: str, candles: List[Dict]):
    """Check if the latest candle is new and fire registered callbacks."""
    if not candles:
        return
    
    latest_ts = candles[-1].get("timestamp", 0)
    if not latest_ts:
        return
    
    cache_key = f"{symbol}:{timeframe}"
    prev_ts = _last_candle_ts.get(cache_key, 0)
    
    if latest_ts > prev_ts:
        _last_candle_ts[cache_key] = latest_ts
        
        # Skip first-time (seed) — no event on initial load
        if prev_ts == 0:
            return
        
        callbacks = _candle_close_callbacks.get(timeframe, [])
        if callbacks:
            logger.info(f"[DataHub] Candle close detected: {symbol}/{timeframe} ts={latest_ts}, firing {len(callbacks)} callbacks")
            for cb in callbacks:
                try:
                    asyncio.create_task(cb(symbol, timeframe))
                except Exception as e:
                    logger.error(f"[DataHub] Candle close callback error ({cb.__name__}): {e}")


def get_market_data_source() -> str:
    source = (settings.market_data_source or "mt5_redis").strip().lower()
    if source not in {"mt5_redis", "hybrid"}:
        return "mt5_redis"
    return source


def _upstream_market_fetch_enabled() -> bool:
    # Only "hybrid" allows the upstream poll (Yahoo fallback for commodities);
    # "mt5_redis" relies solely on the MT5 -> Redis bridge.
    return get_market_data_source() == "hybrid"


def _canonical_symbol(symbol: str) -> str:
    value = (symbol or "").strip()
    upper = value.upper()
    aliases = {
        "NDX": "NDX.INDX",
        "NASDAQ": "NDX.INDX",
        "NDX.INDX": "NDX.INDX",
        "USTEC": "NDX.INDX",
        "US100": "NDX.INDX",
        "NAS100": "NDX.INDX",
        "NDAQ100": "NDX.INDX",
        "USNDAQ100": "NDX.INDX",
        "NASDAQ100": "NDX.INDX",
        "US100.CASH": "NDX.INDX",
        "XAUUSD": "XAUUSD",
        "XAUUSD.FOREX": "XAUUSD",
        "GOLD": "XAUUSD",
        "GDAXI": "GDAXI.INDX",
        "DAX": "GDAXI.INDX",
        "GDAXI.INDX": "GDAXI.INDX",
        "DE30": "GDAXI.INDX",
        "GER30": "GDAXI.INDX",
        "DE40": "GDAXI.INDX",
        "GER40": "GDAXI.INDX",
        "USOIL": "USOIL.FOREX",
        "USOIL.FOREX": "USOIL.FOREX",
        "CL": "USOIL.FOREX",
        "WTI": "USOIL.FOREX",
    }
    return aliases.get(upper, value)


# ═══════════════════════════════════════════════════════════════
# SYMBOL NORMALIZATION
# ═══════════════════════════════════════════════════════════════
def _normalize_symbol(symbol: str) -> str:
    s = (symbol or "").strip()
    if not s:
        return s
    # Explicit commodity mappings - upstream uses specific formats
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


def _normalize_timeframe(timeframe: str) -> str:
    tf = (timeframe or "").lower().strip()
    tf_map = {
        "m1": "1m", "m5": "5m", "m15": "15m", "m20": "20m", "m30": "30m",
        "h1": "1h", "h4": "4h", "d1": "eod", "1d": "eod", "daily": "eod",
    }
    return tf_map.get(tf, tf)


def _get_store_for_timeframe(timeframe: str):
    tf = _normalize_timeframe(timeframe)
    store_map = {
        "1m": _candles_1m,
        "5m": _candles_5m,
        "20m": _candles_20m,
        "15m": _candles_15m,
        "30m": _candles_30m,
        "1h": _candles_1h,
        "4h": _candles_4h,
        "eod": _candles_eod,
    }
    return tf, store_map.get(tf)


def _coerce_epoch_seconds(timestamp: Any) -> float:
    if timestamp is None:
        return datetime.now(timezone.utc).timestamp()
    if isinstance(timestamp, (int, float)):
        value = float(timestamp)
        return value / 1000.0 if value > 10_000_000_000 else value
    try:
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        return parsed.timestamp()
    except Exception:
        return datetime.now(timezone.utc).timestamp()


def _coerce_timestamp_ms(timestamp: Any) -> int:
    return int(_coerce_epoch_seconds(timestamp) * 1000)


# ── Bucket alignment (2026-07-08 tick-pollution fix) ──────────────────
# Tick-built bars with arbitrary second offsets (:48, :53...) were entering the
# closed-bar stores and cascading through every derived timeframe (XAUUSD worst:
# ~90% of bars misaligned). All merge/resample/persist paths now snap or reject
# by clock bucket.
_TF_INTERVAL_MS: Dict[str, int] = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000, "20m": 1_200_000,
    "30m": 1_800_000, "1h": 3_600_000, "4h": 14_400_000,
}


def _tf_interval_ms(timeframe: str) -> Optional[int]:
    """Millisecond interval for an intraday timeframe (None for eod/unknown)."""
    return _TF_INTERVAL_MS.get(_normalize_timeframe(timeframe))


def _is_bucket_aligned(ts_ms: int, interval_ms: int) -> bool:
    """True if the timestamp sits exactly on a clock-bucket boundary."""
    return interval_ms > 0 and int(ts_ms) % interval_ms == 0


def _entry_age_seconds(entry: Dict[str, Any]) -> Optional[float]:
    timestamp = entry.get("timestamp")
    if timestamp is None:
        return None
    try:
        age = time.time() - _coerce_epoch_seconds(timestamp)
        return round(max(age, 0.0), 1)
    except Exception:
        return None


def _get_latest_candle_age_hours(candles: List[Dict]) -> Optional[float]:
    """Return how many hours old the most recent candle in `candles` is.

    Candles must be sorted ascending (oldest → newest).  Returns None if the
    list is empty or the timestamp cannot be parsed.
    """
    if not candles:
        return None
    latest_ts = candles[-1].get("timestamp", 0)  # milliseconds
    if not latest_ts:
        return None
    try:
        age_hours = (time.time() - float(latest_ts) / 1000) / 3600
        return round(max(age_hours, 0.0), 2)
    except Exception:
        return None


def _mt5_price_is_fresh(symbol: str) -> bool:
    """Return True when a recent MT5 price exists and is newer than the threshold.

    Used in hybrid mode to prevent upstream polls from overwriting live MT5 data.
    """
    entry = _prices.get(symbol, {})
    if entry.get("source") != "mt5_redis":
        return False
    ts = entry.get("timestamp", 0)
    if not ts:
        return False
    age_seconds = time.time() - float(ts)
    return age_seconds < MT5_PRICE_FRESHNESS_THRESHOLD


def _mt5_candles_are_fresh(symbol: str, timeframe: str) -> bool:
    """Return True when MT5 has recently written candles for symbol/timeframe.

    Checks the `_last_fetch` stamp set by `ingest_candles` as well as the
    source tag on the candle store so that upstream does not overwrite fresh
    MT5 intraday data in hybrid mode.
    """
    tf, store = _get_store_for_timeframe(timeframe)
    if store is None:
        return False
    entry = store.get(symbol, {})
    source = entry.get("source", "")
    if "mt5" not in source:
        return False
    last_ingest = _last_fetch.get(f"{tf}:{symbol}", 0)
    return (time.time() - last_ingest) < MT5_CANDLES_FRESHNESS_THRESHOLD


# ═══════════════════════════════════════════════════════════════
# YAHOO FINANCE FALLBACK (Commodities/Forex bypassing upstream)
# ═══════════════════════════════════════════════════════════════
def _is_us_market_open() -> bool:
    """Check if it's currently US Market Hours (09:30 - 16:00 EST/EDT, Mon-Fri)."""
    try:
        now_ny = datetime.now(zoneinfo.ZoneInfo("America/New_York"))
    except Exception:
        now_ny = datetime.now(timezone.utc) - timedelta(hours=5)
    
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
    # Use 1m interval for most recent price, 5m as fallback for stability
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval=1m&range=1d"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                result = data['chart']['result'][0]
                meta = result.get('meta', {})
                
                # Try meta regularMarketPrice first
                if meta.get('regularMarketPrice'):
                    price = float(meta['regularMarketPrice'])
                    if price > 0:
                        return price
                
                # Fallback: use last candle close (more recent for commodities)
                timestamps = result.get('timestamp', [])
                quote = result.get('indicators', {}).get('quote', [{}])[0]
                if timestamps and quote.get('close'):
                    closes = quote['close']
                    # Find last valid close price
                    for i in range(len(closes) - 1, -1, -1):
                        if closes[i] is not None and closes[i] > 0:
                            return float(closes[i])
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
    if yf_interval == "1m": yf_range = "7d"
    elif yf_interval in ("5m", "15m", "30m", "60m"): yf_range = "60d"
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
                    o = quote['open'][i]
                    h = quote['high'][i]
                    l = quote['low'][i]
                    c = quote['close'][i]
                    # Reject candles where any OHLC field is None or close=0 (Yahoo partial bar)
                    if o is None or h is None or l is None or c is None:
                        continue
                    o_f, h_f, l_f, c_f = float(o), float(h), float(l), float(c)
                    if c_f <= 0 or h_f <= 0:
                        continue
                    # Convert to milliseconds for standard Datahub format
                    ts_ms = timestamps[i] * 1000
                    dt_str = datetime.fromtimestamp(timestamps[i]).isoformat()

                    candles.append({
                        "timestamp": ts_ms,
                        "date": dt_str,
                        "open": o_f,
                        "high": h_f,
                        "low": l_f,
                        "close": c_f,
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
# UPSTREAM PRICE/CANDLE FETCHERS (only called by DataHub pump)
# Indices (NDX, GDAXI) arrive via the MT5 -> Redis bridge. Commodities
# (USOIL/XAUUSD) keep a Yahoo Finance fallback. No external market-data
# vendor API is used here.
# ═══════════════════════════════════════════════════════════════
async def _fetch_price_from_api(symbol: str) -> Optional[float]:
    """Fetch real-time price — Yahoo for commodities/indices fallback, else nothing."""
    eod_symbol = _normalize_symbol(symbol)

    # --- YAHOO FINANCE FALLBACK ---
    if eod_symbol == "CL":  # USOil / WTI
        return await _fetch_yahoo_price("CL=F")
    if eod_symbol in ("XAUUSD.FOREX", "XAUUSD"):  # Gold
        return await _fetch_yahoo_price("GC=F")
    if eod_symbol == "NDX.INDX":  # Nasdaq
        return await _fetch_yahoo_price("^NDX")
    if eod_symbol == "GDAXI.INDX":  # DAX
        return await _fetch_yahoo_price("^GDAXI")

    # Indices come from the MT5 -> Redis bridge; no upstream HTTP fetch.
    return None


async def _fetch_candles_from_api(symbol: str, interval: str, limit: int = 500) -> List[Dict]:
    """Fetch intraday candles — Yahoo for commodities/indices fallback, else nothing."""
    eod_symbol = _normalize_symbol(symbol)

    # --- YAHOO FINANCE FALLBACK ---
    if eod_symbol == "CL":
        return await _fetch_yahoo_candles("CL=F", interval, limit)
    if eod_symbol in ("XAUUSD.FOREX", "XAUUSD"):
        return await _fetch_yahoo_candles("GC=F", interval, limit)
    if eod_symbol == "NDX.INDX":
        return await _fetch_yahoo_candles("^NDX", interval, limit)
    if eod_symbol == "GDAXI.INDX":
        return await _fetch_yahoo_candles("^GDAXI", interval, limit)

    # Indices come from the MT5 -> Redis bridge; no upstream HTTP fetch.
    return []


async def _fetch_eod_from_api(symbol: str, limit: int = 300) -> List[Dict]:
    """Fetch EOD candles — Yahoo for commodities/indices fallback, else nothing."""
    eod_symbol = _normalize_symbol(symbol)

    # --- YAHOO FINANCE FALLBACK ---
    if eod_symbol == "CL":
        return await _fetch_yahoo_candles("CL=F", "1d", limit)
    if eod_symbol in ("XAUUSD.FOREX", "XAUUSD"):
        return await _fetch_yahoo_candles("GC=F", "1d", limit)
    if eod_symbol == "NDX.INDX":
        return await _fetch_yahoo_candles("^NDX", "1d", limit)
    if eod_symbol == "GDAXI.INDX":
        return await _fetch_yahoo_candles("^GDAXI", "1d", limit)

    # Indices come from the MT5 -> Redis bridge; no upstream HTTP fetch.
    return []


# ═══════════════════════════════════════════════════════════════
# RESAMPLE LOGIC (0 API calls - pure computation)
# ═══════════════════════════════════════════════════════════════
def _resample(candles: List[Dict], period: int, base_ms: Optional[int] = None) -> List[Dict]:
    """Resample candles to a larger timeframe by CLOCK BUCKET. E.g., 5m×3=15m.

    2026-07-08 rewrite (tick-pollution fix): the old implementation grouped by
    POSITION (candles[i:i+period]) with a base interval guessed from the first
    two candles and the group's first timestamp as output. On a polluted or
    gappy base series this produced phase-shifted 15m bars at :48/:53, 12-minute
    "1h" bars, and collapsed 4h series. Now:
      - base_ms comes from the caller (timeframe constant), falling back to the
        MEDIAN of observed diffs (robust against a bad first pair);
      - candles are grouped by `ts // out_interval` (true clock buckets);
      - output timestamp is the BUCKET START (always aligned, e.g. :00/:15/:30);
      - misaligned input bars (ts not on a base_ms boundary — tick artifacts)
        are skipped;
      - the still-open trailing bucket is excluded so live partial bars never
        enter closed-bar stores.
    """
    if not candles:
        return []

    if base_ms is None or base_ms <= 0:
        diffs = sorted(
            int(candles[i + 1].get("timestamp", 0)) - int(candles[i].get("timestamp", 0))
            for i in range(len(candles) - 1)
        )
        diffs = [d for d in diffs if d > 0]
        base_ms = diffs[len(diffs) // 2] if diffs else 5 * 60 * 1000

    out_interval = base_ms * period
    now_ms = int(time.time() * 1000)
    current_bucket = (now_ms // out_interval) * out_interval

    buckets: Dict[int, List[Dict]] = {}
    for c in candles:
        ts = int(c.get("timestamp", 0) or 0)
        if ts <= 0 or not _is_bucket_aligned(ts, base_ms):
            continue  # tick artifact / phase-drifted bar — never aggregate it
        bucket = (ts // out_interval) * out_interval
        if bucket >= current_bucket:
            continue  # bucket still forming — exclude live partial bar
        buckets.setdefault(bucket, []).append(c)

    result = []
    for bucket in sorted(buckets):
        group = sorted(buckets[bucket], key=lambda c: c.get("timestamp", 0))
        result.append({
            "timestamp": bucket,
            "date":      group[0].get("date", ""),
            "open":      group[0].get("open", 0),
            "high":      max(c.get("high", 0) for c in group),
            "low":       min(c.get("low", float("inf")) for c in group),
            "close":     group[-1].get("close", 0),
            "volume":    sum(c.get("volume", 0) for c in group),
        })
    return result


def _merge_1h_tail(real_candles: List[Dict], derived_candles: List[Dict]) -> List[Dict]:
    """Preserve the full real 1h history and APPEND freshly-derived 1h bars that
    fall strictly AFTER the last real bar.

    2026-08-02: guards against a frozen upstream mt5:bar:1h stream silently
    freezing the chart. The 2026-07-01 fix (don't clobber ~2400 real 1h bars with
    the ~125 we can derive from the 5m window) meant that when the real 1h stream
    stalled (indices/XAU froze 2026-07-31) the system clung to stale real bars and
    refused to advance from the LIVE 5m/30m feed. This merges the two: deep real
    history is kept, the live-derived tail extends it, dedup by timestamp. Bars are
    bucket-start aligned on both sides, so the strict `> last_real_ts` cut never
    double-counts. Self-heals the moment the real stream resumes.
    """
    if not real_candles:
        return derived_candles or []
    if not derived_candles:
        return real_candles
    last_real_ts = max(int(c.get("timestamp", 0) or 0) for c in real_candles)
    tail = [c for c in derived_candles if int(c.get("timestamp", 0) or 0) > last_real_ts]
    if not tail:
        return real_candles
    return real_candles + tail


def _rebuild_derived(symbol: str):
    """Rebuild derived timeframes from raw data.

    NDX.INDX: 5m→15m, 5m→30m, 1h(fetched)→4h
    XAUUSD:   5m→15m, 30m(fetched)→1h→4h  (30m also from 5m if not fetched)
    """
    now = datetime.now(timezone.utc).timestamp()
    market_data_source = get_market_data_source()
    use_direct_30m = False  # direct upstream 30m fetch retired with the vendor API
    derive_from_30m = symbol in _30M_DIRECT_SYMBOLS
    
    raw_5m = _candles_5m.get(symbol, {}).get("candles", [])
    if raw_5m:
        _candles_20m[symbol] = {"candles": _resample(raw_5m, 4, base_ms=300_000), "timestamp": now, "source": "derived_from_5m"}
        # 15m = 5m × 3 (always)
        _candles_15m[symbol] = {"candles": _resample(raw_5m, 3, base_ms=300_000), "timestamp": now, "source": "derived_from_5m"}

        # 30m: use directly-fetched 30m if available, otherwise derive from 5m
        if not use_direct_30m:
            _candles_30m[symbol] = {"candles": _resample(raw_5m, 6, base_ms=300_000), "timestamp": now, "source": "derived_from_5m"}

        if market_data_source in {"mt5_redis", "hybrid"} and not use_direct_30m and not derive_from_30m:
            # Respect directly-ingested 1h from MT5 (mt5:bar:1h stream) or Supabase
            # persistent cache; only fall back to 5m-derived 1h when no richer source
            # is available. This prevents clobbering ~2400 real 1h bars with the
            # ~125 bars we can derive from the 5m window, which in turn collapses
            # the 4h chain (4h = 1h × 4) from ~600 candles down to ~31.
            existing_1h = _candles_1h.get(symbol, {}) or {}
            existing_1h_candles = existing_1h.get("candles", [])
            existing_1h_source = (existing_1h.get("source") or "").lower()
            richer_1h_available = (
                len(existing_1h_candles) > len(raw_5m) // 12
                or ("derived" not in existing_1h_source and existing_1h_source not in {"", "unknown"})
            )
            derived_1h = _resample(raw_5m, 12, base_ms=300_000)
            if not richer_1h_available:
                if derived_1h:
                    _candles_1h[symbol] = {"candles": derived_1h, "timestamp": now, "source": "derived_from_5m"}
            elif derived_1h:
                # Real 1h present: keep its deep history but append any fresh
                # 5m-derived 1h bars beyond its last timestamp so a stalled
                # mt5:bar:1h stream cannot freeze the chart (self-heals on resume).
                merged = _merge_1h_tail(existing_1h_candles, derived_1h)
                if len(merged) > len(existing_1h_candles):
                    _candles_1h[symbol] = {
                        "candles": merged,
                        "timestamp": now,
                        "source": f"{existing_1h_source or 'mt5_redis'}+5m_tail",
                    }
    
    # XAUUSD keeps its 1h/4h chain on top of 30m, whether 30m was fetched or derived.
    if derive_from_30m:
        raw_30m = _candles_30m.get(symbol, {}).get("candles", [])

        # 2026-07-01 (rapor aksiyon #8): MT5 mt5:bar:1h stream'inden veya
        # persistent cache'ten gelen GERÇEK 1h barlarını 30m çift-resample
        # türeviyle EZME. Çift resample (5m→30m→1h) ara swing'leri siliyor ve
        # PULSE 3 / SMC'nin 1h-4h okumalarını sentetik barlara mahkum ediyordu.
        # XAU_REAL_H1_ENABLED=0 ile eski davranışa dönülür.
        _existing_1h = _candles_1h.get(symbol, {}) or {}
        _existing_1h_candles = _existing_1h.get("candles", [])
        _existing_1h_source = (_existing_1h.get("source") or "").lower()
        _real_1h_available = (
            os.getenv("XAU_REAL_H1_ENABLED", "1") != "0"
            and bool(_existing_1h_candles)
            and "derived" not in _existing_1h_source
            and _existing_1h_source not in {"", "unknown"}
        )

        if raw_30m:
            derived_1h = _resample(raw_30m, 2, base_ms=1_800_000)  # 1h = 30m × 2
            if not _real_1h_available:
                if derived_1h:
                    _candles_1h[symbol] = {"candles": derived_1h, "timestamp": now, "source": "derived_from_30m"}
            elif derived_1h:
                # Real 1h present: preserve history, append fresh 30m-derived tail
                # beyond its last bar (self-heals a stalled mt5:bar:1h stream).
                merged = _merge_1h_tail(_existing_1h_candles, derived_1h)
                if len(merged) > len(_existing_1h_candles):
                    _candles_1h[symbol] = {
                        "candles": merged,
                        "timestamp": now,
                        "source": f"{_existing_1h_source or 'mt5_redis'}+30m_tail",
                    }

        # 4h is built from the FINAL 1h series (already merged above), so the fresh
        # tail flows into 4h too instead of freezing with the stale real 1h.
        final_1h = _candles_1h.get(symbol, {}).get("candles", [])
        derived_4h = None
        _src_4h = "derived_from_30m"
        if final_1h:
            derived_4h = _resample(final_1h, 4, base_ms=3_600_000)  # 4h = 1h × 4
            _src_4h = "derived_from_1h"
        if not derived_4h and raw_30m:
            derived_4h = _resample(raw_30m, 8, base_ms=1_800_000)  # 4h = 30m × 8 (fallback)
            _src_4h = "derived_from_30m"
        if derived_4h:
            _candles_4h[symbol] = {"candles": derived_4h, "timestamp": now, "source": _src_4h}
    else:
        # NDX: 4h = 1h × 4
        raw_1h = _candles_1h.get(symbol, {}).get("candles", [])
        if raw_1h:
            _candles_4h[symbol] = {"candles": _resample(raw_1h, 4, base_ms=3_600_000), "timestamp": now, "source": "derived_from_1h"}


# ═══════════════════════════════════════════════════════════════
# DATA PUMP (background loop)
# ═══════════════════════════════════════════════════════════════
def _should_fetch(key: str, interval: float) -> bool:
    now = datetime.now(timezone.utc).timestamp()
    last = _last_fetch.get(key, 0)
    return (now - last) >= interval


def _mark_fetched(key: str):
    _last_fetch[key] = datetime.now(timezone.utc).timestamp()


# Track whether initial seed has been done (first fetch = full, subsequent = delta)
_initial_seed_done: Dict[str, bool] = {}

# Delta fetch limits (much smaller than full seed)
DELTA_LIMIT_5M = 24       # ~2 hours of 5m candles
DELTA_LIMIT_30M = 12      # ~6 hours of 30m candles
DELTA_LIMIT_1H = 6        # ~6 hours of 1h candles
DELTA_LIMIT_EOD = 5       # ~5 days of EOD candles

# Full seed limits — sized so EMA200 works on ALL derived timeframes:
#   5m:  1500 → 15m=500, 30m=250
#   30m: 1600 → 1h=800, 4h=200 (XAUUSD: fetched directly)
#   1h:  2400 → 4h=600 (~100 days) — needed for harmonic pattern history
#   EOD: 730  → EMA200 with 2 full years of data
FULL_SEED_LIMIT_5M = 1500   # ~5.2 days of 5m candles
FULL_SEED_LIMIT_30M = 1600  # ~54 days of 30m candles (XAUUSD max 1h limit capacity)
FULL_SEED_LIMIT_1H = 2400   # ~200+ days of 1h candles → 4h derived = ~600 candles (~100 days)
FULL_SEED_LIMIT_EOD = 730   # ~2 years of daily candles

# upstream interval support varies by symbol:
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


def _merge_candles(
    existing: List[Dict],
    new_candles: List[Dict],
    limit: int,
    interval_ms: Optional[int] = None,
) -> List[Dict]:
    """Merge new candles into existing, deduplicate by clock bucket, keep latest `limit`.

    2026-07-08: dedup key is now the INTERVAL-ALIGNED bucket (when interval_ms
    is given) instead of the exact timestamp. Exact-ts keying let a bar at
    12:45:00 and a tick artifact at 12:48:23 coexist forever, densifying the
    store beyond its nominal interval. One bucket → one bar; new data wins;
    an aligned timestamp wins over a misaligned one within the same bucket.
    """
    if not new_candles:
        return existing

    def _key(c: Dict) -> Any:
        ts = c.get("timestamp")
        if ts and interval_ms:
            return (int(ts) // interval_ms) * interval_ms
        return ts or c.get("date", "")

    merged: Dict[Any, Dict] = {}
    for c in existing:
        key = _key(c)
        if key:
            merged[key] = c
    for c in new_candles:
        key = _key(c)
        if not key:
            continue
        prev = merged.get(key)
        if prev is not None and interval_ms:
            # Keep the bucket-aligned bar over a misaligned artifact
            prev_aligned = _is_bucket_aligned(int(prev.get("timestamp", 0) or 0), interval_ms)
            new_aligned = _is_bucket_aligned(int(c.get("timestamp", 0) or 0), interval_ms)
            if prev_aligned and not new_aligned:
                continue
        merged[key] = c  # New data overwrites old

    # Sort by timestamp ascending and trim
    result = sorted(merged.values(), key=lambda x: x.get("timestamp", 0) or 0)
    return result[-limit:]


def _has_required_seed_data(symbol: str) -> bool:
    """Check whether a symbol has the minimum intraday caches required for seed completion.

    Why this matters:
    - Marking a symbol as "seeded" too early causes future cycles to fetch only small deltas.
    - If 1h cache is thin (e.g. ~150 bars), frontend requests like limit=720 will never be satisfied.
    """
    has_5m = bool((_candles_5m.get(symbol) or {}).get("candles"))
    has_30m = bool((_candles_30m.get(symbol) or {}).get("candles"))
    has_1h = bool((_candles_1h.get(symbol) or {}).get("candles"))

    # XAUUSD derives 1h/4h primarily from directly-fetched 30m candles.
    if symbol in _30M_DIRECT_SYMBOLS:
        return has_5m and (has_30m or has_1h)

    # Index symbols rely on directly-fetched 1h candles.
    return has_5m and has_1h


def _has_sufficient_cached_history(
    symbol: str,
    cached_5m: Optional[List[Dict]],
    cached_30m: Optional[List[Dict]],
    cached_1h: Optional[List[Dict]],
) -> bool:
    """Determine if persistent cache is deep enough to skip a full seed."""
    has_enough_5m = bool(cached_5m and len(cached_5m) >= int(FULL_SEED_LIMIT_5M * 0.5))
    has_enough_30m = bool(cached_30m and len(cached_30m) >= int(FULL_SEED_LIMIT_30M * 0.5))
    has_enough_1h = bool(cached_1h and len(cached_1h) >= int(FULL_SEED_LIMIT_1H * 0.5))

    if symbol in _30M_DIRECT_SYMBOLS:
        return has_enough_5m and (has_enough_30m or has_enough_1h)

    return has_enough_5m and has_enough_1h


async def _pump_cycle():
    """One pump cycle: fetch what's due, rebuild derived data."""
    now_ts = datetime.now(timezone.utc).timestamp()
    allow_upstream_market_fetch = get_market_data_source() == "hybrid"
    allow_upstream_direct_30m_fetch = False

    for symbol in TRACKED_SYMBOLS:
        seed_key = symbol
        is_seeded = bool(_initial_seed_done.get(seed_key))

        is_hybrid = get_market_data_source() == "hybrid"

        # ── Price (every 5s) ──
        if allow_upstream_market_fetch and _should_fetch(f"price:{symbol}", PRICE_INTERVAL):
            # In hybrid mode, skip upstream poll when MT5 has pushed a fresh price
            # recently — prevents stale upstream data from overwriting live MT5 quotes.
            if is_hybrid and _mt5_price_is_fresh(symbol):
                _mark_fetched(f"price:{symbol}")
                logger.debug("[DataHub] %s price: MT5 fresh — skipping upstream poll", symbol)
            else:
                price = await _fetch_price_from_api(symbol)
                if price is not None:
                    with _lock:
                        _prices[symbol] = {"price": price, "timestamp": now_ts, "source": "upstream_poll"}
                    _mark_fetched(f"price:{symbol}")
                    try:
                        from services.ws_manager import manager
                        await manager.broadcast(symbol, {
                            "type": "price_update",
                            "symbol": symbol,
                            "price": price,
                            "timestamp": now_ts,
                        })
                    except Exception as e:
                        logger.warning(f"[DataHub] Price broadcast failed for {symbol}: {e}")

        # ── 5m candles (every 5min) ──
        if allow_upstream_market_fetch and _should_fetch(f"5m:{symbol}", CANDLE_5M_INTERVAL):
            # In hybrid mode, skip upstream if MT5 has been actively feeding 5m bars.
            if is_hybrid and _mt5_candles_are_fresh(symbol, "5m"):
                _mark_fetched(f"5m:{symbol}")
                logger.debug("[DataHub] %s 5m: MT5 fresh — skipping upstream candle fetch", symbol)
            else:
                is_seed = not is_seeded

                if symbol in _1M_ONLY_SYMBOLS:
                    raw_limit = (FULL_SEED_LIMIT_5M * 5) if is_seed else (DELTA_LIMIT_5M * 5)
                    raw_1m = await _fetch_candles_from_api(symbol, "1m", limit=raw_limit)
                    candles = _resample(raw_1m, 5, base_ms=60_000) if raw_1m else []
                    logger.info(f"[DataHub] {symbol}: fetched {len(raw_1m)} 1m → resampled to {len(candles)} 5m candles")
                else:
                    fetch_limit = FULL_SEED_LIMIT_5M if is_seed else DELTA_LIMIT_5M
                    candles = await _fetch_candles_from_api(symbol, "5m", limit=fetch_limit)

                if candles:
                    with _lock:
                        existing = (_candles_5m.get(symbol) or {}).get("candles", [])
                        merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_5M, interval_ms=300_000)
                        _candles_5m[symbol] = {"candles": merged, "timestamp": now_ts, "source": "upstream_poll"}
                        _rebuild_derived(symbol)
                    _mark_fetched(f"5m:{symbol}")
                    _persist_async(symbol, "5m", merged if is_seed else candles)
                    await _fire_candle_close_events(symbol, "5m", merged)
                    d15 = (_candles_15m.get(symbol) or {}).get("candles", [])
                    if d15:
                        await _fire_candle_close_events(symbol, "15m", d15)
                    d30 = (_candles_30m.get(symbol) or {}).get("candles", [])
                    if d30:
                        await _fire_candle_close_events(symbol, "30m", d30)

        # ── 30m candles (XAUUSD only — direct upstream only in pure upstream mode) ──
        if allow_upstream_direct_30m_fetch and symbol in _30M_DIRECT_SYMBOLS and _should_fetch(f"30m:{symbol}", CANDLE_30M_INTERVAL):
            is_seed = not is_seeded
            fetch_limit = FULL_SEED_LIMIT_30M if is_seed else DELTA_LIMIT_30M
            candles = await _fetch_candles_from_api(symbol, "30m", limit=fetch_limit)
            if candles:
                with _lock:
                    existing = (_candles_30m.get(symbol) or {}).get("candles", [])
                    merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_30M, interval_ms=1_800_000)
                    _candles_30m[symbol] = {"candles": merged, "timestamp": now_ts, "source": "upstream_poll"}
                    _rebuild_derived(symbol)
                _mark_fetched(f"30m:{symbol}")
                _persist_async(symbol, "30m", merged if is_seed else candles)
                logger.info(f"[DataHub] {symbol}: fetched {len(candles)} 30m candles → 1h={len(_candles_1h.get(symbol, {}).get('candles', []))}, 4h={len(_candles_4h.get(symbol, {}).get('candles', []))}")
                await _fire_candle_close_events(symbol, "30m", merged)
                d1h = (_candles_1h.get(symbol) or {}).get("candles", [])
                if d1h:
                    await _fire_candle_close_events(symbol, "1h", d1h)
                d4h = (_candles_4h.get(symbol) or {}).get("candles", [])
                if d4h:
                    await _fire_candle_close_events(symbol, "4h", d4h)

        # ── 1h candles (every 5min) ──
        if allow_upstream_market_fetch and _should_fetch(f"1h:{symbol}", CANDLE_1H_INTERVAL):
            is_seed = not is_seeded

            if symbol in _30M_DIRECT_SYMBOLS:
                _mark_fetched(f"1h:{symbol}")
            else:
                # In hybrid mode, skip upstream if MT5 has been feeding 1h bars.
                if is_hybrid and _mt5_candles_are_fresh(symbol, "1h"):
                    _mark_fetched(f"1h:{symbol}")
                    logger.debug("[DataHub] %s 1h: MT5 fresh — skipping upstream candle fetch", symbol)
                else:
                    fetch_limit = FULL_SEED_LIMIT_1H if is_seed else DELTA_LIMIT_1H
                    candles = await _fetch_candles_from_api(symbol, "1h", limit=fetch_limit)
                    if candles:
                        with _lock:
                            existing = (_candles_1h.get(symbol) or {}).get("candles", [])
                            merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_1H, interval_ms=3_600_000)
                            _candles_1h[symbol] = {"candles": merged, "timestamp": now_ts, "source": "upstream_poll"}
                            _rebuild_derived(symbol)
                        _mark_fetched(f"1h:{symbol}")
                        _persist_async(symbol, "1h", merged if is_seed else candles)
                        await _fire_candle_close_events(symbol, "1h", merged)
                        d4h = (_candles_4h.get(symbol) or {}).get("candles", [])
                        if d4h:
                            await _fire_candle_close_events(symbol, "4h", d4h)

        # ── EOD candles (every 30min) ──
        if allow_upstream_market_fetch and _should_fetch(f"eod:{symbol}", CANDLE_EOD_INTERVAL):
            is_seed = not is_seeded
            fetch_limit = FULL_SEED_LIMIT_EOD if is_seed else DELTA_LIMIT_EOD
            candles = await _fetch_eod_from_api(symbol, limit=fetch_limit)
            if candles:
                with _lock:
                    existing = (_candles_eod.get(symbol) or {}).get("candles", [])
                    merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_EOD)
                    _candles_eod[symbol] = {"candles": merged, "timestamp": now_ts, "source": "upstream_poll"}
                _mark_fetched(f"eod:{symbol}")
                _persist_async(symbol, "eod", merged if is_seed else candles)

        if not is_seeded and _has_required_seed_data(symbol):
            has_5m = len((_candles_5m.get(symbol) or {}).get("candles", []))
            has_30m = len((_candles_30m.get(symbol) or {}).get("candles", []))
            has_1h = len((_candles_1h.get(symbol) or {}).get("candles", []))
            _initial_seed_done[seed_key] = True
            logger.info(
                f"[DataHub] {symbol} seeded with intraday depth "
                f"(5m={has_5m}, 30m={has_30m}, 1h={has_1h})"
            )

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
    
    now_ts = datetime.now(timezone.utc).timestamp()
    loaded_any = False
    
    for symbol in TRACKED_SYMBOLS:
        # ── 5m candles ──────────────────────────────────────────────────────────
        cached_5m_raw = load_candles(symbol, "5m", limit=FULL_SEED_LIMIT_5M)
        cached_5m: Optional[List[Dict]] = None
        if cached_5m_raw:
            age_5m = _get_latest_candle_age_hours(cached_5m_raw)
            if age_5m is not None and age_5m > MAX_CACHE_AGE_HOURS:
                logger.warning(
                    "[DataHub] %s 5m cache is %.1fh old (>%dh) — skipping stale cache, full re-seed will run",
                    symbol, age_5m, MAX_CACHE_AGE_HOURS,
                )
            else:
                cached_5m = cached_5m_raw
                with _lock:
                    _candles_5m[symbol] = {"candles": cached_5m, "timestamp": now_ts, "source": "persistent_cache"}
                    _rebuild_derived(symbol)
                loaded_any = True
                logger.info(f"[DataHub] Loaded {len(cached_5m)} cached 5m candles for {symbol} (age={age_5m}h)")

        # ── 30m candles (XAUUSD: fetched directly from upstream only in upstream mode) ──
        # In mt5_redis/hybrid mode, XAUUSD 30m is derived from 5m - skip loading stale cache
        cached_30m: Optional[List[Dict]] = None
        if symbol not in _30M_DIRECT_SYMBOLS:
            cached_30m_raw = load_candles(symbol, "30m", limit=FULL_SEED_LIMIT_30M)
            if cached_30m_raw:
                age_30m = _get_latest_candle_age_hours(cached_30m_raw)
                if age_30m is not None and age_30m > MAX_CACHE_AGE_HOURS:
                    logger.warning(
                        "[DataHub] %s 30m cache is %.1fh old (>%dh) — skipping stale cache",
                        symbol, age_30m, MAX_CACHE_AGE_HOURS,
                    )
                else:
                    cached_30m = cached_30m_raw
                    with _lock:
                        _candles_30m[symbol] = {"candles": cached_30m, "timestamp": now_ts, "source": "persistent_cache"}
                        _rebuild_derived(symbol)
                    loaded_any = True
                    logger.info(f"[DataHub] Loaded {len(cached_30m)} cached 30m candles for {symbol}")
        else:
            logger.info(f"[DataHub] Skipping 30m cache load for {symbol} (derived from 5m in {get_market_data_source()} mode)")

        # ── 1h candles ──────────────────────────────────────────────────────────
        cached_1h: Optional[List[Dict]] = None
        if symbol not in _30M_DIRECT_SYMBOLS:
            cached_1h_raw = load_candles(symbol, "1h", limit=FULL_SEED_LIMIT_1H)
            if cached_1h_raw:
                age_1h = _get_latest_candle_age_hours(cached_1h_raw)
                if age_1h is not None and age_1h > MAX_CACHE_AGE_HOURS:
                    logger.warning(
                        "[DataHub] %s 1h cache is %.1fh old (>%dh) — skipping stale cache",
                        symbol, age_1h, MAX_CACHE_AGE_HOURS,
                    )
                else:
                    cached_1h = cached_1h_raw
                    with _lock:
                        _candles_1h[symbol] = {"candles": cached_1h, "timestamp": now_ts, "source": "persistent_cache"}
                        _rebuild_derived(symbol)
                    loaded_any = True
                    logger.info(f"[DataHub] Loaded {len(cached_1h)} cached 1h candles for {symbol}")
        else:
            logger.info(f"[DataHub] Skipping 1h cache load for {symbol} (derived from 30m in {get_market_data_source()} mode)")

        # ── EOD candles ──────────────────────────────────────────────────────────
        cached_eod_raw = load_candles(symbol, "eod", limit=FULL_SEED_LIMIT_EOD)
        cached_eod: Optional[List[Dict]] = None
        if cached_eod_raw:
            age_eod = _get_latest_candle_age_hours(cached_eod_raw)
            # EOD data is fine up to 7 days old (weekly gap / market holidays)
            max_eod_age = max(MAX_CACHE_AGE_HOURS, 168)
            if age_eod is not None and age_eod > max_eod_age:
                logger.warning(
                    "[DataHub] %s EOD cache is %.1fh old (>%dh) — skipping stale cache",
                    symbol, age_eod, max_eod_age,
                )
            else:
                cached_eod = cached_eod_raw
                with _lock:
                    _candles_eod[symbol] = {"candles": cached_eod, "timestamp": now_ts, "source": "persistent_cache"}
                loaded_any = True
                logger.info(f"[DataHub] Loaded {len(cached_eod)} cached EOD candles for {symbol}")
        
        # Check sufficiency per-symbol using required caches (not loose OR logic).
        # This prevents symbols from being marked "seeded" when 1h history is still thin.
        is_enough = _has_sufficient_cached_history(symbol, cached_5m, cached_30m, cached_1h)

        if is_enough:
            _initial_seed_done[symbol] = True
            logger.info(
                f"[DataHub] Cache sufficient for {symbol} "
                f"(5m={len(cached_5m or [])}, 30m={len(cached_30m or [])}, 1h={len(cached_1h or [])})"
            )
        else:
            _initial_seed_done[symbol] = False
            logger.info(
                f"[DataHub] Cache insufficient for {symbol} "
                f"(5m={len(cached_5m or [])}, 30m={len(cached_30m or [])}, 1h={len(cached_1h or [])}) "
                f"→ full seed will run"
            )
    
    # Final rebuild for symbols with derived timeframes (especially XAUUSD in mt5_redis/hybrid)
    if get_market_data_source() in {"mt5_redis", "hybrid"}:
        for symbol in TRACKED_SYMBOLS:
            with _lock:
                _rebuild_derived(symbol)
            logger.info(f"[DataHub] Final derived rebuild completed for {symbol}")
    
    if loaded_any:
        if get_market_data_source() == "mt5_redis":
            logger.info("[DataHub] Persistent cache loaded — waiting for MT5 Redis live updates")
        else:
            logger.info("[DataHub] Persistent cache loaded — will only fetch delta from upstream")
    else:
        if get_market_data_source() == "mt5_redis":
            logger.info("[DataHub] No persistent cache found — MT5 Redis must seed live candles")
        else:
            logger.info("[DataHub] No persistent cache found — will do full seed from upstream")


async def start_data_hub():
    """Start the DataHub background pump."""
    global _hub_running
    if _hub_running:
        logger.warning("DataHub already running")
        return
    
    _hub_running = True
    logger.info("DataHub started - centralized market data pump (%s)", get_market_data_source())
    
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
            _candles_1m.pop(symbol, None)
            _candles_5m.pop(symbol, None)
            _candles_20m.pop(symbol, None)
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
    symbol = _canonical_symbol(symbol)
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
    
    Supported timeframes: 1m, 5m, 15m, 20m, 30m, 1h, 4h, 1d/eod
    Also accepts: M1, M5, M15, M20, M30, H1, H4, D1
    """
    symbol = _canonical_symbol(symbol)
    tf, store = _get_store_for_timeframe(timeframe)
    if store is None:
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
    
    # Filter out completely invalid candles (all OHLC = 0) but keep zero-volume candles
    # Zero-volume candles are valid (e.g., low-liquidity periods, weekends for forex)
    # Removing them causes large data loss and limits visible history
    filtered = [
        c for c in data
        if not (c.get("open", 0) == 0 and c.get("high", 0) == 0 and c.get("low", 0) == 0 and c.get("close", 0) == 0)
    ]
    
    # If filtering removes everything, return original
    if not filtered and data:
        return data[-limit:]
    
    return filtered[-limit:]


def build_subminute_candles(
    symbol: str,
    bar_seconds: int = 15,
    limit: int = 600,
    max_gap_bars: int = 4,
    max_staleness_seconds: float = 90.0,
) -> List[Dict]:
    """Synthesize sub-minute OHLC bars from the live tick buffer.

    The MT5 tick stream is real-time but only the latest tick is kept in
    ``_prices``; ``_tick_buffer`` retains the recent tick *series* so we can
    resample below the 1m/5m floor for the rhythm detector.

    Gap handling: empty buckets are forward-filled with the previous close
    (flat bar, volume 0) for short gaps; a gap longer than ``max_gap_bars``
    truncates the series and we keep only the most recent contiguous segment
    (so a weekend / session close does not become one giant flat run).

    Returns at most ``limit`` bars in the same shape as ``get_candles`` (ms
    timestamp, OHLCV). Empty list if the buffer is missing, stale, or too thin.
    """
    symbol = _canonical_symbol(symbol)
    if bar_seconds <= 0:
        return []

    with _lock:
        buf = _tick_buffer.get(symbol)
        ticks: List[Tuple[float, float]] = list(buf) if buf else []

    if len(ticks) < 2:
        return []

    now = datetime.now(timezone.utc).timestamp()
    if now - ticks[-1][0] > max_staleness_seconds:
        return []   # tick flow has dried up (market closed / bridge down) — honest no-data

    # Bucket ticks into fixed sub-minute windows keyed by floor(ts / bar_seconds).
    buckets: Dict[int, Dict[str, float]] = {}
    for ts, price in ticks:
        if price <= 0:
            continue
        key = int(ts // bar_seconds)
        b = buckets.get(key)
        if b is None:
            buckets[key] = {"open": price, "high": price, "low": price, "close": price, "volume": 1.0}
        else:
            b["high"] = max(b["high"], price)
            b["low"] = min(b["low"], price)
            b["close"] = price
            b["volume"] += 1.0

    if not buckets:
        return []

    first_key, last_key = min(buckets), max(buckets)
    candles: List[Dict] = []
    prev_close: Optional[float] = None
    gap_run = 0
    for key in range(first_key, last_key + 1):
        b = buckets.get(key)
        if b is None:
            gap_run += 1
            if gap_run > max_gap_bars or prev_close is None:
                # Long gap — discard everything before it; restart the contiguous run.
                candles = []
                continue
            candles.append({
                "timestamp": key * bar_seconds * 1000,
                "open": prev_close, "high": prev_close,
                "low": prev_close, "close": prev_close, "volume": 0.0,
            })
            continue
        gap_run = 0
        candles.append({
            "timestamp": key * bar_seconds * 1000,
            "open": b["open"], "high": b["high"],
            "low": b["low"], "close": b["close"], "volume": b["volume"],
        })
        prev_close = b["close"]

    return candles[-limit:]


def get_macro() -> Dict[str, Any]:
    """Get macro context (DXY, VIX, US10Y, EURUSD, USDTRY).

    Sourced from the yfinance-backed macro_data_service snapshot. Falls back to
    any locally cached values if the snapshot is not ready yet.
    """
    try:
        from services import macro_data_service
        macro = macro_data_service.get_macro_dict()
        if macro and any(v.get("price") for v in macro.values()):
            return macro
    except Exception as exc:
        logger.debug("[DataHub] macro snapshot unavailable: %s", exc)
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
                    hours_old = (datetime.now(timezone.utc).timestamp() - latest_ts/1000) / 3600
                else:
                    # ISO date string
                    try:
                        dt = datetime.fromisoformat(str(latest_ts).replace('Z', '+00:00'))
                        hours_old = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
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
                "1m": _get_volume_stats(s, _candles_1m),
                "5m": _get_volume_stats(s, _candles_5m),
                "20m": _get_volume_stats(s, _candles_20m),
                "15m": _get_volume_stats(s, _candles_15m),
                "30m": _get_volume_stats(s, _candles_30m),
                "1h": _get_volume_stats(s, _candles_1h),
                "4h": _get_volume_stats(s, _candles_4h),
                "eod": _get_volume_stats(s, _candles_eod),
            }
        
        status = {
            "running": _hub_running,
            "market_data_source": get_market_data_source(),
            "symbols": TRACKED_SYMBOLS,
            "prices": {s: _prices.get(s, {}).get("price") for s in TRACKED_SYMBOLS},
            "price_sources": {s: _prices.get(s, {}).get("source") for s in TRACKED_SYMBOLS},
            "price_staleness": price_staleness,
            "candles_1m": {s: len(_candles_1m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_5m": {s: len(_candles_5m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_20m": {s: len(_candles_20m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_15m": {s: len(_candles_15m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_30m": {s: len(_candles_30m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_1h": {s: len(_candles_1h.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_4h": {s: len(_candles_4h.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_eod": {s: len(_candles_eod.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candle_sources": {
                s: {
                    "1m": _candles_1m.get(s, {}).get("source"),
                    "5m": _candles_5m.get(s, {}).get("source"),
                    "20m": _candles_20m.get(s, {}).get("source"),
                    "15m": _candles_15m.get(s, {}).get("source"),
                    "30m": _candles_30m.get(s, {}).get("source"),
                    "1h": _candles_1h.get(s, {}).get("source"),
                    "4h": _candles_4h.get(s, {}).get("source"),
                    "eod": _candles_eod.get(s, {}).get("source"),
                }
                for s in TRACKED_SYMBOLS
            },
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


def get_flow_check(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    selected_symbols = symbols or TRACKED_SYMBOLS
    checked_at = datetime.now(timezone.utc).isoformat()
    symbol_reports: Dict[str, Any] = {}

    for symbol in selected_symbols:
        canonical_symbol = _canonical_symbol(symbol)
        price = get_price(symbol)
        timeframe_reports: Dict[str, Any] = {}

        for timeframe in ("5m", "15m", "20m", "30m", "1h", "4h", "eod"):
            _, store = _get_store_for_timeframe(timeframe)
            candles = get_candles(symbol, timeframe, limit=3)
            latest = None
            if candles:
                latest = candles[-1].get("timestamp") or candles[-1].get("date")
            entry = (store or {}).get(canonical_symbol, {}) if store else {}
            timeframe_reports[timeframe] = {
                "available": bool(candles),
                "count": len(candles),
                "latest": latest,
                "source": entry.get("source") or "datahub_cache",
                "cache_age_seconds": _entry_age_seconds(entry),
            }

        intraday_ready = timeframe_reports["5m"]["available"] and (
            timeframe_reports["1h"]["available"] or timeframe_reports["30m"]["available"]
        )
        analysis_ready = intraday_ready and timeframe_reports["eod"]["available"] and price is not None

        symbol_reports[symbol] = {
            "price_available": price is not None,
            "price_source": _prices.get(canonical_symbol, {}).get("source") or "datahub_cache",
            "price_age_seconds": _entry_age_seconds(_prices.get(canonical_symbol, {})),
            "timeframes": timeframe_reports,
            "intraday_ready": intraday_ready,
            "analysis_ready": analysis_ready,
        }

    ok = all(report["analysis_ready"] for report in symbol_reports.values()) if symbol_reports else False

    return {
        "ok": ok,
        "checked_at": checked_at,
        "running": _hub_running,
        "market_data_source": get_market_data_source(),
        "symbols": symbol_reports,
    }


async def ingest_live_price(
    symbol: str,
    price: float,
    timestamp: Any = None,
    bid: Optional[float] = None,
    ask: Optional[float] = None,
    source: str = "mt5_redis",
) -> bool:
    canonical_symbol = _canonical_symbol(symbol)
    if canonical_symbol not in TRACKED_SYMBOLS and canonical_symbol not in REFERENCE_SYMBOLS:
        logger.warning("[DataHub] Ignoring live price for untracked symbol %s", symbol)
        return False

    ts_seconds = _coerce_epoch_seconds(timestamp)
    payload: Dict[str, Any] = {
        "price": float(price),
        "timestamp": ts_seconds,
        "source": source,
    }
    if bid is not None:
        payload["bid"] = float(bid)
    if ask is not None:
        payload["ask"] = float(ask)

    with _lock:
        existing = _prices.get(canonical_symbol, {})
        existing_ts = _coerce_epoch_seconds(existing.get("timestamp")) if existing else 0.0
        if existing_ts and ts_seconds + 1 < existing_ts:
            return False
        _prices[canonical_symbol] = payload

        buf = _tick_buffer.get(canonical_symbol)
        if buf is None:
            buf = deque(maxlen=_TICK_BUFFER_MAXLEN)
            _tick_buffer[canonical_symbol] = buf
        buf.append((ts_seconds, float(price)))

    _last_fetch[f"price:{canonical_symbol}"] = time.time()

    try:
        from services.ws_manager import manager
        await manager.broadcast(canonical_symbol, {
            "type": "price_update",
            "symbol": canonical_symbol,
            "price": payload["price"],
            "timestamp": ts_seconds,
            "source": source,
        })
    except Exception as e:
        logger.debug("[DataHub] Live price broadcast skipped for %s: %s", canonical_symbol, e)

    return True


def _normalize_ingested_candle(candle: Dict[str, Any], timeframe: str) -> Optional[Dict[str, Any]]:
    if not candle:
        return None

    normalized = {
        "open": float(candle.get("open", 0) or 0),
        "high": float(candle.get("high", 0) or 0),
        "low": float(candle.get("low", 0) or 0),
        "close": float(candle.get("close", 0) or 0),
        "volume": float(candle.get("volume", 0) or 0),
    }
    timestamp = candle.get("timestamp") or candle.get("time") or candle.get("date")

    if timeframe == "eod":
        ts_seconds = _coerce_epoch_seconds(timestamp)
        normalized["timestamp"] = int(ts_seconds * 1000)
        normalized["date"] = datetime.fromtimestamp(ts_seconds, tz=timezone.utc).date().isoformat()
    else:
        ts_ms = _coerce_timestamp_ms(timestamp)
        interval_ms = _tf_interval_ms(timeframe)
        if interval_ms:
            # Broker-time guard: MT5 bridge bars can arrive stamped in broker
            # time (UTC+2/+3) before the offset detector locks on, landing
            # hours in the future. Whole-hour offsets survive sub-hour bucket
            # alignment, so correct them deterministically here.
            now_ms = int(time.time() * 1000)
            if ts_ms > now_ms + interval_ms:
                offset_h = round((ts_ms - now_ms) / 3_600_000)
                if 1 <= offset_h <= 12:
                    ts_ms -= offset_h * 3_600_000
            # Tick-pollution guard: reject bars not on a clock-bucket boundary
            # (tick snapshots carry arbitrary second offsets like :48:23).
            if not _is_bucket_aligned(ts_ms, interval_ms):
                return None
            if ts_ms > now_ms:
                return None  # still-forming bucket — closed-bar stores only
        normalized["timestamp"] = ts_ms

    if all(normalized[key] == 0 for key in ("open", "high", "low", "close")):
        return None
    return normalized


async def ingest_candles(
    symbol: str,
    timeframe: str,
    candles: List[Dict[str, Any]],
    source: str = "mt5_redis",
) -> int:
    canonical_symbol = _canonical_symbol(symbol)
    tf, store = _get_store_for_timeframe(timeframe)
    if canonical_symbol not in TRACKED_SYMBOLS and canonical_symbol not in REFERENCE_SYMBOLS:
        logger.warning("[DataHub] Ignoring candles for untracked symbol %s", symbol)
        return 0
    # 15m and 4h are derived-only — never ingested directly
    if store is None or tf in {"15m", "4h", "20m"}:
        logger.debug("[DataHub] Derived-only timeframe %s skipped for %s", timeframe, canonical_symbol)
        return 0

    normalized_candles = [
        normalized for normalized in (_normalize_ingested_candle(candle, tf) for candle in candles or []) if normalized
    ]
    if not normalized_candles:
        return 0

    # 1m raw capacity: FULL_SEED_LIMIT_5M × 5 bars so we can always resample to full 5m depth
    limit_map = {
        "1m": FULL_SEED_LIMIT_5M * 5,
        "5m": FULL_SEED_LIMIT_5M,
        "30m": FULL_SEED_LIMIT_30M,
        "1h": FULL_SEED_LIMIT_1H,
        "eod": FULL_SEED_LIMIT_EOD,
    }
    candle_limit = limit_map.get(tf, FULL_SEED_LIMIT_5M)  # safe fallback — never KeyError
    now_ts = time.time()

    with _lock:
        existing = (store.get(canonical_symbol) or {}).get("candles", [])
        merged = _merge_candles(existing, normalized_candles, candle_limit, interval_ms=_tf_interval_ms(tf))
        store[canonical_symbol] = {"candles": merged, "timestamp": now_ts, "source": source}

        if tf == "1m":
            # For symbols that use 1m as primary (XAUUSD), cascade: 1m → 5m → derived TFs
            if canonical_symbol in _1M_ONLY_SYMBOLS:
                resampled_5m = _resample(merged, 5, base_ms=60_000)
                if resampled_5m:
                    existing_5m = (_candles_5m.get(canonical_symbol) or {}).get("candles", [])
                    merged_5m = _merge_candles(existing_5m, resampled_5m, FULL_SEED_LIMIT_5M, interval_ms=300_000)
                    _candles_5m[canonical_symbol] = {
                        "candles": merged_5m, "timestamp": now_ts, "source": f"{source}_1m_resampled"
                    }
                    _rebuild_derived(canonical_symbol)
                    logger.debug(
                        "[DataHub] %s: ingested %d 1m bars → resampled to %d 5m candles",
                        canonical_symbol, len(merged), len(resampled_5m),
                    )
        elif tf in {"5m", "30m", "1h"}:
            _rebuild_derived(canonical_symbol)

    _last_fetch[f"{tf}:{canonical_symbol}"] = now_ts
    _persist_async(canonical_symbol, tf, merged if len(normalized_candles) > 1 else normalized_candles)
    return len(normalized_candles)


async def ingest_candle(
    symbol: str,
    timeframe: str,
    candle: Dict[str, Any],
    source: str = "mt5_redis",
) -> bool:
    ingested = await ingest_candles(symbol, timeframe, [candle], source=source)
    return ingested > 0
