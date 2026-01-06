import pytest
import os


class TestMCPServerStructure:

    def test_server_file_exists(self):
        """Test that server.py exists."""
        server_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'server.py'
        )
        assert os.path.exists(server_path), "server.py should exist"

    def test_server_has_api_error_class(self):
        """Test that APIError class is defined in server."""
        server_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'server.py'
        )
        with open(server_path, 'r') as f:
            content = f.read()

        assert 'class APIError' in content, "APIError class should be defined"
        assert 'def __init__(self, status_code' in content, "APIError should have status_code"

    def test_server_has_authenticate_function(self):
        """Test that authenticate function is defined."""
        server_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'server.py'
        )
        with open(server_path, 'r') as f:
            content = f.read()

        assert 'def authenticate(' in content, "authenticate function should be defined"

    def test_server_has_api_call_function(self):
        """Test that _api_call function is defined."""
        server_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'server.py'
        )
        with open(server_path, 'r') as f:
            content = f.read()

        assert 'def _api_call(' in content, "_api_call function should be defined"

    def test_server_defines_mcp_tools(self):
        """Test that MCP tools are defined."""
        server_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'server.py'
        )
        with open(server_path, 'r') as f:
            content = f.read()

        # Check for key MCP tool decorators
        assert '@mcp.tool()' in content, "Should have MCP tool decorators"

        # Check for expected tools (core catalog operations)
        expected_tools = [
            'search_catalog',
            'get_catalog_item',
            'list_catalog',  # Actual name in server.py
            'create_request',
            'enrich_product',
        ]

        for tool in expected_tools:
            assert f'def {tool}(' in content or f'async def {tool}(' in content, \
                f"Tool {tool} should be defined"

    def test_server_uses_correct_api_endpoints(self):
        """Test that server uses correct API endpoint paths."""
        server_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'server.py'
        )
        with open(server_path, 'r') as f:
            content = f.read()

        # Check for correct endpoints (fixed from earlier bug)
        assert '/api/catalog/items' in content, "Should use /api/catalog/items endpoint"
        assert '/api/catalog/search' in content, "Should use /api/catalog/search endpoint"
        assert '/api/requests' in content, "Should use /api/requests endpoint"

    def test_server_raises_api_error_on_http_errors(self):
        """Test that server raises APIError instead of returning error dict in _api_call."""
        server_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'server.py'
        )
        with open(server_path, 'r') as f:
            content = f.read()

        # Check that _api_call raises APIError on HTTP errors
        assert 'raise APIError(' in content, "Should raise APIError on HTTP errors"

        # Extract _api_call function to verify it doesn't return error dicts
        # Find _api_call function boundaries
        api_call_start = content.find('def _api_call(')
        assert api_call_start != -1, "_api_call function should exist"

        # Find the next function definition (end of _api_call)
        next_func = content.find('\ndef ', api_call_start + 1)
        api_call_body = content[api_call_start:next_func] if next_func != -1 else content[api_call_start:]

        # _api_call should raise APIError, not return error dicts
        assert 'return {"error":' not in api_call_body, \
            "_api_call should raise APIError, not return error dicts"


class TestCodeExecutor:
    """Test code executor file structure."""

    def test_code_executor_exists(self):
        """Test that code_executor.py exists."""
        executor_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'code_executor.py'
        )
        assert os.path.exists(executor_path), "code_executor.py should exist"

    def test_code_executor_has_proper_cleanup(self):
        """Test that code executor has proper container cleanup."""
        executor_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'code_executor.py'
        )
        with open(executor_path, 'r') as f:
            content = f.read()

        # Check for proper cleanup pattern (fixed from earlier bug)
        assert 'container.remove(force=True)' in content, \
            "Should have container cleanup with force=True"
        assert 'finally:' in content, "Should have finally block for cleanup"

    def test_code_executor_uses_specific_exceptions(self):
        """Test that code executor uses specific exceptions, not bare except."""
        executor_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'code_executor.py'
        )
        with open(executor_path, 'r') as f:
            content = f.read()

        # Check for specific exception handling (fixed from earlier bug)
        assert 'except OSError:' in content or 'except Exception as' in content, \
            "Should use specific exceptions, not bare except"

    def test_code_executor_has_execute_method(self):
        """Test that CodeExecutor class has execute method."""
        executor_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'code_executor.py'
        )
        with open(executor_path, 'r') as f:
            content = f.read()

        assert 'class CodeExecutor' in content, "CodeExecutor class should be defined"
        assert 'def execute(' in content, "execute method should be defined"


class TestMCPPackageStructure:
    """Test MCP package structure."""

    def test_init_file_exists(self):
        """Test that __init__.py exists."""
        init_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', '__init__.py'
        )
        assert os.path.exists(init_path), "__init__.py should exist"

    def test_sandbox_dockerfile_exists(self):
        """Test that sandbox.Dockerfile exists."""
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'sandbox.Dockerfile'
        )
        assert os.path.exists(dockerfile_path), "sandbox.Dockerfile should exist"

    def test_sandbox_dockerfile_has_security(self):
        """Test that sandbox Dockerfile has security measures."""
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'sandbox.Dockerfile'
        )
        with open(dockerfile_path, 'r') as f:
            content = f.read()

        # Check for security measures
        assert 'useradd' in content.lower() or 'adduser' in content.lower(), \
            "Should create non-root user"
        assert 'USER' in content, "Should switch to non-root user"

    def test_test_setup_script_exists(self):
        """Test that test_setup.py exists for MCP verification."""
        test_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'catalogai_mcp', 'test_setup.py'
        )
        assert os.path.exists(test_path), "test_setup.py should exist"
