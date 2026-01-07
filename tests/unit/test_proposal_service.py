import pytest
from unittest.mock import Mock, patch
from app.services import proposal_service


class TestProposalService:

    @patch('app.services.proposal_service.get_supabase_admin')
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


    @patch('app.services.proposal_service.get_supabase_admin')
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

    @patch('app.services.proposal_service.get_supabase_admin')
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
    @patch('app.services.proposal_service._get_client')
    @patch('app.services.proposal_service.encode_catalog_item')
    @patch('app.services.audit_service.log_event')
    def test_approve_add_item_proposal(self, mock_audit, mock_encode, mock_get_client, mock_get_proposal):
        """Test approving ADD_ITEM proposal via atomic RPC."""
        mock_encode.return_value = [0.1] * 768

        mock_get_proposal.side_effect = [
            {
                "id": "proposal-123",
                "org_id": "org-123",
                "proposal_type": "ADD_ITEM",
                "item_name": "New Laptop",
                "item_description": "High-performance",
                "item_category": "Electronics",
                "status": "pending"
            },
            {
                "id": "proposal-123",
                "org_id": "org-123",
                "status": "merged",
                "reviewed_by": "admin-123"
            }
        ]

        mock_rpc_response = Mock()
        mock_rpc_response.data = {
            'proposal_id': 'proposal-123',
            'status': 'merged',
            'created_item_id': 'item-new-123'
        }

        mock_client = Mock()
        mock_client.rpc.return_value.execute.return_value = mock_rpc_response
        mock_get_client.return_value = mock_client

        result = proposal_service.approve_proposal(
            proposal_id="proposal-123",
            reviewed_by="admin-123",
            review_notes="Looks good"
        )

        mock_client.rpc.assert_called_once_with(
            'merge_add_item_proposal',
            {
                'p_proposal_id': 'proposal-123',
                'p_reviewed_by': 'admin-123',
                'p_review_notes': 'Looks good',
                'p_embedding': [0.1] * 768
            }
        )
        assert result["status"] == "merged"

    @patch('app.services.proposal_service.get_proposal')
    @patch('app.services.proposal_service.get_supabase_admin')
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


    @patch('app.services.proposal_service.get_supabase_admin')
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

    @patch('app.services.proposal_service.get_proposal')
    @patch('app.services.proposal_service._get_client')
    @patch('app.services.audit_service.log_event')
    def test_approve_deprecate_item_proposal(self, mock_audit, mock_get_client, mock_get_proposal):
        """Test approving DEPRECATE_ITEM proposal via atomic RPC."""
        mock_get_proposal.side_effect = [
            {
                "id": "proposal-125",
                "org_id": "org-123",
                "proposal_type": "DEPRECATE_ITEM",
                "replacing_item_id": "item-old-123",
                "status": "pending"
            },
            {"id": "proposal-125", "status": "merged"}
        ]

        mock_rpc_response = Mock()
        mock_rpc_response.data = {
            'proposal_id': 'proposal-125',
            'status': 'merged',
            'deprecated_item_id': 'item-old-123'
        }

        mock_client = Mock()
        mock_client.rpc.return_value.execute.return_value = mock_rpc_response
        mock_get_client.return_value = mock_client

        result = proposal_service.approve_proposal(
            proposal_id="proposal-125",
            reviewed_by="admin-123"
        )

        mock_client.rpc.assert_called_once_with(
            'merge_deprecate_item_proposal',
            {
                'p_proposal_id': 'proposal-125',
                'p_reviewed_by': 'admin-123',
                'p_review_notes': None
            }
        )
        assert result["status"] == "merged"
