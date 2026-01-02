"""
Request service for managing procurement requests.
Requests represent the search → approval workflow.
"""
from typing import List, Dict, Optional, Any
from app.extensions import get_supabase_client
from app.services.audit_service import log_event


def _validate_search_results(search_results: Any) -> List[Dict]:
    """
    Validate and normalize search_results structure.

    Args:
        search_results: Raw search results (can be list of dicts or other formats)

    Returns:
        Validated list of search result dictionaries

    Raises:
        ValueError: If search results format is invalid
    """
    if not isinstance(search_results, list):
        raise ValueError("search_results must be a list")

    validated_results = []
    for idx, result in enumerate(search_results):
        if not isinstance(result, dict):
            raise ValueError(f"search_results[{idx}] must be a dictionary")

        # Ensure required fields exist
        if 'name' not in result:
            raise ValueError(f"search_results[{idx}] missing required field 'name'")

        # Build normalized result with optional fields
        normalized = {
            'name': str(result['name']),
            'description': result.get('description', ''),
            'category': result.get('category', ''),
            'similarity_score': float(result.get('similarity_score', 0.0))
        }

        # Add optional product fields if present
        if 'price' in result:
            normalized['price'] = result['price']
        if 'vendor' in result:
            normalized['vendor'] = result['vendor']
        if 'sku' in result:
            normalized['sku'] = result['sku']

        validated_results.append(normalized)

    return validated_results


def create_request(
    org_id: str,
    created_by: str,
    search_query: str,
    search_results: List[Dict],
    justification: Optional[str] = None
) -> Dict:
    """
    Create a new procurement request.

    Args:
        org_id: Organization ID
        created_by: User ID of requester
        search_query: Original search query
        search_results: Snapshot of search results (will be validated and normalized)
        justification: Optional justification text

    Returns:
        Created request data

    Raises:
        ValueError: If search_results format is invalid
    """
    # Validate and normalize search results
    validated_results = _validate_search_results(search_results)

    supabase = get_supabase_client()
    response = supabase.table('requests').insert({
        'org_id': org_id,
        'created_by': created_by,
        'search_query': search_query,
        'search_results': validated_results,
        'justification': justification,
        'status': 'pending'
    }).execute()

    if not response.data:
        raise Exception("Failed to create request")

    request = response.data[0]

    # Log audit event
    log_event(
        org_id=org_id,
        event_type='request.created',
        actor_id=created_by,
        resource_type='request',
        resource_id=request['id'],
        metadata={'search_query': search_query}
    )

    return request


def get_request(request_id: str) -> Dict:
    """
    Get a single request by ID.

    Args:
        request_id: Request UUID

    Returns:
        Request data

    Raises:
        Exception: If request not found
    """
    supabase = get_supabase_client()
    response = supabase.table('requests') \
        .select('*') \
        .eq('id', request_id) \
        .single() \
        .execute()

    if not response.data:
        raise Exception(f"Request not found: {request_id}")

    return response.data


def list_requests(
    org_id: str,
    status: Optional[str] = None,
    created_by: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    List requests for an organization.

    Args:
        org_id: Organization ID
        status: Filter by status (optional)
        created_by: Filter by creator (optional)
        limit: Maximum number of results

    Returns:
        List of requests
    """
    supabase = get_supabase_client()
    query = supabase.table('requests') \
        .select('*') \
        .eq('org_id', org_id) \
        .order('created_at', desc=True) \
        .limit(limit)

    if status:
        query = query.eq('status', status)
    if created_by:
        query = query.eq('created_by', created_by)

    response = query.execute()
    return response.data if response.data else []


def review_request(
    request_id: str,
    reviewed_by: str,
    status: str,
    review_notes: Optional[str] = None,
    create_proposal: Optional[Dict] = None,
    org_id: Optional[str] = None
) -> Dict:
    """
    Approve or reject a request.
    Requires reviewer or admin role (enforced by RLS).

    This function supports an optional auto-proposal workflow:
    - If create_proposal is provided and status is 'approved', a proposal is auto-created
    - If create_proposal is omitted, the request is simply marked approved/rejected
    - This flexibility allows reviewers to handle cases where the requested item already exists

    Args:
        request_id: Request UUID
        reviewed_by: User ID of reviewer
        status: New status ('approved' or 'rejected')
        review_notes: Optional review comments
        create_proposal: Optional dict to auto-create proposal on approval (ignored if rejecting):
            {
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
                "replacing_item_id": "..." (for REPLACE/DEPRECATE only)
            }

    Returns:
        Updated request data with optional 'proposal' key if auto-created

    Example:
        # Approve without creating proposal (item already exists)
        review_request(req_id, user_id, 'approved', 'Item already in catalog')

        # Approve and auto-create proposal (streamlined workflow)
        review_request(req_id, user_id, 'approved', create_proposal={
            'proposal_type': 'ADD_ITEM',
            'item_name': 'MacBook Pro 16"',
            'item_category': 'Electronics'
        })
    """
    if status not in ['approved', 'rejected']:
        raise ValueError("Status must be 'approved' or 'rejected'")

    # Get current request to validate status transition
    # Note: get_request raises Exception if not found, no null check needed
    current_request = get_request(request_id)

    # Issue #9: Validate org_id matches if provided (defense in depth)
    if org_id and current_request['org_id'] != org_id:
        raise PermissionError("Cannot review request from different organization")

    # Only pending requests can be reviewed
    if current_request['status'] != 'pending':
        raise Exception(f"Only pending requests can be reviewed (current status: {current_request['status']})")

    # Issue #7: Prevent race condition by including status check in update query
    # This ensures atomic check-and-update (optimistic locking)
    supabase = get_supabase_client()
    response = supabase.table('requests') \
        .update({
            'status': status,
            'reviewed_by': reviewed_by,
            'review_notes': review_notes,
            'reviewed_at': 'now()'
        }) \
        .eq('id', request_id) \
        .eq('status', 'pending') \
        .execute()

    if not response.data:
        # Either request not found or status changed (race condition)
        raise Exception("Failed to review request - it may have been already reviewed")

    request = response.data[0]

    # Log audit event
    log_event(
        org_id=request['org_id'],
        event_type=f'request.{status}',
        actor_id=reviewed_by,
        resource_type='request',
        resource_id=request_id,
        metadata={'review_notes': review_notes}
    )

    # Auto-create proposal if requested and status is approved
    if status == 'approved' and create_proposal:
        from app.services.proposal_service import create_proposal as create_prop

        proposal = create_prop(
            org_id=request['org_id'],
            proposed_by=reviewed_by,
            proposal_type=create_proposal['proposal_type'],
            request_id=request_id,
            item_name=create_proposal.get('item_name'),
            item_description=create_proposal.get('item_description'),
            item_category=create_proposal.get('item_category'),
            item_metadata=create_proposal.get('item_metadata', {}),
            item_price=create_proposal.get('item_price'),
            item_pricing_type=create_proposal.get('item_pricing_type'),
            item_product_url=create_proposal.get('item_product_url'),
            item_vendor=create_proposal.get('item_vendor'),
            item_sku=create_proposal.get('item_sku'),
            replacing_item_id=create_proposal.get('replacing_item_id')
        )
        request['proposal'] = proposal

    return request
