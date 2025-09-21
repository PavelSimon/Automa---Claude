import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.services.agent_service import AgentService
from app.services.job_service import JobService
from app.services.monitoring_service import MonitoringService


def test_agent_service_import():
    """Test that AgentService can be imported and instantiated"""
    assert AgentService is not None


def test_job_service_import():
    """Test that JobService can be imported and instantiated"""
    assert JobService is not None


def test_monitoring_service_import():
    """Test that MonitoringService can be imported and instantiated"""
    assert MonitoringService is not None


@pytest.mark.asyncio
async def test_monitoring_service_system_status():
    """Test that monitoring service can get system status"""
    service = MonitoringService(None)  # session not needed for system status
    status = await service.get_system_status()

    assert "cpu" in status
    assert "memory" in status
    assert "disk" in status

    # Check CPU data
    assert "usage_percent" in status["cpu"]
    assert "cores" in status["cpu"]

    # Check memory data
    assert "total_gb" in status["memory"]
    assert "usage_percent" in status["memory"]

    # Check disk data
    assert "total_gb" in status["disk"]
    assert "usage_percent" in status["disk"]