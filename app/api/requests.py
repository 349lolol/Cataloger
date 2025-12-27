"""
Requests API endpoints for procurement request management.
"""
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.services import request_service

bp = Blueprint('requests', __name__)


@bp.route('/requests', methods=['POST'])
@require_auth
def create_request():
    """
    Create a new procurement request.
    POST /api/requests
    Body: {
        "search_query": "...",
        "search_results": [...],
        "justification": "..."
    }
    """
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
        return jsonify({"error": str(e)}), 500


@bp.route('/requests', methods=['GET'])
@require_auth
def list_requests():
    """
    List requests for current organization.
    GET /api/requests?status=pending&created_by=...
    """
    try:
        status = request.args.get('status')
        created_by = request.args.get('created_by')
        limit = int(request.args.get('limit', 100))

        requests_list = request_service.list_requests(
            org_id=g.org_id,
            status=status,
            created_by=created_by,
            limit=limit
        )
        return jsonify({"requests": requests_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/requests/<request_id>', methods=['GET'])
@require_auth
def get_request(request_id):
    """
    Get a single request by ID.
    GET /api/requests/:id
    """
    try:
        req = request_service.get_request(request_id)
        if not req:
            return jsonify({"error": "Request not found"}), 404

        # Verify org ownership
        if req['org_id'] != g.org_id:
            return jsonify({"error": "Forbidden"}), 403

        return jsonify(req), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/requests/<request_id>/review', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def review_request(request_id):
    """
    Approve or reject a request (reviewer/admin only).
    POST /api/requests/:id/review
    Body: {
        "status": "approved" | "rejected",
        "review_notes": "..."
    }
    """
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
            review_notes=data.get('review_notes')
        )
        return jsonify(req), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
