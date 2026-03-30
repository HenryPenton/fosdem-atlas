"""Tests for health, cache control, and navigation infrastructure endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.adapters.web.app import create_app
from src.application.services import AnalyticsService, ScheduleService, SpeakerService
from src.config import Settings


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


class TestHealthEndpointUnhealthy:
    @pytest.fixture
    def broken_client(
        self,
        analytics_service: AnalyticsService,
        speaker_service: SpeakerService,
        settings: Settings,
    ) -> TestClient:
        broken_service = MagicMock(spec=ScheduleService)
        broken_service.get_event_count.side_effect = RuntimeError("db failure")
        app = create_app(
            schedule_service=broken_service,
            analytics_service=analytics_service,
            speaker_service=speaker_service,
            settings=settings,
        )
        return TestClient(app, raise_server_exceptions=False)

    def test_returns_503(self, broken_client: TestClient) -> None:
        response = broken_client.get("/health")
        assert response.status_code == 503

    def test_returns_unhealthy_status(self, broken_client: TestClient) -> None:
        data = broken_client.get("/health").json()
        assert data["status"] == "unhealthy"

    def test_logs_exception(self, broken_client: TestClient) -> None:
        with patch("src.adapters.web.routers.health.logger") as mock_logger:
            broken_client.get("/health")
            mock_logger.exception.assert_called_once()


class TestNavMyScheduleLink:
    def test_nav_has_my_schedule_link(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "/my-schedule" in resp.text
        assert "schedule-badge" in resp.text
