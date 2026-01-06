from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.services import audit_service, catalog_service
from app.utils.resilience import safe_int

bp = Blueprint('admin', __name__)


@bp.route('/admin/audit-log', methods=['GET'])
@require_auth
@require_role(['admin'])
def get_audit_log():
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


@bp.route('/admin/embeddings/check', methods=['POST'])
@require_auth
@require_role(['admin'])
def check_and_repair_embeddings():
    result = catalog_service.check_and_repair_embeddings(g.org_id)
    return jsonify(result), 200
