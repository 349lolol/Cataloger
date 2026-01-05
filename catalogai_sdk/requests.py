"""
Request operations for CatalogAI SDK
"""


class RequestClient:
    """Client for procurement request operations."""

    def __init__(self, http_client):
        self.client = http_client

    def create(self, search_query: str, search_results: list, justification: str = None):
        """
        Create a new procurement request.

        Args:
            search_query: Original search query
            search_results: Snapshot of search results
            justification: Optional justification text

        Returns:
            Created request data
        """
        response = self.client.post("/api/requests", json={
            "search_query": search_query,
            "search_results": search_results,
            "justification": justification
        })
        response.raise_for_status()
        return response.json()

    def get(self, request_id: str):
        """Get request by ID."""
        response = self.client.get(f"/api/requests/{request_id}")
        response.raise_for_status()
        return response.json()

    def list(self, status: str = None, created_by: str = None, limit: int = 100):
        """
        List requests.

        Args:
            status: Filter by status (optional)
            created_by: Filter by creator (optional)
            limit: Maximum number of results

        Returns:
            List of requests
        """
        params = {"limit": limit}
        if status:
            params["status"] = status
        if created_by:
            params["created_by"] = created_by

        response = self.client.get("/api/requests", params=params)
        response.raise_for_status()
        return response.json()["requests"]

    def review(self, request_id: str, status: str, review_notes: str = None,
               create_proposal: dict = None):
        """
        Approve or reject a request (requires reviewer/admin role).

        Args:
            request_id: Request UUID
            status: "approved" or "rejected"
            review_notes: Optional review comments
            create_proposal: Optional dict to auto-create a proposal when approving.
                            Keys: proposal_type, item_name, item_description, item_category,
                            item_metadata, item_price, item_pricing_type, item_vendor,
                            item_sku, item_product_url, replacing_item_id

        Returns:
            Updated request data (includes 'proposal' key if create_proposal was used)
        """
        data = {
            "status": status,
            "review_notes": review_notes
        }
        if create_proposal:
            data["create_proposal"] = create_proposal

        response = self.client.post(f"/api/requests/{request_id}/review", json=data)
        response.raise_for_status()
        return response.json()
