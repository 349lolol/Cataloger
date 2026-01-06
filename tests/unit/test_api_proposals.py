import pytest
import json
from unittest.mock import Mock, patch
from app import create_app

TEST_PROPOSAL_UUID = '22222222-3333-4444-5555-666666666666'
TEST_ORG_UUID = '87654321-4321-4321-4321-cba987654321'
TEST_USER_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'


class TestProposalsAPI:

    @pytest.fixture
    def app(self):
        app = create_app()
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_create_add_item_proposal(self, mock_service, mock_org_role, mock_get_user, client):
        """Test creating ADD_ITEM proposal."""
        # Setup mocks
        user_mock = Mock()
        user_mock.id = "user-123"
        mock_get_user.return_value = (user_mock, 'test-token')
        mock_org_role.return_value = ("org-123", "reviewer")

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

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_create_replace_item_proposal(self, mock_service, mock_org_role, mock_get_user, client):
        """Test creating REPLACE_ITEM proposal."""
        # Setup mocks
        user_mock = Mock()
        user_mock.id = "user-123"
        mock_get_user.return_value = (user_mock, 'test-token')
        mock_org_role.return_value = ("org-123", "reviewer")

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

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_create_proposal_missing_type(self, mock_org_role, mock_get_user, client):
        """Test proposal creation fails without proposal_type."""
        # Setup mocks
        user_mock = Mock()
        user_mock.id = "user-123"
        mock_get_user.return_value = (user_mock, 'test-token')
        mock_org_role.return_value = ("org-123", "reviewer")

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

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_list_proposals(self, mock_service, mock_org_role, mock_get_user, client):
        """Test listing proposals."""
        # Setup mocks
        user_mock = Mock()
        user_mock.id = "user-123"
        mock_get_user.return_value = (user_mock, 'test-token')
        mock_org_role.return_value = ("org-123", "reviewer")

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
        assert len(data["proposals"]) == 2

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_list_proposals_with_status_filter(self, mock_service, mock_org_role, mock_get_user, client):
        """Test listing proposals with status filter."""
        # Setup mocks
        user_mock = Mock()
        user_mock.id = "user-123"
        mock_get_user.return_value = (user_mock, 'test-token')
        mock_org_role.return_value = ("org-123", "reviewer")

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
        assert len(data["proposals"]) == 2
        assert all(p["status"] == "open" for p in data["proposals"])

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_get_proposal_by_id(self, mock_service, mock_org_role, mock_get_user, client):
        """Test getting a specific proposal."""
        # Setup mocks
        user_mock = Mock()
        user_mock.id = TEST_USER_UUID
        mock_get_user.return_value = (user_mock, 'test-token')
        mock_org_role.return_value = (TEST_ORG_UUID, "reviewer")

        mock_service.get_proposal.return_value = {
            "id": TEST_PROPOSAL_UUID,
            "proposal_type": "ADD_ITEM",
            "status": "open",
            "org_id": TEST_ORG_UUID
        }

        # Make request
        response = client.get(
            f'/api/proposals/{TEST_PROPOSAL_UUID}',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == TEST_PROPOSAL_UUID

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_approve_proposal_as_admin(self, mock_service, mock_org_role, mock_get_user, client):
        """Test approving a proposal as admin."""
        admin_uuid = 'dddddddd-dddd-dddd-dddd-dddddddddddd'
        # Setup mocks
        user_mock = Mock()
        user_mock.id = admin_uuid
        mock_get_user.return_value = (user_mock, 'test-token')
        mock_org_role.return_value = (TEST_ORG_UUID, "admin")

        mock_service.approve_proposal.return_value = {
            "id": TEST_PROPOSAL_UUID,
            "status": "merged",
            "reviewed_by": admin_uuid
        }

        # Make request
        response = client.post(
            f'/api/proposals/{TEST_PROPOSAL_UUID}/approve',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({"review_notes": "Looks good"}),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "merged"

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_reject_proposal_as_reviewer(self, mock_service, mock_org_role, mock_get_user, client):
        """Test rejecting a proposal as reviewer."""
        reviewer_uuid = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'
        # Setup mocks
        user_mock = Mock()
        user_mock.id = reviewer_uuid
        mock_get_user.return_value = (user_mock, 'test-token')
        mock_org_role.return_value = (TEST_ORG_UUID, "reviewer")

        mock_service.reject_proposal.return_value = {
            "id": TEST_PROPOSAL_UUID,
            "status": "rejected",
            "reviewed_by": reviewer_uuid
        }

        # Make request
        response = client.post(
            f'/api/proposals/{TEST_PROPOSAL_UUID}/reject',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({"review_notes": "Not needed"}),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "rejected"

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_approve_proposal_requires_admin_or_reviewer(self, mock_service, mock_org_role, mock_get_user, client):
        """Test that only admin/reviewer can approve proposals."""
        # Setup mocks - regular requester role (should be forbidden)
        user_mock = Mock()
        user_mock.id = TEST_USER_UUID
        mock_get_user.return_value = (user_mock, 'test-token')
        mock_org_role.return_value = (TEST_ORG_UUID, "requester")

        # Make request
        response = client.post(
            f'/api/proposals/{TEST_PROPOSAL_UUID}/approve',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({"review_notes": "Trying to approve"}),
            content_type='application/json'
        )

        # Should be forbidden
        assert response.status_code == 403

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.proposals.proposal_service')
    def test_create_deprecate_item_proposal(self, mock_service, mock_org_role, mock_get_user, client):
        """Test creating DEPRECATE_ITEM proposal."""
        # Setup mocks
        user_mock = Mock()
        user_mock.id = "user-123"
        mock_get_user.return_value = (user_mock, 'test-token')
        mock_org_role.return_value = ("org-123", "reviewer")

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
