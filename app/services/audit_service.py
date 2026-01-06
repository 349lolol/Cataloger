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
        logger.warning(f"Failed to log audit event: {event_type}")
        return {}

    return response.data[0]


def get_audit_log(
    org_id: str,
    limit: int = 100,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> List[Dict]:
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
