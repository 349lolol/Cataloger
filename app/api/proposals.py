"""
Proposals API endpoints for catalog change governance.
"""
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.services import proposal_service

bp = Blueprint('proposals', __name__)


@bp.route('/proposals', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def create_proposal():
    """
    Create a new proposal for catalog changes (reviewer/admin only).
    POST /api/proposals
    Body: {
        "proposal_type": "ADD_ITEM" | "REPLACE_ITEM" | "DEPRECATE_ITEM",
        "item_name": "...",
        "item_description": "...",
        "item_category": "...",
        "item_metadata": {},
        "item_price": 99.99,  // Optional
        "item_pricing_type": "one_time | monthly | yearly | usage_based",  // Optional
        "item_product_url": "https://...",  // Optional
        "item_vendor": "...",  // Optional
        "item_sku": "...",  // Optional
        "replacing_item_id": "...",  // For REPLACE_ITEM and DEPRECATE_ITEM
        "request_id": "..."  // Optional link to originating request
    }
    """
    data = request.get_json()
    if not data or 'proposal_type' not in data:
        return jsonify({"error": "proposal_type is required"}), 400

    try:
        proposal = proposal_service.create_proposal(
            org_id=g.org_id,
            proposed_by=g.user_id,
            proposal_type=data['proposal_type'],
            item_name=data.get('item_name'),
            item_description=data.get('item_description'),
            item_category=data.get('item_category'),
            item_metadata=data.get('item_metadata'),
            item_price=data.get('item_price'),
            item_pricing_type=data.get('item_pricing_type'),
            item_product_url=data.get('item_product_url'),
            item_vendor=data.get('item_vendor'),
            item_sku=data.get('item_sku'),
            replacing_item_id=data.get('replacing_item_id'),
            request_id=data.get('request_id')
        )
        return jsonify(proposal), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/proposals', methods=['GET'])
@require_auth
def list_proposals():
    """
    List proposals (review queue).
    GET /api/proposals?status=pending
    """
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))

        proposals = proposal_service.list_proposals(
            org_id=g.org_id,
            status=status,
            limit=limit
        )
        return jsonify({"proposals": proposals}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/proposals/<proposal_id>', methods=['GET'])
@require_auth
def get_proposal(proposal_id):
    """
    Get a single proposal by ID.
    GET /api/proposals/:id
    """
    try:
        proposal = proposal_service.get_proposal(proposal_id)

        # Verify org ownership
        if proposal['org_id'] != g.org_id:
            return jsonify({"error": "Forbidden"}), 403

        return jsonify(proposal), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/proposals/<proposal_id>/approve', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def approve_proposal(proposal_id):
    """
    Approve and merge a proposal (reviewer/admin only).
    POST /api/proposals/:id/approve
    Body: {
        "review_notes": "..."
    }
    """
    data = request.get_json() or {}

    try:
        proposal = proposal_service.approve_proposal(
            proposal_id=proposal_id,
            reviewed_by=g.user_id,
            review_notes=data.get('review_notes')
        )
        return jsonify(proposal), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/proposals/<proposal_id>/reject', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def reject_proposal(proposal_id):
    """
    Reject a proposal (reviewer/admin only).
    POST /api/proposals/:id/reject
    Body: {
        "review_notes": "..."
    }
    """
    data = request.get_json() or {}

    try:
        proposal = proposal_service.reject_proposal(
            proposal_id=proposal_id,
            reviewed_by=g.user_id,
            review_notes=data.get('review_notes')
        )
        return jsonify(proposal), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
