"""
Supabase client singleton for database operations.
"""
from __future__ import annotations

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_client: Optional["supabase.Client"] = None


_init_error: Optional[str] = None

def get_supabase_client():
    """
    Returns a Supabase client instance (singleton).
    Returns None if credentials are not configured.
    """
    global _client, _init_error
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if _client is not None:
        return _client
    
    if not url or not key:
        _init_error = f"Missing env vars: SUPABASE_URL={'set' if url else 'not set'}, SUPABASE_KEY={'set' if key else 'not set'}"
        logger.warning(_init_error)
        return None
    
    try:
        from supabase import create_client, Client
        _client = create_client(url, key)
        logger.info("Supabase client initialized successfully.")
        return _client
    except ImportError as e:
        _init_error = f"supabase-py not installed: {e}"
        logger.error(_init_error)
        return None
    except Exception as e:
        _init_error = f"Failed to initialize Supabase client: {e}"
        logger.error(_init_error)
        return None

def get_init_error() -> Optional[str]:
    """Return the initialization error if any."""
    return _init_error


def is_db_available() -> bool:
    """Check if database is configured and available."""
    client = get_supabase_client()
    return client is not None
