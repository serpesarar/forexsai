"""
Supabase client singleton for database operations.
"""
from __future__ import annotations

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_client: Optional["supabase.Client"] = None


def get_supabase_client():
    """
    Returns a Supabase client instance (singleton).
    Returns None if credentials are not configured.
    """
    global _client
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if _client is not None:
        return _client
    
    if not url or not key:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not set. Database features disabled.")
        return None
    
    try:
        from supabase import create_client, Client
        _client = create_client(url, key)
        logger.info("Supabase client initialized successfully.")
        return _client
    except ImportError:
        logger.error("supabase-py not installed. Run: pip install supabase")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


def is_db_available() -> bool:
    """Check if database is configured and available."""
    client = get_supabase_client()
    return client is not None
