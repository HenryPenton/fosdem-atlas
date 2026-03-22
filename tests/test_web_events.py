"""Tests for event detail pages, bookmark UI, and the events API (v1)."""

import pytest
from fastapi.testclient import TestClient

from src.adapters.persistence.duckdb_ingestion_repository import DuckDBIngestionRepository
from src.adapters.web.app import create_app
from src.application.services import AnalyticsService, ScheduleService, SpeakerService
from src.config import Settings
from src.domain.models import Link


class TestEventDetailPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert response.status_code == 200

    def test_shows_event_title(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert "Intro to Rust" in response.text

    def test_shows_abstract(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert "Learn Rust basics" in response.text

    def test_shows_speaker(self, client: TestClient) -> None:
        response = client.get("/event/3")
        assert "Mark" in response.text

    def test_shows_track_and_room(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert "Rust" in response.text
        assert "Room A" in response.text

    def test_shows_back_link(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert "/day/2026-02-07/track/Rust" in response.text

    def test_returns_404_for_unknown_event(self, client: TestClient) -> None:
        response = client.get("/event/nonexistent")
        assert response.status_code == 404

    def test_404_default_back_link(self, client: TestClient) -> None:
        response = client.get("/event/nonexistent")
        assert "Back to schedule" in response.text

    def test_404_referer_back_link(self, client: TestClient) -> None:
        response = client.get(
            "/event/nonexistent", headers={"Referer": "http://testserver/speakers"}
        )
        assert "Back to speakers" in response.text


class TestEventVideoLink:
    @pytest.fixture
    def client_with_video(
        self,
        seeded_ingestion_repository: DuckDBIngestionRepository,
        schedule_service: ScheduleService,
        analytics_service: AnalyticsService,
        speaker_service: SpeakerService,
        settings: Settings,
    ) -> TestClient:
        from tests.conftest import _make_event

        event = _make_event(
            id="vid1",
            title="Talk With Video",
            links=[
                Link(href="https://fosdem.org/2026/schedule/event/vid1/", title="Event page"),
                Link(href="https://video.fosdem.org/2026/h1234/vid1.webm", title="Video recording"),
            ],
        )
        seeded_ingestion_repository.insert_events([event])
        app = create_app(
            schedule_service=schedule_service,
            analytics_service=analytics_service,
            speaker_service=speaker_service,
            settings=settings,
        )
        return TestClient(app)

    def test_shows_video_link(self, client_with_video: TestClient) -> None:
        response = client_with_video.get("/event/vid1")
        assert "video.fosdem.org" in response.text
        assert "Video recording" in response.text

    def test_no_video_link_when_absent(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert "video.fosdem.org" not in response.text


class TestEventLinks:
    @pytest.fixture
    def client_with_links(
        self,
        seeded_ingestion_repository: DuckDBIngestionRepository,
        schedule_service: ScheduleService,
        analytics_service: AnalyticsService,
        speaker_service: SpeakerService,
        settings: Settings,
    ) -> TestClient:
        from tests.conftest import _make_event

        event = _make_event(
            id="lnk1",
            title="Talk With Links",
            links=[
                Link(href="https://fosdem.org/2026/schedule/event/lnk1/", title="FOSDEM page"),
                Link(href="https://example.com/slides.pdf", title="Slides"),
            ],
        )
        seeded_ingestion_repository.insert_events([event])
        app = create_app(
            schedule_service=schedule_service,
            analytics_service=analytics_service,
            speaker_service=speaker_service,
            settings=settings,
        )
        return TestClient(app)

    def test_shows_all_links(self, client_with_links: TestClient) -> None:
        response = client_with_links.get("/event/lnk1")
        assert "FOSDEM page" in response.text
        assert "Slides" in response.text
        assert "example.com/slides.pdf" in response.text

    def test_no_links_shows_back_link_only(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert response.status_code == 200


class TestApiV1EventDetailLinks:
    @pytest.fixture
    def client_with_links(
        self,
        seeded_ingestion_repository: DuckDBIngestionRepository,
        schedule_service: ScheduleService,
        analytics_service: AnalyticsService,
        speaker_service: SpeakerService,
        settings: Settings,
    ) -> TestClient:
        from tests.conftest import _make_event

        event = _make_event(
            id="api_lnk1",
            title="API Link Talk",
            links=[
                Link(href="https://fosdem.org/2026/schedule/event/api_lnk1/", title="FOSDEM page"),
                Link(href="https://example.com/code", title="Source code"),
            ],
        )
        seeded_ingestion_repository.insert_events([event])
        app = create_app(
            schedule_service=schedule_service,
            analytics_service=analytics_service,
            speaker_service=speaker_service,
            settings=settings,
        )
        return TestClient(app)

    def test_event_detail_includes_links(self, client_with_links: TestClient) -> None:
        data = client_with_links.get("/api/v1/events/api_lnk1").json()
        assert "links" in data
        assert len(data["links"]) == 2
        hrefs = {lk["href"] for lk in data["links"]}
        assert "https://example.com/code" in hrefs


class TestEventDetailBookmark:
    def test_event_page_has_bookmark_button(self, client: TestClient) -> None:
        resp = client.get("/event/1")
        assert resp.status_code == 200
        assert 'data-bookmark-id="1"' in resp.text


class TestApiV1Events:
    def test_returns_json(self, client: TestClient) -> None:
        response = client.get("/api/v1/events")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_event_has_expected_fields(self, client: TestClient) -> None:
        data = client.get("/api/v1/events").json()
        event = data[0]
        for field in ("id", "title", "start_time", "duration_minutes", "room", "track", "day"):
            assert field in event

    def test_sort_by_track(self, client: TestClient) -> None:
        data = client.get("/api/v1/events?sort=track").json()
        assert len(data) == 3


class TestApiV1EventsSearch:
    def test_search_returns_results(self, client: TestClient) -> None:
        data = client.get("/api/v1/events/search?q=Rust").json()
        assert len(data) == 1
        assert data[0]["title"] == "Intro to Rust"

    def test_filter_by_track(self, client: TestClient) -> None:
        data = client.get("/api/v1/events/search?track=Python").json()
        assert len(data) == 1
        assert data[0]["title"] == "Python Packaging"

    def test_empty_query_returns_empty(self, client: TestClient) -> None:
        data = client.get("/api/v1/events/search").json()
        assert data == []


class TestApiV1EventDetail:
    def test_returns_event(self, client: TestClient) -> None:
        data = client.get("/api/v1/events/1").json()
        assert data["title"] == "Intro to Rust"

    def test_includes_speakers(self, client: TestClient) -> None:
        data = client.get("/api/v1/events/3").json()
        assert "speakers" in data
        assert data["speakers"][0]["name"] == "Mark"

    def test_404_for_unknown(self, client: TestClient) -> None:
        response = client.get("/api/v1/events/nonexistent")
        assert response.status_code == 404


class TestApiV1Days:
    def test_returns_days(self, client: TestClient) -> None:
        data = client.get("/api/v1/days").json()
        assert data == ["2026-02-07", "2026-02-08"]

    def test_day_detail_returns_tracks(self, client: TestClient) -> None:
        data = client.get("/api/v1/days/2026-02-07").json()
        assert data["day"] == "2026-02-07"
        assert set(data["tracks"]) == {"Python", "Rust"}
        assert "track_event_counts" in data
