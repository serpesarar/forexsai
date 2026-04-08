"""
Centralized API Cache for EOD Historical Data
Prevents duplicate API calls across services
"""

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, Optional, Tuple
import hashlib
import json

class APICache:
    """
    Thread-safe centralized cache for all EOD API responses.
    
    TTL values (seconds):
    - real-time price: 30s (was 5s - too aggressive)
    - intraday candles: 60s 
    - EOD candles: 600s (10 min)
    - news: 300s (5 min)
    - economic events: 600s (10 min)
    """
    
    # Optimized for 100K daily EODHD API call limit
    # Each intraday request = 5 API calls, real-time = 1 API call
    TTL_REALTIME = 60      # Real-time price (1 API call each)
    TTL_INTRADAY = 300     # Intraday candles (5 API calls each)
    TTL_EOD = 1800         # Daily candles (5 API calls each)
    TTL_NEWS = 600         # News articles (5 API calls each)
    TTL_EVENTS = 1800      # Economic events
    TTL_FUNDAMENTALS = 3600  # Fundamentals (1 hour)
    
    def __init__(self):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "api_calls_saved": 0
        }
    
    def _make_key(self, endpoint: str, params: Dict) -> str:
        """Generate unique cache key from endpoint and params"""
        # Remove api_token from params for key generation
        clean_params = {k: v for k, v in sorted(params.items()) if k != "api_token"}
        param_str = json.dumps(clean_params, sort_keys=True)
        return hashlib.sha256(f"{endpoint}:{param_str}".encode()).hexdigest()[:32]
    
    def get(self, endpoint: str, params: Dict, ttl: int) -> Optional[Any]:
        """
        Get cached response if exists and not expired.
        Returns None if cache miss.
        """
        key = self._make_key(endpoint, params)
        now = datetime.now(timezone.utc).timestamp()
        
        with self._lock:
            cached = self._cache.get(key)
            if cached:
                ts, data = cached
                if now - ts < ttl:
                    self._stats["hits"] += 1
                    self._stats["api_calls_saved"] += 1
                    return data
            self._stats["misses"] += 1
        return None
    
    def set(self, endpoint: str, params: Dict, data: Any) -> None:
        """Store response in cache"""
        key = self._make_key(endpoint, params)
        now = datetime.now(timezone.utc).timestamp()
        
        with self._lock:
            self._cache[key] = (now, data)
    
    def get_stale(self, endpoint: str, params: Dict) -> Optional[Any]:
        """Get cached data even if expired (for fallback on API errors)"""
        key = self._make_key(endpoint, params)
        with self._lock:
            cached = self._cache.get(key)
            if cached:
                return cached[1]
        return None
    
    def clear(self) -> None:
        """Clear all cached data"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
            return {
                **self._stats,
                "total_requests": total,
                "hit_rate_percent": round(hit_rate, 1),
                "cache_size": len(self._cache)
            }
    
    def cleanup_expired(self, max_age: int = 3600) -> int:
        """Remove entries older than max_age seconds"""
        now = datetime.now(timezone.utc).timestamp()
        removed = 0
        
        with self._lock:
            keys_to_remove = []
            for key, (ts, _) in self._cache.items():
                if now - ts > max_age:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
                removed += 1
        
        return removed


# Global singleton instance
api_cache = APICache()


# Convenience functions for common endpoints
def cache_realtime_price(symbol: str) -> Optional[float]:
    """Check cache for real-time price"""
    return api_cache.get(
        "real-time",
        {"symbol": symbol},
        APICache.TTL_REALTIME
    )

def cache_intraday(symbol: str, interval: str) -> Optional[list]:
    """Check cache for intraday candles"""
    return api_cache.get(
        "intraday",
        {"symbol": symbol, "interval": interval},
        APICache.TTL_INTRADAY
    )

def cache_eod(symbol: str) -> Optional[list]:
    """Check cache for EOD candles"""
    return api_cache.get(
        "eod",
        {"symbol": symbol},
        APICache.TTL_EOD
    )

def cache_news(symbols: str) -> Optional[list]:
    """Check cache for news"""
    return api_cache.get(
        "news",
        {"symbols": symbols},
        APICache.TTL_NEWS
    )
