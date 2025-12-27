"""
Unit tests for CatalogAI Python SDK - Proposal operations.
"""
import pytest
from unittest.mock import Mock, patch
import httpx
from catalogai_sdk.proposals import ProposalClient


class TestProposalClient:
    """Test CatalogAI SDK proposal client."""

    def test_create_add_item_proposal(self):
        """Test creating ADD_ITEM proposal."""
        # Setup mock HTTP client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-123",
            "proposal_type": "ADD_ITEM",
            "status": "open"
        }
        mock_client.post.return_value = mock_response

        # Create client and proposal
        client = ProposalClient(mock_client)
        result = client.create(
            proposal_type="ADD_ITEM",
            item_name="New Laptop",
            item_description="High-performance laptop",
            item_category="Electronics"
        )

        # Assertions
        mock_client.post.assert_called_once_with(
            "/api/proposals",
            json={
                "proposal_type": "ADD_ITEM",
                "item_name": "New Laptop",
                "item_description": "High-performance laptop",
                "item_category": "Electronics",
                "item_metadata": {},
                "deprecated_item_id": None,
                "justification": None
            }
        )
        assert result["id"] == "proposal-123"
        assert result["proposal_type"] == "ADD_ITEM"

    def test_create_replace_item_proposal(self):
        """Test creating REPLACE_ITEM proposal."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-124",
            "proposal_type": "REPLACE_ITEM",
            "deprecated_item_id": "item-old",
            "status": "open"
        }
        mock_client.post.return_value = mock_response

        # Create client and proposal
        client = ProposalClient(mock_client)
        result = client.create(
            proposal_type="REPLACE_ITEM",
            deprecated_item_id="item-old",
            item_name="New Model",
            item_description="Updated version"
        )

        # Assertions
        assert result["proposal_type"] == "REPLACE_ITEM"
        assert result["deprecated_item_id"] == "item-old"

    def test_create_deprecate_item_proposal(self):
        """Test creating DEPRECATE_ITEM proposal."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-125",
            "proposal_type": "DEPRECATE_ITEM",
            "deprecated_item_id": "item-old-123",
            "status": "open"
        }
        mock_client.post.return_value = mock_response

        # Create client and proposal
        client = ProposalClient(mock_client)
        result = client.create(
            proposal_type="DEPRECATE_ITEM",
            deprecated_item_id="item-old-123",
            justification="No longer available"
        )

        # Assertions
        assert result["proposal_type"] == "DEPRECATE_ITEM"

    def test_create_proposal_with_metadata(self):
        """Test creating proposal with custom metadata."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "proposal-123"}
        mock_client.post.return_value = mock_response

        # Create client and proposal
        client = ProposalClient(mock_client)
        result = client.create(
            proposal_type="ADD_ITEM",
            item_name="Custom Item",
            item_metadata={"brand": "Dell", "warranty": "3 years"}
        )

        # Verify metadata was passed
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["item_metadata"] == {"brand": "Dell", "warranty": "3 years"}

    def test_create_proposal_raises_on_error(self):
        """Test create raises exception on HTTP error."""
        # Setup mock to raise error
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad request", request=Mock(), response=Mock(status_code=400)
        )
        mock_client.post.return_value = mock_response

        # Create client
        client = ProposalClient(mock_client)

        # Should raise exception
        with pytest.raises(httpx.HTTPStatusError):
            client.create(proposal_type="ADD_ITEM", item_name="Test")

    def test_get_proposal(self):
        """Test get proposal by ID."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-123",
            "proposal_type": "ADD_ITEM",
            "status": "open"
        }
        mock_client.get.return_value = mock_response

        # Create client and get proposal
        client = ProposalClient(mock_client)
        result = client.get("proposal-123")

        # Assertions
        mock_client.get.assert_called_once_with("/api/proposals/proposal-123")
        assert result["id"] == "proposal-123"

    def test_list_proposals(self):
        """Test list all proposals."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "proposal-1", "status": "open"},
            {"id": "proposal-2", "status": "approved"}
        ]
        mock_client.get.return_value = mock_response

        # Create client and list
        client = ProposalClient(mock_client)
        result = client.list()

        # Assertions
        mock_client.get.assert_called_once_with("/api/proposals", params={})
        assert len(result) == 2

    def test_list_proposals_with_status_filter(self):
        """Test list proposals with status filter."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "proposal-1", "status": "open"},
            {"id": "proposal-2", "status": "open"}
        ]
        mock_client.get.return_value = mock_response

        # Create client and list with filter
        client = ProposalClient(mock_client)
        result = client.list(status="open")

        # Assertions
        mock_client.get.assert_called_once_with("/api/proposals", params={"status": "open"})
        assert len(result) == 2

    def test_list_proposals_with_type_filter(self):
        """Test list proposals with proposal_type filter."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "proposal-1", "proposal_type": "ADD_ITEM"}
        ]
        mock_client.get.return_value = mock_response

        # Create client and list with type filter
        client = ProposalClient(mock_client)
        result = client.list(proposal_type="ADD_ITEM")

        # Verify filter was passed
        mock_client.get.assert_called_once_with("/api/proposals", params={"proposal_type": "ADD_ITEM"})

    def test_approve_proposal(self):
        """Test approving a proposal."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-123",
            "status": "merged",
            "reviewed_by": "admin-123"
        }
        mock_client.post.return_value = mock_response

        # Create client and approve
        client = ProposalClient(mock_client)
        result = client.approve("proposal-123", review_notes="Looks good")

        # Assertions
        mock_client.post.assert_called_once_with(
            "/api/proposals/proposal-123/approve",
            json={"review_notes": "Looks good"}
        )
        assert result["status"] == "merged"

    def test_reject_proposal(self):
        """Test rejecting a proposal."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-123",
            "status": "rejected",
            "reviewed_by": "admin-123"
        }
        mock_client.post.return_value = mock_response

        # Create client and reject
        client = ProposalClient(mock_client)
        result = client.reject("proposal-123", review_notes="Not needed")

        # Assertions
        mock_client.post.assert_called_once_with(
            "/api/proposals/proposal-123/reject",
            json={"review_notes": "Not needed"}
        )
        assert result["status"] == "rejected"

    def test_approve_proposal_without_notes(self):
        """Test approving proposal without review notes."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "proposal-123", "status": "merged"}
        mock_client.post.return_value = mock_response

        # Create client and approve without notes
        client = ProposalClient(mock_client)
        result = client.approve("proposal-123")

        # Should pass None for review_notes
        mock_client.post.assert_called_once_with(
            "/api/proposals/proposal-123/approve",
            json={"review_notes": None}
        )
