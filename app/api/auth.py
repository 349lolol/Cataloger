from flask import Blueprint, jsonify, g
from app.middleware.auth_middleware import require_auth

bp = Blueprint('auth', __name__)


@bp.route('/auth/verify', methods=['GET'])
@require_auth
def verify_auth():
    return jsonify({
        "user_id": g.user_id,
        "org_id": g.org_id,
        "role": g.user_role
    }), 200
