"""
Catalog API endpoints for item management and semantic search.
"""
import logging
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.services import catalog_service, proposal_service
from app.utils.resilience import safe_int, is_valid_uuid, validate_metadata

logger = logging.getLogger(__name__)

bp = Blueprint('catalog', __name__)


@bp.route('/catalog/search', methods=['POST'])
@require_auth
def search_items():
    """
    Semantic search for catalog items.
    POST /api/catalog/search
    Body: {"query": "search text", "threshold": 0.3, "limit": 10}
    """
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Query is required"}), 400

    # Issue #3.3: Validate threshold range (0.0 to 1.0)
    threshold = data.get('threshold', 0.3)
    if not isinstance(threshold, (int, float)) or threshold < 0.0 or threshold > 1.0:
        return jsonify({"error": "threshold must be a number between 0.0 and 1.0"}), 400

    # Issue #3.3: Validate limit range (1 to 100 for search to prevent abuse)
    limit = data.get('limit', 10)
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        return jsonify({"error": "limit must be an integer between 1 and 100"}), 400

    try:
        results = catalog_service.search_items(
            query=data['query'],
            org_id=g.org_id,
            threshold=threshold,
            limit=limit
        )
        return jsonify({"results": results}), 200
    except Exception as e:
        logger.exception(f"Catalog search failed: {e}")
        return jsonify({"error": "Search temporarily unavailable"}), 500


@bp.route('/catalog/items', methods=['GET'])
@require_auth
def list_items():
    """
    List catalog items for current organization.
    GET /api/catalog/items?status=active&limit=100
    """
    try:
        status = request.args.get('status')
        limit = safe_int(request.args.get('limit'), default=100, min_val=1, max_val=1000)

        items = catalog_service.list_items(
            org_id=g.org_id,
            status=status,
            limit=limit
        )
        return jsonify({"items": items}), 200
    except Exception as e:
        logger.exception(f"List items failed: {e}")
        return jsonify({"error": "Failed to retrieve catalog items"}), 500


@bp.route('/catalog/items/<item_id>', methods=['GET'])
@require_auth
def get_item(item_id):
    """
    Get a single catalog item by ID.
    GET /api/catalog/items/:id
    """
    # Issue #23: Validate UUID format
    if not is_valid_uuid(item_id):
        return jsonify({"error": "Invalid item ID format"}), 400

    try:
        item = catalog_service.get_item(item_id)

        # Verify org ownership (RLS should handle this, but double-check)
        if item['org_id'] != g.org_id:
            return jsonify({"error": "Forbidden"}), 403

        return jsonify(item), 200
    except Exception as e:
        logger.exception(f"Get item failed for {item_id}: {e}")
        return jsonify({"error": "Item not found or unavailable"}), 500


@bp.route('/catalog/items', methods=['POST'])
@require_auth
@require_role(['admin'])
def create_item():
    """
    Create a new catalog item (admin only).
    POST /api/catalog/items
    Body: {
        "name": "Product Name",
        "description": "Product description",
        "category": "Electronics | Furniture | Services | Office Supplies",
        "price": 99.99,  // Optional
        "pricing_type": "one_time | monthly | yearly | usage_based",  // Optional
        "product_url": "https://vendor.com/product",  // Optional
        "vendor": "Vendor Name",  // Optional
        "sku": "PRODUCT-123",  // Optional
        "metadata": {"brand": "...", "warranty": "..."}  // Optional flexible attrs
    }
    """
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400

    # Issue #7.4: Validate metadata size to prevent abuse
    valid, error = validate_metadata(data.get('metadata'))
    if not valid:
        return jsonify({"error": error}), 400

    try:
        item = catalog_service.create_item(
            org_id=g.org_id,
            name=data['name'],
            description=data.get('description', ''),
            category=data.get('category', ''),
            created_by=g.user_id,
            price=data.get('price'),
            pricing_type=data.get('pricing_type'),
            product_url=data.get('product_url'),
            vendor=data.get('vendor'),
            sku=data.get('sku'),
            metadata=data.get('metadata')
        )
        return jsonify(item), 201
    except Exception as e:
        logger.exception(f"Create item failed: {e}")
        return jsonify({"error": "Failed to create catalog item"}), 500


