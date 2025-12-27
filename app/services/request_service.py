"""
Request service for managing procurement requests.
Requests represent the search → approval workflow.
"""
from typing import List, Dict, Optional
from app.extensions import get_supabase_client, get_supabase_admin
from app.services.audit_service import log_event


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
        search_results: Snapshot of search results
        justification: Optional justification text

    Returns:
        Created request data
    """
    supabase = get_supabase_client()
    response = supabase.table('requests').insert({
        'org_id': org_id,
        'created_by': created_by,
        'search_query': search_query,
        'search_results': search_results,
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


def get_request(request_id: str) -> Optional[Dict]:
    """
    Get a single request by ID.

    Args:
        request_id: Request UUID

    Returns:
        Request data or None if not found
    """
    supabase = get_supabase_client()
    response = supabase.table('requests') \
        .select('*') \
        .eq('id', request_id) \
        .single() \
        .execute()

    return response.data if response.data else None


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
    review_notes: Optional[str] = None
) -> Dict:
    """
    Approve or reject a request.
    Requires reviewer or admin role (enforced by RLS).

    Args:
        request_id: Request UUID
        reviewed_by: User ID of reviewer
        status: New status ('approved' or 'rejected')
        review_notes: Optional review comments

    Returns:
        Updated request data
    """
    if status not in ['approved', 'rejected']:
        raise ValueError("Status must be 'approved' or 'rejected'")

    supabase = get_supabase_client()
    response = supabase.table('requests') \
        .update({
            'status': status,
            'reviewed_by': reviewed_by,
            'review_notes': review_notes,
            'reviewed_at': 'now()'
        }) \
        .eq('id', request_id) \
        .execute()

    if not response.data:
        raise Exception("Failed to review request")

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

    return request
