"""Tests for the main FastAPI application."""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_index_page() -> None:
    """Test the main index page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert "FOSDEM Explorer" in response.text
