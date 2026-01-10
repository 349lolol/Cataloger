"""
Code executor for running user Python code in isolated sandbox.
"""
import docker
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Executes user code in isolated Docker sandbox."""

    def __init__(self, image_name="catalogai-sandbox:latest", timeout: int = 30):
        """
        Initialize code executor.

        Args:
            image_name: Docker image to use for sandboxing
            timeout: Maximum execution time in seconds (default: 30)
        """
        self.docker_client = docker.from_env()
        self.image_name = image_name
        self.timeout = timeout
        self.skills_dir = os.path.join(os.path.dirname(__file__), 'skills')

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

        # Convert localhost URLs to host.docker.internal for container access
        api_url = context["api_url"]
        if "localhost" in api_url:
            api_url = api_url.replace("localhost", "host.docker.internal")
        elif "127.0.0.1" in api_url:
            api_url = api_url.replace("127.0.0.1", "host.docker.internal")

        container = None
        try:
            # Run in Docker container (don't use remove=True so we can cleanup manually)
            container = self.docker_client.containers.run(
                self.image_name,
                f"python /code/{os.path.basename(code_file)}",
                environment={
                    "CATALOGAI_API_URL": api_url,
                    "CATALOGAI_AUTH_TOKEN": context["auth_token"],
                    "PYTHONPATH": "/code"
                },
                volumes={
                    os.path.dirname(code_file): {'bind': '/code', 'mode': 'ro'},
                    self.skills_dir: {'bind': '/code/skills', 'mode': 'ro'}
                },
                mem_limit="512m",  # 512MB RAM limit
                cpu_period=100000,
                cpu_quota=50000,  # 50% CPU
                network_mode="bridge",  # Isolated network
                detach=True,
                remove=False  # We'll handle removal manually for proper cleanup
            )

            # Wait for completion with timeout
            try:
                result = container.wait(timeout=self.timeout)
                logs = container.logs().decode('utf-8')

                return {
                    "status": "success" if result["StatusCode"] == 0 else "error",
                    "output": logs,
                    "exit_code": result["StatusCode"]
                }
            except Exception as wait_error:
                # Timeout or other wait error - kill the container
                try:
                    container.kill()
                except Exception:
                    pass
                return {
                    "status": "error",
                    "output": f"Execution timed out after {self.timeout} seconds",
                    "exit_code": -1
                }

        except docker.errors.ContainerError as e:
            return {
                "status": "error",
                "output": str(e),
                "exit_code": -1
            }
        except docker.errors.ImageNotFound:
            return {
                "status": "error",
                "output": f"Docker image '{self.image_name}' not found. Build it first.",
                "exit_code": -1
            }
        except docker.errors.APIError as e:
            return {
                "status": "error",
                "output": f"Docker API error: {str(e)}",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"Execution error: {str(e)}",
                "exit_code": -1
            }
        finally:
            # Always cleanup container if it exists
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup container: {cleanup_error}")

            # Cleanup temp file
            try:
                os.unlink(code_file)
            except OSError:
                pass
