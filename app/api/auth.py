"""
Authentication blueprint.
Auth is handled client-side via Supabase, but this blueprint
can be extended for user info endpoints.
"""
from flask import Blueprint

bp = Blueprint('auth', __name__)

# Auth endpoints can be added here if needed
# For now, authentication is handled via Supabase client-side
