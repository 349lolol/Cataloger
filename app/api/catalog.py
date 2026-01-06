import logging
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.services import catalog_service, proposal_service
from app.utils.resilience import safe_int, is_valid_uuid, validate_metadata

logger = logging.getLogger(__name__)
bp = Blueprint('catalog', __name__)

VALID_PRICING_TYPES = ('one_time', 'monthly', 'yearly', 'usage_based')

MAX_NAME_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 10000
MAX_CATEGORY_LENGTH = 100
MAX_VENDOR_LENGTH = 255
MAX_SKU_LENGTH = 100
MAX_URL_LENGTH = 2048
MAX_PRICE = 10000000


def _validate_string_field(value, field_name: str, max_length: int, required: bool = False) -> tuple:
    if value is None:
        if required:
            return False, f"{field_name} is required"
        return True, None

    if not isinstance(value, str):
        return False, f"{field_name} must be a string"

    if len(value) > max_length:
        return False, f"{field_name} must be at most {max_length} characters"

    if '<script' in value.lower() or 'javascript:' in value.lower():
        return False, f"{field_name} contains invalid content"

    return True, None


def _validate_url(url: str) -> tuple:
    if url is None:
        return True, None

    if not isinstance(url, str):
        return False, "product_url must be a string"

    if len(url) > MAX_URL_LENGTH:
        return False, f"product_url must be at most {MAX_URL_LENGTH} characters"

    if url and not (url.startswith('http://') or url.startswith('https://')):
        return False, "product_url must start with http:// or https://"

    return True, None


@bp.route('/catalog/search', methods=['POST'])
@require_auth
def search_items():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Query is required"}), 400

    threshold = data.get('threshold', 0.3)
    if not isinstance(threshold, (int, float)) or threshold < 0.0 or threshold > 1.0:
        return jsonify({"error": "threshold must be a number between 0.0 and 1.0"}), 400

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
    if not is_valid_uuid(item_id):
        return jsonify({"error": "Invalid item ID format"}), 400

    try:
        item = catalog_service.get_item(item_id)

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
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400

    valid, error = _validate_string_field(data.get('name'), 'name', MAX_NAME_LENGTH, required=True)
    if not valid:
        return jsonify({"error": error}), 400

    valid, error = _validate_string_field(data.get('description'), 'description', MAX_DESCRIPTION_LENGTH)
    if not valid:
        return jsonify({"error": error}), 400

    valid, error = _validate_string_field(data.get('category'), 'category', MAX_CATEGORY_LENGTH)
    if not valid:
        return jsonify({"error": error}), 400

    valid, error = _validate_string_field(data.get('vendor'), 'vendor', MAX_VENDOR_LENGTH)
    if not valid:
        return jsonify({"error": error}), 400

    valid, error = _validate_string_field(data.get('sku'), 'sku', MAX_SKU_LENGTH)
    if not valid:
        return jsonify({"error": error}), 400

    valid, error = _validate_url(data.get('product_url'))
    if not valid:
        return jsonify({"error": error}), 400

    price = data.get('price')
    if price is not None:
        if not isinstance(price, (int, float)):
            return jsonify({"error": "price must be a number"}), 400
        if price < 0:
            return jsonify({"error": "price cannot be negative"}), 400
        if price > MAX_PRICE:
            return jsonify({"error": f"price cannot exceed {MAX_PRICE}"}), 400
        price = round(price, 2)
        data['price'] = price

    pricing_type = data.get('pricing_type')
    if pricing_type is not None and pricing_type not in VALID_PRICING_TYPES:
        return jsonify({"error": f"pricing_type must be one of: {', '.join(VALID_PRICING_TYPES)}"}), 400

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
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Item name is required"}), 400

    try:
        use_ai = data.get('use_ai_enrichment', False)

        if use_ai:
            from app.services.product_enrichment_service import enrich_product

            enriched = enrich_product(
                product_name=data['name'],
                category=data.get('category'),
                additional_context=data.get('justification')
            )

            item_name = data.get('name', enriched['name'])
            item_description = data.get('description', enriched['description'])
            item_category = data.get('category', enriched['category'])
            item_vendor = data.get('vendor', enriched['vendor'])
            item_price = data.get('price', enriched.get('price'))
            item_pricing_type = data.get('pricing_type', enriched.get('pricing_type'))
            item_product_url = data.get('product_url', enriched.get('product_url'))
            item_sku = data.get('sku', enriched.get('sku'))
            item_metadata = data.get('metadata', enriched.get('metadata', {}))

            item_metadata['ai_enriched'] = True
            item_metadata['ai_confidence'] = enriched.get('confidence', 'unknown')
        else:
            item_name = data['name']
            item_description = data.get('description', '')
            item_category = data.get('category', '')
            item_vendor = data.get('vendor')
            item_price = data.get('price')
            item_pricing_type = data.get('pricing_type')
            item_product_url = data.get('product_url')
            item_sku = data.get('sku')
            item_metadata = data.get('metadata', {})

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
            "proposal": proposal
        }

        if use_ai:
            response_data["ai_enrichment"] = enriched

        return jsonify(response_data), 201

    except Exception as e:
        logger.exception(f"Request new item failed: {e}")
        return jsonify({"error": "Failed to submit item request"}), 500
