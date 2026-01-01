"""
Application extensions and shared instances.
Lazy-loaded to avoid circular imports and optimize startup time.
"""
from functools import lru_cache
from supabase import create_client, Client
from app.config import get_settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Supabase clients (initialized lazily)
_supabase_client: Optional[Client] = None
_supabase_admin: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get Supabase client with anon key (RLS applies).
    Used for user operations with row-level security.

    Note: Supabase Python client uses httpx internally which manages
    connection pooling automatically. Default pool size is 100 connections.
    """
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        logger.info("Initialized Supabase client (RLS-enabled)")
    return _supabase_client


def get_supabase_admin() -> Client:
    """
    Get Supabase client with service role key (bypasses RLS).
    Used for system operations like audit logging and embedding management.
    ⚠️ NEVER expose this client to frontend or untrusted code.

    Note: Supabase Python client uses httpx internally which manages
    connection pooling automatically. Default pool size is 100 connections.
    """
    global _supabase_admin
    if _supabase_admin is None:
        settings = get_settings()
        _supabase_admin = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        logger.info("Initialized Supabase admin client (RLS-bypassed)")
    return _supabase_admin
