"""
Requests API endpoints for procurement request management.
"""
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
        logger.exception(f"Create request failed: {e}")
        return jsonify({"error": "Failed to create request"}), 500


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
    """
    Get a single request by ID.
    GET /api/requests/:id
    """
    # Issue #23: Validate UUID format
    if not is_valid_uuid(request_id):
        return jsonify({"error": "Invalid request ID format"}), 400

    try:
        req = request_service.get_request(request_id)

        # Verify org ownership
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
    """
    Approve or reject a request (reviewer/admin only).

    POST /api/requests/:id/review

    Body: {
        "status": "approved" | "rejected",
        "review_notes": "...",  // Optional

        // OPTIONAL: Auto-create proposal when approving
        // Use this to streamline the workflow: approve request + create proposal in one step
        // If omitted, the request is simply marked approved (useful when item already exists)
        "create_proposal": {
            "proposal_type": "ADD_ITEM" | "REPLACE_ITEM" | "DEPRECATE_ITEM",
            "item_name": "...",
            "item_description": "...",
            "item_category": "...",
            "item_metadata": {},
            "item_price": 99.99,
            "item_pricing_type": "one_time | monthly | yearly | usage_based",
            "item_product_url": "https://...",
            "item_vendor": "...",
            "item_sku": "...",
            "replacing_item_id": "..."  // For REPLACE/DEPRECATE only
        }
    }

    Response (if create_proposal provided):
    {
        ...request fields...,
        "proposal": {...}  // Auto-created proposal linked to this request
    }

    Workflow Options:
    1. Approve WITHOUT proposal: Request marked approved, no further action
    2. Approve WITH proposal: Request marked approved + proposal auto-created
    3. Reject: Request marked rejected (create_proposal ignored)
    """
    # Issue #23: Validate UUID format
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
            org_id=g.org_id  # Issue #9: Pass org_id for authorization
        )
        return jsonify(req), 200
    except PermissionError as e:
        return jsonify({"error": "Forbidden"}), 403
    except Exception as e:
        logger.exception(f"Review request failed for {request_id}: {e}")
        return jsonify({"error": "Failed to process review"}), 500
