"""
Authentication blueprint.
Auth is handled client-side via Supabase, but this blueprint
provides endpoints to verify auth and get user info.
"""
from flask import Blueprint, jsonify, g
from app.middleware.auth_middleware import require_auth

bp = Blueprint('auth', __name__)


@bp.route('/auth/verify', methods=['GET'])
@require_auth
def verify_auth():
    """
    Verify authentication and return user info.
    GET /api/auth/verify

    Returns:
        User ID, organization ID, and role

    Used by MCP server to get user context after Supabase authentication.
    """
    return jsonify({
        "user_id": g.user_id,
        "org_id": g.org_id,
        "role": g.user_role
    }), 200
