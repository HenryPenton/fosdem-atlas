"""Smoke tests for the main app composition (reuses conftest fixtures).

Detailed endpoint tests live in test_web.py. These just verify the
create_app factory produces a working app.
"""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_index_page(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "FOSDEM Atlas" in response.text
