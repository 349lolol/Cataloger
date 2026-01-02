"""
Proposal service for managing catalog change proposals.
Implements governance workflow for adding, replacing, or deprecating items.
"""
import logging
from typing import List, Dict, Optional
from app.extensions import get_supabase_client
from app.services.audit_service import log_event
from app.services.catalog_service import create_item, update_item

logger = logging.getLogger(__name__)

# Valid proposal types - single source of truth
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
    """
    Create a new proposal for catalog changes.

    Args:
        org_id: Organization ID
        proposed_by: User ID of proposer
        proposal_type: Type of proposal ('ADD_ITEM', 'REPLACE_ITEM', 'DEPRECATE_ITEM')
        item_name: Item name (for ADD/REPLACE)
        item_description: Item description (for ADD/REPLACE)
        item_category: Item category (for ADD/REPLACE)
        item_metadata: Item metadata (for ADD/REPLACE)
        item_price: Item price (for ADD/REPLACE)
        item_pricing_type: Item pricing type (for ADD/REPLACE)
        item_product_url: Item product URL (for ADD/REPLACE)
        item_vendor: Item vendor (for ADD/REPLACE)
        item_sku: Item SKU (for ADD/REPLACE)
        replacing_item_id: ID of item to replace/deprecate
        request_id: Optional link to originating request

    Returns:
        Created proposal data
    """
    if proposal_type not in VALID_PROPOSAL_TYPES:
        raise ValueError(f"Invalid proposal type. Must be one of: {', '.join(VALID_PROPOSAL_TYPES)}")

    supabase = get_supabase_client()
    proposal_data = {
        'org_id': org_id,
        'proposed_by': proposed_by,
        'proposal_type': proposal_type,
        'status': 'pending'
    }

    # Add optional fields
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
        raise Exception("Failed to create proposal")

    proposal = response.data[0]

    # Log audit event
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
    """
    Get a single proposal by ID.

    Args:
        proposal_id: Proposal UUID

    Returns:
        Proposal data

    Raises:
        Exception: If proposal not found
    """
    supabase = get_supabase_client()
    response = supabase.table('proposals') \
        .select('*') \
        .eq('id', proposal_id) \
        .single() \
        .execute()

    if not response.data:
        raise Exception(f"Proposal not found: {proposal_id}")

    return response.data


