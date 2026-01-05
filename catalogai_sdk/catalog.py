"""
Catalog operations for CatalogAI SDK
"""


class CatalogClient:
    """Client for catalog item operations."""

    def __init__(self, http_client):
        self.client = http_client

    def search(self, query: str, threshold: float = 0.3, limit: int = 10):
        """
        Search catalog items with semantic search.

        Args:
            query: Natural language search query
            threshold: Minimum similarity score (0-1)
            limit: Maximum number of results

        Returns:
            List of matching catalog items with similarity scores
        """
        response = self.client.post("/api/catalog/search", json={
            "query": query,
            "threshold": threshold,
            "limit": limit
        })
        response.raise_for_status()
        return response.json()["results"]

    def get(self, item_id: str):
        """
        Get catalog item by ID.

        Args:
            item_id: Catalog item UUID

        Returns:
            Catalog item data
        """
        response = self.client.get(f"/api/catalog/items/{item_id}")
        response.raise_for_status()
        return response.json()

    def list(self, status: str = None, limit: int = 100):
        """
        List catalog items.

        Args:
            status: Filter by status (optional)
            limit: Maximum number of results

        Returns:
            List of catalog items
        """
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = self.client.get("/api/catalog/items", params=params)
        response.raise_for_status()
        return response.json()["items"]

    def create(self, name: str, description: str = "", category: str = "",
               metadata: dict = None, price: float = None, pricing_type: str = None,
               vendor: str = None, sku: str = None, product_url: str = None):
        """
        Create a new catalog item (requires admin role).

        Args:
            name: Item name
            description: Item description
            category: Item category
            metadata: Additional metadata dict
            price: Price in USD (optional)
            pricing_type: "one_time", "monthly", "yearly", or "usage_based" (optional)
            vendor: Vendor name (optional)
            sku: SKU or product code (optional)
            product_url: Product URL (optional)

        Returns:
            Created catalog item
        """
        data = {
            "name": name,
            "description": description,
            "category": category,
            "metadata": metadata or {}
        }
        if price is not None:
            data["price"] = price
        if pricing_type:
            data["pricing_type"] = pricing_type
        if vendor:
            data["vendor"] = vendor
        if sku:
            data["sku"] = sku
        if product_url:
            data["product_url"] = product_url

        response = self.client.post("/api/catalog/items", json=data)
        response.raise_for_status()
        return response.json()

    def request_new_item(self, name: str, description: str = "", category: str = "",
                        metadata: dict = None, justification: str = None,
                        use_ai_enrichment: bool = True):
        """
        Request a new item to be added to the catalog.
        This creates a proposal that requires reviewer/admin approval.

        Use this when search doesn't return good results and you need a new item.

        Args:
            name: Item name (if use_ai_enrichment=True, just the product name is enough)
            description: Item description (optional if AI enrichment is on)
            category: Item category (optional if AI enrichment is on)
            metadata: Additional metadata
            justification: Why this item is needed
            use_ai_enrichment: Use Gemini AI to auto-fill product details (default: True)

        Returns:
            Dict with proposal data and next steps
        """
        response = self.client.post("/api/catalog/request-new-item", json={
            "name": name,
            "description": description,
            "category": category,
            "metadata": metadata or {},
            "justification": justification,
            "use_ai_enrichment": use_ai_enrichment
        })
        response.raise_for_status()
        return response.json()
