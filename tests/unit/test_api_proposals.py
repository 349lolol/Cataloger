"""
Unit tests for CatalogAI proposals API endpoints.
"""
import pytest
import json
from unittest.mock import Mock, patch
from app import create_app


class TestProposalsAPI:
    """Test proposals API endpoints."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        app = create_app()
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_create_add_item_proposal(self, mock_service, mock_org_role, mock_jwt, client):
        """Test creating ADD_ITEM proposal."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "user-123"}
        mock_org_role.return_value = ("org-123", "requester")

        mock_service.create_proposal.return_value = {
            "id": "proposal-123",
            "proposal_type": "ADD_ITEM",
            "status": "open"
        }

        # Make request
        response = client.post(
            '/api/proposals',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({
                "proposal_type": "ADD_ITEM",
                "item_name": "New Laptop",
                "item_description": "High-performance laptop",
                "item_category": "Electronics"
            }),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["id"] == "proposal-123"
        assert data["proposal_type"] == "ADD_ITEM"

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_create_replace_item_proposal(self, mock_service, mock_org_role, mock_jwt, client):
        """Test creating REPLACE_ITEM proposal."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "user-123"}
        mock_org_role.return_value = ("org-123", "requester")

        mock_service.create_proposal.return_value = {
            "id": "proposal-124",
            "proposal_type": "REPLACE_ITEM",
            "deprecated_item_id": "item-old",
            "status": "open"
        }

        # Make request
        response = client.post(
            '/api/proposals',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({
                "proposal_type": "REPLACE_ITEM",
                "deprecated_item_id": "item-old",
                "item_name": "New Model",
                "item_description": "Updated version"
            }),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["proposal_type"] == "REPLACE_ITEM"

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_create_proposal_missing_type(self, mock_org_role, mock_jwt, client):
        """Test proposal creation fails without proposal_type."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "user-123"}
        mock_org_role.return_value = ("org-123", "requester")

        # Make request without proposal_type
        response = client.post(
            '/api/proposals',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({
                "item_name": "New Item"
            }),
            content_type='application/json'
        )

        # Should return 400
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_list_proposals(self, mock_service, mock_org_role, mock_jwt, client):
        """Test listing proposals."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "user-123"}
        mock_org_role.return_value = ("org-123", "requester")

        mock_service.list_proposals.return_value = [
            {"id": "proposal-1", "status": "open"},
            {"id": "proposal-2", "status": "approved"}
        ]

        # Make request
        response = client.get(
            '/api/proposals',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_list_proposals_with_status_filter(self, mock_service, mock_org_role, mock_jwt, client):
        """Test listing proposals with status filter."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "user-123"}
        mock_org_role.return_value = ("org-123", "requester")

        mock_service.list_proposals.return_value = [
            {"id": "proposal-1", "status": "open"},
            {"id": "proposal-2", "status": "open"}
        ]

        # Make request with filter
        response = client.get(
            '/api/proposals?status=open',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert all(p["status"] == "open" for p in data)

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_get_proposal_by_id(self, mock_service, mock_org_role, mock_jwt, client):
        """Test getting a specific proposal."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "user-123"}
        mock_org_role.return_value = ("org-123", "requester")

        mock_service.get_proposal.return_value = {
            "id": "proposal-123",
            "proposal_type": "ADD_ITEM",
            "status": "open"
        }

        # Make request
        response = client.get(
            '/api/proposals/proposal-123',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == "proposal-123"

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_approve_proposal_as_admin(self, mock_service, mock_org_role, mock_jwt, client):
        """Test approving a proposal as admin."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "admin-123"}
        mock_org_role.return_value = ("org-123", "admin")

        mock_service.approve_proposal.return_value = {
            "id": "proposal-123",
            "status": "merged",
            "reviewed_by": "admin-123"
        }

        # Make request
        response = client.post(
            '/api/proposals/proposal-123/approve',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({"review_notes": "Looks good"}),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "merged"

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_reject_proposal_as_reviewer(self, mock_service, mock_org_role, mock_jwt, client):
        """Test rejecting a proposal as reviewer."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "reviewer-123"}
        mock_org_role.return_value = ("org-123", "reviewer")

        mock_service.reject_proposal.return_value = {
            "id": "proposal-123",
            "status": "rejected",
            "reviewed_by": "reviewer-123"
        }

        # Make request
        response = client.post(
            '/api/proposals/proposal-123/reject',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({"review_notes": "Not needed"}),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "rejected"

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_approve_proposal_requires_admin_or_reviewer(self, mock_org_role, mock_jwt, client):
        """Test that only admin/reviewer can approve proposals."""
        # Setup mocks - regular requester role
        mock_jwt.return_value = {"sub": "user-123"}
        mock_org_role.return_value = ("org-123", "requester")

        # Make request
        response = client.post(
            '/api/proposals/proposal-123/approve',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({"review_notes": "Trying to approve"}),
            content_type='application/json'
        )

        # Should be forbidden
        assert response.status_code == 403

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_create_deprecate_item_proposal(self, mock_service, mock_org_role, mock_jwt, client):
        """Test creating DEPRECATE_ITEM proposal."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "user-123"}
        mock_org_role.return_value = ("org-123", "requester")

        mock_service.create_proposal.return_value = {
            "id": "proposal-125",
            "proposal_type": "DEPRECATE_ITEM",
            "deprecated_item_id": "item-old-123",
            "status": "open"
        }

        # Make request
        response = client.post(
            '/api/proposals',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({
                "proposal_type": "DEPRECATE_ITEM",
                "deprecated_item_id": "item-old-123",
                "justification": "No longer available from supplier"
            }),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["proposal_type"] == "DEPRECATE_ITEM"
