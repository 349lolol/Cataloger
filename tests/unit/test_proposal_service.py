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
            "deprecated_item_id": "item-old",
            "item_name": "New Model Laptop",
            "status": "open"
        }]

        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

        # Create proposal
        result = proposal_service.create_proposal(
            org_id="org-123",
            proposed_by="user-123",
            proposal_type="REPLACE_ITEM",
            deprecated_item_id="item-old",
            item_name="New Model Laptop",
            item_description="Updated model"
        )

        # Assertions
        assert result["proposal_type"] == "REPLACE_ITEM"
        assert result["deprecated_item_id"] == "item-old"

    @patch('app.services.proposal_service.get_supabase_client')
    def test_get_proposal_by_id(self, mock_supabase_getter):
        """Test retrieving proposal by ID."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_response = Mock()
        mock_response.data = [{
            "id": "proposal-123",
            "proposal_type": "ADD_ITEM",
            "status": "open"
        }]

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        # Get proposal
        result = proposal_service.get_proposal("proposal-123")

        # Assertions
        assert result["id"] == "proposal-123"
        assert result["status"] == "open"

    @patch('app.services.proposal_service.get_supabase_client')
    @patch('app.services.proposal_service.get_supabase_admin')
    @patch('app.services.proposal_service.catalog_service')
    @patch('app.services.audit_service.log_event')
    def test_approve_add_item_proposal(self, mock_audit, mock_catalog, mock_admin_getter, mock_supabase_getter):
        """Test approving ADD_ITEM proposal and auto-merging."""
        # Setup mocks
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        mock_admin = Mock()
        mock_admin_getter.return_value = mock_admin

        # Mock get proposal
        mock_get_response = Mock()
        mock_get_response.data = [{
            "id": "proposal-123",
            "org_id": "org-123",
            "proposal_type": "ADD_ITEM",
            "item_name": "New Laptop",
            "item_description": "High-performance",
            "item_category": "Electronics",
            "item_metadata": {"brand": "Dell"},
            "status": "open",
            "proposed_by": "user-123"
        }]

        # Mock update to approved
        mock_approved_response = Mock()
        mock_approved_response.data = [{
            "id": "proposal-123",
            "status": "approved",
            "reviewed_by": "admin-123"
        }]

        # Mock update to merged
        mock_merged_response = Mock()
        mock_merged_response.data = [{
            "id": "proposal-123",
            "status": "merged"
        }]

        # Mock catalog item creation
        mock_catalog.create_item.return_value = {
            "id": "item-new-123",
            "name": "New Laptop"
        }

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_get_response
        mock_admin.table.return_value.update.return_value.eq.return_value.execute.side_effect = [
            mock_approved_response,
            mock_merged_response
        ]

        # Approve proposal
        result = proposal_service.approve_proposal(
            proposal_id="proposal-123",
            reviewed_by="admin-123",
            review_notes="Looks good"
        )

        # Assertions
        assert result["status"] == "merged"

        # Verify catalog item was created
        mock_catalog.create_item.assert_called_once()

        assert mock_audit.call_count >= 2  # approve + merge

    @patch('app.services.proposal_service.get_supabase_client')
    @patch('app.services.audit_service.log_event')
    def test_reject_proposal(self, mock_audit, mock_supabase_getter):
        """Test rejecting a proposal."""
        # Setup mock
        mock_supabase = Mock()
        mock_supabase_getter.return_value = mock_supabase

        # Mock get proposal
        mock_get_response = Mock()
        mock_get_response.data = [{
            "id": "proposal-123",
            "status": "open",
            "org_id": "org-123"
        }]

        # Mock update
        mock_update_response = Mock()
        mock_update_response.data = [{
            "id": "proposal-123",
            "status": "rejected",
            "reviewed_by": "admin-123"
        }]

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_get_response
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

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
            {"id": "proposal-1", "status": "open", "proposal_type": "ADD_ITEM"},
            {"id": "proposal-2", "status": "open", "proposal_type": "REPLACE_ITEM"}
        ]

        mock_query = Mock()
        mock_query.eq.return_value.execute.return_value = mock_response
        mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

        # List proposals
        result = proposal_service.list_proposals(org_id="org-123", status="open")

        # Assertions
        assert len(result) == 2
        assert all(p["status"] == "open" for p in result)

    @patch('app.services.proposal_service.get_supabase_admin')
    @patch('app.services.proposal_service.catalog_service')
    @patch('app.services.audit_service.log_event')
    def test_merge_deprecate_item_proposal(self, mock_audit, mock_catalog, mock_admin_getter):
        """Test merging DEPRECATE_ITEM proposal."""
        # Setup mock
        mock_admin = Mock()
        mock_admin_getter.return_value = mock_admin

        proposal = {
            "id": "proposal-125",
            "org_id": "org-123",
            "proposal_type": "DEPRECATE_ITEM",
            "deprecated_item_id": "item-old-123",
            "proposed_by": "user-123"
        }

        mock_update_response = Mock()
        mock_update_response.data = [{"id": "proposal-125", "status": "merged"}]
        mock_admin.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        mock_catalog.deprecate_item.return_value = {"id": "item-old-123", "status": "deprecated"}

        # Merge (this is called internally during approve)
        proposal_service._merge_deprecate_item(proposal, "admin-123")

        # Verify catalog deprecation
        mock_catalog.deprecate_item.assert_called_once_with("item-old-123")
