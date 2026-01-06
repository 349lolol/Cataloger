class RequestClient:
    def __init__(self, http_client):
        self.client = http_client

    def create(self, search_query: str, search_results: list, justification: str = None):
        response = self.client.post("/api/requests", json={
            "search_query": search_query,
            "search_results": search_results,
            "justification": justification
        })
        response.raise_for_status()
        return response.json()

    def get(self, request_id: str):
        response = self.client.get(f"/api/requests/{request_id}")
        response.raise_for_status()
        return response.json()

    def list(self, status: str = None, created_by: str = None, limit: int = 100):
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
        data = {
            "status": status,
            "review_notes": review_notes
        }
        if create_proposal:
            data["create_proposal"] = create_proposal

        response = self.client.post(f"/api/requests/{request_id}/review", json=data)
        response.raise_for_status()
        return response.json()
