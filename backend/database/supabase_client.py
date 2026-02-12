"""Supabase REST API client for database operations.
Uses httpx directly instead of supabase-py to avoid dependency conflicts.

Connection-pool-safe:
  - Single persistent httpx.Client (reuses TCP connections via keepalive)
  - max_connections=5 so we never exceed Supabase pooler limits (pool_size=20)
  - Retry with exponential backoff on transient errors
  - Short read timeout (15s) to free slots quickly
"""
from __future__ import annotations

import os
import time
import logging
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger(__name__)

_init_error: Optional[str] = None
_initialized: bool = False

# ── Retry config ──────────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_BASE_WAIT = 1.5          # seconds
RETRY_MAX_WAIT = 12.0          # seconds
RETRIABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504, 520, 522, 524}


def _retry_request(fn, label: str = "supabase"):
    """Execute *fn()* with exponential-backoff retry on transient failures."""
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = fn()
            if resp.status_code in RETRIABLE_STATUS_CODES and attempt < MAX_RETRIES:
                wait = min(RETRY_BASE_WAIT * (2 ** (attempt - 1)), RETRY_MAX_WAIT)
                logger.warning(f"[{label}] HTTP {resp.status_code}, retry {attempt}/{MAX_RETRIES} in {wait:.1f}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.PoolTimeout,
                httpx.ConnectError, httpx.RemoteProtocolError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                wait = min(RETRY_BASE_WAIT * (2 ** (attempt - 1)), RETRY_MAX_WAIT)
                logger.warning(f"[{label}] {type(exc).__name__}, retry {attempt}/{MAX_RETRIES} in {wait:.1f}s")
                time.sleep(wait)
            else:
                raise
        except httpx.HTTPStatusError:
            raise  # 4xx client errors — don't retry
    raise last_exc  # pragma: no cover


class SupabaseRestClient:
    """Supabase REST client with persistent connection pool."""

    def __init__(self, url: str, key: str):
        self.url = url.rstrip('/')
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        # Persistent client — reuses TCP connections (keepalive)
        # max_connections=5 keeps us well under the 20-slot Supabase pool
        self._http = httpx.Client(
            timeout=httpx.Timeout(connect=8.0, read=15.0, write=15.0, pool=10.0),
            limits=httpx.Limits(max_connections=5, max_keepalive_connections=3, keepalive_expiry=120),
            headers=self.headers,
        )

    @property
    def http(self) -> httpx.Client:
        """Return the persistent HTTP client, recreate if closed."""
        if self._http.is_closed:
            logger.info("Recreating closed httpx client")
            self._http = httpx.Client(
                timeout=httpx.Timeout(connect=8.0, read=15.0, write=15.0, pool=10.0),
                limits=httpx.Limits(max_connections=5, max_keepalive_connections=3, keepalive_expiry=120),
                headers=self.headers,
            )
        return self._http

    def table(self, table_name: str) -> "TableQuery":
        return TableQuery(self, table_name)


class TableQuery:
    """Query builder for Supabase tables — uses the shared persistent client."""

    def __init__(self, client: SupabaseRestClient, table_name: str):
        self.client = client
        self.table_name = table_name
        self.filters: List[str] = []
        self.order_by: Optional[str] = None
        self.limit_val: Optional[int] = None

    def select(self, columns: str = "*") -> "TableQuery":
        self._columns = columns
        return self

    def eq(self, column: str, value: Any) -> "TableQuery":
        self.filters.append(f"{column}=eq.{value}")
        return self

    def gte(self, column: str, value: Any) -> "TableQuery":
        self.filters.append(f"{column}=gte.{value}")
        return self

    def lte(self, column: str, value: Any) -> "TableQuery":
        self.filters.append(f"{column}=lte.{value}")
        return self

    def lt(self, column: str, value: Any) -> "TableQuery":
        self.filters.append(f"{column}=lt.{value}")
        return self

    def gt(self, column: str, value: Any) -> "TableQuery":
        self.filters.append(f"{column}=gt.{value}")
        return self

    def neq(self, column: str, value: Any) -> "TableQuery":
        self.filters.append(f"{column}=neq.{value}")
        return self

    def is_(self, column: str, value: Any) -> "TableQuery":
        self.filters.append(f"{column}=is.{value}")
        return self

    def order(self, column: str, desc: bool = False) -> "TableQuery":
        direction = "desc" if desc else "asc"
        self.order_by = f"{column}.{direction}"
        return self

    def limit(self, count: int) -> "TableQuery":
        self.limit_val = count
        return self

    def _build_url(self) -> str:
        url = f"{self.client.url}/rest/v1/{self.table_name}"
        params = []
        if hasattr(self, '_columns'):
            params.append(f"select={self._columns}")
        params.extend(self.filters)
        if self.order_by:
            params.append(f"order={self.order_by}")
        if self.limit_val:
            params.append(f"limit={self.limit_val}")
        if params:
            url += "?" + "&".join(params)
        return url

    def execute(self) -> Dict[str, Any]:
        try:
            resp = _retry_request(
                lambda: self.client.http.get(self._build_url()),
                label=f"SELECT {self.table_name}",
            )
            return {"data": resp.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase query error [{self.table_name}]: {e}")
            return {"data": None, "error": str(e)}

    def insert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.client.url}/rest/v1/{self.table_name}"
        try:
            resp = _retry_request(
                lambda: self.client.http.post(url, json=data),
                label=f"INSERT {self.table_name}",
            )
            return {"data": resp.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase insert error [{self.table_name}]: {e}")
            return {"data": None, "error": str(e)}

    def upsert(self, data, on_conflict: str = "") -> Dict[str, Any]:
        """Insert or update rows. data can be a dict (single) or list of dicts (bulk)."""
        url = f"{self.client.url}/rest/v1/{self.table_name}"
        if on_conflict:
            url += f"?on_conflict={on_conflict}"
        headers = {"Prefer": "return=representation,resolution=merge-duplicates"}
        payload = data if isinstance(data, list) else [data]
        try:
            resp = _retry_request(
                lambda: self.client.http.post(url, json=payload, headers=headers),
                label=f"UPSERT {self.table_name}",
            )
            return {"data": resp.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase upsert error [{self.table_name}]: {e}")
            return {"data": None, "error": str(e)}

    def update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            resp = _retry_request(
                lambda: self.client.http.patch(self._build_url(), json=data),
                label=f"UPDATE {self.table_name}",
            )
            return {"data": resp.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase update error [{self.table_name}]: {e}")
            return {"data": None, "error": str(e)}

    def delete(self) -> Dict[str, Any]:
        try:
            resp = _retry_request(
                lambda: self.client.http.delete(self._build_url()),
                label=f"DELETE {self.table_name}",
            )
            return {"data": resp.json() if resp.text else [], "error": None}
        except Exception as e:
            logger.error(f"Supabase delete error [{self.table_name}]: {e}")
            return {"data": None, "error": str(e)}


_client: Optional[SupabaseRestClient] = None


def get_supabase_client() -> Optional[SupabaseRestClient]:
    """
    Returns a Supabase REST client instance (singleton).
    Returns None if credentials are not configured.
    """
    global _client, _init_error, _initialized

    if _initialized:
        return _client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        _init_error = f"Missing env vars: SUPABASE_URL={'set' if url else 'not set'}, SUPABASE_KEY={'set' if key else 'not set'}"
        logger.warning(_init_error)
        _initialized = True
        return None

    try:
        _client = SupabaseRestClient(url, key)
        # No blocking test query at startup — avoids hanging when pool is
        # exhausted.  The retry mechanism handles transient failures on
        # first real use.
        logger.info("Supabase REST client created (pool: max_conn=5, keepalive=3). No blocking test.")
        _initialized = True
        return _client
    except Exception as e:
        _init_error = f"Failed to create Supabase client: {e}"
        logger.error(_init_error)
        _initialized = True
        return None


def get_init_error() -> Optional[str]:
    """Return the initialization error if any."""
    return _init_error


def is_db_available() -> bool:
    """Check if database is configured and available."""
    client = get_supabase_client()
    return client is not None
