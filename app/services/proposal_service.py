import logging
from typing import List, Dict, Optional
from app.extensions import get_supabase_admin, get_supabase_user_client
from app.services.audit_service import log_event
from app.services.embedding_service import encode_catalog_item
from app.middleware.error_responses import NotFoundError, BadRequestError, ForbiddenError, ConflictError, DatabaseError

logger = logging.getLogger(__name__)

VALID_PROPOSAL_TYPES = ('ADD_ITEM', 'REPLACE_ITEM', 'DEPRECATE_ITEM')


def _get_client(user_token: Optional[str] = None):
    if user_token:
        return get_supabase_user_client(user_token)
    return get_supabase_admin()


def create_proposal(
    org_id: str,
    proposed_by: str,
    proposal_type: str,
    item_name: Optional[str] = None,
    item_description: Optional[str] = None,
    item_category: Optional[str] = None,
    item_metadata: Optional[Dict] = None,
    item_price: Optional[float] = None,
    item_pricing_type: Optional[str] = None,
    item_product_url: Optional[str] = None,
    item_vendor: Optional[str] = None,
    item_sku: Optional[str] = None,
    replacing_item_id: Optional[str] = None,
    request_id: Optional[str] = None,
    user_token: Optional[str] = None
) -> Dict:
    if proposal_type not in VALID_PROPOSAL_TYPES:
        raise BadRequestError(f"Invalid proposal type. Must be one of: {', '.join(VALID_PROPOSAL_TYPES)}")

    supabase = _get_client(user_token)
    proposal_data = {
        'org_id': org_id,
        'proposed_by': proposed_by,
        'proposal_type': proposal_type,
        'status': 'pending'
    }

    if item_name:
        proposal_data['item_name'] = item_name
    if item_description:
        proposal_data['item_description'] = item_description
    if item_category:
        proposal_data['item_category'] = item_category
    if item_metadata:
        proposal_data['item_metadata'] = item_metadata
    if item_price is not None:
        proposal_data['item_price'] = item_price
    if item_pricing_type:
        proposal_data['item_pricing_type'] = item_pricing_type
    if item_product_url:
        proposal_data['item_product_url'] = item_product_url
    if item_vendor:
        proposal_data['item_vendor'] = item_vendor
    if item_sku:
        proposal_data['item_sku'] = item_sku
    if replacing_item_id:
        proposal_data['replacing_item_id'] = replacing_item_id
    if request_id:
        proposal_data['request_id'] = request_id

    response = supabase.table('proposals').insert(proposal_data).execute()

    if not response.data:
        raise DatabaseError("Failed to create proposal")

    proposal = response.data[0]

    log_event(
        org_id=org_id,
        event_type='proposal.created',
        actor_id=proposed_by,
        resource_type='proposal',
        resource_id=proposal['id'],
        metadata={'proposal_type': proposal_type}
    )

    return proposal


def get_proposal(proposal_id: str, user_token: Optional[str] = None) -> Dict:
    supabase = _get_client(user_token)
    response = supabase.table('proposals') \
        .select('*') \
        .eq('id', proposal_id) \
        .single() \
        .execute()

    if not response.data:
        raise NotFoundError("Proposal", proposal_id)

    return response.data


def list_proposals(org_id: str, status: Optional[str] = None, limit: int = 100, user_token: Optional[str] = None) -> List[Dict]:
    supabase = _get_client(user_token)
    query = supabase.table('proposals') \
        .select('*') \
        .eq('org_id', org_id) \
        .order('created_at', desc=True) \
        .limit(limit)

    if status:
        query = query.eq('status', status)

    response = query.execute()
    return response.data if response.data else []


def approve_proposal(
    proposal_id: str,
    reviewed_by: str,
    review_notes: Optional[str] = None,
    org_id: Optional[str] = None,
    user_token: Optional[str] = None
) -> Dict:
    supabase = _get_client(user_token)
    proposal = get_proposal(proposal_id, user_token=user_token)

    if org_id and proposal['org_id'] != org_id:
        raise ForbiddenError("Cannot approve proposal from different organization")

    if proposal['status'] != 'pending':
        raise ConflictError("Only pending proposals can be approved")

    embedding = None
    if proposal['proposal_type'] in ['ADD_ITEM', 'REPLACE_ITEM']:
        embedding = encode_catalog_item(
            proposal['item_name'],
            proposal.get('item_description', ''),
            proposal.get('item_category', '')
        )

    if proposal['proposal_type'] == 'ADD_ITEM':
        response = supabase.rpc('merge_add_item_proposal', {
            'p_proposal_id': proposal_id,
            'p_reviewed_by': reviewed_by,
            'p_review_notes': review_notes,
            'p_embedding': embedding
        }).execute()
    elif proposal['proposal_type'] == 'REPLACE_ITEM':
        response = supabase.rpc('merge_replace_item_proposal', {
            'p_proposal_id': proposal_id,
            'p_reviewed_by': reviewed_by,
            'p_review_notes': review_notes,
            'p_embedding': embedding
        }).execute()
    elif proposal['proposal_type'] == 'DEPRECATE_ITEM':
        response = supabase.rpc('merge_deprecate_item_proposal', {
            'p_proposal_id': proposal_id,
            'p_reviewed_by': reviewed_by,
            'p_review_notes': review_notes
        }).execute()
    else:
        raise BadRequestError(f"Unknown proposal type: {proposal['proposal_type']}")

    if not response.data:
        raise DatabaseError("Failed to merge proposal")

    result = response.data
    logger.info(f"Merged {proposal['proposal_type']} proposal {proposal_id}")

    log_event(
        org_id=proposal['org_id'],
        event_type='proposal.merged',
        actor_id=reviewed_by,
        resource_type='proposal',
        resource_id=proposal_id,
        metadata={'proposal_type': proposal['proposal_type']}
    )

    if proposal['proposal_type'] in ['ADD_ITEM', 'REPLACE_ITEM']:
        item_id = result.get('created_item_id') or result.get('new_item_id')
        log_event(
            org_id=proposal['org_id'],
            event_type='catalog.item.created',
            actor_id=reviewed_by,
            resource_type='catalog_item',
            resource_id=item_id,
            metadata={'name': proposal['item_name'], 'via_proposal': proposal_id}
        )

    return get_proposal(proposal_id, user_token=user_token)


def reject_proposal(
    proposal_id: str,
    reviewed_by: str,
    review_notes: Optional[str] = None,
    org_id: Optional[str] = None,
    user_token: Optional[str] = None
) -> Dict:
    proposal = get_proposal(proposal_id, user_token=user_token)

    if org_id and proposal['org_id'] != org_id:
        raise ForbiddenError("Cannot reject proposal from different organization")

    if proposal['status'] != 'pending':
        raise ConflictError("Only pending proposals can be rejected")

    supabase = _get_client(user_token)
    response = supabase.table('proposals') \
        .update({
            'status': 'rejected',
            'reviewed_by': reviewed_by,
            'review_notes': review_notes,
            'reviewed_at': 'now()'
        }) \
        .eq('id', proposal_id) \
        .eq('status', 'pending') \
        .execute()

    if not response.data:
        raise ConflictError("Failed to reject proposal - may have been already processed")

    log_event(
        org_id=proposal['org_id'],
        event_type='proposal.rejected',
        actor_id=reviewed_by,
        resource_type='proposal',
        resource_id=proposal_id,
        metadata={}
    )

    return response.data[0]
