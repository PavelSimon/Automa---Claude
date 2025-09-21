from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.main import app

client = TestClient(app)


def test_agents_endpoints_exist():
    """Test that agent endpoints are properly registered"""
    # Test endpoints without auth (should return 401 or 307)
    response = client.get("/api/v1/agents/")
    assert response.status_code in [401, 307, 422]  # Unauthorized or redirect

    response = client.post("/api/v1/agents/", json={
        "name": "test",
        "script_id": 1
    })
    assert response.status_code in [401, 307, 422]


def test_jobs_endpoints_exist():
    """Test that job endpoints are properly registered"""
    response = client.get("/api/v1/jobs/")
    assert response.status_code in [401, 307, 422]


def test_monitoring_endpoints_exist():
    """Test that monitoring endpoints are properly registered"""
    response = client.get("/api/v1/monitoring/dashboard")
    assert response.status_code in [401, 307, 422]

    response = client.get("/api/v1/monitoring/system")
    assert response.status_code in [401, 307, 422]


def test_app_health():
    """Test basic app health"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "environment" in data


def test_detailed_health():
    """Test detailed health check"""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "components" in data
    assert "database" in data["components"]
    assert "system" in data["components"]


def test_liveness_probe():
    """Test Kubernetes liveness probe"""
    response = client.get("/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_probe():
    """Test Kubernetes readiness probe"""
    response = client.get("/readiness")
    assert response.status_code in [200, 503]  # May fail if directories don't exist


def test_metrics_endpoint():
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "automa_cpu_usage_percent" in response.text
    assert "automa_memory_usage_bytes" in response.text


def test_app_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "0.1.0"