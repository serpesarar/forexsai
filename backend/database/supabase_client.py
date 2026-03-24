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
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import httpx

logger = logging.getLogger(__name__)

_init_error: Optional[str] = None
_initialized: bool = False


def _resolve_supabase_key() -> Optional[str]:
    return os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

# ── Retry config ──────────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_BASE_WAIT = 1.5          # seconds
RETRY_MAX_WAIT = 12.0          # seconds
RETRIABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504, 520, 522, 524}


def _retry_request(fn, label: str = "supabase", client: "SupabaseRestClient | None" = None):
    """Execute *fn()* with exponential-backoff retry on transient failures."""
    if client:
        client.record_request()
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = fn()
            if resp.status_code in RETRIABLE_STATUS_CODES and attempt < MAX_RETRIES:
                wait = min(RETRY_BASE_WAIT * (2 ** (attempt - 1)), RETRY_MAX_WAIT)
                logger.warning(f"[{label}] HTTP {resp.status_code}, retry {attempt}/{MAX_RETRIES} in {wait:.1f}s")
                if client:
                    client.record_retry()
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.PoolTimeout,
                httpx.ConnectError, httpx.RemoteProtocolError) as exc:
            last_exc = exc
            if client:
                client.record_retry()
            if attempt < MAX_RETRIES:
                wait = min(RETRY_BASE_WAIT * (2 ** (attempt - 1)), RETRY_MAX_WAIT)
                logger.warning(f"[{label}] {type(exc).__name__}, retry {attempt}/{MAX_RETRIES} in {wait:.1f}s")
                time.sleep(wait)
            else:
                if client:
                    client.record_error()
                raise
        except httpx.HTTPStatusError as exc:
            if client:
                client.record_error()
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code in {401, 403}:
                    client.mark_auth_failed(status_code)
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
        # ── Observability counters ──
        self._stats = {
            "total_requests": 0,
            "total_errors": 0,
            "total_retries": 0,
            "created_at": time.time(),
            "last_request_at": 0.0,
            "last_error_at": 0.0,
        }
        self._auth_failed = False
        self._auth_error_message: Optional[str] = None

    def record_request(self):
        self._stats["total_requests"] += 1
        self._stats["last_request_at"] = time.time()

    def record_error(self):
        self._stats["total_errors"] += 1
        self._stats["last_error_at"] = time.time()

    def record_retry(self):
        self._stats["total_retries"] += 1

    def mark_auth_failed(self, status_code: Optional[int] = None):
        if self._auth_failed:
            return
        self._auth_failed = True
        self._auth_error_message = (
            f"Supabase authentication failed with HTTP {status_code or 'unknown'}. "
            "Check SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY."
        )
        logger.error(self._auth_error_message)

    def get_auth_error(self) -> Optional[str]:
        return self._auth_error_message

    def is_auth_failed(self) -> bool:
        return self._auth_failed

    def get_stats(self) -> Dict[str, Any]:
        """Return connection pool stats for observability."""
        uptime = time.time() - self._stats["created_at"]
        pool = self._http.pool if hasattr(self._http, 'pool') else None
        return {
            "uptime_seconds": round(uptime, 1),
            "total_requests": self._stats["total_requests"],
            "total_errors": self._stats["total_errors"],
            "total_retries": self._stats["total_retries"],
            "error_rate_pct": round(
                (self._stats["total_errors"] / max(self._stats["total_requests"], 1)) * 100, 2
            ),
            "requests_per_minute": round(
                self._stats["total_requests"] / max(uptime / 60, 1), 1
            ),
            "pool_max_connections": 5,
            "pool_keepalive": 3,
            "client_closed": self._http.is_closed,
        }

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

    def rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a PostgreSQL function via Supabase RPC endpoint."""
        url = f"{self.url}/rest/v1/rpc/{function_name}"
        body = params or {}
        try:
            resp = _retry_request(
                lambda: self.http.post(url, json=body),
                label=f"RPC {function_name}",
                client=self,
            )
            return {"data": resp.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase RPC error [{function_name}]: {e}")
            return {"data": None, "error": str(e)}

    def close(self):
        """Gracefully close the HTTP client."""
        if not self._http.is_closed:
            self._http.close()
            logger.info("Supabase HTTP client closed gracefully.")

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

    def in_(self, column: str, values: Any) -> "TableQuery":
        serialized: List[str] = []
        for value in values or []:
            value_str = str(value)
            if any(ch in value_str for ch in [",", "(", ")", " "]):
                value_str = f"\"{value_str}\""
            serialized.append(value_str)
        self.filters.append(f"{column}=in.({','.join(serialized)})")
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

    def or_(self, expression: str) -> "TableQuery":
        raw_expression = str(expression or "").strip()
        if not raw_expression:
            return self
        if not raw_expression.startswith("("):
            raw_expression = f"({raw_expression})"
        self.filters.append(f"or={raw_expression}")
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
        params: List[tuple[str, Any]] = []
        if hasattr(self, '_columns'):
            params.append(("select", self._columns))
        for raw_filter in self.filters:
            if "=" not in raw_filter:
                continue
            key, value = raw_filter.split("=", 1)
            params.append((key, value))
        if self.order_by:
            params.append(("order", self.order_by))
        if self.limit_val:
            params.append(("limit", self.limit_val))
        if params:
            url += "?" + urlencode(params, doseq=True, safe="(),.*")
        return url

    def execute(self) -> Dict[str, Any]:
        if self.client.is_auth_failed():
            return {"data": None, "error": self.client.get_auth_error()}
        try:
            resp = _retry_request(
                lambda: self.client.http.get(self._build_url()),
                label=f"SELECT {self.table_name}",
                client=self.client,
            )
            return {"data": resp.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase query error [{self.table_name}]: {e}")
            return {"data": None, "error": str(e)}

    def insert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.client.url}/rest/v1/{self.table_name}"
        if self.client.is_auth_failed():
            return {"data": None, "error": self.client.get_auth_error()}
        try:
            resp = _retry_request(
                lambda: self.client.http.post(url, json=data),
                label=f"INSERT {self.table_name}",
                client=self.client,
            )
            return {"data": resp.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase insert error [{self.table_name}]: {e}")
            return {"data": None, "error": str(e)}

    def insert_ignore(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a row, returning {\"data\":None,\"duplicate\":True} on unique-constraint violation instead of raising."""
        url = f"{self.client.url}/rest/v1/{self.table_name}"
        headers = {"Prefer": "return=representation"}
        if self.client.is_auth_failed():
            return {"data": None, "error": self.client.get_auth_error(), "duplicate": False}
        try:
            resp = self.client.http.post(url, json=data, headers=headers)
            if resp.status_code in {401, 403}:
                self.client.record_error()
                self.client.mark_auth_failed(resp.status_code)
                return {"data": None, "error": self.client.get_auth_error(), "duplicate": False}
            if resp.status_code == 409 or (resp.status_code == 400 and "23505" in resp.text):
                logger.debug(f"insert_ignore: duplicate detected in {self.table_name}")
                return {"data": None, "error": None, "duplicate": True}
            resp.raise_for_status()
            return {"data": resp.json(), "error": None, "duplicate": False}
        except Exception as e:
            err_text = str(e)
            if "23505" in err_text or "duplicate" in err_text.lower():
                logger.debug(f"insert_ignore: duplicate constraint in {self.table_name}")
                return {"data": None, "error": None, "duplicate": True}
            logger.error(f"Supabase insert_ignore error [{self.table_name}]: {e}")
            return {"data": None, "error": str(e), "duplicate": False}

    def upsert(self, data, on_conflict: str = "") -> Dict[str, Any]:
        """Insert or update rows. data can be a dict (single) or list of dicts (bulk)."""
        url = f"{self.client.url}/rest/v1/{self.table_name}"
        if on_conflict:
            url += f"?on_conflict={on_conflict}"
        headers = {"Prefer": "return=representation,resolution=merge-duplicates"}
        payload = data if isinstance(data, list) else [data]
        if self.client.is_auth_failed():
            return {"data": None, "error": self.client.get_auth_error()}
        try:
            resp = _retry_request(
                lambda: self.client.http.post(url, json=payload, headers=headers),
                label=f"UPSERT {self.table_name}",
                client=self.client,
            )
            return {"data": resp.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase upsert error [{self.table_name}]: {e}")
            return {"data": None, "error": str(e)}

    def update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.client.is_auth_failed():
            return {"data": None, "error": self.client.get_auth_error()}
        try:
            resp = _retry_request(
                lambda: self.client.http.patch(self._build_url(), json=data),
                label=f"UPDATE {self.table_name}",
                client=self.client,
            )
            return {"data": resp.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase update error [{self.table_name}]: {e}")
            return {"data": None, "error": str(e)}

    def delete(self) -> Dict[str, Any]:
        if self.client.is_auth_failed():
            return {"data": None, "error": self.client.get_auth_error()}
        try:
            resp = _retry_request(
                lambda: self.client.http.delete(self._build_url()),
                label=f"DELETE {self.table_name}",
                client=self.client,
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
    key = _resolve_supabase_key()

    if not url or not key:
        _init_error = (
            "Missing env vars: "
            f"SUPABASE_URL={'set' if url else 'not set'}, "
            f"SUPABASE_SERVICE_ROLE_KEY={'set' if os.environ.get('SUPABASE_SERVICE_ROLE_KEY') else 'not set'}, "
            f"SUPABASE_KEY={'set' if os.environ.get('SUPABASE_KEY') else 'not set'}"
        )
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


def get_auth_error() -> Optional[str]:
    client = get_supabase_client()
    if client is None:
        return None
    return client.get_auth_error()


def is_auth_failed() -> bool:
    client = get_supabase_client()
    if client is None:
        return False
    return client.is_auth_failed()
