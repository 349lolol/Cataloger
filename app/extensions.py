"""
Application extensions and shared instances.
Lazy-loaded to avoid circular imports and optimize startup time.
"""
from functools import lru_cache
from supabase import create_client, Client
from app.config import get_settings


# Supabase clients (initialized lazily)
_supabase_client: Client = None
_supabase_admin: Client = None


def get_supabase_client() -> Client:
    """
    Get Supabase client with anon key (RLS applies).
    Used for user operations with row-level security.
    """
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
    return _supabase_client


def get_supabase_admin() -> Client:
    """
    Get Supabase client with service role key (bypasses RLS).
    Used for system operations like audit logging and embedding management.
    ⚠️ NEVER expose this client to frontend or untrusted code.
    """
    global _supabase_admin
    if _supabase_admin is None:
        settings = get_settings()
        _supabase_admin = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
    return _supabase_admin


@lru_cache()
def get_embedding_model():
    """
    Get SentenceTransformer embedding model (cached).
    Model is downloaded and cached on first call.
    """
    from sentence_transformers import SentenceTransformer
    settings = get_settings()
    return SentenceTransformer(settings.EMBEDDING_MODEL)
