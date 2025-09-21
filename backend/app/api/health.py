from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database import get_async_session
from ..config import settings
import psutil
import time
from datetime import datetime, timezone

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment
    }

@router.get("/health/detailed")
async def detailed_health_check(session: AsyncSession = Depends(get_async_session)):
    """Detailed health check with database and system metrics"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
        "components": {}
    }

    # Database health check
    try:
        start_time = time.time()
        result = await session.execute(text("SELECT 1"))
        db_latency = (time.time() - start_time) * 1000  # Convert to milliseconds

        health_data["components"]["database"] = {
            "status": "healthy",
            "latency_ms": round(db_latency, 2),
            "url": settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url
        }
    except Exception as e:
        health_data["status"] = "unhealthy"
        health_data["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        health_data["components"]["system"] = {
            "status": "healthy",
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": round((disk.used / disk.total) * 100, 2)
            }
        }
    except Exception as e:
        health_data["components"]["system"] = {
            "status": "partial",
            "error": str(e)
        }

    # Overall status determination
    component_statuses = [comp.get("status") for comp in health_data["components"].values()]
    if "unhealthy" in component_statuses:
        health_data["status"] = "unhealthy"
    elif "partial" in component_statuses:
        health_data["status"] = "degraded"

    return health_data

@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus-style metrics endpoint"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        metrics = [
            f"# HELP automa_cpu_usage_percent CPU usage percentage",
            f"# TYPE automa_cpu_usage_percent gauge",
            f"automa_cpu_usage_percent {cpu_percent}",
            "",
            f"# HELP automa_memory_usage_bytes Memory usage in bytes",
            f"# TYPE automa_memory_usage_bytes gauge",
            f"automa_memory_usage_bytes {memory.used}",
            "",
            f"# HELP automa_memory_total_bytes Total memory in bytes",
            f"# TYPE automa_memory_total_bytes gauge",
            f"automa_memory_total_bytes {memory.total}",
            "",
            f"# HELP automa_disk_usage_bytes Disk usage in bytes",
            f"# TYPE automa_disk_usage_bytes gauge",
            f"automa_disk_usage_bytes {disk.used}",
            "",
            f"# HELP automa_disk_total_bytes Total disk space in bytes",
            f"# TYPE automa_disk_total_bytes gauge",
            f"automa_disk_total_bytes {disk.total}",
            ""
        ]

        return "\n".join(metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect metrics: {str(e)}")

@router.get("/readiness")
async def readiness_check(session: AsyncSession = Depends(get_async_session)):
    """Kubernetes-style readiness probe"""
    try:
        # Check database connectivity
        await session.execute(text("SELECT 1"))

        # Check if critical directories exist
        import os
        required_dirs = [settings.scripts_directory, settings.data_directory]
        for directory in required_dirs:
            if not os.path.exists(directory):
                raise HTTPException(
                    status_code=503,
                    detail=f"Required directory not found: {directory}"
                )

        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@router.get("/liveness")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}