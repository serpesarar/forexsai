"""
Supabase REST API client for database operations.
Uses httpx directly instead of supabase-py to avoid dependency conflicts.
"""
from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger(__name__)

_init_error: Optional[str] = None
_initialized: bool = False


class SupabaseRestClient:
    """Simple Supabase REST API client using httpx."""
    
    def __init__(self, url: str, key: str):
        self.url = url.rstrip('/')
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    def table(self, table_name: str) -> "TableQuery":
        return TableQuery(self, table_name)


class TableQuery:
    """Query builder for Supabase tables."""
    
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
            with httpx.Client(timeout=30.0) as client:
                response = client.get(self._build_url(), headers=self.client.headers)
                response.raise_for_status()
                return {"data": response.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase query error: {e}")
            return {"data": None, "error": str(e)}
    
    def insert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=30.0) as client:
                url = f"{self.client.url}/rest/v1/{self.table_name}"
                response = client.post(url, json=data, headers=self.client.headers)
                response.raise_for_status()
                return {"data": response.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase insert error: {e}")
            return {"data": None, "error": str(e)}
    
    def update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=30.0) as client:
                url = self._build_url()
                response = client.patch(url, json=data, headers=self.client.headers)
                response.raise_for_status()
                return {"data": response.json(), "error": None}
        except Exception as e:
            logger.error(f"Supabase update error: {e}")
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
        # Test connection
        test_result = _client.table("prediction_logs").select("id").limit(1).execute()
        if test_result.get("error"):
            raise Exception(test_result["error"])
        logger.info("Supabase REST client initialized successfully.")
        _initialized = True
        return _client
    except Exception as e:
        _init_error = f"Failed to initialize Supabase client: {e}"
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
