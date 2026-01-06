import logging
from typing import List, Dict, Optional
from app.extensions import get_supabase_admin
from app.services.audit_service import log_event
from app.services.catalog_service import create_item, update_item
from app.middleware.error_responses import NotFoundError, BadRequestError, ForbiddenError, ConflictError, DatabaseError

logger = logging.getLogger(__name__)

VALID_PROPOSAL_TYPES = ('ADD_ITEM', 'REPLACE_ITEM', 'DEPRECATE_ITEM')


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
    request_id: Optional[str] = None
) -> Dict:
    if proposal_type not in VALID_PROPOSAL_TYPES:
        raise BadRequestError(f"Invalid proposal type. Must be one of: {', '.join(VALID_PROPOSAL_TYPES)}")

    supabase = get_supabase_admin()
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


def get_proposal(proposal_id: str) -> Dict:
    supabase = get_supabase_admin()
    response = supabase.table('proposals') \
        .select('*') \
        .eq('id', proposal_id) \
        .single() \
        .execute()

    if not response.data:
        raise NotFoundError("Proposal", proposal_id)

    return response.data


def list_proposals(org_id: str, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    supabase = get_supabase_admin()
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
    org_id: Optional[str] = None
) -> Dict:
    proposal = get_proposal(proposal_id)

    if org_id and proposal['org_id'] != org_id:
        raise ForbiddenError("Cannot approve proposal from different organization")

    if proposal['status'] != 'pending':
        raise ConflictError("Only pending proposals can be approved")

    supabase = get_supabase_admin()
    response = supabase.table('proposals') \
        .update({
            'status': 'approved',
            'reviewed_by': reviewed_by,
            'review_notes': review_notes,
            'reviewed_at': 'now()'
        }) \
        .eq('id', proposal_id) \
        .eq('status', 'pending') \
        .execute()

    if not response.data:
        raise ConflictError("Failed to approve proposal - may have been already processed")

    try:
        if proposal['proposal_type'] == 'ADD_ITEM':
            _merge_add_item(proposal, reviewed_by)
        elif proposal['proposal_type'] == 'REPLACE_ITEM':
            _merge_replace_item(proposal, reviewed_by)
        elif proposal['proposal_type'] == 'DEPRECATE_ITEM':
            _merge_deprecate_item(proposal, reviewed_by)
    except Exception as e:
        logger.error(f"Merge failed for proposal {proposal_id}, reverting: {e}")
        supabase.table('proposals') \
            .update({'status': 'pending', 'reviewed_by': None, 'review_notes': None}) \
            .eq('id', proposal_id) \
            .execute()
        raise DatabaseError(f"Merge failed: {str(e)}")

    supabase.table('proposals') \
        .update({'status': 'merged', 'merged_at': 'now()'}) \
        .eq('id', proposal_id) \
        .eq('status', 'approved') \
        .execute()

    log_event(
        org_id=proposal['org_id'],
        event_type='proposal.approved',
        actor_id=reviewed_by,
        resource_type='proposal',
        resource_id=proposal_id,
        metadata={'proposal_type': proposal['proposal_type']}
    )

    return get_proposal(proposal_id)


def reject_proposal(
    proposal_id: str,
    reviewed_by: str,
    review_notes: Optional[str] = None,
    org_id: Optional[str] = None
) -> Dict:
    proposal = get_proposal(proposal_id)

    if org_id and proposal['org_id'] != org_id:
        raise ForbiddenError("Cannot reject proposal from different organization")

    if proposal['status'] != 'pending':
        raise ConflictError("Only pending proposals can be rejected")

    supabase = get_supabase_admin()
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


def _merge_add_item(proposal: Dict, created_by: str):
    logger.info(f"Merging ADD_ITEM proposal {proposal['id']}")
    try:
        item = create_item(
            org_id=proposal['org_id'],
            name=proposal['item_name'],
            description=proposal.get('item_description', ''),
            category=proposal.get('item_category', ''),
            created_by=created_by,
            price=proposal.get('item_price'),
            pricing_type=proposal.get('item_pricing_type'),
            product_url=proposal.get('item_product_url'),
            vendor=proposal.get('item_vendor'),
            sku=proposal.get('item_sku'),
            metadata=proposal.get('item_metadata', {})
        )
        logger.info(f"Created item {item['id']} from proposal {proposal['id']}")
        return item
    except Exception as e:
        logger.error(f"Failed to merge ADD_ITEM proposal {proposal['id']}: {e}")
        raise


def _merge_replace_item(proposal: Dict, created_by: str):
    old_item_id = proposal['replacing_item_id']
    logger.info(f"Merging REPLACE_ITEM proposal {proposal['id']}, replacing {old_item_id}")

    try:
        new_item = create_item(
            org_id=proposal['org_id'],
            name=proposal['item_name'],
            description=proposal.get('item_description', ''),
            category=proposal.get('item_category', ''),
            created_by=created_by,
            price=proposal.get('item_price'),
            pricing_type=proposal.get('item_pricing_type'),
            product_url=proposal.get('item_product_url'),
            vendor=proposal.get('item_vendor'),
            sku=proposal.get('item_sku'),
            metadata=proposal.get('item_metadata', {})
        )

        update_item(old_item_id, {
            'status': 'deprecated',
            'replacement_item_id': new_item['id']
        }, updated_by=created_by)

        logger.info(f"Replaced {old_item_id} with {new_item['id']}")
    except Exception as e:
        logger.error(f"Failed to merge REPLACE_ITEM proposal {proposal['id']}: {e}")
        raise


def _merge_deprecate_item(proposal: Dict, updated_by: str):
    item_id = proposal['replacing_item_id']
    logger.info(f"Merging DEPRECATE_ITEM proposal {proposal['id']}, deprecating {item_id}")

    try:
        update_item(item_id, {'status': 'deprecated'}, updated_by=updated_by)
        logger.info(f"Deprecated item {item_id}")
    except Exception as e:
        logger.error(f"Failed to merge DEPRECATE_ITEM proposal {proposal['id']}: {e}")
        raise
