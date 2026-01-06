import pytest
from unittest.mock import patch, Mock
from flask import Flask, g, jsonify
from app.middleware.auth_middleware import (
    get_user_from_token,
    get_user_org_and_role,
    require_auth,
    require_role
)


class TestAuthMiddleware:

    @patch('app.middleware.auth_middleware.get_supabase_client')
    def test_get_user_from_token_success(self, mock_supabase):
        """Test successful token validation."""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.email = 'test@example.com'

        mock_response = Mock()
        mock_response.user = mock_user

        mock_auth = Mock()
        mock_auth.get_user.return_value = mock_response
        mock_supabase.return_value.auth = mock_auth

        app = Flask(__name__)
        with app.test_request_context(headers={'Authorization': 'Bearer valid-token'}):
            user, token = get_user_from_token()

        assert user is not None
        assert user.id == 'user-123'
        assert token == 'valid-token'
        mock_auth.get_user.assert_called_once_with('valid-token')

    def test_get_user_from_token_no_header(self):
        """Test token validation without Authorization header."""
        app = Flask(__name__)
        with app.test_request_context():
            user, token = get_user_from_token()

        assert user is None
        assert token is None

    def test_get_user_from_token_invalid_format(self):
        """Test token validation with invalid Authorization format."""
        app = Flask(__name__)

        # Test missing Bearer prefix
        with app.test_request_context(headers={'Authorization': 'invalid-token'}):
            user, token = get_user_from_token()
        assert user is None
        assert token is None

        # Test wrong prefix
        with app.test_request_context(headers={'Authorization': 'Basic token'}):
            user, token = get_user_from_token()
        assert user is None
        assert token is None

        # Test only Bearer without token
        with app.test_request_context(headers={'Authorization': 'Bearer'}):
            user, token = get_user_from_token()
        assert user is None
        assert token is None

    @patch('app.middleware.auth_middleware.get_supabase_client')
    def test_get_user_from_token_validation_error(self, mock_supabase):
        """Test token validation when Supabase returns error."""
        mock_auth = Mock()
        mock_auth.get_user.side_effect = Exception("Invalid token")
        mock_supabase.return_value.auth = mock_auth

        app = Flask(__name__)
        with app.test_request_context(headers={'Authorization': 'Bearer invalid-token'}):
            user, token = get_user_from_token()

        assert user is None
        assert token is None

    @patch('app.middleware.auth_middleware.get_supabase_client')
    def test_get_user_from_token_no_user(self, mock_supabase):
        """Test token validation when no user is returned."""
        mock_auth = Mock()
        mock_auth.get_user.return_value = None
        mock_supabase.return_value.auth = mock_auth

        app = Flask(__name__)
        with app.test_request_context(headers={'Authorization': 'Bearer token'}):
            user, token = get_user_from_token()

        assert user is None
        assert token is None

    @patch('app.middleware.auth_middleware.get_supabase_admin')
    def test_get_user_org_and_role_success(self, mock_supabase):
        """Test successful org and role retrieval."""
        mock_response = Mock()
        # Now returns a list since we use limit(1) instead of single()
        mock_response.data = [{'org_id': 'org-123', 'role': 'admin'}]

        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        mock_supabase.return_value.table.return_value.select.return_value = mock_query

        org_id, role = get_user_org_and_role('user-123')

        assert org_id == 'org-123'
        assert role == 'admin'

    @patch('app.middleware.auth_middleware.get_supabase_admin')
    def test_get_user_org_and_role_not_found(self, mock_supabase):
        """Test org retrieval when user has no org membership."""
        mock_response = Mock()
        mock_response.data = []  # Empty list instead of None

        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        mock_supabase.return_value.table.return_value.select.return_value = mock_query

        org_id, role = get_user_org_and_role('user-123')

        assert org_id is None
        assert role is None

    @patch('app.middleware.auth_middleware.get_supabase_admin')
    def test_get_user_org_and_role_error(self, mock_supabase):
        """Test org retrieval when database error occurs."""
        mock_query = Mock()
        mock_query.select.side_effect = Exception("Database error")
        mock_supabase.return_value.table.return_value = mock_query

        org_id, role = get_user_org_and_role('user-123')

        assert org_id is None
        assert role is None

    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_require_auth_success(self, mock_get_user, mock_get_org):
        """Test require_auth decorator with valid auth."""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_get_user.return_value = (mock_user, 'test-token')
        mock_get_org.return_value = ('org-123', 'member')

        app = Flask(__name__)

        @require_auth
        def protected_route():
            return jsonify({'success': True, 'user_id': g.user_id})

        with app.test_request_context(headers={'Authorization': 'Bearer token'}):
            response = protected_route()
            data = response.get_json()

        assert data['success'] is True
        assert data['user_id'] == 'user-123'

    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_require_auth_no_token(self, mock_get_user):
        """Test require_auth decorator without token."""
        mock_get_user.return_value = (None, None)

        app = Flask(__name__)

        @require_auth
        def protected_route():
            return jsonify({'success': True})

        with app.test_request_context():
            response, status_code = protected_route()
            data = response.get_json()

        assert status_code == 401
        assert 'Unauthorized' in data['error']

    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_require_auth_no_org(self, mock_get_user, mock_get_org):
        """Test require_auth when user has no org membership."""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_get_user.return_value = (mock_user, 'test-token')
        mock_get_org.return_value = (None, None)

        app = Flask(__name__)

        @require_auth
        def protected_route():
            return jsonify({'success': True})

        with app.test_request_context(headers={'Authorization': 'Bearer token'}):
            response, status_code = protected_route()
            data = response.get_json()

        assert status_code == 403
        assert 'not a member of any organization' in data['error']

    def test_require_role_success(self):
        """Test require_role decorator with correct role."""
        app = Flask(__name__)

        @require_role(['admin', 'reviewer'])
        def admin_route():
            return jsonify({'success': True})

        with app.test_request_context():
            g.user_role = 'admin'
            response = admin_route()
            data = response.get_json()

        assert data['success'] is True

    def test_require_role_forbidden(self):
        """Test require_role decorator with insufficient role."""
        app = Flask(__name__)

        @require_role(['admin'])
        def admin_route():
            return jsonify({'success': True})

        with app.test_request_context():
            g.user_role = 'member'
            response, status_code = admin_route()
            data = response.get_json()

        assert status_code == 403
        assert 'Requires role' in data['error']

    def test_require_role_no_user_role(self):
        """Test require_role decorator without user role in context."""
        app = Flask(__name__)

        @require_role(['admin'])
        def admin_route():
            return jsonify({'success': True})

        with app.test_request_context():
            response, status_code = admin_route()
            data = response.get_json()

        assert status_code == 401
        assert 'Unauthorized' in data['error']

    def test_require_role_multiple_allowed(self):
        """Test require_role with multiple allowed roles."""
        app = Flask(__name__)

        @require_role(['admin', 'reviewer', 'member'])
        def multi_role_route():
            return jsonify({'success': True})

        with app.test_request_context():
            g.user_role = 'reviewer'
            response = multi_role_route()
            data = response.get_json()

        assert data['success'] is True

    @patch('app.middleware.auth_middleware.get_user_org_and_role')
    @patch('app.middleware.auth_middleware.get_user_from_token')
    def test_require_auth_sets_context_variables(self, mock_get_user, mock_get_org):
        """Test that require_auth sets all context variables correctly."""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.email = 'test@example.com'
        mock_get_user.return_value = (mock_user, 'test-token')
        mock_get_org.return_value = ('org-456', 'reviewer')

        app = Flask(__name__)

        @require_auth
        def check_context():
            return jsonify({
                'user_id': g.user_id,
                'org_id': g.org_id,
                'user_role': g.user_role,
                'has_user': hasattr(g, 'user'),
                'has_user_token': hasattr(g, 'user_token')
            })

        with app.test_request_context(headers={'Authorization': 'Bearer token'}):
            response = check_context()
            data = response.get_json()

        assert data['user_id'] == 'user-123'
        assert data['org_id'] == 'org-456'
        assert data['user_role'] == 'reviewer'
        assert data['has_user'] is True
        assert data['has_user_token'] is True

    @patch('app.middleware.auth_middleware.get_supabase_client')
    def test_get_user_from_token_case_insensitive_bearer(self, mock_supabase):
        """Test that Bearer keyword is case insensitive."""
        mock_user = Mock()
        mock_user.id = 'user-123'

        mock_response = Mock()
        mock_response.user = mock_user

        mock_auth = Mock()
        mock_auth.get_user.return_value = mock_response
        mock_supabase.return_value.auth = mock_auth

        app = Flask(__name__)

        # Test lowercase bearer
        with app.test_request_context(headers={'Authorization': 'bearer valid-token'}):
            user, token = get_user_from_token()

        assert user is not None
        assert user.id == 'user-123'
        assert token == 'valid-token'
