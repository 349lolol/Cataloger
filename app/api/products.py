import logging
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth
from app.services.product_enrichment_service import enrich_product, enrich_product_batch

logger = logging.getLogger(__name__)
bp = Blueprint('products', __name__)


@bp.route('/products/enrich', methods=['POST'])
@require_auth
def enrich_product_endpoint():
    data = request.get_json()

    if not data or 'product_name' not in data:
        return jsonify({"error": "product_name is required"}), 400

    try:
        enriched_data = enrich_product(
            product_name=data['product_name'],
            category=data.get('category'),
            additional_context=data.get('additional_context')
        )

        return jsonify(enriched_data), 200

    except ValueError as e:
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception as e:
        logger.exception(f"Product enrichment failed: {e}")
        return jsonify({"error": "Product enrichment temporarily unavailable"}), 500


@bp.route('/products/enrich-batch', methods=['POST'])
@require_auth
def enrich_product_batch_endpoint():
    data = request.get_json()

    if not data or 'product_names' not in data:
        return jsonify({"error": "product_names is required"}), 400

    if not isinstance(data['product_names'], list):
        return jsonify({"error": "product_names must be an array"}), 400

    if len(data['product_names']) > 20:
        return jsonify({"error": "Maximum 20 products per batch"}), 400

    try:
        results = enrich_product_batch(data['product_names'])
        return jsonify({"results": results}), 200

    except Exception as e:
        logger.exception(f"Batch enrichment failed: {e}")
        return jsonify({"error": "Batch enrichment temporarily unavailable"}), 500
