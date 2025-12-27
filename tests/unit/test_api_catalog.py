"""
Unit tests for catalog API endpoints.
"""
import pytest
import json
from unittest.mock import patch, Mock


class TestCatalogAPI:
    """Test catalog API endpoints."""

    @patch('app.api.catalog.catalog_service.search_items')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_search_items_success(self, mock_org_role, mock_user, mock_search, client):
        """Test successful catalog search."""
        # Setup mocks
        mock_user.return_value = Mock(id='user-123')
        mock_org_role.return_value = ('org-123', 'requester')
        mock_search.return_value = [
            {'item_name': 'Laptop', 'similarity_score': 0.9}
        ]

        # Make request
        response = client.post(
            '/api/catalog/search',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({'query': 'laptop', 'limit': 5}),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert len(data['results']) == 1

    def test_search_items_missing_query(self, client, auth_headers):
        """Test search with missing query parameter."""
        with patch('app.middleware.auth_middleware.get_user_from_token') as mock_user, \
             patch('app.middleware.auth_middleware.get_user_org_and_role') as mock_org:
            mock_user.return_value = Mock(id='user-123')
            mock_org.return_value = ('org-123', 'requester')

            response = client.post(
                '/api/catalog/search',
                headers=auth_headers,
                data=json.dumps({}),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data

    @patch('app.api.catalog.catalog_service.list_items')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_list_items_success(self, mock_org_role, mock_user, mock_list, client):
        """Test successful item listing."""
        # Setup mocks
        mock_user.return_value = Mock(id='user-123')
        mock_org_role.return_value = ('org-123', 'requester')
        mock_list.return_value = [
            {'id': 'item-1', 'name': 'Item 1'},
            {'id': 'item-2', 'name': 'Item 2'}
        ]

        # Make request
        response = client.get(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'}
        )

        # Assertions
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'items' in data
        assert len(data['items']) == 2

    @patch('app.api.catalog.proposal_service.create_proposal')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_request_new_item_success(self, mock_org_role, mock_user, mock_proposal, client):
        """Test successful new item request."""
        # Setup mocks
        mock_user.return_value = Mock(id='user-123')
        mock_org_role.return_value = ('org-123', 'requester')
        mock_proposal.return_value = {
            'id': 'proposal-123',
            'status': 'pending',
            'proposal_type': 'ADD_ITEM'
        }

        # Make request
        response = client.post(
            '/api/catalog/request-new-item',
            headers={'Authorization': 'Bearer test-token'},
            data=json.dumps({
                'name': 'New Item',
                'description': 'Test description',
                'category': 'Test'
            }),
            content_type='application/json'
        )

        # Assertions
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'message' in data
        assert 'proposal' in data
        assert data['proposal']['id'] == 'proposal-123'

    def test_request_new_item_missing_name(self, client):
        """Test request new item without name."""
        with patch('app.middleware.auth_middleware.get_user_from_token') as mock_user, \
             patch('app.middleware.auth_middleware.get_user_org_and_role') as mock_org:
            mock_user.return_value = Mock(id='user-123')
            mock_org.return_value = ('org-123', 'requester')

            response = client.post(
                '/api/catalog/request-new-item',
                headers={'Authorization': 'Bearer test-token'},
                data=json.dumps({'description': 'No name provided'}),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
