import docker
import tempfile
import os
from typing import Dict, Any, Optional
from ..config import settings
from ..models.script import Script
from ..core.retry import with_retry


class SandboxService:
    def __init__(self):
        self.docker_client = docker.from_env()

    async def execute_script(
        self,
        script: Script,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        # Determine which file to execute
        exec_file_path = script.file_path

        # For file-based scripts, use the external file if it exists and is different
        if script.is_file_based and script.external_file_path:
            # Clean the path - remove surrounding quotes if present
            clean_path = script.external_file_path.strip().strip('"').strip("'")
            if os.path.exists(clean_path):
                exec_file_path = clean_path
            else:
                raise ValueError(f"External script file not found: {clean_path}")

        if not exec_file_path or not os.path.exists(exec_file_path):
            raise ValueError("Script file not found")

        container_name = f"automa_script_{script.id}"

        try:
            container = self.docker_client.containers.run(
                image=settings.sandbox_image,
                command="python /app/script.py",
                volumes={
                    exec_file_path: {
                        'bind': '/app/script.py',
                        'mode': 'ro'
                    }
                },
                mem_limit=settings.sandbox_memory_limit,
                cpuset_cpus="0",
                network_mode="none",
                remove=True,
                detach=True,
                name=container_name,
                user="sandbox:sandbox"
            )

            # Wait for completion with timeout
            result = container.wait(timeout=settings.sandbox_timeout)

            # Get logs
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')

            return {
                "status": "success" if result["StatusCode"] == 0 else "failed",
                "exit_code": result["StatusCode"],
                "output": logs,
                "error": None if result["StatusCode"] == 0 else logs
            }

        except docker.errors.ContainerError as e:
            return {
                "status": "failed",
                "exit_code": e.exit_status,
                "output": "",
                "error": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "exit_code": -1,
                "output": "",
                "error": str(e)
            }

    async def check_sandbox_health(self) -> bool:
        try:
            self.docker_client.ping()
            # Test if sandbox image exists
            try:
                self.docker_client.images.get(settings.sandbox_image)
                return True
            except docker.errors.ImageNotFound:
                return False
        except Exception:
            return False

    async def build_sandbox_image(self) -> bool:
        dockerfile_content = """
FROM python:3.13-slim

RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

RUN apt-get update && apt-get install -y \\
    --no-install-recommends \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

USER sandbox:sandbox

CMD ["python", "/app/script.py"]
"""

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dockerfile', delete=False) as f:
                f.write(dockerfile_content)
                dockerfile_path = f.name

            self.docker_client.images.build(
                path=os.path.dirname(dockerfile_path),
                dockerfile=os.path.basename(dockerfile_path),
                tag=settings.sandbox_image,
                rm=True
            )

            os.unlink(dockerfile_path)
            return True
        except Exception as e:
            print(f"Failed to build sandbox image: {e}")
            return False

    @with_retry(max_retries=3, delay=1.0, exceptions=(docker.errors.APIError, docker.errors.DockerException))
    async def start_agent_container(
        self,
        script: Script,
        agent_id: int,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a long-running agent container in detached mode with retry logic"""
        # Determine which file to execute
        exec_file_path = script.file_path

        # For file-based scripts, use the external file if it exists
        if script.is_file_based and script.external_file_path:
            clean_path = script.external_file_path.strip().strip('"').strip("'")
            if os.path.exists(clean_path):
                exec_file_path = clean_path
            else:
                raise ValueError(f"External script file not found: {clean_path}")

        if not exec_file_path or not os.path.exists(exec_file_path):
            raise ValueError("Script file not found")

        container_name = f"automa_agent_{agent_id}"

        # Remove existing container with same name if exists
        try:
            existing = self.docker_client.containers.get(container_name)
            existing.remove(force=True)
        except docker.errors.NotFound:
            pass

        # Prepare environment variables from config
        env_vars = {}
        if config:
            env_vars.update(config)

        try:
            container = self.docker_client.containers.run(
                image=settings.sandbox_image,
                command="python /app/script.py",
                volumes={
                    exec_file_path: {
                        'bind': '/app/script.py',
                        'mode': 'ro'
                    }
                },
                environment=env_vars,
                mem_limit=settings.sandbox_memory_limit,
                cpuset_cpus="0",
                network_mode="bridge",  # Allow network for agents
                detach=True,
                name=container_name,
                user="sandbox:sandbox",
                restart_policy={"Name": "unless-stopped"}
            )

            return container.id

        except docker.errors.ContainerError as e:
            raise RuntimeError(f"Failed to start agent container: {e}")
        except Exception as e:
            raise RuntimeError(f"Error starting agent container: {e}")

    @with_retry(max_retries=3, delay=1.0, exceptions=(docker.errors.APIError,))
    async def stop_agent_container(self, container_id: str) -> None:
        """Stop and remove an agent container with retry logic"""
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)
            container.remove()
        except docker.errors.NotFound:
            # Container already removed
            pass
        except Exception as e:
            raise RuntimeError(f"Error stopping agent container: {e}")

    async def get_agent_container_status(self, container_id: str) -> Dict[str, Any]:
        """Get status and logs of an agent container"""
        try:
            container = self.docker_client.containers.get(container_id)
            status = container.status
            logs = container.logs(tail=100).decode('utf-8')

            return {
                "status": status,
                "logs": logs,
                "running": status == "running"
            }
        except docker.errors.NotFound:
            return {
                "status": "not_found",
                "logs": "",
                "running": False
            }
        except Exception as e:
            return {
                "status": "error",
                "logs": str(e),
                "running": False
            }