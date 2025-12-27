"""
Unit tests for CatalogAI Python SDK - Catalog operations.
"""
import pytest
from unittest.mock import Mock, patch
import httpx
from catalogai_sdk.catalog import CatalogClient


class TestCatalogClient:
    """Test CatalogAI SDK catalog client."""

    def test_search_success(self):
        """Test successful catalog search."""
        # Setup mock HTTP client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {"item_name": "Laptop", "similarity_score": 0.9}
            ]
        }
        mock_client.post.return_value = mock_response

        # Create client and call search
        client = CatalogClient(mock_client)
        results = client.search("laptop", limit=5)

        # Assertions
        mock_client.post.assert_called_once()
        assert len(results) == 1
        assert results[0]["item_name"] == "Laptop"

    def test_search_raises_on_error(self):
        """Test search raises exception on HTTP error."""
        # Setup mock to raise error
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=Mock(), response=Mock(status_code=404)
        )
        mock_client.post.return_value = mock_response

        # Create client
        client = CatalogClient(mock_client)

        # Should raise exception
        with pytest.raises(httpx.HTTPStatusError):
            client.search("test")

    def test_get_item(self):
        """Test get item by ID."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "item-123",
            "name": "Test Item"
        }
        mock_client.get.return_value = mock_response

        # Create client and get item
        client = CatalogClient(mock_client)
        item = client.get("item-123")

        # Assertions
        mock_client.get.assert_called_once_with("/api/catalog/items/item-123")
        assert item["id"] == "item-123"
        assert item["name"] == "Test Item"

    def test_list_items_with_filters(self):
        """Test list items with status filter."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {"id": "item-1", "status": "active"},
                {"id": "item-2", "status": "active"}
            ]
        }
        mock_client.get.return_value = mock_response

        # Create client and list
        client = CatalogClient(mock_client)
        items = client.list(status="active", limit=10)

        # Assertions
        mock_client.get.assert_called_once()
        assert len(items) == 2

    def test_request_new_item(self):
        """Test request new item creates proposal."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": "New item request submitted",
            "proposal": {"id": "proposal-123", "status": "pending"}
        }
        mock_client.post.return_value = mock_response

        # Create client and request item
        client = CatalogClient(mock_client)
        result = client.request_new_item(
            name="New Item",
            description="Test",
            category="Test",
            justification="Needed for testing"
        )

        # Assertions
        mock_client.post.assert_called_once_with(
            "/api/catalog/request-new-item",
            json={
                "name": "New Item",
                "description": "Test",
                "category": "Test",
                "metadata": {},
                "justification": "Needed for testing"
            }
        )
        assert "proposal" in result
        assert result["proposal"]["id"] == "proposal-123"
