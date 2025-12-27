"""
Unit tests for CatalogAI request service.
"""
import pytest
from unittest.mock import Mock, patch
from app.services import request_service


class TestRequestService:
    """Test request service operations."""

    @patch('app.services.request_service.get_supabase_client')
    @patch('app.services.request_service.log_event')
    def test_create_request_success(self, mock_log_event, mock_supabase_getter):
        """Test creating a new request."""
        # Setup mocks
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [{
            "id": "request-123",
            "org_id": "org-123",
            "created_by": "user-123",
            "search_query": "laptop",
            "search_results": [{"name": "Laptop"}],
            "justification": "Need for work",
            "status": "pending",
            "created_at": "2025-01-15T10:00:00Z"
        }]

        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

        # Create request
        result = request_service.create_request(
            org_id="org-123",
            created_by="user-123",
            search_query="laptop",
            search_results=[{"name": "Laptop"}],
            justification="Need for work"
        )

        # Assertions
        assert result["id"] == "request-123"
        assert result["search_query"] == "laptop"
        assert result["status"] == "pending"

        # Verify audit log
        mock_log_event.assert_called_once_with(
            org_id="org-123",
            event_type="request.created",
            actor_id="user-123",
            resource_type="request",
            resource_id="request-123",
            metadata={"search_query": "laptop"}
        )

    @patch('app.services.request_service.get_supabase_client')
    def test_get_request_by_id(self, mock_supabase_getter):
        """Test retrieving request by ID."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = {
            "id": "request-123",
            "search_query": "laptop",
            "status": "pending"
        }

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        # Get request
        result = request_service.get_request("request-123")

        # Assertions
        assert result["id"] == "request-123"
        assert result["search_query"] == "laptop"

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
        mock_limit = Mock()
        mock_limit.execute.return_value = mock_response
        mock_order = Mock()
        mock_order.limit.return_value = mock_limit
        mock_eq2 = Mock()
        mock_eq2.order.return_value = mock_order
        mock_eq1 = Mock()
        mock_eq1.eq.return_value = mock_eq2
        mock_select = Mock()
        mock_select.eq.return_value = mock_eq1

        mock_supabase.table.return_value.select.return_value = mock_select

        # List requests
        result = request_service.list_requests(org_id="org-123", status="pending")

        # Assertions
        assert len(result) == 2
        assert result[0]["status"] == "pending"

    @patch('app.services.request_service.get_supabase_client')
    @patch('app.services.request_service.log_event')
    def test_review_request_approve(self, mock_log_event, mock_supabase_getter):
        """Test approving a request via review."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        # Mock update
        mock_update_response = Mock()
        mock_update_response.data = [{
            "id": "request-123",
            "org_id": "org-123",
            "status": "approved",
            "reviewed_by": "admin-123"
        }]

        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        # Review request (approve)
        result = request_service.review_request(
            request_id="request-123",
            reviewed_by="admin-123",
            status="approved",
            review_notes="Approved for Q1"
        )

        # Assertions
        assert result["status"] == "approved"
        assert result["reviewed_by"] == "admin-123"

        # Verify audit log
        mock_log_event.assert_called_once_with(
            org_id="org-123",
            event_type="request.approved",
            actor_id="admin-123",
            resource_type="request",
            resource_id="request-123",
            metadata={"review_notes": "Approved for Q1"}
        )

    @patch('app.services.request_service.get_supabase_client')
    @patch('app.services.request_service.log_event')
    def test_review_request_reject(self, mock_log_event, mock_supabase_getter):
        """Test rejecting a request via review."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        # Mock update
        mock_update_response = Mock()
        mock_update_response.data = [{
            "id": "request-123",
            "org_id": "org-123",
            "status": "rejected",
            "reviewed_by": "admin-123"
        }]

        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        # Review request (reject)
        result = request_service.review_request(
            request_id="request-123",
            reviewed_by="admin-123",
            status="rejected",
            review_notes="Budget constraints"
        )

        # Assertions
        assert result["status"] == "rejected"
        assert result["reviewed_by"] == "admin-123"

        # Verify audit log
        mock_log_event.assert_called_once_with(
            org_id="org-123",
            event_type="request.rejected",
            actor_id="admin-123",
            resource_type="request",
            resource_id="request-123",
            metadata={"review_notes": "Budget constraints"}
        )
