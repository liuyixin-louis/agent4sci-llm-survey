"""
Tests for FastAPI main application
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Survey Generation API"
    assert data["version"] == "1.0.0"
    assert "docs" in data
    assert "health" in data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Survey Generation API"
    assert data["version"] == "1.0.0"


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_docs_available(client):
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200
    # Swagger UI returns HTML
    assert "swagger" in response.text.lower()


def test_openapi_schema(client):
    """Test OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Survey Generation API"
    assert schema["info"]["version"] == "1.0.0"


def test_error_handler(client):
    """Test global error handler for non-existent endpoint."""
    response = client.get("/nonexistent")
    assert response.status_code == 404


class TestApplicationStartup:
    """Test application startup and configuration."""
    
    def test_app_instance(self):
        """Test FastAPI app instance is created."""
        assert app is not None
        assert app.title == "Survey Generation API"
        assert app.version == "1.0.0"
    
    def test_lifespan_context(self):
        """Test lifespan context manager."""
        # This is tested implicitly when the client is created
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])