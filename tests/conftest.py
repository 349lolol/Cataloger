import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Mock external dependencies before any app imports
sys.modules['supabase'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

from app import create_app
from app.config import get_settings


def get_error_message(response_json):
    """Extract error message from API response (handles both old and new format)."""
    error = response_json.get('error')
    if isinstance(error, dict):
        return error.get('message', '')
    return error or ''


@pytest.fixture(scope='session', autouse=True)
def setup_test_env():
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key-for-testing-only'
    os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
    os.environ['SUPABASE_KEY'] = 'test-anon-key'
    os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-role-key'
    os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
    yield


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_user_token():
    return "mock-jwt-token-for-testing"


@pytest.fixture
def mock_org_id():
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def mock_user_id():
    return "00000000-0000-0000-0000-000000000002"


@pytest.fixture
def auth_headers(mock_user_token):
    return {
        'Authorization': f'Bearer {mock_user_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_catalog_item():
    return {
        'name': 'Test Laptop',
        'description': 'A test laptop for unit testing',
        'category': 'Electronics',
        'metadata': {'brand': 'TestBrand', 'price': 999.99}
    }


@pytest.fixture
def sample_search_query():
    return {
        'query': 'laptop for development',
        'threshold': 0.3,
        'limit': 5
    }


@pytest.fixture
def sample_proposal():
    return {
        'proposal_type': 'ADD_ITEM',
        'item_name': 'New Test Item',
        'item_description': 'Description for new item',
        'item_category': 'Test Category'
    }
