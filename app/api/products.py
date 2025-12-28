"""
Product enrichment API endpoints.
Uses AI to automatically populate product fields from a product name.
"""
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth
from app.services.product_enrichment_service import enrich_product, enrich_product_batch

bp = Blueprint('products', __name__')


@bp.route('/products/enrich', methods=['POST'])
@require_auth
def enrich_product_endpoint():
    """
    Enrich a product name with AI-populated fields.

    POST /api/products/enrich

    Body: {
        "product_name": "MacBook Pro 16 inch M3 Max",
        "category": "Electronics",  // Optional hint
        "additional_context": "..."  // Optional disambiguation
    }

    Response: {
        "name": "MacBook Pro 16-inch (M3 Max, 2023)",
        "description": "High-performance laptop with M3 Max chip...",
        "category": "Electronics",
        "vendor": "Apple",
        "price": 3499.00,
        "pricing_type": "one_time",
        "product_url": "https://www.apple.com/macbook-pro/",
        "sku": "MRW13LL/A",
        "metadata": {
            "brand": "Apple",
            "screen_size": "16 inches",
            "processor": "M3 Max",
            "ram": "36GB",
            "storage": "1TB SSD"
        },
        "confidence": "high"
    }

    Use Cases:
    1. User types product name → AI fills in all fields → reviewer approves
    2. Pre-fill proposal form with enriched data
    3. Validate/update existing catalog items

    Note: This uses Gemini with Google Search grounding for real-time data.
    """
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
        return jsonify({"error": f"Enrichment failed: {str(e)}"}), 500


@bp.route('/products/enrich-batch', methods=['POST'])
@require_auth
def enrich_product_batch_endpoint():
    """
    Enrich multiple products in batch.

    POST /api/products/enrich-batch

    Body: {
        "product_names": [
            "MacBook Pro 16 inch M3 Max",
            "Dell XPS 15",
            "Logitech MX Master 3S"
        ]
    }

    Response: {
        "results": [
            { ...enriched product 1... },
            { ...enriched product 2... },
            { ...enriched product 3... }
        ]
    }

    Note: Processes sequentially to avoid rate limits.
    For large batches, consider pagination or async processing.
    """
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
        return jsonify({"error": f"Batch enrichment failed: {str(e)}"}), 500
