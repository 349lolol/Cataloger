import threading
from supabase import create_client, Client
from app.config import get_settings
from typing import Optional

_supabase_client: Optional[Client] = None
_supabase_admin: Optional[Client] = None
_client_lock = threading.Lock()
_admin_lock = threading.Lock()


def get_supabase_client() -> Client:
    """Get Supabase client with anon key (RLS applies)."""
    global _supabase_client
    if _supabase_client is None:
        with _client_lock:
            if _supabase_client is None:
                settings = get_settings()
                _supabase_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
    return _supabase_client


def get_supabase_admin() -> Client:
    """Get Supabase client with service role key (bypasses RLS)."""
    global _supabase_admin
    if _supabase_admin is None:
        with _admin_lock:
            if _supabase_admin is None:
                settings = get_settings()
                _supabase_admin = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
    return _supabase_admin
