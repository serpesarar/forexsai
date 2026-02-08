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
  Price: 2 symbols × 1 call × 2/min × 60min × 24h = 5,760 calls
  5m:    2 symbols × 1 call × 12/hour × 24h = 576 calls (delta=24 candles)
  1h:    2 symbols × 1 call × 12/hour × 24h = 576 calls (delta=6 candles)
  EOD:   2 symbols × 1 call × 2/hour × 24h = 96 calls (delta=5 candles)
  TOTAL: ~7,000 / 100,000 limit (7% usage)

  First-time seed (one-time): ~20 extra calls for full history
  Subsequent days: only delta → 93% reduction vs original design
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional

import httpx
import numpy as np

from config import settings

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# TRACKED SYMBOLS
# ═══════════════════════════════════════════════════════════════
TRACKED_SYMBOLS = ["NDX.INDX", "XAUUSD"]

# ═══════════════════════════════════════════════════════════════
# FETCH INTERVALS (seconds)
# ═══════════════════════════════════════════════════════════════
PRICE_INTERVAL = 30       # Fetch live price every 30 seconds
CANDLE_5M_INTERVAL = 300  # Fetch 5m candles every 5 minutes
CANDLE_1H_INTERVAL = 300  # Fetch 1h candles every 5 minutes
CANDLE_EOD_INTERVAL = 1800  # Fetch EOD candles every 30 minutes
MACRO_INTERVAL = 300      # Fetch macro (DXY, VIX, USDTRY) every 5 minutes

