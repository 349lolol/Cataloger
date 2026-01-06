class CatalogClient:
    def __init__(self, http_client):
        self.client = http_client

    def search(self, query: str, threshold: float = 0.3, limit: int = 10):
        response = self.client.post("/api/catalog/search", json={
            "query": query,
            "threshold": threshold,
            "limit": limit
        })
        response.raise_for_status()
        return response.json()["results"]

    def get(self, item_id: str):
        response = self.client.get(f"/api/catalog/items/{item_id}")
        response.raise_for_status()
        return response.json()

    def list(self, status: str = None, limit: int = 100):
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = self.client.get("/api/catalog/items", params=params)
        response.raise_for_status()
        return response.json()["items"]

    def create(self, name: str, description: str = "", category: str = "",
               metadata: dict = None, price: float = None, pricing_type: str = None,
               vendor: str = None, sku: str = None, product_url: str = None):
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
