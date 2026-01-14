"""Database module for Supabase integration."""
from backend.database.supabase_client import get_supabase_client, is_db_available

__all__ = ["get_supabase_client", "is_db_available"]
