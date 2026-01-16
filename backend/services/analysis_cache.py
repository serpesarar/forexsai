"""
In-Memory Analysis Cache
Simple TTL-based caching for trend analysis results
"""

from __future__ import annotations
from datetime import datetime
from threading import Lock
from typing import Any, Optional, Dict

_cache: Dict[str, tuple[float, Any]] = {}  # key -> (expiry_timestamp, value)
_cache_lock = Lock()


def get_cached(key: str) -> Optional[Any]:
    """Get cached value if not expired"""
    with _cache_lock:
        if key not in _cache:
            return None
        
        expiry, value = _cache[key]
        now = datetime.utcnow().timestamp()
        
        if now > expiry:
            del _cache[key]
            return None
        
        return value


def set_cached(key: str, value: Any, ttl: int = 300) -> None:
    """Set cache with TTL in seconds (default 5 minutes)"""
    with _cache_lock:
        expiry = datetime.utcnow().timestamp() + ttl
        _cache[key] = (expiry, value)


def invalidate_cache(key: str) -> None:
    """Remove specific key from cache"""
    with _cache_lock:
        if key in _cache:
            del _cache[key]


def invalidate_pattern(pattern: str) -> None:
    """Remove all keys matching pattern (simple prefix match)"""
    with _cache_lock:
        keys_to_delete = [k for k in _cache if k.startswith(pattern)]
        for k in keys_to_delete:
            del _cache[k]


def clear_all() -> None:
    """Clear entire cache"""
    with _cache_lock:
        _cache.clear()


def get_cache_stats() -> dict:
    """Get cache statistics"""
    with _cache_lock:
        now = datetime.utcnow().timestamp()
        total = len(_cache)
        expired = sum(1 for _, (expiry, _) in _cache.items() if now > expiry)
        return {
            "total_keys": total,
            "expired_keys": expired,
            "active_keys": total - expired
        }
