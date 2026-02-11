"""
Redis Client Service
=====================
Provides Redis connection for fast caching and pub/sub messaging.
Used by the broadcast system to:
1. Cache computed data (ML predictions, TA snapshots, etc.)
2. Serve cached data instantly to new WebSocket connections
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_redis_client = None
_redis_available = False


def get_redis_url() -> Optional[str]:
    """Get Redis URL from environment variables (Railway sets these automatically)."""
    # Railway Redis addon sets REDIS_URL automatically
    return (
        os.getenv("REDIS_URL")
        or os.getenv("REDIS_PRIVATE_URL")  # Railway internal network
        or os.getenv("CELERY_BROKER_URL")
    )


def get_redis() -> Optional[Any]:
    """Get or create Redis client singleton."""
    global _redis_client, _redis_available

    if _redis_client is not None:
        return _redis_client

    redis_url = get_redis_url()
    if not redis_url:
        logger.warning("No REDIS_URL found — broadcast cache disabled, using in-memory fallback")
        _redis_available = False
        return None

    try:
        import redis

        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        # Test connection
        _redis_client.ping()
        _redis_available = True
        logger.info(f"Redis connected: {redis_url[:30]}...")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis connection failed: {e} — using in-memory fallback")
        _redis_client = None
        _redis_available = False
        return None


def is_redis_available() -> bool:
    """Check if Redis is connected."""
    return _redis_available


# ─── In-memory fallback cache (used when Redis is not available) ───
_memory_cache: Dict[str, str] = {}
_memory_ttl: Dict[str, float] = {}

DEFAULT_TTL = 300  # 5 minutes


def cache_set(key: str, data: Any, ttl: int = DEFAULT_TTL) -> bool:
    """Set a value in cache (Redis or memory fallback)."""
    import time

    try:
        value = json.dumps(data, default=str, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize cache data for {key}: {e}")
        return False

    r = get_redis()
    if r:
        try:
            r.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed for {key}: {e}")

    # Fallback to memory
    _memory_cache[key] = value
    _memory_ttl[key] = time.time() + ttl
    return True


def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache (Redis or memory fallback)."""
    import time

    r = get_redis()
    if r:
        try:
            value = r.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis GET failed for {key}: {e}")

    # Fallback to memory
    if key in _memory_cache:
        if time.time() < _memory_ttl.get(key, 0):
            return json.loads(_memory_cache[key])
        else:
            del _memory_cache[key]
            _memory_ttl.pop(key, None)
    return None


def cache_get_raw(key: str) -> Optional[str]:
    """Get raw string value from cache."""
    import time

    r = get_redis()
    if r:
        try:
            return r.get(key)
        except Exception:
            pass

    if key in _memory_cache:
        if time.time() < _memory_ttl.get(key, 0):
            return _memory_cache[key]
    return None


def publish(channel: str, data: Any) -> int:
    """Publish message to Redis pub/sub channel. Returns number of subscribers."""
    r = get_redis()
    if not r:
        return 0
    try:
        value = json.dumps(data, default=str, ensure_ascii=False)
        return r.publish(channel, value)
    except Exception as e:
        logger.warning(f"Redis PUBLISH failed on {channel}: {e}")
        return 0


def get_redis_info() -> Dict[str, Any]:
    """Get Redis connection info for debugging."""
    return {
        "available": _redis_available,
        "url_configured": bool(get_redis_url()),
        "memory_cache_keys": len(_memory_cache),
    }