def list_proposals(
    org_id: str,
    status: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """List proposals (review queue)."""
    supabase = get_supabase_client()
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
    """
    Approve a proposal and AUTOMATICALLY merge it into the catalog.
    Requires reviewer or admin role (enforced by RLS).

    This function performs the complete approval workflow in one transaction:
    1. Marks proposal as 'approved'
    2. Executes merge logic (creates/updates catalog items automatically)
    3. Marks proposal as 'merged'
    4. Logs audit event

    Merge behavior by proposal type:
    - ADD_ITEM: Creates new catalog item with all product fields
    - REPLACE_ITEM: Creates new catalog item + marks old item as deprecated
    - DEPRECATE_ITEM: Marks existing item as deprecated

    Args:
        proposal_id: Proposal UUID
        reviewed_by: User ID of reviewer
        review_notes: Optional review comments

    Returns:
        Updated proposal data with status='merged'

    Example:
        # Approve proposal - catalog item is auto-created
        proposal = approve_proposal(proposal_id, reviewer_user_id, "LGTM")
        # At this point, the catalog item already exists in catalog_items table
    """
    # Get proposal (raises Exception if not found, so no need for null check)
    proposal = get_proposal(proposal_id)

    # Issue #9: Validate org_id matches if provided (defense in depth)
    if org_id and proposal['org_id'] != org_id:
        raise PermissionError("Cannot approve proposal from different organization")

    if proposal['status'] != 'pending':
        raise Exception("Only pending proposals can be approved")

    # Issue #8: Prevent race condition by including status check in update query
    # This ensures atomic check-and-update (optimistic locking)
    supabase = get_supabase_client()
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
        raise Exception("Failed to approve proposal - it may have been already processed")

    # Execute merge logic based on proposal type
    # Wrap in try-except to handle merge failures and revert status
    try:
        if proposal['proposal_type'] == 'ADD_ITEM':
            _merge_add_item(proposal, reviewed_by)
        elif proposal['proposal_type'] == 'REPLACE_ITEM':
            _merge_replace_item(proposal, reviewed_by)
        elif proposal['proposal_type'] == 'DEPRECATE_ITEM':
            _merge_deprecate_item(proposal, reviewed_by)
    except Exception as e:
        # Merge failed - revert proposal status back to pending
        logger.error(f"Merge failed for proposal {proposal_id}, reverting to pending: {e}")
        supabase.table('proposals') \
            .update({'status': 'pending', 'reviewed_by': None, 'review_notes': None}) \
            .eq('id', proposal_id) \
            .execute()
        raise Exception(f"Merge failed: {str(e)}")

    # Mark as merged (only reached if merge succeeded)
    supabase.table('proposals') \
        .update({
            'status': 'merged',
            'merged_at': 'now()'
        }) \
        .eq('id', proposal_id) \
        .eq('status', 'approved') \
        .execute()

    # Log audit event
    log_event(
        org_id=proposal['org_id'],
        event_type='proposal.approved',
        actor_id=reviewed_by,
        resource_type='proposal',
        resource_id=proposal_id,
        metadata={'proposal_type': proposal['proposal_type']}
    )

    # Return the updated proposal data from our update, avoiding extra query
    return get_proposal(proposal_id)


def reject_proposal(
    proposal_id: str,
    reviewed_by: str,
    review_notes: Optional[str] = None,
    org_id: Optional[str] = None
) -> Dict:
    """Reject a proposal."""
    # Get proposal (raises Exception if not found, so no need for null check)
    proposal = get_proposal(proposal_id)

    # Issue #9: Validate org_id matches if provided (defense in depth)
    if org_id and proposal['org_id'] != org_id:
        raise PermissionError("Cannot reject proposal from different organization")

    if proposal['status'] != 'pending':
        raise Exception("Only pending proposals can be rejected")

    # Issue #8: Prevent race condition by including status check in update query
    supabase = get_supabase_client()
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
        raise Exception("Failed to reject proposal - it may have been already processed")

    # Log audit event
    log_event(
        org_id=proposal['org_id'],
        event_type='proposal.rejected',
        actor_id=reviewed_by,
        resource_type='proposal',
        resource_id=proposal_id,
        metadata={}
    )

    return response.data[0]


# =====================================================
# PRIVATE MERGE HELPERS
# =====================================================

def _merge_add_item(proposal: Dict, created_by: str):
    """Create new catalog item from proposal."""
    # Issue #5.2: Log merge operation start
    logger.info(f"Merging ADD_ITEM proposal {proposal['id']}: creating item '{proposal['item_name']}'")
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
        logger.info(f"Successfully merged ADD_ITEM proposal {proposal['id']}: created item {item['id']}")
        return item
    except Exception as e:
        logger.error(f"Failed to merge ADD_ITEM proposal {proposal['id']}: {e}")
        raise


def _merge_replace_item(proposal: Dict, created_by: str):
    """Deprecate old item and create replacement."""
    old_item_id = proposal['replacing_item_id']
    # Issue #5.2: Log merge operation start
    logger.info(f"Merging REPLACE_ITEM proposal {proposal['id']}: replacing item {old_item_id}")

    try:
        # Create new item (audit logging happens inside create_item)
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

        # Update old item to deprecated with replacement link (audit logging happens inside update_item)
        update_item(old_item_id, {
            'status': 'deprecated',
            'replacement_item_id': new_item['id']
        }, updated_by=created_by)

        logger.info(f"Successfully merged REPLACE_ITEM proposal {proposal['id']}: deprecated {old_item_id}, created {new_item['id']}")
    except Exception as e:
        logger.error(f"Failed to merge REPLACE_ITEM proposal {proposal['id']}: {e}")
        raise


def _merge_deprecate_item(proposal: Dict, updated_by: str):
    """Mark item as deprecated."""
    item_id = proposal['replacing_item_id']
    # Issue #5.2: Log merge operation start
    logger.info(f"Merging DEPRECATE_ITEM proposal {proposal['id']}: deprecating item {item_id}")

    try:
        update_item(item_id, {'status': 'deprecated'}, updated_by=updated_by)
        logger.info(f"Successfully merged DEPRECATE_ITEM proposal {proposal['id']}: deprecated item {item_id}")
    except Exception as e:
        logger.error(f"Failed to merge DEPRECATE_ITEM proposal {proposal['id']}: {e}")
        raise
