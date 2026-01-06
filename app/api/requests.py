import logging
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.services import request_service
from app.utils.resilience import safe_int, is_valid_uuid

logger = logging.getLogger(__name__)
bp = Blueprint('requests', __name__)


@bp.route('/requests', methods=['POST'])
@require_auth
def create_request():
    data = request.get_json()
    if not data or 'search_query' not in data:
        return jsonify({"error": "search_query is required"}), 400

    try:
        req = request_service.create_request(
            org_id=g.org_id,
            created_by=g.user_id,
            search_query=data['search_query'],
            search_results=data.get('search_results', []),
            justification=data.get('justification')
        )
        return jsonify(req), 201
    except Exception as e:
        logger.exception(f"Create request failed: {e}")
        return jsonify({"error": "Failed to create request"}), 500


@bp.route('/requests', methods=['GET'])
@require_auth
def list_requests():
    try:
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
    except Exception as e:
        logger.exception(f"List requests failed: {e}")
        return jsonify({"error": "Failed to retrieve requests"}), 500


@bp.route('/requests/<request_id>', methods=['GET'])
@require_auth
def get_request(request_id):
    if not is_valid_uuid(request_id):
        return jsonify({"error": "Invalid request ID format"}), 400

    try:
        req = request_service.get_request(request_id)

        if req['org_id'] != g.org_id:
            return jsonify({"error": "Forbidden"}), 403

        return jsonify(req), 200
    except Exception as e:
        logger.exception(f"Get request failed for {request_id}: {e}")
        return jsonify({"error": "Request not found or unavailable"}), 500


@bp.route('/requests/<request_id>/review', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def review_request(request_id):
    if not is_valid_uuid(request_id):
        return jsonify({"error": "Invalid request ID format"}), 400

    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "status is required"}), 400

    if data['status'] not in ['approved', 'rejected']:
        return jsonify({"error": "status must be 'approved' or 'rejected'"}), 400

    try:
        req = request_service.review_request(
            request_id=request_id,
            reviewed_by=g.user_id,
            status=data['status'],
            review_notes=data.get('review_notes'),
            create_proposal=data.get('create_proposal'),
            org_id=g.org_id
        )
        return jsonify(req), 200
    except PermissionError:
        return jsonify({"error": "Forbidden"}), 403
    except Exception as e:
        logger.exception(f"Review request failed for {request_id}: {e}")
        return jsonify({"error": "Failed to process review"}), 500
