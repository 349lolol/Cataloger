import logging
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.services import proposal_service
from app.services.proposal_service import VALID_PROPOSAL_TYPES
from app.utils.resilience import safe_int, is_valid_uuid, validate_metadata

logger = logging.getLogger(__name__)
bp = Blueprint('proposals', __name__)


@bp.route('/proposals', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def create_proposal():
    data = request.get_json()
    if not data or 'proposal_type' not in data:
        return jsonify({"error": "proposal_type is required"}), 400

    if data['proposal_type'] not in VALID_PROPOSAL_TYPES:
        return jsonify({"error": f"Invalid proposal_type. Must be one of: {', '.join(VALID_PROPOSAL_TYPES)}"}), 400

    replacing_item_id = data.get('replacing_item_id')
    if replacing_item_id and not is_valid_uuid(replacing_item_id):
        return jsonify({"error": "Invalid replacing_item_id format"}), 400

    request_id = data.get('request_id')
    if request_id and not is_valid_uuid(request_id):
        return jsonify({"error": "Invalid request_id format"}), 400

    valid, error = validate_metadata(data.get('item_metadata'))
    if not valid:
        return jsonify({"error": error}), 400

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
        logger.exception(f"Create proposal failed: {e}")
        return jsonify({"error": "Failed to create proposal"}), 500


@bp.route('/proposals', methods=['GET'])
@require_auth
def list_proposals():
    try:
        status = request.args.get('status')
        limit = safe_int(request.args.get('limit'), default=100, min_val=1, max_val=1000)

        proposals = proposal_service.list_proposals(
            org_id=g.org_id,
            status=status,
            limit=limit
        )
        return jsonify({"proposals": proposals}), 200
    except Exception as e:
        logger.exception(f"List proposals failed: {e}")
        return jsonify({"error": "Failed to retrieve proposals"}), 500


@bp.route('/proposals/<proposal_id>', methods=['GET'])
@require_auth
def get_proposal(proposal_id):
    if not is_valid_uuid(proposal_id):
        return jsonify({"error": "Invalid proposal ID format"}), 400

    try:
        proposal = proposal_service.get_proposal(proposal_id)

        if proposal['org_id'] != g.org_id:
            return jsonify({"error": "Forbidden"}), 403

        return jsonify(proposal), 200
    except Exception as e:
        logger.exception(f"Get proposal failed for {proposal_id}: {e}")
        return jsonify({"error": "Proposal not found or unavailable"}), 500


@bp.route('/proposals/<proposal_id>/approve', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def approve_proposal(proposal_id):
    if not is_valid_uuid(proposal_id):
        return jsonify({"error": "Invalid proposal ID format"}), 400

    data = request.get_json() or {}

    try:
        proposal = proposal_service.approve_proposal(
            proposal_id=proposal_id,
            reviewed_by=g.user_id,
            review_notes=data.get('review_notes'),
            org_id=g.org_id
        )
        return jsonify(proposal), 200
    except PermissionError:
        return jsonify({"error": "Forbidden"}), 403
    except Exception as e:
        logger.exception(f"Approve proposal failed for {proposal_id}: {e}")
        return jsonify({"error": "Failed to approve proposal"}), 500


@bp.route('/proposals/<proposal_id>/reject', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def reject_proposal(proposal_id):
    if not is_valid_uuid(proposal_id):
        return jsonify({"error": "Invalid proposal ID format"}), 400

    data = request.get_json() or {}

    try:
        proposal = proposal_service.reject_proposal(
            proposal_id=proposal_id,
            reviewed_by=g.user_id,
            review_notes=data.get('review_notes'),
            org_id=g.org_id
        )
        return jsonify(proposal), 200
    except PermissionError:
        return jsonify({"error": "Forbidden"}), 403
    except Exception as e:
        logger.exception(f"Reject proposal failed for {proposal_id}: {e}")
        return jsonify({"error": "Failed to reject proposal"}), 500
