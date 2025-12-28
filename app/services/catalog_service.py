"""
Catalog service for managing catalog items and semantic search.
"""
from typing import List, Dict, Optional
from uuid import UUID
from app.extensions import get_supabase_client, get_supabase_admin
from app.services.embedding_service import encode_text, encode_catalog_item
from app.services.audit_service import log_event


def check_and_repair_embeddings(org_id: str) -> Dict:
    """
    Check for catalog items missing embeddings and regenerate them.
    This is a maintenance function to fix any orphaned items.

    Args:
        org_id: Organization ID to check

    Returns:
        Dict with repair results:
        {
            "total_items": int,
            "items_with_embeddings": int,
            "items_without_embeddings": int,
            "repaired": int,
            "failed": int,
            "failed_items": [item_ids]
        }
    """
    supabase_admin = get_supabase_admin()

    # Get all active catalog items for this org
    items_response = supabase_admin.table('catalog_items') \
        .select('id, name, description, category') \
        .eq('org_id', org_id) \
        .eq('status', 'active') \
        .execute()

    total_items = len(items_response.data) if items_response.data else 0

    # Get all embeddings for this org's items
    if total_items == 0:
        return {
            "total_items": 0,
            "items_with_embeddings": 0,
            "items_without_embeddings": 0,
            "repaired": 0,
            "failed": 0,
            "failed_items": []
        }

    item_ids = [item['id'] for item in items_response.data]

    embeddings_response = supabase_admin.table('catalog_item_embeddings') \
        .select('catalog_item_id') \
        .in_('catalog_item_id', item_ids) \
        .execute()

    embedded_item_ids = set(
        emb['catalog_item_id'] for emb in (embeddings_response.data or [])
    )

    # Find items without embeddings
    items_without_embeddings = [
        item for item in items_response.data
        if item['id'] not in embedded_item_ids
    ]

    repaired = 0
    failed = 0
    failed_items = []

    # Repair missing embeddings
    for item in items_without_embeddings:
        try:
            embedding = encode_catalog_item(
                item['name'],
                item.get('description', ''),
                item.get('category', '')
            )
            supabase_admin.table('catalog_item_embeddings').insert({
                'catalog_item_id': item['id'],
                'embedding': embedding
            }).execute()
            repaired += 1
        except Exception as e:
            failed += 1
            failed_items.append(item['id'])
            print(f"Failed to repair embedding for item {item['id']}: {e}")

    return {
        "total_items": total_items,
        "items_with_embeddings": len(embedded_item_ids),
        "items_without_embeddings": len(items_without_embeddings),
        "repaired": repaired,
        "failed": failed,
        "failed_items": failed_items
    }


def search_items(
    query: str,
    org_id: str,
    threshold: float = 0.3,
    limit: int = 10
) -> List[Dict]:
    """
    Search catalog items using semantic similarity.

    Args:
        query: Natural language search query
        org_id: Organization ID for filtering
        threshold: Minimum similarity score (0-1)
        limit: Maximum number of results

    Returns:
        List of matching catalog items with similarity scores
    """
    # Generate embedding for search query
    query_embedding = encode_text(query)

    # Call Supabase RPC function for vector search
    supabase = get_supabase_client()
    response = supabase.rpc(
        'search_catalog_items',
        {
            'query_embedding': query_embedding,
            'org_uuid': org_id,
            'similarity_threshold': threshold,
            'result_limit': limit
        }
    ).execute()

    return response.data if response.data else []


def get_item(item_id: str) -> Dict:
    """
    Get a single catalog item by ID.

    Args:
        item_id: Catalog item UUID

    Returns:
        Catalog item data

    Raises:
        Exception: If item not found
    """
    supabase = get_supabase_client()
    response = supabase.table('catalog_items') \
        .select('*') \
        .eq('id', item_id) \
        .single() \
        .execute()

    if not response.data:
        raise Exception(f"Catalog item not found: {item_id}")

    return response.data


