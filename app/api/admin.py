"""
Admin API endpoints for audit logs and system management.
"""
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.services import audit_service

bp = Blueprint('admin', __name__)


@bp.route('/admin/audit-log', methods=['GET'])
@require_auth
@require_role(['admin'])
def get_audit_log():
    """
    View audit events (admin only).
    GET /api/admin/audit-log?limit=100&event_type=...&resource_type=...&resource_id=...
    """
    try:
        limit = int(request.args.get('limit', 100))
        event_type = request.args.get('event_type')
        resource_type = request.args.get('resource_type')
        resource_id = request.args.get('resource_id')

        events = audit_service.get_audit_log(
            org_id=g.org_id,
            limit=limit,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id
        )
        return jsonify({"events": events}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
