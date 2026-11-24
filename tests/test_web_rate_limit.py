"""Tests for global rate limiting."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from slowapi import Limiter

from src.adapters.web import app as app_module
from src.application.services import AnalyticsService, ScheduleService, SpeakerService
from src.config import Settings


def _make_rate_limited_client(
    schedule_service: ScheduleService,
    analytics_service: AnalyticsService,
    speaker_service: SpeakerService,
    settings: Settings,
    limit: str = "1/minute",
) -> TestClient:
    """Create a test client with a tight rate limit for testing."""
    tight_limiter = Limiter(
        key_func=lambda *_args, **_kwargs: "global",
        default_limits=[limit],
        headers_enabled=True,
    )
    with patch.object(app_module, "limiter", tight_limiter):
        app = app_module.create_app(
            schedule_service=schedule_service,
            analytics_service=analytics_service,
            speaker_service=speaker_service,
            settings=settings,
        )
    return TestClient(app)


class TestRateLimiting:
    def test_normal_request_succeeds(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_returns_429_when_limit_exceeded(
        self,
        schedule_service: ScheduleService,
        analytics_service: AnalyticsService,
        speaker_service: SpeakerService,
        settings: Settings,
    ) -> None:
        c = _make_rate_limited_client(
            schedule_service, analytics_service, speaker_service, settings
        )
        c.get("/")
        response = c.get("/")
        assert response.status_code == 429

    def test_429_response_contains_retry_after(
        self,
        schedule_service: ScheduleService,
        analytics_service: AnalyticsService,
        speaker_service: SpeakerService,
        settings: Settings,
    ) -> None:
        c = _make_rate_limited_client(
            schedule_service, analytics_service, speaker_service, settings
        )
        c.get("/")
        response = c.get("/")
        assert "Retry-After" in response.headers

    def test_429_response_body_has_error(
        self,
        schedule_service: ScheduleService,
        analytics_service: AnalyticsService,
        speaker_service: SpeakerService,
        settings: Settings,
    ) -> None:
        c = _make_rate_limited_client(
            schedule_service, analytics_service, speaker_service, settings
        )
        c.get("/")
        response = c.get("/")
        assert "Rate limit exceeded" in response.json()["error"]

    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/speakers",
            "/analytics",
            "/events",
            "/export/events.csv",
            "/health",
            "/api/v1/days",
            "/api/v1/speakers",
            "/api/v1/overview",
        ],
    )
    def test_every_included_router_is_rate_limited(
        self,
        path: str,
        schedule_service: ScheduleService,
        analytics_service: AnalyticsService,
        speaker_service: SpeakerService,
        settings: Settings,
    ) -> None:
        c = _make_rate_limited_client(
            schedule_service, analytics_service, speaker_service, settings
        )
        c.get(path)
        assert c.get(path).status_code == 429

    def test_static_files_are_not_rate_limited(
        self,
        schedule_service: ScheduleService,
        analytics_service: AnalyticsService,
        speaker_service: SpeakerService,
        settings: Settings,
    ) -> None:
        c = _make_rate_limited_client(
            schedule_service, analytics_service, speaker_service, settings
        )
        statuses = [c.get("/static/css/style.css").status_code for _ in range(3)]
        assert statuses == [200, 200, 200]
