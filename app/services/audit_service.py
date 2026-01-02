"""
Audit service for logging immutable event records.
All catalog operations are logged for compliance and debugging.
"""
import logging
from typing import Dict, List, Optional
from app.extensions import get_supabase_admin

logger = logging.getLogger(__name__)


def log_event(
    org_id: str,
    event_type: str,
    actor_id: str,
    resource_type: str,
    resource_id: str,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Log an audit event.
    Events are written via service role to bypass RLS.

    Args:
        org_id: Organization ID
        event_type: Type of event (e.g., 'catalog.item.created')
        actor_id: User ID who performed the action
        resource_type: Type of resource affected (e.g., 'catalog_item')
        resource_id: ID of the affected resource
        metadata: Additional event data (optional)

    Returns:
        Created audit event data
    """
    supabase_admin = get_supabase_admin()

    event_data = {
        'org_id': org_id,
        'event_type': event_type,
        'actor_id': actor_id,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'metadata': metadata or {}
    }

    response = supabase_admin.table('audit_events').insert(event_data).execute()

    if not response.data:
        # Issue #4.4: Log failure using logger instead of print
        logger.warning(f"Failed to log audit event: {event_type} for resource {resource_type}/{resource_id}")
        return {}

    return response.data[0]


def get_audit_log(
    org_id: str,
    limit: int = 100,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> List[Dict]:
    """
    Retrieve audit log entries for an organization.

    Args:
        org_id: Organization ID
        limit: Maximum number of entries to return
        event_type: Filter by event type (optional)
        resource_type: Filter by resource type (optional)
        resource_id: Filter by specific resource ID (optional)

    Returns:
        List of audit events
    """
    supabase_admin = get_supabase_admin()

    query = supabase_admin.table('audit_events') \
        .select('*') \
        .eq('org_id', org_id) \
        .order('created_at', desc=True) \
        .limit(limit)

    if event_type:
        query = query.eq('event_type', event_type)
    if resource_type:
        query = query.eq('resource_type', resource_type)
    if resource_id:
        query = query.eq('resource_id', resource_id)

    response = query.execute()
    return response.data if response.data else []