@bp.route('/catalog/request-new-item', methods=['POST'])
@require_auth
def request_new_item():
    """
    Request a new item to be added to the catalog.
    This creates a proposal that needs reviewer/admin approval.

    Use this when search doesn't return good results and you need a new item added.

    POST /api/catalog/request-new-item

    Body Option 1 - AI Enrichment (Recommended):
    {
        "name": "MacBook Pro 16 inch M3 Max",  // Just the product name
        "use_ai_enrichment": true,             // Enable AI auto-fill
        "justification": "Why this item is needed"
    }
    → AI will automatically populate: description, category, vendor, price, SKU, product_url, metadata

    Body Option 2 - Manual Entry:
    {
        "name": "Item name",
        "description": "Item description",
        "category": "Category",
        "metadata": {},
        "price": 99.99,
        "pricing_type": "one_time | monthly | yearly | usage_based",
        "product_url": "https://...",
        "vendor": "Vendor name",
        "sku": "SKU-123",
        "justification": "Why this item is needed",
        "use_ai_enrichment": false  // or omit (default)
    }

    Returns:
        Created proposal that will be reviewed by admins
    """
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Item name is required"}), 400

    try:
        # Determine if AI enrichment should be used
        use_ai = data.get('use_ai_enrichment', False)

        if use_ai:
            # Use AI to enrich product data
            from app.services.product_enrichment_service import enrich_product

            enriched = enrich_product(
                product_name=data['name'],
                category=data.get('category'),
                additional_context=data.get('justification')
            )

            # Use enriched data, but allow manual overrides
            item_name = data.get('name', enriched['name'])
            item_description = data.get('description', enriched['description'])
            item_category = data.get('category', enriched['category'])
            item_vendor = data.get('vendor', enriched['vendor'])
            item_price = data.get('price', enriched.get('price'))
            item_pricing_type = data.get('pricing_type', enriched.get('pricing_type'))
            item_product_url = data.get('product_url', enriched.get('product_url'))
            item_sku = data.get('sku', enriched.get('sku'))
            item_metadata = data.get('metadata', enriched.get('metadata', {}))

            # Add AI enrichment metadata
            item_metadata['ai_enriched'] = True
            item_metadata['ai_confidence'] = enriched.get('confidence', 'unknown')

        else:
            # Use manually provided data
            item_name = data['name']
            item_description = data.get('description', '')
            item_category = data.get('category', '')
            item_vendor = data.get('vendor')
            item_price = data.get('price')
            item_pricing_type = data.get('pricing_type')
            item_product_url = data.get('product_url')
            item_sku = data.get('sku')
            item_metadata = data.get('metadata', {})

        # Create a proposal for adding the new item
        proposal = proposal_service.create_proposal(
            org_id=g.org_id,
            proposed_by=g.user_id,
            proposal_type='ADD_ITEM',
            item_name=item_name,
            item_description=item_description,
            item_category=item_category,
            item_metadata=item_metadata,
            item_price=item_price,
            item_pricing_type=item_pricing_type,
            item_product_url=item_product_url,
            item_vendor=item_vendor,
            item_sku=item_sku
        )

        response_data = {
            "message": "New item request submitted for review",
            "proposal": proposal,
            "next_steps": "A reviewer will approve or reject your request. You'll be notified of the decision."
        }

        # If AI enrichment was used, include the enrichment data in response
        if use_ai:
            response_data["ai_enrichment"] = enriched

        return jsonify(response_data), 201

    except Exception as e:
        logger.exception(f"Request new item failed: {e}")
        return jsonify({"error": "Failed to submit item request"}), 500
