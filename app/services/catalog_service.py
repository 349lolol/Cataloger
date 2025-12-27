"""
Catalog service for managing catalog items and semantic search.
"""
from typing import List, Dict, Optional
from uuid import UUID
from app.extensions import get_supabase_client, get_supabase_admin
from app.services.embedding_service import encode_text, encode_catalog_item


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


def get_item(item_id: str) -> Optional[Dict]:
    """
    Get a single catalog item by ID.

    Args:
        item_id: Catalog item UUID

    Returns:
        Catalog item data or None if not found
    """
    supabase = get_supabase_client()
    response = supabase.table('catalog_items') \
        .select('*') \
        .eq('id', item_id) \
        .single() \
        .execute()

    return response.data if response.data else None


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
    metadata: Dict,
    created_by: str
) -> Dict:
    """
    Create a new catalog item with embedding.
    This operation requires admin privileges (enforced by RLS).

    Args:
        org_id: Organization ID
        name: Item name
        description: Item description
        category: Item category
        metadata: Additional metadata (JSONB)
        created_by: User ID of creator

    Returns:
        Created catalog item data
    """
    # Create catalog item
    supabase_admin = get_supabase_admin()
    item_response = supabase_admin.table('catalog_items').insert({
        'org_id': org_id,
        'name': name,
        'description': description,
        'category': category,
        'metadata': metadata,
        'created_by': created_by,
        'status': 'active'
    }).execute()

    if not item_response.data:
        raise Exception("Failed to create catalog item")

    item = item_response.data[0]

    # Generate and store embedding
    embedding = encode_catalog_item(name, description, category)
    supabase_admin.table('catalog_item_embeddings').insert({
        'catalog_item_id': item['id'],
        'embedding': embedding
    }).execute()

    return item


def update_item(item_id: str, updates: Dict) -> Dict:
    """
    Update a catalog item and regenerate its embedding if content changed.

    Args:
        item_id: Catalog item UUID
        updates: Dictionary of fields to update

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
        embedding = encode_catalog_item(
            updated_item['name'],
            updated_item.get('description', ''),
            updated_item.get('category', '')
        )
        supabase_admin.table('catalog_item_embeddings') \
            .update({'embedding': embedding}) \
            .eq('catalog_item_id', item_id) \
            .execute()

    return updated_item
