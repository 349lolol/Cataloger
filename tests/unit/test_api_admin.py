"""
Unit tests for CatalogAI admin API endpoints.
"""
import pytest
import json
from unittest.mock import Mock, patch
from app import create_app


class TestAdminAPI:
    """Test admin API endpoints."""

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
    @patch('app.api.admin.audit_service')
    def test_get_audit_logs_as_admin(self, mock_service, mock_org_role, mock_jwt, client):
        """Test getting audit logs as admin."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "admin-123"}
        mock_org_role.return_value = ("org-123", "admin")

        mock_service.get_audit_logs.return_value = [
            {
                "id": "audit-1",
                "event_type": "CATALOG_ITEM_CREATED",
                "created_at": "2025-01-15T10:00:00Z"
            },
            {
                "id": "audit-2",
                "event_type": "PROPOSAL_APPROVED",
                "created_at": "2025-01-15T11:00:00Z"
            }
        ]

        # Make request
        response = client.get(
            '/api/admin/audit-logs',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]["event_type"] == "CATALOG_ITEM_CREATED"

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.admin.audit_service')
    def test_get_audit_logs_with_filters(self, mock_service, mock_org_role, mock_jwt, client):
        """Test getting audit logs with event type filter."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "admin-123"}
        mock_org_role.return_value = ("org-123", "admin")

        mock_service.get_audit_logs.return_value = [
            {"id": "audit-1", "event_type": "CATALOG_ITEM_CREATED"},
            {"id": "audit-2", "event_type": "CATALOG_ITEM_CREATED"}
        ]

        # Make request with filter
        response = client.get(
            '/api/admin/audit-logs?event_type=CATALOG_ITEM_CREATED&limit=50',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2

        # Verify filter was passed to service
        mock_service.get_audit_logs.assert_called_once_with(
            org_id="org-123",
            event_type="CATALOG_ITEM_CREATED",
            resource_type=None,
            resource_id=None,
            limit=50
        )

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_get_audit_logs_requires_admin(self, mock_org_role, mock_jwt, client):
        """Test that only admins can access audit logs."""
        # Setup mocks - requester role
        mock_jwt.return_value = {"sub": "user-123"}
        mock_org_role.return_value = ("org-123", "requester")

        # Make request
        response = client.get(
            '/api/admin/audit-logs',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Should be forbidden
        assert response.status_code == 403

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.admin.audit_service')
    def test_get_audit_logs_for_resource(self, mock_service, mock_org_role, mock_jwt, client):
        """Test getting audit logs for a specific resource."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "admin-123"}
        mock_org_role.return_value = ("org-123", "admin")

        mock_service.get_audit_logs.return_value = [
            {
                "id": "audit-1",
                "resource_type": "catalog_item",
                "resource_id": "item-123",
                "event_type": "CATALOG_ITEM_CREATED"
            },
            {
                "id": "audit-2",
                "resource_type": "catalog_item",
                "resource_id": "item-123",
                "event_type": "CATALOG_ITEM_UPDATED"
            }
        ]

        # Make request with resource filters
        response = client.get(
            '/api/admin/audit-logs?resource_type=catalog_item&resource_id=item-123',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert all(log["resource_id"] == "item-123" for log in data)

        # Verify filters were passed
        mock_service.get_audit_logs.assert_called_once_with(
            org_id="org-123",
            event_type=None,
            resource_type="catalog_item",
            resource_id="item-123",
            limit=100
        )

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_get_audit_logs_reviewer_forbidden(self, mock_org_role, mock_jwt, client):
        """Test that reviewers cannot access audit logs."""
        # Setup mocks - reviewer role
        mock_jwt.return_value = {"sub": "reviewer-123"}
        mock_org_role.return_value = ("org-123", "reviewer")

        # Make request
        response = client.get(
            '/api/admin/audit-logs',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Should be forbidden
        assert response.status_code == 403

    @patch('app.middleware.auth_middleware.verify_jwt_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.api.admin.audit_service')
    def test_get_audit_logs_with_default_limit(self, mock_service, mock_org_role, mock_jwt, client):
        """Test that default limit is applied when not specified."""
        # Setup mocks
        mock_jwt.return_value = {"sub": "admin-123"}
        mock_org_role.return_value = ("org-123", "admin")

        mock_service.get_audit_logs.return_value = []

        # Make request without limit parameter
        response = client.get(
            '/api/admin/audit-logs',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Should use default limit of 100
        mock_service.get_audit_logs.assert_called_once_with(
            org_id="org-123",
            event_type=None,
            resource_type=None,
            resource_id=None,
            limit=100
        )
