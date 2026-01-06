import pytest
from unittest.mock import Mock
import httpx
from catalogai_sdk.proposals import ProposalClient


class TestProposalClient:

    def test_create_add_item_proposal(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-123",
            "proposal_type": "ADD_ITEM",
            "status": "open"
        }
        mock_client.post.return_value = mock_response

        client = ProposalClient(mock_client)
        result = client.create(
            proposal_type="ADD_ITEM",
            item_name="New Laptop",
            item_description="High-performance laptop",
            item_category="Electronics"
        )

        mock_client.post.assert_called_once_with(
            "/api/proposals",
            json={
                "proposal_type": "ADD_ITEM",
                "item_name": "New Laptop",
                "item_description": "High-performance laptop",
                "item_category": "Electronics"
            }
        )
        assert result["id"] == "proposal-123"
        assert result["proposal_type"] == "ADD_ITEM"

    def test_create_replace_item_proposal(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-124",
            "proposal_type": "REPLACE_ITEM",
            "replacing_item_id": "item-old",
            "status": "pending"
        }
        mock_client.post.return_value = mock_response

        client = ProposalClient(mock_client)
        result = client.create(
            proposal_type="REPLACE_ITEM",
            replacing_item_id="item-old",
            item_name="New Model",
            item_description="Updated version"
        )

        assert result["proposal_type"] == "REPLACE_ITEM"
        assert result["replacing_item_id"] == "item-old"

    def test_create_deprecate_item_proposal(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-125",
            "proposal_type": "DEPRECATE_ITEM",
            "replacing_item_id": "item-old-123",
            "status": "pending"
        }
        mock_client.post.return_value = mock_response

        client = ProposalClient(mock_client)
        result = client.create(
            proposal_type="DEPRECATE_ITEM",
            replacing_item_id="item-old-123"
        )

        assert result["proposal_type"] == "DEPRECATE_ITEM"

    def test_create_proposal_with_metadata(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "proposal-123"}
        mock_client.post.return_value = mock_response

        client = ProposalClient(mock_client)
        result = client.create(
            proposal_type="ADD_ITEM",
            item_name="Custom Item",
            item_metadata={"brand": "Dell", "warranty": "3 years"}
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["item_metadata"] == {"brand": "Dell", "warranty": "3 years"}

    def test_create_proposal_raises_on_error(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad request", request=Mock(), response=Mock(status_code=400)
        )
        mock_client.post.return_value = mock_response

        client = ProposalClient(mock_client)

        with pytest.raises(httpx.HTTPStatusError):
            client.create(proposal_type="ADD_ITEM", item_name="Test")

    def test_get_proposal(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-123",
            "proposal_type": "ADD_ITEM",
            "status": "open"
        }
        mock_client.get.return_value = mock_response

        client = ProposalClient(mock_client)
        result = client.get("proposal-123")

        mock_client.get.assert_called_once_with("/api/proposals/proposal-123")
        assert result["id"] == "proposal-123"

    def test_list_proposals(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "proposals": [
                {"id": "proposal-1", "status": "pending"},
                {"id": "proposal-2", "status": "approved"}
            ]
        }
        mock_client.get.return_value = mock_response

        client = ProposalClient(mock_client)
        result = client.list()

        mock_client.get.assert_called_once_with("/api/proposals", params={"limit": 100})
        assert len(result) == 2

    def test_list_proposals_with_status_filter(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "proposals": [
                {"id": "proposal-1", "status": "pending"},
                {"id": "proposal-2", "status": "pending"}
            ]
        }
        mock_client.get.return_value = mock_response

        client = ProposalClient(mock_client)
        result = client.list(status="pending")

        mock_client.get.assert_called_once_with("/api/proposals", params={"limit": 100, "status": "pending"})
        assert len(result) == 2

    def test_approve_proposal(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-123",
            "status": "merged",
            "reviewed_by": "admin-123"
        }
        mock_client.post.return_value = mock_response

        client = ProposalClient(mock_client)
        result = client.approve("proposal-123", review_notes="Looks good")

        mock_client.post.assert_called_once_with(
            "/api/proposals/proposal-123/approve",
            json={"review_notes": "Looks good"}
        )
        assert result["status"] == "merged"

    def test_reject_proposal(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "proposal-123",
            "status": "rejected",
            "reviewed_by": "admin-123"
        }
        mock_client.post.return_value = mock_response

        client = ProposalClient(mock_client)
        result = client.reject("proposal-123", review_notes="Not needed")

        mock_client.post.assert_called_once_with(
            "/api/proposals/proposal-123/reject",
            json={"review_notes": "Not needed"}
        )
        assert result["status"] == "rejected"

    def test_approve_proposal_without_notes(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "proposal-123", "status": "merged"}
        mock_client.post.return_value = mock_response

        client = ProposalClient(mock_client)
        result = client.approve("proposal-123")

        mock_client.post.assert_called_once_with(
            "/api/proposals/proposal-123/approve",
            json={}
        )
