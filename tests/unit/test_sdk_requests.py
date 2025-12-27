"""
Unit tests for CatalogAI Python SDK - Request operations.
"""
import pytest
from unittest.mock import Mock, patch
import httpx
from catalogai_sdk.requests import RequestClient


class TestRequestClient:
    """Test CatalogAI SDK request client."""

    def test_create_request_success(self):
        """Test successful request creation."""
        # Setup mock HTTP client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "request-123",
            "item_name": "Laptop",
            "quantity": 1,
            "status": "pending"
        }
        mock_client.post.return_value = mock_response

        # Create client and create request
        client = RequestClient(mock_client)
        result = client.create(
            item_name="Laptop",
            quantity=1,
            urgency="normal",
            justification="Need for work"
        )

        # Assertions
        mock_client.post.assert_called_once_with(
            "/api/requests",
            json={
                "item_name": "Laptop",
                "quantity": 1,
                "urgency": "normal",
                "justification": "Need for work",
                "metadata": {}
            }
        )
        assert result["id"] == "request-123"
        assert result["status"] == "pending"

    def test_create_request_with_metadata(self):
        """Test creating request with custom metadata."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "request-123"}
        mock_client.post.return_value = mock_response

        # Create client and request
        client = RequestClient(mock_client)
        result = client.create(
            item_name="Custom Item",
            quantity=2,
            metadata={"color": "blue", "size": "large"}
        )

        # Verify metadata was passed
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["metadata"] == {"color": "blue", "size": "large"}

    def test_create_request_raises_on_error(self):
        """Test create raises exception on HTTP error."""
        # Setup mock to raise error
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad request", request=Mock(), response=Mock(status_code=400)
        )
        mock_client.post.return_value = mock_response

        # Create client
        client = RequestClient(mock_client)

        # Should raise exception
        with pytest.raises(httpx.HTTPStatusError):
            client.create(item_name="Test", quantity=1)

    def test_get_request(self):
        """Test get request by ID."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "request-123",
            "item_name": "Laptop",
            "status": "pending"
        }
        mock_client.get.return_value = mock_response

        # Create client and get request
        client = RequestClient(mock_client)
        result = client.get("request-123")

        # Assertions
        mock_client.get.assert_called_once_with("/api/requests/request-123")
        assert result["id"] == "request-123"
        assert result["item_name"] == "Laptop"

    def test_list_requests(self):
        """Test list all requests."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "request-1", "status": "pending"},
            {"id": "request-2", "status": "approved"}
        ]
        mock_client.get.return_value = mock_response

        # Create client and list
        client = RequestClient(mock_client)
        result = client.list()

        # Assertions
        mock_client.get.assert_called_once_with("/api/requests", params={})
        assert len(result) == 2

    def test_list_requests_with_status_filter(self):
        """Test list requests with status filter."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "request-1", "status": "pending"},
            {"id": "request-2", "status": "pending"}
        ]
        mock_client.get.return_value = mock_response

        # Create client and list with filter
        client = RequestClient(mock_client)
        result = client.list(status="pending")

        # Assertions
        mock_client.get.assert_called_once_with("/api/requests", params={"status": "pending"})
        assert len(result) == 2

    def test_approve_request(self):
        """Test approving a request."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "request-123",
            "status": "approved",
            "reviewed_by": "admin-123"
        }
        mock_client.post.return_value = mock_response

        # Create client and approve
        client = RequestClient(mock_client)
        result = client.approve("request-123", notes="Approved for Q1")

        # Assertions
        mock_client.post.assert_called_once_with(
            "/api/requests/request-123/approve",
            json={"notes": "Approved for Q1"}
        )
        assert result["status"] == "approved"

    def test_reject_request(self):
        """Test rejecting a request."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "request-123",
            "status": "rejected",
            "reviewed_by": "admin-123"
        }
        mock_client.post.return_value = mock_response

        # Create client and reject
        client = RequestClient(mock_client)
        result = client.reject("request-123", notes="Budget constraints")

        # Assertions
        mock_client.post.assert_called_once_with(
            "/api/requests/request-123/reject",
            json={"notes": "Budget constraints"}
        )
        assert result["status"] == "rejected"

    def test_approve_request_without_notes(self):
        """Test approving request without notes."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "request-123", "status": "approved"}
        mock_client.post.return_value = mock_response

        # Create client and approve without notes
        client = RequestClient(mock_client)
        result = client.approve("request-123")

        # Should pass empty notes
        mock_client.post.assert_called_once_with(
            "/api/requests/request-123/approve",
            json={"notes": None}
        )
