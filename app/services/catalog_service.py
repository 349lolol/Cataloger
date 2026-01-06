import logging
from typing import List, Dict, Optional
from app.extensions import get_supabase_admin
from app.services.embedding_service import encode_text, encode_catalog_item
from app.services.audit_service import log_event
from app.middleware.error_responses import NotFoundError, DatabaseError

logger = logging.getLogger(__name__)


def check_and_repair_embeddings(org_id: str) -> Dict:
    supabase_admin = get_supabase_admin()

    items_response = supabase_admin.table('catalog_items') \
        .select('id, name, description, category') \
        .eq('org_id', org_id) \
        .eq('status', 'active') \
        .execute()

    total_items = len(items_response.data) if items_response.data else 0

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

    items_without_embeddings = [
        item for item in items_response.data
        if item['id'] not in embedded_item_ids
    ]

    failed = 0
    failed_items = []
    embeddings_to_insert = []

    for item in items_without_embeddings:
        try:
            embedding = encode_catalog_item(
                item['name'],
                item.get('description', ''),
                item.get('category', '')
            )
            embeddings_to_insert.append({
                'catalog_item_id': item['id'],
                'embedding': embedding
            })
        except Exception as e:
            failed += 1
            failed_items.append(item['id'])
            logger.error(f"Failed to generate embedding for item {item['id']}: {e}")

    repaired = 0

    if embeddings_to_insert:
        try:
            supabase_admin.table('catalog_item_embeddings').insert(embeddings_to_insert).execute()
            repaired = len(embeddings_to_insert)
        except Exception as e:
            logger.warning(f"Batch insert failed, falling back to individual inserts: {e}")
            for emb_data in embeddings_to_insert:
                try:
                    supabase_admin.table('catalog_item_embeddings').insert(emb_data).execute()
                    repaired += 1
                except Exception as insert_error:
                    failed += 1
                    failed_items.append(emb_data['catalog_item_id'])
                    logger.error(f"Failed to insert embedding: {insert_error}")

    return {
        "total_items": total_items,
        "items_with_embeddings": len(embedded_item_ids),
        "items_without_embeddings": len(items_without_embeddings),
        "repaired": repaired,
        "failed": failed,
        "failed_items": failed_items
    }


def search_items(query: str, org_id: str, threshold: float = 0.3, limit: int = 10) -> List[Dict]:
    query_embedding = encode_text(query)

    supabase = get_supabase_admin()
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
    supabase = get_supabase_admin()
    response = supabase.table('catalog_items') \
        .select('*') \
        .eq('id', item_id) \
        .single() \
        .execute()

    if not response.data:
        raise NotFoundError("Catalog item", item_id)

    return response.data


def list_items(org_id: str, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    supabase = get_supabase_admin()
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
    supabase_admin = get_supabase_admin()
    item_data = {
        'org_id': org_id,
        'name': name,
        'description': description,
        'category': category,
        'created_by': created_by,
        'status': 'active'
    }

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
        raise DatabaseError("Failed to create catalog item")

    item = item_response.data[0]
    item_id = item['id']

    try:
        embedding = encode_catalog_item(name, description, category)
        embedding_response = supabase_admin.table('catalog_item_embeddings').insert({
            'catalog_item_id': item_id,
            'embedding': embedding
        }).execute()

        if not embedding_response.data:
            raise DatabaseError("Failed to create embedding")

    except Exception as e:
        try:
            supabase_admin.table('catalog_items').delete().eq('id', item_id).execute()
        except Exception as delete_error:
            logger.error(f"Failed to rollback item {item_id}: {delete_error}")
        raise DatabaseError(f"Item creation failed: {str(e)}")

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
    supabase_admin = get_supabase_admin()

    response = supabase_admin.table('catalog_items') \
        .update(updates) \
        .eq('id', item_id) \
        .execute()

    if not response.data:
        raise DatabaseError("Failed to update catalog item")

    updated_item = response.data[0]

    if any(key in updates for key in ['name', 'description', 'category']):
        try:
            embedding = encode_catalog_item(
                updated_item['name'],
                updated_item.get('description', ''),
                updated_item.get('category', '')
            )
            supabase_admin.table('catalog_item_embeddings') \
                .update({'embedding': embedding}) \
                .eq('catalog_item_id', item_id) \
                .execute()
        except Exception as e:
            logger.error(f"Embedding regeneration failed for item {item_id}: {str(e)}")

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
