from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.middleware.error_responses import BadRequestError, ForbiddenError
from app.services import proposal_service
from app.services.proposal_service import VALID_PROPOSAL_TYPES
from app.utils.resilience import safe_int, is_valid_uuid, validate_metadata

bp = Blueprint('proposals', __name__)


@bp.route('/proposals', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def create_proposal():
    data = request.get_json()
    if not data or 'proposal_type' not in data:
        raise BadRequestError("proposal_type is required")

    if data['proposal_type'] not in VALID_PROPOSAL_TYPES:
        raise BadRequestError(f"Invalid proposal_type. Must be one of: {', '.join(VALID_PROPOSAL_TYPES)}")

    replacing_item_id = data.get('replacing_item_id')
    if replacing_item_id and not is_valid_uuid(replacing_item_id):
        raise BadRequestError("Invalid replacing_item_id format")

    request_id = data.get('request_id')
    if request_id and not is_valid_uuid(request_id):
        raise BadRequestError("Invalid request_id format")

    valid, error = validate_metadata(data.get('item_metadata'))
    if not valid:
        raise BadRequestError(error)

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


@bp.route('/proposals', methods=['GET'])
@require_auth
def list_proposals():
    status = request.args.get('status')
    limit = safe_int(request.args.get('limit'), default=100, min_val=1, max_val=1000)

    proposals = proposal_service.list_proposals(
        org_id=g.org_id,
        status=status,
        limit=limit
    )
    return jsonify({"proposals": proposals}), 200


@bp.route('/proposals/<proposal_id>', methods=['GET'])
@require_auth
def get_proposal(proposal_id):
    if not is_valid_uuid(proposal_id):
        raise BadRequestError("Invalid proposal ID format")

    proposal = proposal_service.get_proposal(proposal_id)

    if proposal['org_id'] != g.org_id:
        raise ForbiddenError()

    return jsonify(proposal), 200


@bp.route('/proposals/<proposal_id>/approve', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def approve_proposal(proposal_id):
    if not is_valid_uuid(proposal_id):
        raise BadRequestError("Invalid proposal ID format")

    data = request.get_json() or {}

    proposal = proposal_service.approve_proposal(
        proposal_id=proposal_id,
        reviewed_by=g.user_id,
        review_notes=data.get('review_notes'),
        org_id=g.org_id
    )
    return jsonify(proposal), 200


@bp.route('/proposals/<proposal_id>/reject', methods=['POST'])
@require_auth
@require_role(['reviewer', 'admin'])
def reject_proposal(proposal_id):
    if not is_valid_uuid(proposal_id):
        raise BadRequestError("Invalid proposal ID format")

    data = request.get_json() or {}

    proposal = proposal_service.reject_proposal(
        proposal_id=proposal_id,
        reviewed_by=g.user_id,
        review_notes=data.get('review_notes'),
        org_id=g.org_id
    )
    return jsonify(proposal), 200
