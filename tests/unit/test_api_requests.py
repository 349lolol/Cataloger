"""
Unit tests for CatalogAI requests API endpoints.
"""
import pytest
import json
from unittest.mock import Mock, patch
from app import create_app


class TestRequestsAPI:
    """Test requests API endpoints."""

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def _mock_auth(self, user_id="user-123", org_id="org-123", role="requester"):
        """Helper to mock authentication."""
        def mock_user_from_token():
            user = Mock()
            user.id = user_id
            return user

        def mock_org_and_role(uid):
            return org_id, role

        return mock_user_from_token, mock_org_and_role

    @patch('app.api.requests.request_service')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_create_request_success(self, mock_get_user, mock_get_org, mock_service, client):
        """Test successful request creation."""
        # Setup auth mocks
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ("org-123", "requester")

        # Setup service mock
        mock_service.create_request.return_value = {
            "id": "request-123",
            "search_query": "laptop",
            "status": "pending"
        }

        # Make request
        response = client.post(
            '/api/requests',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({
                "search_query": "laptop",
                "search_results": [{"name": "Dell Laptop"}],
                "justification": "Need for work"
            }),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["id"] == "request-123"
        assert data["status"] == "pending"

    @patch('app.api.requests.request_service')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_list_requests(self, mock_get_user, mock_get_org, mock_service, client):
        """Test listing requests."""
        # Setup auth mocks
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ("org-123", "requester")

        # Setup service mock
        mock_service.list_requests.return_value = [
            {"id": "request-1", "status": "pending"},
            {"id": "request-2", "status": "approved"}
        ]

        # Make request
        response = client.get(
            '/api/requests',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "requests" in data  # Wrapped in object
        assert len(data["requests"]) == 2

    @patch('app.api.requests.request_service')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_get_request_by_id(self, mock_get_user, mock_get_org, mock_service, client):
        """Test getting a specific request."""
        # Setup auth mocks
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ("org-123", "requester")

        # Setup service mock
        mock_service.get_request.return_value = {
            "id": "request-123",
            "org_id": "org-123",
            "search_query": "laptop",
            "status": "pending"
        }

        # Make request
        response = client.get(
            '/api/requests/request-123',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == "request-123"

    @patch('app.api.requests.request_service')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_review_request_approve(self, mock_get_user, mock_get_org, mock_service, client):
        """Test approving a request via review endpoint."""
        # Setup auth mocks - reviewer role
        mock_user = Mock()
        mock_user.id = "reviewer-123"
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ("org-123", "reviewer")

        # Setup service mock
        mock_service.review_request.return_value = {
            "id": "request-123",
            "status": "approved",
            "reviewed_by": "reviewer-123"
        }

        # Make request
        response = client.post(
            '/api/requests/request-123/review',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({
                "status": "approved",
                "review_notes": "Looks good"
            }),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "approved"

    @patch('app.api.requests.request_service')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_review_request_reject(self, mock_get_user, mock_get_org, mock_service, client):
        """Test rejecting a request via review endpoint."""
        # Setup auth mocks - admin role
        mock_user = Mock()
        mock_user.id = "admin-123"
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ("org-123", "admin")

        # Setup service mock
        mock_service.review_request.return_value = {
            "id": "request-123",
            "status": "rejected",
            "reviewed_by": "admin-123"
        }

        # Make request
        response = client.post(
            '/api/requests/request-123/review',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({
                "status": "rejected",
                "review_notes": "Budget constraints"
            }),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "rejected"

    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_review_requires_reviewer_role(self, mock_get_user, mock_get_org, client):
        """Test that review endpoint requires reviewer or admin role."""
        # Setup auth mocks - requester role (insufficient)
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ("org-123", "requester")

        # Make request
        response = client.post(
            '/api/requests/request-123/review',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({
                "status": "approved",
                "review_notes": "Trying to approve"
            }),
            content_type='application/json'
        )

        # Should be forbidden
        assert response.status_code == 403

    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_unauthorized_without_token(self, mock_get_user, client):
        """Test that requests without auth token are rejected."""
        mock_get_user.return_value = None

        # Make request without token
        response = client.get('/api/requests')

        # Should be unauthorized
        assert response.status_code == 401
