"""
Catalog API endpoints for item management and semantic search.
"""
from flask import Blueprint, request, jsonify, g
from app.middleware.auth_middleware import require_auth, require_role
from app.services import catalog_service, proposal_service

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

    try:
        results = catalog_service.search_items(
            query=data['query'],
            org_id=g.org_id,
            threshold=data.get('threshold', 0.3),
            limit=data.get('limit', 10)
        )
        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/catalog/items', methods=['GET'])
@require_auth
def list_items():
    """
    List catalog items for current organization.
    GET /api/catalog/items?status=active&limit=100
    """
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))

        items = catalog_service.list_items(
            org_id=g.org_id,
            status=status,
            limit=limit
        )
        return jsonify({"items": items}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/catalog/items/<item_id>', methods=['GET'])
@require_auth
def get_item(item_id):
    """
    Get a single catalog item by ID.
    GET /api/catalog/items/:id
    """
    try:
        item = catalog_service.get_item(item_id)
        if not item:
            return jsonify({"error": "Item not found"}), 404

        # Verify org ownership (RLS should handle this, but double-check)
        if item['org_id'] != g.org_id:
            return jsonify({"error": "Forbidden"}), 403

        return jsonify(item), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/catalog/items', methods=['POST'])
@require_auth
@require_role(['admin'])
def create_item():
    """
    Create a new catalog item (admin only).
    POST /api/catalog/items
    Body: {"name": "...", "description": "...", "category": "...", "metadata": {}}
    """
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400

    try:
        item = catalog_service.create_item(
            org_id=g.org_id,
            name=data['name'],
            description=data.get('description', ''),
            category=data.get('category', ''),
            metadata=data.get('metadata', {}),
            created_by=g.user_id
        )
        return jsonify(item), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/catalog/request-new-item', methods=['POST'])
@require_auth
def request_new_item():
    """
    Request a new item to be added to the catalog.
    This creates a proposal that needs reviewer/admin approval.

    Use this when search doesn't return good results and you need a new item added.

    POST /api/catalog/request-new-item
    Body: {
        "name": "Item name",
        "description": "Item description",
        "category": "Category",
        "metadata": {},
        "justification": "Why this item is needed",
        "search_query": "Original search query that failed" (optional)
    }

    Returns:
        Created proposal that will be reviewed by admins
    """
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Item name is required"}), 400

    try:
        # Create a proposal for adding the new item
        proposal = proposal_service.create_proposal(
            org_id=g.org_id,
            proposed_by=g.user_id,
            proposal_type='ADD_ITEM',
            item_name=data['name'],
            item_description=data.get('description', ''),
            item_category=data.get('category', ''),
            item_metadata=data.get('metadata', {})
        )

        return jsonify({
            "message": "New item request submitted for review",
            "proposal": proposal,
            "next_steps": "A reviewer will approve or reject your request. You'll be notified of the decision."
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
