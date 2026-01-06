import pytest
from unittest.mock import Mock
import httpx
from catalogai_sdk.catalog import CatalogClient


class TestCatalogClient:

    def test_search_success(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [{"item_name": "Laptop", "similarity_score": 0.9}]
        }
        mock_client.post.return_value = mock_response

        client = CatalogClient(mock_client)
        results = client.search("laptop", limit=5)

        mock_client.post.assert_called_once()
        assert len(results) == 1
        assert results[0]["item_name"] == "Laptop"

    def test_search_raises_on_error(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=Mock(), response=Mock(status_code=404)
        )
        mock_client.post.return_value = mock_response

        client = CatalogClient(mock_client)

        with pytest.raises(httpx.HTTPStatusError):
            client.search("test")

    def test_get_item(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "item-123", "name": "Test Item"}
        mock_client.get.return_value = mock_response

        client = CatalogClient(mock_client)
        item = client.get("item-123")

        mock_client.get.assert_called_once_with("/api/catalog/items/item-123")
        assert item["id"] == "item-123"
        assert item["name"] == "Test Item"

    def test_list_items_with_filters(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {"id": "item-1", "status": "active"},
                {"id": "item-2", "status": "active"}
            ]
        }
        mock_client.get.return_value = mock_response

        client = CatalogClient(mock_client)
        items = client.list(status="active", limit=10)

        mock_client.get.assert_called_once()
        assert len(items) == 2

    def test_request_new_item(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": "New item request submitted",
            "proposal": {"id": "proposal-123", "status": "pending"}
        }
        mock_client.post.return_value = mock_response

        client = CatalogClient(mock_client)
        result = client.request_new_item(
            name="New Item",
            description="Test",
            category="Test",
            justification="Needed for testing"
        )

        mock_client.post.assert_called_once_with(
            "/api/catalog/request-new-item",
            json={
                "name": "New Item",
                "description": "Test",
                "category": "Test",
                "metadata": {},
                "justification": "Needed for testing",
                "use_ai_enrichment": True
            }
        )
        assert "proposal" in result
        assert result["proposal"]["id"] == "proposal-123"
