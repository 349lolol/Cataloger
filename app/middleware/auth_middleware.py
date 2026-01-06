import logging
from functools import wraps
from flask import request, g, jsonify
from app.extensions import get_supabase_client, get_supabase_admin

logger = logging.getLogger(__name__)


def get_user_from_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    token = parts[1]

    try:
        supabase = get_supabase_client()
        response = supabase.auth.get_user(token)
        return response.user if response else None
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None


def get_user_org_and_role(user_id: str):
    try:
        supabase = get_supabase_admin()
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
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_user_from_token()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        g.user = user
        g.user_id = user.id

        org_id, role = get_user_org_and_role(user.id)
        if not org_id:
            return jsonify({"error": "User is not a member of any organization"}), 403

        g.org_id = org_id
        g.user_role = role

        return f(*args, **kwargs)

    return decorated_function


def require_role(allowed_roles: list):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user_role'):
                return jsonify({"error": "Unauthorized"}), 401

            if g.user_role not in allowed_roles:
                return jsonify({"error": f"Requires role: {', '.join(allowed_roles)}"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
