"""Tests for health, cache control, and navigation infrastructure endpoints."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_returns_healthy_status(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_includes_version(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "version" in data

    def test_includes_event_count(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "events" in data
        assert isinstance(data["events"], int)
        assert data["events"] >= 0


class TestCacheControl:
    def test_page_has_cache_header(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.headers["Cache-Control"] == "public, max-age=20"

    def test_api_has_cache_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/events")
        assert response.headers["Cache-Control"] == "public, max-age=20"

    def test_health_has_no_cache_header(self, client: TestClient) -> None:
        response = client.get("/health")
        assert "Cache-Control" not in response.headers


class TestNavMyScheduleLink:
    def test_nav_has_my_schedule_link(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "/my-schedule" in resp.text
        assert "schedule-badge" in resp.text
