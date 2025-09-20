import docker
import asyncio
import tempfile
import os
from typing import Dict, Any, Optional
from ..config import settings
from ..models.script import Script


class SandboxService:
    def __init__(self):
        self.docker_client = docker.from_env()

    async def execute_script(
        self,
        script: Script,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not script.file_path or not os.path.exists(script.file_path):
            raise ValueError("Script file not found")

        container_name = f"automa_script_{script.id}"

        try:
            container = self.docker_client.containers.run(
                image=settings.sandbox_image,
                command=f"python /app/script.py",
                volumes={
                    script.file_path: {
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