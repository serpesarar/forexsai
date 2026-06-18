"""
Candle Cache Store - Persistent candle storage via Supabase
============================================================
Bridges DataHub (in-memory) ↔ Supabase (persistent).

Flow:
  1. On startup: Load historical candles from Supabase → DataHub memory
  2. On fetch:   upstream vendor API → DataHub memory → persist new candles to Supabase
  3. On restart:  Skip upstream vendor for historical data, only fetch latest delta

This reduces upstream vendor API usage by ~90% after the initial seed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from utils.safe_supabase import safe_get_data, safe_get_error
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_db():
    """Get Supabase client, returns None if unavailable."""
    try:
        from database.supabase_client import get_supabase_client
        return get_supabase_client()
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# PERSIST: Save candles from DataHub → Supabase
# ═══════════════════════════════════════════════════════════════

def persist_candles(symbol: str, timeframe: str, candles: List[Dict]) -> int:
    """
    Save candles to Supabase. Uses upsert to avoid duplicates.
    Returns number of candles persisted.
    """
    db = _get_db()
    if not db or not candles:
        return 0

    rows = []
    for c in candles:
        # Determine candle time from either timestamp (ms) or date string
        candle_time = None
        if c.get("timestamp") and c["timestamp"] > 0:
            candle_time = datetime.fromtimestamp(
                c["timestamp"] / 1000, tz=timezone.utc
            ).isoformat()
        elif c.get("date"):
            date_str = c["date"]
            # Handle both "2025-01-15" and "2025-01-15 09:30:00" formats
            if "T" not in date_str and " " not in date_str:
                date_str += "T00:00:00+00:00"
            candle_time = date_str

        if not candle_time:
            continue

        rows.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "candle_time": candle_time,
            "open": c.get("open", 0),
            "high": c.get("high", 0),
            "low": c.get("low", 0),
            "close": c.get("close", 0),
            "volume": c.get("volume", 0),
        })

    if not rows:
        return 0

    # Batch upsert in chunks of 500 to avoid payload limits
    persisted = 0
    CHUNK = 500
    for i in range(0, len(rows), CHUNK):
        chunk = rows[i:i + CHUNK]
        result = db.table("candle_cache").upsert(
            chunk, on_conflict="symbol,timeframe,candle_time"
        )
        if safe_get_error(result):
            logger.error(f"Persist candles error ({symbol}/{timeframe}): {result['error']}")
        else:
            persisted += len(chunk)

    # Update metadata
    if persisted > 0:
        _update_meta(db, symbol, timeframe, rows)

    logger.info(f"[CandleCache] Persisted {persisted}/{len(candles)} candles for {symbol}/{timeframe}")
    return persisted


def _update_meta(db, symbol: str, timeframe: str, rows: List[Dict]):
    """Update candle_cache_meta with latest info."""
    try:
        # Find the latest candle time
        latest = max(r["candle_time"] for r in rows)
        db.table("candle_cache_meta").upsert({
            "symbol": symbol,
            "timeframe": timeframe,
            "last_candle_time": latest,
            "candle_count": len(rows),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="symbol,timeframe")
    except Exception as e:
        logger.debug(f"Meta update failed: {e}")


# ═══════════════════════════════════════════════════════════════
# LOAD: Read candles from Supabase → DataHub
# ═══════════════════════════════════════════════════════════════

def load_candles(symbol: str, timeframe: str, limit: int = 500) -> List[Dict]:
    """
    Load cached candles from Supabase.
    Returns candles in DataHub format (sorted by time ascending).
    """
    db = _get_db()
    if not db:
        return []

    try:
        result = (
            db.table("candle_cache")
            .select("candle_time,open,high,low,close,volume")
            .eq("symbol", symbol)
            .eq("timeframe", timeframe)
            .order("candle_time", desc=True)
            .limit(limit)
            .execute()
        )

        if safe_get_error(result) or not safe_get_data(result):
            return []

        # Convert to DataHub format and reverse to ascending order
        candles = []
        for row in reversed(result["data"]):
            ct = row["candle_time"]
            # Parse candle_time to timestamp ms
            try:
                if isinstance(ct, str):
                    dt = datetime.fromisoformat(ct.replace("Z", "+00:00"))
                    ts = int(dt.timestamp() * 1000)
                else:
                    ts = 0
            except Exception:
                ts = 0

            candles.append({
                "timestamp": ts,
                "date": ct,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })

        logger.info(f"[CandleCache] Loaded {len(candles)} cached candles for {symbol}/{timeframe}")
        return candles

    except Exception as e:
        logger.error(f"Load candles error ({symbol}/{timeframe}): {e}")
        return []


def get_last_candle_time(symbol: str, timeframe: str) -> Optional[str]:
    """Get the timestamp of the most recent cached candle for a symbol/timeframe."""
    db = _get_db()
    if not db:
        return None

    try:
        result = (
            db.table("candle_cache_meta")
            .select("last_candle_time")
            .eq("symbol", symbol)
            .eq("timeframe", timeframe)
            .limit(1)
            .execute()
        )
        if safe_get_data(result) and len(result["data"]) > 0:
            return result["data"][0].get("last_candle_time")
    except Exception as e:
        logger.debug(f"Get last candle time error: {e}")
    return None


def purge_stale_candles(symbol: Optional[str] = None, max_age_hours: float = 96) -> Dict:
    """Delete cached candles older than `max_age_hours`.

    If `symbol` is None, purges ALL tracked symbols.
    Returns a dict with per-symbol/timeframe counts of deleted rows.
    """
    from datetime import timedelta
    db = _get_db()
    if not db:
        return {"available": False, "deleted": {}}

    cutoff_dt = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    cutoff_iso = cutoff_dt.isoformat()

    deleted: Dict = {}
    try:
        query = db.table("candle_cache").delete().lt("candle_time", cutoff_iso)
        if symbol:
            query = query.eq("symbol", symbol)
        result = query.execute()
        deleted["rows_deleted"] = len(result.data) if result.data else 0
        deleted["cutoff"] = cutoff_iso
        if symbol:
            deleted["symbol"] = symbol
        logger.info(
            "[CandleCache] Purged stale candles (symbol=%s, max_age_hours=%.1f, cutoff=%s, rows=%s)",
            symbol or "ALL", max_age_hours, cutoff_iso, deleted["rows_deleted"],
        )
    except Exception as e:
        logger.error(f"purge_stale_candles error: {e}")
        deleted["error"] = str(e)

    return {"available": True, "deleted": deleted}


def get_cache_stats() -> Dict:
    """Get cache statistics for monitoring."""
    db = _get_db()
    if not db:
        return {"available": False}

    try:
        result = db.table("candle_cache_meta").select("*").execute()
        if safe_get_data(result):
            stats = {}
            for row in result["data"]:
                key = f"{row['symbol']}/{row['timeframe']}"
                stats[key] = {
                    "count": row.get("candle_count", 0),
                    "last_candle": row.get("last_candle_time"),
                    "updated": row.get("updated_at"),
                }
            return {"available": True, "entries": stats}
    except Exception as e:
        logger.debug(f"Cache stats error: {e}")
    return {"available": True, "entries": {}}
