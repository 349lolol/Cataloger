from flask import Blueprint, request, jsonify
from app.middleware.auth_middleware import require_auth
from app.middleware.error_responses import BadRequestError
from app.services.product_enrichment_service import enrich_product, enrich_product_batch

bp = Blueprint('products', __name__)


@bp.route('/products/enrich', methods=['POST'])
@require_auth
def enrich_product_endpoint():
    data = request.get_json()

    if not data or 'product_name' not in data:
        raise BadRequestError("product_name is required")

    enriched_data = enrich_product(
        product_name=data['product_name'],
        category=data.get('category'),
        additional_context=data.get('additional_context')
    )

    return jsonify(enriched_data), 200


@bp.route('/products/enrich-batch', methods=['POST'])
@require_auth
def enrich_product_batch_endpoint():
    data = request.get_json()

    if not data or 'product_names' not in data:
        raise BadRequestError("product_names is required")

    if not isinstance(data['product_names'], list):
        raise BadRequestError("product_names must be an array")

    if len(data['product_names']) > 20:
        raise BadRequestError("Maximum 20 products per batch")

    results = enrich_product_batch(data['product_names'])
    return jsonify({"results": results}), 200