# Macro symbols
MACRO_SYMBOLS = {
    "dxy": "DXY.INDX",
    "vix": "VIX.INDX",
    "usdtry": "USDTRY",
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
    if "." in s:
        return s
    if s.upper() == "XAUUSD":
        return "XAUUSD.FOREX"
    if len(s) == 6 and s.isalnum():
        return f"{s}.FOREX"
    return s


# ═══════════════════════════════════════════════════════════════
# EODHD API FETCHERS (only called by DataHub pump)
# ═══════════════════════════════════════════════════════════════
async def _fetch_price_from_api(symbol: str) -> Optional[float]:
    """Fetch real-time price from EODHD. Costs 1 API call."""
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
                for key in ("close", "price", "last", "value", "previousClose"):
                    if key in data and data[key] is not None:
                        try:
                            return float(data[key])
                        except (TypeError, ValueError):
                            continue
    except Exception as e:
        logger.debug(f"Price fetch failed for {symbol}: {e}")
    return None


async def _fetch_candles_from_api(symbol: str, interval: str, limit: int = 500) -> List[Dict]:
    """Fetch intraday candles from EODHD. Costs 5 API calls."""
    if not settings.eodhd_api_key:
        return []
    eod_symbol = _normalize_symbol(symbol)
    
    # Calculate how far back we need to go based on interval and limit
    # EODHD requires 'from' param for historical intraday data
    import math
    candles_per_day = {"5m": 78, "1h": 7, "1m": 390}.get(interval, 78)
    trading_days_needed = math.ceil(limit / max(candles_per_day, 1))
    # Add buffer for weekends/holidays (multiply by 1.6)
    calendar_days = max(int(trading_days_needed * 1.6) + 5, 7)
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
            return cleaned[-limit:]
    except Exception as e:
        logger.debug(f"Candle fetch failed for {symbol} {interval}: {e}")
    return []


async def _fetch_eod_from_api(symbol: str, limit: int = 300) -> List[Dict]:
    """Fetch EOD candles from EODHD. Costs 5 API calls."""
    if not settings.eodhd_api_key:
        return []
    eod_symbol = _normalize_symbol(symbol)
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
    """Rebuild 15m, 30m, 4h candles from raw 5m and 1h data."""
    now = datetime.utcnow().timestamp()
    
    # 15m = 5m × 3
    raw_5m = _candles_5m.get(symbol, {}).get("candles", [])
    if raw_5m:
        _candles_15m[symbol] = {"candles": _resample(raw_5m, 3), "timestamp": now}
        _candles_30m[symbol] = {"candles": _resample(raw_5m, 6), "timestamp": now}
    
    # 4h = 1h × 4
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
DELTA_LIMIT_5M = 24      # ~2 hours of 5m candles
DELTA_LIMIT_1H = 6        # ~6 hours of 1h candles
DELTA_LIMIT_EOD = 5       # ~5 days of EOD candles
FULL_SEED_LIMIT_5M = 500  # Full seed: ~41 hours
FULL_SEED_LIMIT_1H = 500  # Full seed: ~20 days
FULL_SEED_LIMIT_EOD = 100 # Full seed: ~100 days


def _persist_async(symbol: str, timeframe: str, candles: List[Dict]):
    """Persist candles to Supabase in background (non-blocking)."""
    try:
        from services.candle_cache_store import persist_candles
        persist_candles(symbol, timeframe, candles)
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
        
        # ── 5m candles (every 5min) ──
        if _should_fetch(f"5m:{symbol}", CANDLE_5M_INTERVAL):
            fetch_limit = FULL_SEED_LIMIT_5M if not is_seeded else DELTA_LIMIT_5M
            candles = await _fetch_candles_from_api(symbol, "5m", limit=fetch_limit)
            if candles:
                with _lock:
                    existing = (_candles_5m.get(symbol) or {}).get("candles", [])
                    merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_5M)
                    _candles_5m[symbol] = {"candles": merged, "timestamp": now_ts}
                    _rebuild_derived(symbol)
                _mark_fetched(f"5m:{symbol}")
                _persist_async(symbol, "5m", candles)
        
        # ── 1h candles (every 5min) ──
        if _should_fetch(f"1h:{symbol}", CANDLE_1H_INTERVAL):
            fetch_limit = FULL_SEED_LIMIT_1H if not is_seeded else DELTA_LIMIT_1H
            candles = await _fetch_candles_from_api(symbol, "1h", limit=fetch_limit)
            if candles:
                with _lock:
                    existing = (_candles_1h.get(symbol) or {}).get("candles", [])
                    merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_1H)
                    _candles_1h[symbol] = {"candles": merged, "timestamp": now_ts}
                    _rebuild_derived(symbol)
                _mark_fetched(f"1h:{symbol}")
                _persist_async(symbol, "1h", candles)
        
        # ── EOD candles (every 30min) ──
        if _should_fetch(f"eod:{symbol}", CANDLE_EOD_INTERVAL):
            fetch_limit = FULL_SEED_LIMIT_EOD if not is_seeded else DELTA_LIMIT_EOD
            candles = await _fetch_eod_from_api(symbol, limit=fetch_limit)
            if candles:
                with _lock:
                    existing = (_candles_eod.get(symbol) or {}).get("candles", [])
                    merged = _merge_candles(existing, candles, FULL_SEED_LIMIT_EOD)
                    _candles_eod[symbol] = {"candles": merged, "timestamp": now_ts}
                _mark_fetched(f"eod:{symbol}")
                _persist_async(symbol, "eod", candles)
        
        # Mark this symbol as seeded after first full cycle
        if not is_seeded:
            _initial_seed_done[seed_key] = True
    
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
        
        # If we loaded cached data, mark as seeded so pump only fetches delta
        if cached_5m or cached_1h or cached_eod:
            _initial_seed_done[symbol] = True
    
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
        _last_fetch[f"1h:{symbol}"] = 0
        _last_fetch[f"eod:{symbol}"] = 0
    _last_fetch["macro"] = 0
    
    while _hub_running:
        try:
            await _pump_cycle()
        except Exception as e:
            logger.error(f"DataHub pump error: {e}")
        await asyncio.sleep(1)  # Check every 1s, but fetches respect their intervals


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
    
    return data[-limit:] if data else []


def get_macro() -> Dict[str, Any]:
    """Get cached macro data (DXY, VIX, USDTRY)."""
    with _lock:
        return {k: {"symbol": v.get("symbol"), "price": v.get("price")} for k, v in _macro_data.items()}


def get_hub_status() -> Dict[str, Any]:
    """Get DataHub status for debugging."""
    with _lock:
        status = {
            "running": _hub_running,
            "symbols": TRACKED_SYMBOLS,
            "prices": {s: _prices.get(s, {}).get("price") for s in TRACKED_SYMBOLS},
            "candles_5m": {s: len(_candles_5m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_15m": {s: len(_candles_15m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_30m": {s: len(_candles_30m.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_1h": {s: len(_candles_1h.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_4h": {s: len(_candles_4h.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
            "candles_eod": {s: len(_candles_eod.get(s, {}).get("candles", [])) for s in TRACKED_SYMBOLS},
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
