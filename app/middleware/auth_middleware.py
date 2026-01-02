"""
Authentication and authorization middleware for Flask routes.
Handles JWT validation and role-based access control.
"""
import logging
from functools import wraps
from flask import request, g, jsonify
from app.extensions import get_supabase_client

logger = logging.getLogger(__name__)


def get_user_from_token():
    """
    Extract and validate JWT from Authorization header.
    Returns user data if valid, None otherwise.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    # Extract Bearer token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    token = parts[1]

    try:
        supabase = get_supabase_client()
        # Validate token and get user
        response = supabase.auth.get_user(token)
        return response.user if response else None
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None


# Note: Tests should import get_user_from_token directly
# verify_jwt_token was removed - use get_user_from_token instead


def get_user_org_and_role(user_id: str):
    """
    Get user's organization ID and role from org_memberships.
    Returns tuple (org_id, role) or (None, None) if not found.

    Note: If user has multiple org memberships, returns the first one.
    For multi-org support, the API should accept org_id in request headers.
    """
    try:
        supabase = get_supabase_client()
        # Use limit(1) instead of single() to avoid exception on 0 or 2+ results
        response = supabase.table('org_memberships') \
            .select('org_id, role') \
            .eq('user_id', user_id) \
            .limit(1) \
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]['org_id'], response.data[0]['role']
        return None, None
    except Exception as e:
        logger.error(f"Error fetching org membership: {e}")
        return None, None


def require_auth(f):
    """
    Decorator to require authentication.
    Sets g.user and g.user_id for the request context.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_user_from_token()
        if not user:
            return jsonify({"error": "Unauthorized", "message": "Valid authentication token required"}), 401

        # Store user info in Flask's request context
        g.user = user
        g.user_id = user.id

        # Also fetch and store org info
        org_id, role = get_user_org_and_role(user.id)
        if not org_id:
            return jsonify({
                "error": "Forbidden",
                "message": "User is not a member of any organization"
            }), 403

        g.org_id = org_id
        g.user_role = role

        return f(*args, **kwargs)

    return decorated_function


def require_role(allowed_roles: list):
    """
    Decorator to require specific role(s).
    Must be used after @require_auth.

    Example:
        @require_auth
        @require_role(['admin', 'reviewer'])
        def my_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user_role'):
                return jsonify({
                    "error": "Unauthorized",
                    "message": "Authentication required"
                }), 401

            if g.user_role not in allowed_roles:
                return jsonify({
                    "error": "Forbidden",
                    "message": f"Requires one of these roles: {', '.join(allowed_roles)}"
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