def list_items(org_id: str, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    List catalog items for an organization.

    Args:
        org_id: Organization ID
        status: Filter by status (optional)
        limit: Maximum number of results

    Returns:
        List of catalog items
    """
    supabase = get_supabase_client()
    query = supabase.table('catalog_items') \
        .select('*') \
        .eq('org_id', org_id) \
        .order('created_at', desc=True) \
        .limit(limit)

    if status:
        query = query.eq('status', status)

    response = query.execute()
    return response.data if response.data else []


def create_item(
    org_id: str,
    name: str,
    description: str,
    category: str,
    created_by: str,
    price: Optional[float] = None,
    pricing_type: Optional[str] = None,
    product_url: Optional[str] = None,
    vendor: Optional[str] = None,
    sku: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Create a new catalog item with embedding.
    This operation requires admin privileges (enforced by RLS).

    Args:
        org_id: Organization ID
        name: Item name
        description: Item description
        category: Item category (e.g., Electronics, Furniture, Services)
        created_by: User ID of creator
        price: Price in USD (optional)
        pricing_type: Billing type - 'one_time', 'monthly', 'yearly', 'usage_based' (optional)
        product_url: Link to vendor/product page (optional)
        vendor: Vendor or manufacturer name (optional)
        sku: Stock Keeping Unit or product code (optional)
        metadata: Additional flexible attributes (JSONB, optional)

    Returns:
        Created catalog item data
    """
    # Create catalog item
    supabase_admin = get_supabase_admin()
    item_data = {
        'org_id': org_id,
        'name': name,
        'description': description,
        'category': category,
        'created_by': created_by,
        'status': 'active'
    }

    # Add optional product fields
    if price is not None:
        item_data['price'] = price
    if pricing_type:
        item_data['pricing_type'] = pricing_type
    if product_url:
        item_data['product_url'] = product_url
    if vendor:
        item_data['vendor'] = vendor
    if sku:
        item_data['sku'] = sku
    if metadata:
        item_data['metadata'] = metadata

    item_response = supabase_admin.table('catalog_items').insert(item_data).execute()

    if not item_response.data:
        raise Exception("Failed to create catalog item")

    item = item_response.data[0]

    # Generate and store embedding
    # CRITICAL: This must succeed for search to work
    try:
        embedding = encode_catalog_item(name, description, category)
        embedding_response = supabase_admin.table('catalog_item_embeddings').insert({
            'catalog_item_id': item['id'],
            'embedding': embedding
        }).execute()

        if not embedding_response.data:
            raise Exception("Failed to create embedding - rolling back item creation")

    except Exception as e:
        # Rollback: delete the catalog item if embedding creation fails
        supabase_admin.table('catalog_items').delete().eq('id', item['id']).execute()
        raise Exception(f"Embedding generation failed, item creation rolled back: {str(e)}")

    # Log audit event
    log_event(
        org_id=org_id,
        event_type='catalog.item.created',
        actor_id=created_by,
        resource_type='catalog_item',
        resource_id=item['id'],
        metadata={'name': name, 'category': category}
    )

    return item


def update_item(item_id: str, updates: Dict, updated_by: str = None) -> Dict:
    """
    Update a catalog item and regenerate its embedding if content changed.

    Args:
        item_id: Catalog item UUID
        updates: Dictionary of fields to update
        updated_by: User ID of updater (for audit logging)

    Returns:
        Updated catalog item data
    """
    supabase_admin = get_supabase_admin()

    # Update the item
    response = supabase_admin.table('catalog_items') \
        .update(updates) \
        .eq('id', item_id) \
        .execute()

    if not response.data:
        raise Exception("Failed to update catalog item")

    updated_item = response.data[0]

    # Regenerate embedding if content fields changed
    if any(key in updates for key in ['name', 'description', 'category']):
        try:
            embedding = encode_catalog_item(
                updated_item['name'],
                updated_item.get('description', ''),
                updated_item.get('category', '')
            )
            embedding_response = supabase_admin.table('catalog_item_embeddings') \
                .update({'embedding': embedding}) \
                .eq('catalog_item_id', item_id) \
                .execute()

            if not embedding_response.data:
                # Warning: embedding update failed but item was updated
                # Log this but don't fail the entire operation
                print(f"WARNING: Failed to update embedding for item {item_id}")

        except Exception as e:
            # Log error but don't fail the update operation
            # The item data is still valid, just search might be degraded
            print(f"ERROR: Embedding regeneration failed for item {item_id}: {str(e)}")

    # Log audit event if updated_by is provided
    if updated_by:
        event_type = 'catalog.item.deprecated' if updates.get('status') == 'deprecated' else 'catalog.item.updated'
        log_event(
            org_id=updated_item['org_id'],
            event_type=event_type,
            actor_id=updated_by,
            resource_type='catalog_item',
            resource_id=item_id,
            metadata={k: v for k, v in updates.items() if k in ['name', 'status', 'category']}
        )

    return updated_item
