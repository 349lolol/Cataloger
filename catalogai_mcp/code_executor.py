"""
Code executor for running user Python code in isolated sandbox.
"""
import docker
import tempfile
import os
import json


class CodeExecutor:
    """Executes user code in isolated Docker sandbox."""

    def __init__(self, image_name="catalogai-sandbox:latest"):
        """
        Initialize code executor.

        Args:
            image_name: Docker image to use for sandboxing
        """
        self.docker_client = docker.from_env()
        self.image_name = image_name

    def execute(self, code: str, context: dict) -> dict:
        """
        Execute Python code in sandbox with catalogai SDK available.

        Args:
            code: Python code to execute
            context: Execution context with API URL and auth token

        Returns:
            Dict with status, output, and exit_code
        """
        # Create temp file with user code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            code_file = f.name

        try:
            # Run in Docker container
            container = self.docker_client.containers.run(
                self.image_name,
                f"python /code/{os.path.basename(code_file)}",
                environment={
                    "CATALOGAI_API_URL": context["api_url"],
                    "CATALOGAI_AUTH_TOKEN": context["auth_token"]
                },
                volumes={
                    os.path.dirname(code_file): {'bind': '/code', 'mode': 'ro'}
                },
                mem_limit="512m",  # 512MB RAM limit
                cpu_period=100000,
                cpu_quota=50000,  # 50% CPU
                network_mode="bridge",  # Isolated network
                detach=True,
                remove=True
            )

            # Wait for completion (max 10 seconds)
            result = container.wait(timeout=10)
            logs = container.logs().decode('utf-8')

            return {
                "status": "success" if result["StatusCode"] == 0 else "error",
                "output": logs,
                "exit_code": result["StatusCode"]
            }
        except docker.errors.ContainerError as e:
            return {
                "status": "error",
                "output": str(e),
                "exit_code": -1
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"Execution error: {str(e)}",
                "exit_code": -1
            }
        finally:
            # Cleanup temp file
            try:
                os.unlink(code_file)
            except:
                pass
