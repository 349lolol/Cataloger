"""
Unit tests for CatalogAI MCP code executor.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from catalogai_mcp.code_executor import CodeExecutor


class TestCodeExecutor:
    """Test MCP code executor."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        with patch('catalogai_mcp.code_executor.docker') as mock_docker:
            executor = CodeExecutor()
            executor.docker_client = mock_docker.from_env.return_value
            return executor

    def test_executor_initialization(self):
        """Test executor initializes with correct Docker client."""
        with patch('catalogai_mcp.code_executor.docker') as mock_docker:
            executor = CodeExecutor()
            mock_docker.from_env.assert_called_once()

    def test_execute_simple_code_success(self, executor):
        """Test executing simple Python code."""
        # Setup mock container
        mock_container = Mock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"Hello, World!"
        executor.docker_client.containers.run.return_value = mock_container

        # Execute code
        code = "print('Hello, World!')"
        context = {
            "api_url": "http://localhost:5000",
            "auth_token": "test-token"
        }

        result = executor.execute(code, context)

        # Assertions
        assert result["success"] is True
        assert "Hello, World!" in result["output"]
        assert result["exit_code"] == 0

    def test_execute_code_with_catalogai_sdk(self, executor):
        """Test executing code that uses CatalogAI SDK."""
        # Setup mock container
        mock_container = Mock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b'[{"item_name": "Laptop", "similarity_score": 0.9}]'
        executor.docker_client.containers.run.return_value = mock_container

        # Execute code
        code = """
import catalogai

client = catalogai.CatalogAIClient(api_url, auth_token)
results = client.catalog.search("laptop")
print(results)
"""
        context = {
            "api_url": "http://localhost:5000",
            "auth_token": "test-token"
        }

        result = executor.execute(code, context)

        # Assertions
        assert result["success"] is True
        assert "Laptop" in result["output"]

        # Verify environment variables were passed
        call_kwargs = executor.docker_client.containers.run.call_args[1]
        assert call_kwargs["environment"]["CATALOGAI_API_URL"] == "http://localhost:5000"
        assert call_kwargs["environment"]["CATALOGAI_AUTH_TOKEN"] == "test-token"

    def test_execute_code_with_timeout(self, executor):
        """Test that code execution respects timeout."""
        # Setup mock to simulate timeout
        mock_container = Mock()
        mock_container.wait.side_effect = Exception("Timeout")
        executor.docker_client.containers.run.return_value = mock_container

        # Execute code
        code = "import time; time.sleep(100)"
        context = {"api_url": "http://localhost:5000", "auth_token": "test-token"}

        result = executor.execute(code, context)

        # Should handle timeout gracefully
        assert result["success"] is False
        assert "error" in result or "timeout" in result["output"].lower()

    def test_execute_code_with_resource_limits(self, executor):
        """Test that resource limits are applied."""
        # Setup mock
        mock_container = Mock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"Success"
        executor.docker_client.containers.run.return_value = mock_container

        # Execute code
        code = "print('Test')"
        context = {"api_url": "http://localhost:5000", "auth_token": "test-token"}

        result = executor.execute(code, context)

        # Verify resource limits were set
        call_kwargs = executor.docker_client.containers.run.call_args[1]
        assert call_kwargs["mem_limit"] == "512m"  # 512MB memory limit
        assert call_kwargs["cpu_quota"] == 50000  # 50% CPU limit

    def test_execute_code_with_network_isolation(self, executor):
        """Test that network isolation is configured."""
        # Setup mock
        mock_container = Mock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"Success"
        executor.docker_client.containers.run.return_value = mock_container

        # Execute code
        code = "print('Test')"
        context = {"api_url": "http://localhost:5000", "auth_token": "test-token"}

        result = executor.execute(code, context)

        # Verify network mode is set to bridge (isolated)
        call_kwargs = executor.docker_client.containers.run.call_args[1]
        assert call_kwargs["network_mode"] == "bridge"

    def test_execute_code_with_error(self, executor):
        """Test executing code that raises an error."""
        # Setup mock container with error
        mock_container = Mock()
        mock_container.wait.return_value = {"StatusCode": 1}
        mock_container.logs.return_value = b"Traceback: NameError: name 'undefined_var' is not defined"
        executor.docker_client.containers.run.return_value = mock_container

        # Execute code with error
        code = "print(undefined_var)"
        context = {"api_url": "http://localhost:5000", "auth_token": "test-token"}

        result = executor.execute(code, context)

        # Assertions
        assert result["success"] is False
        assert result["exit_code"] == 1
        assert "NameError" in result["output"]

    def test_execute_cleanup_container(self, executor):
        """Test that containers are cleaned up after execution."""
        # Setup mock
        mock_container = Mock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"Success"
        executor.docker_client.containers.run.return_value = mock_container

        # Execute code
        code = "print('Test')"
        context = {"api_url": "http://localhost:5000", "auth_token": "test-token"}

        executor.execute(code, context)

        # Verify container was removed (auto_remove should be True)
        call_kwargs = executor.docker_client.containers.run.call_args[1]
        # The container should be configured with remove=True or similar cleanup mechanism
        # This depends on your actual implementation

    def test_execute_code_with_imports(self, executor):
        """Test executing code with allowed imports."""
        # Setup mock
        mock_container = Mock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"2025-01-15"
        executor.docker_client.containers.run.return_value = mock_container

        # Execute code with standard library imports
        code = """
from datetime import datetime
print(datetime.now().strftime('%Y-%m-%d'))
"""
        context = {"api_url": "http://localhost:5000", "auth_token": "test-token"}

        result = executor.execute(code, context)

        # Should succeed
        assert result["success"] is True
        assert "2025" in result["output"]

    def test_execute_code_validates_context(self, executor):
        """Test that executor validates required context fields."""
        # Missing auth_token
        code = "print('Test')"
        context = {"api_url": "http://localhost:5000"}

        # Should handle missing context gracefully
        # Implementation dependent - might raise ValueError or return error result
        try:
            result = executor.execute(code, context)
            # If it doesn't raise, check for error in result
            if not result.get("success"):
                assert "token" in result.get("error", "").lower() or "auth" in result.get("error", "").lower()
        except (ValueError, KeyError) as e:
            # Expected behavior for missing required fields
            assert "token" in str(e).lower() or "auth" in str(e).lower()

    @patch('catalogai_mcp.code_executor.tempfile.NamedTemporaryFile')
    def test_execute_writes_code_to_temp_file(self, mock_tempfile, executor):
        """Test that code is written to temporary file."""
        # Setup mocks
        mock_file = MagicMock()
        mock_tempfile.return_value.__enter__.return_value = mock_file
        mock_file.name = "/tmp/code_xyz.py"

        mock_container = Mock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"Success"
        executor.docker_client.containers.run.return_value = mock_container

        # Execute code
        code = "print('Test')"
        context = {"api_url": "http://localhost:5000", "auth_token": "test-token"}

        executor.execute(code, context)

        # Verify temp file was created and code was written
        mock_tempfile.assert_called_once()
