"""
Admin API endpoints for audit logs and system management.
"""
import logging
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.services import audit_service, catalog_service
from app.utils.resilience import safe_int

logger = logging.getLogger(__name__)
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
        limit = safe_int(request.args.get('limit'), default=100, min_val=1, max_val=1000)
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
        logger.exception(f"Get audit log failed: {e}")
        return jsonify({"error": "Failed to retrieve audit log"}), 500


@bp.route('/admin/embeddings/check', methods=['POST'])
@require_auth
@require_role(['admin'])
def check_and_repair_embeddings():
    """
    Check for catalog items missing embeddings and optionally repair them.

    POST /api/admin/embeddings/check

    This endpoint:
    1. Finds all catalog items without embeddings
    2. Automatically regenerates missing embeddings
    3. Returns a report of what was found and fixed

    Response:
    {
        "total_items": 150,
        "items_with_embeddings": 145,
        "items_without_embeddings": 5,
        "repaired": 5,
        "failed": 0,
        "failed_items": []
    }

    Use this:
    - As a health check after migrations
    - To fix search issues
    - As periodic maintenance
    """
    try:
        result = catalog_service.check_and_repair_embeddings(g.org_id)
        return jsonify(result), 200
    except Exception as e:
        logger.exception(f"Check embeddings failed: {e}")
        return jsonify({"error": "Failed to check embeddings"}), 500
