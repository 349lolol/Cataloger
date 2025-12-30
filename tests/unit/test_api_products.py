"""
Unit tests for products API endpoints.
"""
import pytest
import json
from unittest.mock import patch, Mock
from app.api.products import bp


class TestProductsAPI:
    """Test product enrichment API endpoints."""

    @patch('app.api.products.enrich_product')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_product_success(self, mock_get_org, mock_get_user, mock_enrich, client):
        """Test successful product enrichment."""
        # Mock auth
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        # Mock enrichment
        mock_enrich.return_value = {
            "name": "MacBook Pro 16-inch",
            "description": "High-performance laptop",
            "category": "Electronics",
            "vendor": "Apple",
            "price": 3499.00,
            "pricing_type": "one_time",
            "product_url": "https://www.apple.com/macbook-pro/",
            "sku": "MRW13LL/A",
            "metadata": {"brand": "Apple"},
            "confidence": "high"
        }

        response = client.post(
            '/api/products/enrich',
            headers={'Authorization': 'Bearer test-token'},
            json={'product_name': 'MacBook Pro 16 inch'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'MacBook Pro 16-inch'
        assert data['vendor'] == 'Apple'
        assert data['confidence'] == 'high'

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_product_missing_product_name(self, mock_get_org, mock_get_user, client):
        """Test enrichment without product_name."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        response = client.post(
            '/api/products/enrich',
            headers={'Authorization': 'Bearer test-token'},
            json={}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'product_name is required' in data['error']

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_product_no_body(self, mock_get_org, mock_get_user, client):
        """Test enrichment with no request body."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        response = client.post(
            '/api/products/enrich',
            headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
            json=None
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    @patch('app.api.products.enrich_product')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_product_with_category(self, mock_get_org, mock_get_user, mock_enrich, client):
        """Test enrichment with category hint."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        mock_enrich.return_value = {
            "name": "Dell XPS 15",
            "description": "Premium laptop",
            "category": "Electronics",
            "vendor": "Dell",
            "confidence": "high",
            "metadata": {}
        }

        response = client.post(
            '/api/products/enrich',
            headers={'Authorization': 'Bearer test-token'},
            json={
                'product_name': 'Dell XPS 15',
                'category': 'Electronics'
            }
        )

        assert response.status_code == 200
        mock_enrich.assert_called_once_with(
            product_name='Dell XPS 15',
            category='Electronics',
            additional_context=None
        )

    @patch('app.api.products.enrich_product')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_product_with_context(self, mock_get_org, mock_get_user, mock_enrich, client):
        """Test enrichment with additional context."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        mock_enrich.return_value = {
            "name": "Gaming Mouse",
            "description": "High DPI gaming mouse",
            "category": "Electronics",
            "vendor": "Logitech",
            "confidence": "high",
            "metadata": {}
        }

        response = client.post(
            '/api/products/enrich',
            headers={'Authorization': 'Bearer test-token'},
            json={
                'product_name': 'Gaming Mouse',
                'additional_context': 'For competitive gaming'
            }
        )

        assert response.status_code == 200
        mock_enrich.assert_called_once_with(
            product_name='Gaming Mouse',
            category=None,
            additional_context='For competitive gaming'
        )

    @patch('app.api.products.enrich_product')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_product_validation_error(self, mock_get_org, mock_get_user, mock_enrich, client):
        """Test enrichment with validation error."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        mock_enrich.side_effect = ValueError("Missing required field: vendor")

        response = client.post(
            '/api/products/enrich',
            headers={'Authorization': 'Bearer test-token'},
            json={'product_name': 'Test Product'}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Validation error' in data['error']

    @patch('app.api.products.enrich_product')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_product_service_error(self, mock_get_org, mock_get_user, mock_enrich, client):
        """Test enrichment with service error."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        mock_enrich.side_effect = Exception("Gemini API error")

        response = client.post(
            '/api/products/enrich',
            headers={'Authorization': 'Bearer test-token'},
            json={'product_name': 'Test Product'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert 'Enrichment failed' in data['error']

    def test_enrich_product_requires_auth(self, client):
        """Test that enrichment requires authentication."""
        response = client.post(
            '/api/products/enrich',
            json={'product_name': 'Test Product'}
        )

        assert response.status_code == 401

    @patch('app.api.products.enrich_product_batch')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_batch_success(self, mock_get_org, mock_get_user, mock_batch, client):
        """Test successful batch enrichment."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        mock_batch.return_value = [
            {"name": "Product 1", "vendor": "Vendor1", "description": "Desc1",
             "category": "Cat1", "confidence": "high", "metadata": {}},
            {"name": "Product 2", "vendor": "Vendor2", "description": "Desc2",
             "category": "Cat2", "confidence": "high", "metadata": {}},
        ]

        response = client.post(
            '/api/products/enrich-batch',
            headers={'Authorization': 'Bearer test-token'},
            json={'product_names': ['Product 1', 'Product 2']}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert len(data['results']) == 2

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_batch_missing_product_names(self, mock_get_org, mock_get_user, client):
        """Test batch enrichment without product_names."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        response = client.post(
            '/api/products/enrich-batch',
            headers={'Authorization': 'Bearer test-token'},
            json={}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'product_names is required' in data['error']

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_batch_invalid_type(self, mock_get_org, mock_get_user, client):
        """Test batch enrichment with non-array product_names."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        response = client.post(
            '/api/products/enrich-batch',
            headers={'Authorization': 'Bearer test-token'},
            json={'product_names': 'not an array'}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'must be an array' in data['error']

    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_batch_exceeds_limit(self, mock_get_org, mock_get_user, client):
        """Test batch enrichment exceeding maximum batch size."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        product_names = [f'Product {i}' for i in range(25)]

        response = client.post(
            '/api/products/enrich-batch',
            headers={'Authorization': 'Bearer test-token'},
            json={'product_names': product_names}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'Maximum 20 products' in data['error']

    @patch('app.api.products.enrich_product_batch')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_batch_service_error(self, mock_get_org, mock_get_user, mock_batch, client):
        """Test batch enrichment with service error."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        mock_batch.side_effect = Exception("Batch processing failed")

        response = client.post(
            '/api/products/enrich-batch',
            headers={'Authorization': 'Bearer test-token'},
            json={'product_names': ['Product 1', 'Product 2']}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert 'Batch enrichment failed' in data['error']

    def test_enrich_batch_requires_auth(self, client):
        """Test that batch enrichment requires authentication."""
        response = client.post(
            '/api/products/enrich-batch',
            json={'product_names': ['Product 1']}
        )

        assert response.status_code == 401

    @patch('app.api.products.enrich_product_batch')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    def test_enrich_batch_empty_array(self, mock_get_org, mock_get_user, mock_batch, client):
        """Test batch enrichment with empty array."""
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        mock_get_org.return_value = ('test-org-id', 'member')

        mock_batch.return_value = []

        response = client.post(
            '/api/products/enrich-batch',
            headers={'Authorization': 'Bearer test-token'},
            json={'product_names': []}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['results'] == []
