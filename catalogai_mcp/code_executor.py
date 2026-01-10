"""Docker sandbox for code execution."""
import os
import logging
import tempfile
import docker

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Executes user code in isolated Docker container."""

    def __init__(self, image_name="catalogai-sandbox:latest", timeout: int = 30):
        self.docker_client = docker.from_env()
        self.image_name = image_name
        self.timeout = timeout
        self.skills_dir = os.path.join(os.path.dirname(__file__), 'skills')

    def execute(self, code: str, context: dict) -> dict:
        """Execute Python code in sandbox with SDK available."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            code_file = f.name

        api_url = context["api_url"]
        if "localhost" in api_url:
            api_url = api_url.replace("localhost", "host.docker.internal")
        elif "127.0.0.1" in api_url:
            api_url = api_url.replace("127.0.0.1", "host.docker.internal")

        container = None
        try:
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
                mem_limit="512m",
                cpu_period=100000,
                cpu_quota=50000,
                network_mode="bridge",
                detach=True,
                remove=False
            )

            try:
                result = container.wait(timeout=self.timeout)
                logs = container.logs().decode('utf-8')
                return {
                    "status": "success" if result["StatusCode"] == 0 else "error",
                    "output": logs,
                    "exit_code": result["StatusCode"]
                }
            except Exception:
                try:
                    container.kill()
                except Exception:
                    pass
                return {
                    "status": "error",
                    "output": f"Execution timed out after {self.timeout}s",
                    "exit_code": -1
                }

        except docker.errors.ContainerError as e:
            return {"status": "error", "output": str(e), "exit_code": -1}
        except docker.errors.ImageNotFound:
            return {"status": "error", "output": f"Image '{self.image_name}' not found", "exit_code": -1}
        except docker.errors.APIError as e:
            return {"status": "error", "output": f"Docker error: {e}", "exit_code": -1}
        except Exception as e:
            return {"status": "error", "output": f"Execution error: {e}", "exit_code": -1}
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.warning(f"Container cleanup failed: {e}")
            try:
                os.unlink(code_file)
            except OSError:
                pass
