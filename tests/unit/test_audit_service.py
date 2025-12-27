"""
Unit tests for CatalogAI audit service.
"""
import pytest
from unittest.mock import Mock, patch
from app.services import audit_service


class TestAuditService:
    """Test audit service operations."""

    @patch('app.services.audit_service.get_supabase_admin')
    def test_log_event_success(self, mock_admin_getter):
        """Test logging an audit event."""
        # Setup mock
        mock_admin = Mock()
        mock_admin_getter.return_value = mock_admin

        mock_response = Mock()
        mock_response.data = [{
            "id": "audit-123",
            "org_id": "org-123",
            "user_id": "user-123",
            "event_type": "CATALOG_ITEM_CREATED",
            "resource_type": "catalog_item",
            "resource_id": "item-123",
            "details": {"name": "New Laptop"},
            "created_at": "2025-01-15T10:00:00Z"
        }]

        mock_admin.table.return_value.insert.return_value.execute.return_value = mock_response

        # Log event
        result = audit_service.log_event(
            org_id="org-123",
            user_id="user-123",
            event_type="CATALOG_ITEM_CREATED",
            resource_type="catalog_item",
            resource_id="item-123",
            details={"name": "New Laptop"}
        )

        # Assertions
        assert result["id"] == "audit-123"
        assert result["event_type"] == "CATALOG_ITEM_CREATED"
        assert result["resource_id"] == "item-123"

        # Verify insert was called
        mock_admin.table.assert_called_once_with("audit_events")

    @patch('app.services.audit_service.get_supabase_client')
    def test_get_audit_logs_for_org(self, mock_supabase_getter):
        """Test retrieving audit logs for an organization."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [
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

        mock_query = Mock()
        mock_query.order.return_value.limit.return_value.execute.return_value = mock_response
        mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

        # Get audit logs
        result = audit_service.get_audit_logs(org_id="org-123", limit=10)

        # Assertions
        assert len(result) == 2
        assert result[0]["event_type"] == "CATALOG_ITEM_CREATED"
        assert result[1]["event_type"] == "PROPOSAL_APPROVED"

    @patch('app.services.audit_service.get_supabase_client')
    def test_get_audit_logs_with_filters(self, mock_supabase_getter):
        """Test retrieving audit logs with event type filter."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [
            {"id": "audit-1", "event_type": "CATALOG_ITEM_CREATED"},
            {"id": "audit-2", "event_type": "CATALOG_ITEM_CREATED"}
        ]

        mock_query = Mock()
        mock_eq_chain = Mock()
        mock_eq_chain.order.return_value.limit.return_value.execute.return_value = mock_response
        mock_query.eq.return_value = mock_eq_chain
        mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

        # Get filtered logs
        result = audit_service.get_audit_logs(
            org_id="org-123",
            event_type="CATALOG_ITEM_CREATED",
            limit=10
        )

        # Assertions
        assert len(result) == 2
        assert all(log["event_type"] == "CATALOG_ITEM_CREATED" for log in result)

    @patch('app.services.audit_service.get_supabase_client')
    def test_get_audit_logs_for_resource(self, mock_supabase_getter):
        """Test retrieving audit logs for a specific resource."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [
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

        mock_query = Mock()
        mock_eq_chain = Mock()
        mock_eq_chain.order.return_value.limit.return_value.execute.return_value = mock_response
        mock_query.eq.return_value = mock_eq_chain
        mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

        # Get resource logs
        result = audit_service.get_audit_logs(
            org_id="org-123",
            resource_type="catalog_item",
            resource_id="item-123"
        )

        # Assertions
        assert len(result) == 2
        assert all(log["resource_id"] == "item-123" for log in result)

    @patch('app.services.audit_service.get_supabase_admin')
    def test_log_event_handles_missing_details(self, mock_admin_getter):
        """Test logging event with no details provided."""
        # Setup mock
        mock_admin = Mock()
        mock_admin_getter.return_value = mock_admin

        mock_response = Mock()
        mock_response.data = [{
            "id": "audit-123",
            "details": {}
        }]

        mock_admin.table.return_value.insert.return_value.execute.return_value = mock_response

        # Log event without details
        result = audit_service.log_event(
            org_id="org-123",
            user_id="user-123",
            event_type="USER_LOGIN",
            resource_type="user",
            resource_id="user-123"
        )

        # Should still succeed with empty details
        assert result["id"] == "audit-123"
        assert result["details"] == {}
