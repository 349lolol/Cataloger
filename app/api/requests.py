from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.middleware.error_responses import BadRequestError
from app.services import request_service
from app.utils.resilience import safe_int, require_valid_uuid, check_org_access

bp = Blueprint('requests', __name__)


@bp.route('/requests', methods=['POST'])
@require_auth
def create_request():
    data = request.get_json()
    if not data or 'search_query' not in data:
        raise BadRequestError("search_query is required")

    req = request_service.create_request(
        org_id=g.org_id,
        created_by=g.user_id,
        search_query=data['search_query'],
        search_results=data.get('search_results', []),
        justification=data.get('justification')
    )
    return jsonify(req), 201


@bp.route('/requests', methods=['GET'])
@require_auth
def list_requests():
    status = request.args.get('status')
    created_by = request.args.get('created_by')
    limit = safe_int(request.args.get('limit'), default=100, min_val=1, max_val=1000)

    requests_list = request_service.list_requests(
        org_id=g.org_id,
        status=status,
        created_by=created_by,
        limit=limit
    )
    return jsonify({"requests": requests_list}), 200


@bp.route('/requests/<request_id>', methods=['GET'])
@require_auth
def get_request(request_id):
    require_valid_uuid(request_id, "request ID")

    req = request_service.get_request(request_id)
    check_org_access(req, g.org_id, "request")

    return jsonify(req), 200


@bp.route('/requests/<request_id>/review', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def review_request(request_id):
    require_valid_uuid(request_id, "request ID")

    data = request.get_json()
    if not data or 'status' not in data:
        raise BadRequestError("status is required")

    if data['status'] not in ['approved', 'rejected']:
        raise BadRequestError("status must be 'approved' or 'rejected'")

    req = request_service.review_request(
        request_id=request_id,
        reviewed_by=g.user_id,
        status=data['status'],
        review_notes=data.get('review_notes'),
        create_proposal=data.get('create_proposal'),
        org_id=g.org_id
    )
    return jsonify(req), 200
