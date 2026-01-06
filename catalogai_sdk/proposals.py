class ProposalClient:
    def __init__(self, http_client):
        self.client = http_client

    def create(
        self,
        proposal_type: str,
        item_name: str = None,
        item_description: str = None,
        item_category: str = None,
        item_metadata: dict = None,
        item_price: float = None,
        item_pricing_type: str = None,
        item_vendor: str = None,
        item_sku: str = None,
        item_product_url: str = None,
        replacing_item_id: str = None,
        request_id: str = None
    ):
        data = {"proposal_type": proposal_type}
        if item_name:
            data["item_name"] = item_name
        if item_description:
            data["item_description"] = item_description
        if item_category:
            data["item_category"] = item_category
        if item_metadata:
            data["item_metadata"] = item_metadata
        if item_price is not None:
            data["item_price"] = item_price
        if item_pricing_type:
            data["item_pricing_type"] = item_pricing_type
        if item_vendor:
            data["item_vendor"] = item_vendor
        if item_sku:
            data["item_sku"] = item_sku
        if item_product_url:
            data["item_product_url"] = item_product_url
        if replacing_item_id:
            data["replacing_item_id"] = replacing_item_id
        if request_id:
            data["request_id"] = request_id

        response = self.client.post("/api/proposals", json=data)
        response.raise_for_status()
        return response.json()

    def get(self, proposal_id: str):
        response = self.client.get(f"/api/proposals/{proposal_id}")
        response.raise_for_status()
        return response.json()

    def list(self, status: str = None, limit: int = 100):
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = self.client.get("/api/proposals", params=params)
        response.raise_for_status()
        return response.json()["proposals"]

    def approve(self, proposal_id: str, review_notes: str = None):
        response = self.client.post(
            f"/api/proposals/{proposal_id}/approve",
            json={"review_notes": review_notes} if review_notes else {}
        )
        response.raise_for_status()
        return response.json()

    def reject(self, proposal_id: str, review_notes: str = None):
        response = self.client.post(
            f"/api/proposals/{proposal_id}/reject",
            json={"review_notes": review_notes} if review_notes else {}
        )
        response.raise_for_status()
        return response.json()
