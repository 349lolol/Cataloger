import pytest
from unittest.mock import Mock, patch
from app.services import audit_service


class TestAuditService:

    @patch('app.services.audit_service.get_supabase_admin')
    def test_log_event_success(self, mock_admin_getter):
        # Setup mock
        mock_admin = Mock()
        mock_admin_getter.return_value = mock_admin

        mock_response = Mock()
        mock_response.data = [{
            "id": "audit-123",
            "org_id": "org-123",
            "actor_id": "user-123",
            "event_type": "catalog.item.created",
            "resource_type": "catalog_item",
            "resource_id": "item-123",
            "metadata": {"name": "New Laptop"},
            "created_at": "2025-01-15T10:00:00Z"
        }]

        mock_admin.table.return_value.insert.return_value.execute.return_value = mock_response

        # Log event
        result = audit_service.log_event(
            org_id="org-123",
            actor_id="user-123",
            event_type="catalog.item.created",
            resource_type="catalog_item",
            resource_id="item-123",
            metadata={"name": "New Laptop"}
        )

        # Assertions
        assert result["id"] == "audit-123"
        assert result["event_type"] == "catalog.item.created"
        assert result["resource_id"] == "item-123"

        # Verify insert was called
        mock_admin.table.assert_called_once_with("audit_events")

    @patch('app.services.audit_service.get_supabase_admin')
    def test_get_audit_log_for_org(self, mock_admin_getter):
        # Setup mock
        mock_admin = Mock()
        mock_admin_getter.return_value = mock_admin

        mock_response = Mock()
        mock_response.data = [
            {
                "id": "audit-1",
                "event_type": "catalog.item.created",
                "created_at": "2025-01-15T10:00:00Z"
            },
            {
                "id": "audit-2",
                "event_type": "proposal.approved",
                "created_at": "2025-01-15T11:00:00Z"
            }
        ]

        mock_query = Mock()
        mock_query.order.return_value.limit.return_value.execute.return_value = mock_response
        mock_admin.table.return_value.select.return_value.eq.return_value = mock_query

        # Get audit logs
        result = audit_service.get_audit_log(org_id="org-123", limit=10)

        # Assertions
        assert len(result) == 2
        assert result[0]["event_type"] == "catalog.item.created"
        assert result[1]["event_type"] == "proposal.approved"

    @patch('app.services.audit_service.get_supabase_admin')
    def test_get_audit_log_with_filters(self, mock_admin_getter):
        # Setup mock
        mock_admin = Mock()
        mock_admin_getter.return_value = mock_admin

        mock_response = Mock()
        mock_response.data = [
            {"id": "audit-1", "event_type": "catalog.item.created"},
            {"id": "audit-2", "event_type": "catalog.item.created"}
        ]

        # Create a mock query that supports chaining
        mock_query = Mock()
        # Each method in the chain returns self for fluent interface
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        mock_admin.table.return_value.select.return_value = mock_query

        # Get filtered logs
        result = audit_service.get_audit_log(
            org_id="org-123",
            event_type="catalog.item.created",
            limit=10
        )

        # Assertions
        assert len(result) == 2
        assert all(log["event_type"] == "catalog.item.created" for log in result)

    @patch('app.services.audit_service.get_supabase_admin')
    def test_get_audit_log_for_resource(self, mock_admin_getter):
        # Setup mock
        mock_admin = Mock()
        mock_admin_getter.return_value = mock_admin

        mock_response = Mock()
        mock_response.data = [
            {
                "id": "audit-1",
                "resource_type": "catalog_item",
                "resource_id": "item-123",
                "event_type": "catalog.item.created"
            },
            {
                "id": "audit-2",
                "resource_type": "catalog_item",
                "resource_id": "item-123",
                "event_type": "catalog.item.updated"
            }
        ]

        # Create a mock query that supports chaining
        mock_query = Mock()
        # Each method in the chain returns self for fluent interface
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        mock_admin.table.return_value.select.return_value = mock_query

        # Get resource logs
        result = audit_service.get_audit_log(
            org_id="org-123",
            resource_type="catalog_item",
            resource_id="item-123"
        )

        # Assertions
        assert len(result) == 2
        assert all(log["resource_id"] == "item-123" for log in result)

    @patch('app.services.audit_service.get_supabase_admin')
    def test_log_event_handles_missing_metadata(self, mock_admin_getter):
        # Setup mock
        mock_admin = Mock()
        mock_admin_getter.return_value = mock_admin

        mock_response = Mock()
        mock_response.data = [{
            "id": "audit-123",
            "metadata": {}
        }]

        mock_admin.table.return_value.insert.return_value.execute.return_value = mock_response

        # Log event without metadata
        result = audit_service.log_event(
            org_id="org-123",
            actor_id="user-123",
            event_type="user.login",
            resource_type="user",
            resource_id="user-123"
        )

        # Should still succeed with empty metadata
        assert result["id"] == "audit-123"
        assert result["metadata"] == {}
