import pytest
from unittest.mock import Mock
import httpx
from catalogai_sdk.requests import RequestClient


class TestRequestClient:

    def test_create_request_success(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "request-123",
            "search_query": "laptop",
            "search_results": [{"name": "Dell Laptop"}],
            "status": "pending"
        }
        mock_client.post.return_value = mock_response

        client = RequestClient(mock_client)
        result = client.create(
            search_query="laptop",
            search_results=[{"name": "Dell Laptop"}],
            justification="Need for work"
        )

        mock_client.post.assert_called_once_with(
            "/api/requests",
            json={
                "search_query": "laptop",
                "search_results": [{"name": "Dell Laptop"}],
                "justification": "Need for work"
            }
        )
        assert result["id"] == "request-123"
        assert result["status"] == "pending"

    def test_create_request_raises_on_error(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad request", request=Mock(), response=Mock(status_code=400)
        )
        mock_client.post.return_value = mock_response

        client = RequestClient(mock_client)

        with pytest.raises(httpx.HTTPStatusError):
            client.create(search_query="test", search_results=[])

    def test_get_request(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "request-123",
            "search_query": "laptop",
            "status": "pending"
        }
        mock_client.get.return_value = mock_response

        client = RequestClient(mock_client)
        result = client.get("request-123")

        mock_client.get.assert_called_once_with("/api/requests/request-123")
        assert result["id"] == "request-123"
        assert result["search_query"] == "laptop"

    def test_list_requests(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "requests": [
                {"id": "request-1", "status": "pending"},
                {"id": "request-2", "status": "approved"}
            ]
        }
        mock_client.get.return_value = mock_response

        client = RequestClient(mock_client)
        result = client.list()

        mock_client.get.assert_called_once_with("/api/requests", params={"limit": 100})
        assert len(result) == 2

    def test_list_requests_with_status_filter(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "requests": [
                {"id": "request-1", "status": "pending"},
                {"id": "request-2", "status": "pending"}
            ]
        }
        mock_client.get.return_value = mock_response

        client = RequestClient(mock_client)
        result = client.list(status="pending")

        mock_client.get.assert_called_once_with(
            "/api/requests",
            params={"limit": 100, "status": "pending"}
        )
        assert len(result) == 2

    def test_review_request_approve(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "request-123",
            "status": "approved",
            "reviewed_by": "admin-123"
        }
        mock_client.post.return_value = mock_response

        client = RequestClient(mock_client)
        result = client.review(
            request_id="request-123",
            status="approved",
            review_notes="Looks good"
        )

        mock_client.post.assert_called_once_with(
            "/api/requests/request-123/review",
            json={"status": "approved", "review_notes": "Looks good"}
        )
        assert result["status"] == "approved"

    def test_review_request_reject(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "request-123",
            "status": "rejected",
            "reviewed_by": "admin-123"
        }
        mock_client.post.return_value = mock_response

        client = RequestClient(mock_client)
        result = client.review(
            request_id="request-123",
            status="rejected",
            review_notes="Budget constraints"
        )

        mock_client.post.assert_called_once_with(
            "/api/requests/request-123/review",
            json={"status": "rejected", "review_notes": "Budget constraints"}
        )
        assert result["status"] == "rejected"

    def test_review_request_without_notes(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "request-123", "status": "approved"}
        mock_client.post.return_value = mock_response

        client = RequestClient(mock_client)
        result = client.review(request_id="request-123", status="approved")

        mock_client.post.assert_called_once_with(
            "/api/requests/request-123/review",
            json={"status": "approved", "review_notes": None}
        )
