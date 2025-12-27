"""
Pytest configuration and fixtures.
"""
import pytest
import os
from unittest.mock import patch
from app import create_app
from app.config import get_settings


@pytest.fixture(scope='session', autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key-for-testing-only'
    os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
    os.environ['SUPABASE_KEY'] = 'test-anon-key'
    os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-role-key'
    os.environ['JWT_SECRET'] = 'test-jwt-secret'
    yield


@pytest.fixture
def app():
    """Create Flask app for testing."""
    with patch('app.extensions.SentenceTransformer'):
        app = create_app()
        app.config['TESTING'] = True
        return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_user_token():
    """Mock JWT token for authenticated requests."""
    return "mock-jwt-token-for-testing"


@pytest.fixture
def mock_org_id():
    """Mock organization ID."""
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def mock_user_id():
    """Mock user ID."""
    return "00000000-0000-0000-0000-000000000002"


@pytest.fixture
def auth_headers(mock_user_token):
    """Create authorization headers for testing."""
    return {
        'Authorization': f'Bearer {mock_user_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_catalog_item():
    """Sample catalog item data."""
    return {
        'name': 'Test Laptop',
        'description': 'A test laptop for unit testing',
        'category': 'Electronics',
        'metadata': {'brand': 'TestBrand', 'price': 999.99}
    }


@pytest.fixture
def sample_search_query():
    """Sample search query."""
    return {
        'query': 'laptop for development',
        'threshold': 0.3,
        'limit': 5
    }


@pytest.fixture
def sample_proposal():
    """Sample proposal data."""
    return {
        'proposal_type': 'ADD_ITEM',
        'item_name': 'New Test Item',
        'item_description': 'Description for new item',
        'item_category': 'Test Category'
    }
