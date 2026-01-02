"""
Unit tests for CatalogAI proposal service.
"""
import pytest
from unittest.mock import Mock, patch
from app.services import proposal_service


class TestProposalService:
    """Test proposal service operations."""

    @patch('app.services.proposal_service.get_supabase_client')
    @patch('app.services.audit_service.log_event')
    def test_create_add_item_proposal(self, mock_audit, mock_supabase_getter):
        """Test creating ADD_ITEM proposal."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [{
            "id": "proposal-123",
            "org_id": "org-123",
            "proposed_by": "user-123",
            "proposal_type": "ADD_ITEM",
            "item_name": "New Laptop",
            "status": "open",
            "created_at": "2025-01-15T10:00:00Z"
        }]

        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

        # Create proposal
        result = proposal_service.create_proposal(
            org_id="org-123",
            proposed_by="user-123",
            proposal_type="ADD_ITEM",
            item_name="New Laptop",
            item_description="High-performance laptop",
            item_category="Electronics"
        )

        # Assertions
        assert result["id"] == "proposal-123"
        assert result["proposal_type"] == "ADD_ITEM"
        assert result["status"] == "open"


    @patch('app.services.proposal_service.get_supabase_client')
    @patch('app.services.audit_service.log_event')
    def test_create_replace_item_proposal(self, mock_audit, mock_supabase_getter):
        """Test creating REPLACE_ITEM proposal."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [{
            "id": "proposal-124",
            "proposal_type": "REPLACE_ITEM",
            "replacing_item_id": "item-old",
            "item_name": "New Model Laptop",
            "status": "pending"
        }]

        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

        # Create proposal
        result = proposal_service.create_proposal(
            org_id="org-123",
            proposed_by="user-123",
            proposal_type="REPLACE_ITEM",
            replacing_item_id="item-old",
            item_name="New Model Laptop",
            item_description="Updated model"
        )

        # Assertions
        assert result["proposal_type"] == "REPLACE_ITEM"
        assert result["replacing_item_id"] == "item-old"

    @patch('app.services.proposal_service.get_supabase_client')
    def test_get_proposal_by_id(self, mock_supabase_getter):
        """Test retrieving proposal by ID."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        # .single() returns the dict directly, not wrapped in a list
        mock_response = Mock()
        mock_response.data = {
            "id": "proposal-123",
            "proposal_type": "ADD_ITEM",
            "status": "pending"
        }

        # Create a mock query that supports chaining
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.single.return_value = mock_query
        mock_query.execute.return_value = mock_response

        mock_supabase.table.return_value.select.return_value = mock_query

        # Get proposal
        result = proposal_service.get_proposal("proposal-123")

        # Assertions
        assert result["id"] == "proposal-123"
        assert result["status"] == "pending"

    @patch('app.services.proposal_service.get_proposal')
    @patch('app.services.proposal_service.get_supabase_client')
    @patch('app.services.proposal_service.create_item')
    @patch('app.services.audit_service.log_event')
    def test_approve_add_item_proposal(self, mock_audit, mock_create_item, mock_supabase_getter, mock_get_proposal):
        """Test approving ADD_ITEM proposal and auto-merging."""
        # Mock get_proposal to return pending first, then merged
        # First call: get pending proposal to validate
        # Second call: final get_proposal to return result
        mock_get_proposal.side_effect = [
            {
                "id": "proposal-123",
                "org_id": "org-123",
                "proposal_type": "ADD_ITEM",
                "item_name": "New Laptop",
                "item_description": "High-performance",
                "item_category": "Electronics",
                "item_metadata": {"brand": "Dell"},
                "status": "pending",
                "proposed_by": "user-123"
            },
            {
                "id": "proposal-123",
                "org_id": "org-123",
                "proposal_type": "ADD_ITEM",
                "item_name": "New Laptop",
                "status": "merged",
                "reviewed_by": "admin-123"
            }
        ]

        # Setup mocks
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        # Mock update to approved, then merged
        mock_approved_response = Mock()
        mock_approved_response.data = [{
            "id": "proposal-123",
            "org_id": "org-123",
            "status": "approved",
            "reviewed_by": "admin-123"
        }]

        mock_merged_response = Mock()
        mock_merged_response.data = [{
            "id": "proposal-123",
            "org_id": "org-123",
            "status": "merged",
            "reviewed_by": "admin-123"
        }]

        # Mock catalog item creation
        mock_create_item.return_value = {
            "id": "item-new-123",
            "name": "New Laptop"
        }

        # Create a mock query that supports chaining and returns different responses
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.execute.side_effect = [mock_approved_response, mock_merged_response]

        mock_supabase.table.return_value.update.return_value = mock_query

        # Approve proposal
        result = proposal_service.approve_proposal(
            proposal_id="proposal-123",
            reviewed_by="admin-123",
            review_notes="Looks good"
        )

        # Assertions
        assert result["status"] == "merged"

        # Verify catalog item was created
        mock_create_item.assert_called_once()

    @patch('app.services.proposal_service.get_proposal')
    @patch('app.services.proposal_service.get_supabase_client')
    @patch('app.services.audit_service.log_event')
    def test_reject_proposal(self, mock_audit, mock_supabase_getter, mock_get_proposal):
        """Test rejecting a proposal."""
        # Mock get_proposal to return pending proposal
        mock_get_proposal.return_value = {
            "id": "proposal-123",
            "status": "pending",
            "org_id": "org-123"
        }

        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        # Mock update response
        mock_update_response = Mock()
        mock_update_response.data = [{
            "id": "proposal-123",
            "status": "rejected",
            "reviewed_by": "admin-123",
            "org_id": "org-123"
        }]

        # Create a mock query that supports chaining
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_update_response

        mock_supabase.table.return_value.update.return_value = mock_query

        # Reject proposal
        result = proposal_service.reject_proposal(
            proposal_id="proposal-123",
            reviewed_by="admin-123",
            review_notes="Not needed right now"
        )

        # Assertions
        assert result["status"] == "rejected"
        assert result["reviewed_by"] == "admin-123"


    @patch('app.services.proposal_service.get_supabase_client')
    def test_list_proposals_with_filters(self, mock_supabase_getter):
        """Test listing proposals with status filter."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [
            {"id": "proposal-1", "status": "pending", "proposal_type": "ADD_ITEM"},
            {"id": "proposal-2", "status": "pending", "proposal_type": "REPLACE_ITEM"}
        ]

        # Create a mock query that supports chaining
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        mock_supabase.table.return_value.select.return_value = mock_query

        # List proposals
        result = proposal_service.list_proposals(org_id="org-123", status="pending")

        # Assertions
        assert len(result) == 2
        assert all(p["status"] == "pending" for p in result)

    @patch('app.services.proposal_service.update_item')
    def test_merge_deprecate_item_proposal(self, mock_update_item):
        """Test merging DEPRECATE_ITEM proposal."""
        proposal = {
            "id": "proposal-125",
            "org_id": "org-123",
            "proposal_type": "DEPRECATE_ITEM",
            "replacing_item_id": "item-old-123",
            "proposed_by": "user-123"
        }

        mock_update_item.return_value = {"id": "item-old-123", "status": "deprecated"}

        # Merge (this is called internally during approve)
        proposal_service._merge_deprecate_item(proposal, "admin-123")

        # Verify catalog deprecation via update_item
        mock_update_item.assert_called_once_with(
            "item-old-123",
            {"status": "deprecated"},
            updated_by="admin-123"
        )
