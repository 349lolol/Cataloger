import pytest
from unittest.mock import Mock
from catalogai_sdk.client import CatalogAIClient


class TestCatalogAIClient:

    def test_client_initialization(self):
        client = CatalogAIClient(
            base_url="http://localhost:5000",
            auth_token="test-token"
        )
        assert client.client.base_url == "http://localhost:5000"
        assert client.client.headers["Authorization"] == "Bearer test-token"

    def test_catalog_property_returns_catalog_client(self):
        client = CatalogAIClient(
            base_url="http://localhost:5000",
            auth_token="test-token"
        )
        catalog = client.catalog
        assert catalog is not None
        assert hasattr(catalog, 'search')
        assert hasattr(catalog, 'get')
        assert hasattr(catalog, 'list')
        assert hasattr(catalog, 'request_new_item')

    def test_requests_property_returns_request_client(self):
        client = CatalogAIClient(
            base_url="http://localhost:5000",
            auth_token="test-token"
        )
        requests = client.requests
        assert requests is not None
        assert hasattr(requests, 'create')
        assert hasattr(requests, 'list')

    def test_proposals_property_returns_proposal_client(self):
        client = CatalogAIClient(
            base_url="http://localhost:5000",
            auth_token="test-token"
        )
        proposals = client.proposals
        assert proposals is not None
        assert hasattr(proposals, 'create')
        assert hasattr(proposals, 'approve')
        assert hasattr(proposals, 'reject')

    def test_context_manager_closes_client(self):
        with CatalogAIClient("http://localhost:5000", "test-token") as client:
            assert client is not None
