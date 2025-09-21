import psutil
import docker
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession


class MonitoringService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_system_status(self) -> Dict[str, Any]:
        """Get system resource usage statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory usage
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_gb = disk.total / (1024**3)

            # Load average (if available)
            load_avg = None
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                # getloadavg() not available on Windows
                pass

            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "cores": cpu_count,
                    "load_average": load_avg
                },
                "memory": {
                    "total_gb": round(memory_gb, 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk_gb, 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 1)
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to get system status: {str(e)}",
                "cpu": {"usage_percent": 0, "cores": 0},
                "memory": {"total_gb": 0, "available_gb": 0, "used_gb": 0, "usage_percent": 0},
                "disk": {"total_gb": 0, "free_gb": 0, "used_gb": 0, "usage_percent": 0}
            }

    async def get_docker_status(self) -> Dict[str, Any]:
        """Get Docker system status and container information"""
        try:
            client = docker.from_env()

            # Docker system info
            info = client.info()

            # Get containers
            containers = client.containers.list(all=True)
            container_data = []

            for container in containers:
                try:
                    stats = container.stats(stream=False) if container.status == 'running' else None
                    container_data.append({
                        "id": container.id[:12],
                        "name": container.name,
                        "image": container.image.tags[0] if container.image.tags else "unknown",
                        "status": container.status,
                        "created": container.attrs.get("Created", ""),
                        "ports": container.ports,
                        "labels": container.labels
                    })
                except Exception as e:
                    container_data.append({
                        "id": container.id[:12],
                        "name": container.name,
                        "status": container.status,
                        "error": str(e)
                    })

            # Get images
            images = client.images.list()
            image_data = []
            for image in images:
                image_data.append({
                    "id": image.id[:12],
                    "tags": image.tags,
                    "size_mb": round(image.attrs.get("Size", 0) / (1024**2), 2),
                    "created": image.attrs.get("Created", "")
                })

            return {
                "status": "connected",
                "server_version": info.get("ServerVersion", "unknown"),
                "containers": {
                    "total": len(containers),
                    "running": len([c for c in containers if c.status == 'running']),
                    "stopped": len([c for c in containers if c.status == 'exited']),
                    "list": container_data
                },
                "images": {
                    "total": len(images),
                    "list": image_data
                },
                "system": {
                    "containers_running": info.get("ContainersRunning", 0),
                    "containers_paused": info.get("ContainersPaused", 0),
                    "containers_stopped": info.get("ContainersStopped", 0),
                    "images_count": info.get("Images", 0),
                    "memory_limit": info.get("MemTotal", 0)
                }
            }

        except docker.errors.DockerException as e:
            return {
                "status": "error",
                "error": f"Docker connection failed: {str(e)}",
                "containers": {"total": 0, "running": 0, "stopped": 0, "list": []},
                "images": {"total": 0, "list": []},
                "system": {}
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
                "containers": {"total": 0, "running": 0, "stopped": 0, "list": []},
                "images": {"total": 0, "list": []},
                "system": {}
            }

    async def get_automa_containers(self) -> List[Dict[str, Any]]:
        """Get containers specifically related to Automa (sandbox containers)"""
        try:
            client = docker.from_env()
            containers = client.containers.list(
                all=True,
                filters={"label": "automa.sandbox=true"}
            )

            container_data = []
            for container in containers:
                container_data.append({
                    "id": container.id[:12],
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "status": container.status,
                    "created": container.attrs.get("Created", ""),
                    "labels": container.labels,
                    "agent_id": container.labels.get("automa.agent_id"),
                    "script_id": container.labels.get("automa.script_id")
                })

            return container_data

        except Exception as e:
            return []