import pytest
import json
from unittest.mock import patch, Mock
from tests.conftest import get_error_message

TEST_ITEM_UUID = '12345678-1234-1234-1234-123456789abc'
TEST_ORG_UUID = '87654321-4321-4321-4321-cba987654321'
TEST_USER_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'


class TestCatalogAPI:

    @patch('app.api.catalog.catalog_service.search_items')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_search_items_success(self, mock_org_role, mock_user, mock_search, client):
        # Setup mocks
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
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
        with patch('app.middleware.auth_middleware.get_user_from_token') as mock_user, \
             patch('app.middleware.auth_middleware.get_user_org_and_role') as mock_org:
            mock_user.return_value = (Mock(id='user-123'), 'test-token')
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
        # Setup mocks
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
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
        # Setup mocks
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
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
        with patch('app.middleware.auth_middleware.get_user_from_token') as mock_user, \
             patch('app.middleware.auth_middleware.get_user_org_and_role') as mock_org:
            mock_user.return_value = (Mock(id='user-123'), 'test-token')
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

    @patch('app.api.catalog.catalog_service.search_items')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_search_items_with_custom_threshold(self, mock_org, mock_user, mock_search, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')
        mock_search.return_value = [{'item_name': 'Test'}]

        response = client.post(
            '/api/catalog/search',
            headers={'Authorization': 'Bearer test-token'},
            json={'query': 'test', 'threshold': 0.5, 'limit': 20}
        )

        assert response.status_code == 200
        mock_search.assert_called_once_with(
            query='test',
            org_id='org-123',
            threshold=0.5,
            limit=20,
            user_token='test-token'
        )

    @patch('app.api.catalog.catalog_service.search_items')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_search_items_service_error(self, mock_org, mock_user, mock_search, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')
        mock_search.side_effect = Exception("Database error")

        response = client.post(
            '/api/catalog/search',
            headers={'Authorization': 'Bearer test-token'},
            json={'query': 'test'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('app.api.catalog.catalog_service.get_item')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_get_item_success(self, mock_org, mock_user, mock_get, client):
        mock_user.return_value = (Mock(id=TEST_USER_UUID), 'test-token')
        mock_org.return_value = (TEST_ORG_UUID, 'member')
        mock_get.return_value = {
            'id': TEST_ITEM_UUID,
            'name': 'Test Item',
            'org_id': TEST_ORG_UUID
        }

        response = client.get(
            f'/api/catalog/items/{TEST_ITEM_UUID}',
            headers={'Authorization': 'Bearer test-token'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == TEST_ITEM_UUID

    @patch('app.api.catalog.catalog_service.get_item')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_get_item_wrong_org(self, mock_org, mock_user, mock_get, client):
        other_org_uuid = 'cccccccc-dddd-eeee-ffff-000000000000'
        mock_user.return_value = (Mock(id=TEST_USER_UUID), 'test-token')
        mock_org.return_value = (TEST_ORG_UUID, 'member')
        mock_get.return_value = {
            'id': TEST_ITEM_UUID,
            'name': 'Test Item',
            'org_id': other_org_uuid
        }

        response = client.get(
            f'/api/catalog/items/{TEST_ITEM_UUID}',
            headers={'Authorization': 'Bearer test-token'}
        )

        assert response.status_code == 403

    @patch('app.api.catalog.catalog_service.get_item')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_get_item_not_found(self, mock_org, mock_user, mock_get, client):
        nonexistent_uuid = 'ffffffff-ffff-ffff-ffff-ffffffffffff'
        mock_user.return_value = (Mock(id=TEST_USER_UUID), 'test-token')
        mock_org.return_value = (TEST_ORG_UUID, 'member')
        mock_get.side_effect = Exception("Item not found")

        response = client.get(
            f'/api/catalog/items/{nonexistent_uuid}',
            headers={'Authorization': 'Bearer test-token'}
        )

        assert response.status_code == 500

    @patch('app.api.catalog.catalog_service.create_item')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_create_item_success(self, mock_org, mock_user, mock_create, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'admin')
        mock_create.return_value = {
            'id': 'item-123',
            'name': 'New Item',
            'description': 'Test'
        }

        response = client.post(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'},
            json={
                'name': 'New Item',
                'description': 'Test',
                'category': 'Electronics',
                'price': 99.99
            }
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'New Item'

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_create_item_missing_name(self, mock_org, mock_user, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'admin')

        response = client.post(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'},
            json={'description': 'No name'}
        )

        assert response.status_code == 400

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_create_item_non_admin(self, mock_org, mock_user, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')

        response = client.post(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'},
            json={'name': 'New Item'}
        )

        assert response.status_code == 403

    @patch('app.api.catalog.catalog_service.list_items')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_list_items_with_status(self, mock_org, mock_user, mock_list, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')
        mock_list.return_value = [{'id': 'item-1', 'status': 'active'}]

        response = client.get(
            '/api/catalog/items?status=active&limit=50',
            headers={'Authorization': 'Bearer test-token'}
        )

        assert response.status_code == 200
        mock_list.assert_called_once_with(org_id='org-123', status='active', limit=50, user_token='test-token')

    @patch('app.api.catalog.catalog_service.list_items')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_list_items_error(self, mock_org, mock_user, mock_list, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')
        mock_list.side_effect = Exception("Database error")

        response = client.get(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'}
        )

        assert response.status_code == 500

    @patch('app.services.product_enrichment_service.enrich_product')
    @patch('app.api.catalog.proposal_service.create_proposal')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_request_new_item_with_ai(self, mock_org, mock_user, mock_proposal, mock_enrich, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')

        mock_enrich.return_value = {
            'name': 'MacBook Pro 16-inch',
            'description': 'Laptop',
            'category': 'Electronics',
            'vendor': 'Apple',
            'price': 3499.00,
            'pricing_type': 'one_time',
            'product_url': 'https://apple.com',
            'sku': 'MBP-001',
            'metadata': {'brand': 'Apple'},
            'confidence': 'high'
        }

        mock_proposal.return_value = {
            'id': 'proposal-123',
            'status': 'pending',
            'proposal_type': 'ADD_ITEM'
        }

        response = client.post(
            '/api/catalog/request-new-item',
            headers={'Authorization': 'Bearer test-token'},
            json={
                'name': 'MacBook Pro 16 inch',
                'use_ai_enrichment': True,
                'justification': 'Need for development'
            }
        )

        assert response.status_code == 201
        data = response.get_json()
        assert 'ai_enrichment' in data
        assert data['ai_enrichment']['vendor'] == 'Apple'

    @patch('app.api.catalog.proposal_service.create_proposal')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_request_new_item_manual(self, mock_org, mock_user, mock_proposal, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')

        mock_proposal.return_value = {
            'id': 'proposal-123',
            'status': 'pending'
        }

        response = client.post(
            '/api/catalog/request-new-item',
            headers={'Authorization': 'Bearer test-token'},
            json={
                'name': 'Custom Item',
                'description': 'Custom description',
                'category': 'Custom',
                'use_ai_enrichment': False
            }
        )

        assert response.status_code == 201
        data = response.get_json()
        assert 'ai_enrichment' not in data

    @patch('app.services.product_enrichment_service.enrich_product')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_request_new_item_ai_error(self, mock_org, mock_user, mock_enrich, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')
        mock_enrich.side_effect = Exception("AI service error")

        response = client.post(
            '/api/catalog/request-new-item',
            headers={'Authorization': 'Bearer test-token'},
            json={
                'name': 'Test Product',
                'use_ai_enrichment': True
            }
        )

        assert response.status_code == 500

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_create_item_xss_prevention(self, mock_org, mock_user, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'admin')

        # Test script tag in name
        response = client.post(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'},
            json={'name': '<script>alert("xss")</script>'}
        )
        assert response.status_code == 400
        assert 'invalid content' in get_error_message(response.get_json())

        # Test javascript: in description
        response = client.post(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'},
            json={'name': 'Valid Name', 'description': 'javascript:alert(1)'}
        )
        assert response.status_code == 400

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_create_item_invalid_url(self, mock_org, mock_user, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'admin')

        response = client.post(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'},
            json={
                'name': 'Valid Name',
                'product_url': 'not-a-valid-url'
            }
        )
        assert response.status_code == 400
        assert 'http' in get_error_message(response.get_json())

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_create_item_invalid_pricing_type(self, mock_org, mock_user, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'admin')

        response = client.post(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'},
            json={
                'name': 'Valid Name',
                'pricing_type': 'invalid_type'
            }
        )
        assert response.status_code == 400
        assert 'pricing_type' in get_error_message(response.get_json())

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_create_item_negative_price(self, mock_org, mock_user, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'admin')

        response = client.post(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'},
            json={
                'name': 'Valid Name',
                'price': -100
            }
        )
        assert response.status_code == 400
        assert 'negative' in get_error_message(response.get_json())

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_create_item_price_exceeds_max(self, mock_org, mock_user, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'admin')

        response = client.post(
            '/api/catalog/items',
            headers={'Authorization': 'Bearer test-token'},
            json={
                'name': 'Valid Name',
                'price': 99999999  # Over $10M limit
            }
        )
        assert response.status_code == 400
        assert 'exceed' in get_error_message(response.get_json())

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_search_invalid_threshold(self, mock_org, mock_user, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')

        # Threshold > 1.0
        response = client.post(
            '/api/catalog/search',
            headers={'Authorization': 'Bearer test-token'},
            json={'query': 'test', 'threshold': 1.5}
        )
        assert response.status_code == 400
        assert 'threshold' in get_error_message(response.get_json())

        # Threshold < 0
        response = client.post(
            '/api/catalog/search',
            headers={'Authorization': 'Bearer test-token'},
            json={'query': 'test', 'threshold': -0.5}
        )
        assert response.status_code == 400

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_search_invalid_limit(self, mock_org, mock_user, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')

        # Limit > 100
        response = client.post(
            '/api/catalog/search',
            headers={'Authorization': 'Bearer test-token'},
            json={'query': 'test', 'limit': 500}
        )
        assert response.status_code == 400
        assert 'limit' in get_error_message(response.get_json())

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_get_item_invalid_uuid(self, mock_org, mock_user, client):
        mock_user.return_value = (Mock(id='user-123'), 'test-token')
        mock_org.return_value = ('org-123', 'member')

        response = client.get(
            '/api/catalog/items/not-a-valid-uuid',
            headers={'Authorization': 'Bearer test-token'}
        )
        assert response.status_code == 400
        assert 'Invalid' in get_error_message(response.get_json())
