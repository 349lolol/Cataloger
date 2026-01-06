from typing import List, Dict, Optional, Any
from app.extensions import get_supabase_admin
from app.services.audit_service import log_event


def _validate_search_results(search_results: Any) -> List[Dict]:
    if not isinstance(search_results, list):
        raise ValueError("search_results must be a list")

    validated_results = []
    for idx, result in enumerate(search_results):
        if not isinstance(result, dict):
            raise ValueError(f"search_results[{idx}] must be a dictionary")

        if 'name' not in result:
            raise ValueError(f"search_results[{idx}] missing required field 'name'")

        normalized = {
            'name': str(result['name']),
            'description': result.get('description', ''),
            'category': result.get('category', ''),
            'similarity_score': float(result.get('similarity_score', 0.0))
        }

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
    validated_results = _validate_search_results(search_results)

    supabase = get_supabase_admin()
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
    supabase = get_supabase_admin()
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
    supabase = get_supabase_admin()
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
    if status not in ['approved', 'rejected']:
        raise ValueError("Status must be 'approved' or 'rejected'")

    current_request = get_request(request_id)

    if org_id and current_request['org_id'] != org_id:
        raise PermissionError("Cannot review request from different organization")

    if current_request['status'] != 'pending':
        raise Exception(f"Only pending requests can be reviewed (current: {current_request['status']})")

    supabase = get_supabase_admin()
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
        raise Exception("Failed to review request - may have been already reviewed")

    request = response.data[0]

    log_event(
        org_id=request['org_id'],
        event_type=f'request.{status}',
        actor_id=reviewed_by,
        resource_type='request',
        resource_id=request_id,
        metadata={'review_notes': review_notes}
    )

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
