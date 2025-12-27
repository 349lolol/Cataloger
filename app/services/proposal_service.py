"""
Proposal service for managing catalog change proposals.
Implements governance workflow for adding, replacing, or deprecating items.
"""
from typing import List, Dict, Optional
from app.extensions import get_supabase_client, get_supabase_admin
from app.services.audit_service import log_event
from app.services.catalog_service import create_item, update_item


def create_proposal(
    org_id: str,
    proposed_by: str,
    proposal_type: str,
    item_name: Optional[str] = None,
    item_description: Optional[str] = None,
    item_category: Optional[str] = None,
    item_metadata: Optional[Dict] = None,
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
        replacing_item_id: ID of item to replace/deprecate
        request_id: Optional link to originating request

    Returns:
        Created proposal data
    """
    if proposal_type not in ['ADD_ITEM', 'REPLACE_ITEM', 'DEPRECATE_ITEM']:
        raise ValueError("Invalid proposal type")

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


def get_proposal(proposal_id: str) -> Optional[Dict]:
    """Get a single proposal by ID."""
    supabase = get_supabase_client()
    response = supabase.table('proposals') \
        .select('*') \
        .eq('id', proposal_id) \
        .single() \
        .execute()

    return response.data if response.data else None


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
    review_notes: Optional[str] = None
) -> Dict:
    """
    Approve a proposal and merge it into the catalog.
    Requires reviewer or admin role (enforced by RLS).

    Args:
        proposal_id: Proposal UUID
        reviewed_by: User ID of reviewer
        review_notes: Optional review comments

    Returns:
        Updated proposal data
    """
    # Get proposal
    proposal = get_proposal(proposal_id)
    if not proposal:
        raise Exception("Proposal not found")

    if proposal['status'] != 'pending':
        raise Exception("Only pending proposals can be approved")

    # Mark as approved
    supabase = get_supabase_client()
    supabase.table('proposals') \
        .update({
            'status': 'approved',
            'reviewed_by': reviewed_by,
            'review_notes': review_notes,
            'reviewed_at': 'now()'
        }) \
        .eq('id', proposal_id) \
        .execute()

    # Execute merge logic based on proposal type
    if proposal['proposal_type'] == 'ADD_ITEM':
        _merge_add_item(proposal, reviewed_by)
    elif proposal['proposal_type'] == 'REPLACE_ITEM':
        _merge_replace_item(proposal, reviewed_by)
    elif proposal['proposal_type'] == 'DEPRECATE_ITEM':
        _merge_deprecate_item(proposal, reviewed_by)

    # Mark as merged
    supabase.table('proposals') \
        .update({
            'status': 'merged',
            'merged_at': 'now()'
        }) \
        .eq('id', proposal_id) \
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

    return get_proposal(proposal_id)


def reject_proposal(
    proposal_id: str,
    reviewed_by: str,
    review_notes: Optional[str] = None
) -> Dict:
    """Reject a proposal."""
    proposal = get_proposal(proposal_id)
    if not proposal:
        raise Exception("Proposal not found")

    if proposal['status'] != 'pending':
        raise Exception("Only pending proposals can be rejected")

    supabase = get_supabase_client()
    response = supabase.table('proposals') \
        .update({
            'status': 'rejected',
            'reviewed_by': reviewed_by,
            'review_notes': review_notes,
            'reviewed_at': 'now()'
        }) \
        .eq('id', proposal_id) \
        .execute()

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
    create_item(
        org_id=proposal['org_id'],
        name=proposal['item_name'],
        description=proposal.get('item_description', ''),
        category=proposal.get('item_category', ''),
        metadata=proposal.get('item_metadata', {}),
        created_by=created_by
    )


def _merge_replace_item(proposal: Dict, created_by: str):
    """Deprecate old item and create replacement."""
    # Deprecate old item
    old_item_id = proposal['replacing_item_id']

    # Create new item
    new_item = create_item(
        org_id=proposal['org_id'],
        name=proposal['item_name'],
        description=proposal.get('item_description', ''),
        category=proposal.get('item_category', ''),
        metadata=proposal.get('item_metadata', {}),
        created_by=created_by
    )

    # Update old item to deprecated with replacement link
    update_item(old_item_id, {
        'status': 'deprecated',
        'replacement_item_id': new_item['id']
    })


def _merge_deprecate_item(proposal: Dict, updated_by: str):
    """Mark item as deprecated."""
    item_id = proposal['replacing_item_id']
    update_item(item_id, {'status': 'deprecated'})
