"""
Unit tests for CatalogAI request service.
"""
import pytest
from unittest.mock import Mock, patch
from app.services import request_service


class TestRequestService:
    """Test request service operations."""

    @patch('app.services.request_service.get_supabase_client')
    @patch('app.services.request_service.audit_service')
    def test_create_request_success(self, mock_audit, mock_supabase_getter):
        """Test creating a new request."""
        # Setup mocks
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [{
            "id": "request-123",
            "org_id": "org-123",
            "requested_by": "user-123",
            "item_name": "Laptop",
            "quantity": 1,
            "urgency": "normal",
            "status": "pending",
            "created_at": "2025-01-15T10:00:00Z"
        }]

        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

        # Create request
        result = request_service.create_request(
            org_id="org-123",
            requested_by="user-123",
            item_name="Laptop",
            quantity=1,
            urgency="normal",
            justification="Need for work"
        )

        # Assertions
        assert result["id"] == "request-123"
        assert result["item_name"] == "Laptop"
        assert result["status"] == "pending"

        # Verify audit log
        mock_audit.log_event.assert_called_once()

    @patch('app.services.request_service.get_supabase_client')
    def test_get_request_by_id(self, mock_supabase_getter):
        """Test retrieving request by ID."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [{
            "id": "request-123",
            "item_name": "Laptop",
            "status": "pending"
        }]

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        # Get request
        result = request_service.get_request("request-123")

        # Assertions
        assert result["id"] == "request-123"
        assert result["item_name"] == "Laptop"

    @patch('app.services.request_service.get_supabase_client')
    def test_list_requests_with_filters(self, mock_supabase_getter):
        """Test listing requests with status filter."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [
            {"id": "request-1", "status": "pending"},
            {"id": "request-2", "status": "pending"}
        ]

        # Mock the query chain
        mock_query = Mock()
        mock_query.eq.return_value.execute.return_value = mock_response
        mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

        # List requests
        result = request_service.list_requests(org_id="org-123", status="pending")

        # Assertions
        assert len(result) == 2
        assert result[0]["status"] == "pending"

    @patch('app.services.request_service.get_supabase_client')
    @patch('app.services.request_service.audit_service')
    def test_approve_request(self, mock_audit, mock_supabase_getter):
        """Test approving a request."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        # Mock get request
        mock_get_response = Mock()
        mock_get_response.data = [{
            "id": "request-123",
            "status": "pending",
            "org_id": "org-123"
        }]

        # Mock update
        mock_update_response = Mock()
        mock_update_response.data = [{
            "id": "request-123",
            "status": "approved",
            "reviewed_by": "admin-123"
        }]

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_get_response
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        # Approve request
        result = request_service.approve_request(
            request_id="request-123",
            reviewed_by="admin-123",
            notes="Approved for Q1"
        )

        # Assertions
        assert result["status"] == "approved"
        assert result["reviewed_by"] == "admin-123"

        # Verify audit log
        mock_audit.log_event.assert_called_once()

    @patch('app.services.request_service.get_supabase_client')
    @patch('app.services.request_service.audit_service')
    def test_reject_request(self, mock_audit, mock_supabase_getter):
        """Test rejecting a request."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        # Mock get request
        mock_get_response = Mock()
        mock_get_response.data = [{
            "id": "request-123",
            "status": "pending",
            "org_id": "org-123"
        }]

        # Mock update
        mock_update_response = Mock()
        mock_update_response.data = [{
            "id": "request-123",
            "status": "rejected",
            "reviewed_by": "admin-123"
        }]

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_get_response
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        # Reject request
        result = request_service.reject_request(
            request_id="request-123",
            reviewed_by="admin-123",
            notes="Budget constraints"
        )

        # Assertions
        assert result["status"] == "rejected"
        assert result["reviewed_by"] == "admin-123"

        # Verify audit log
        mock_audit.log_event.assert_called_once()
