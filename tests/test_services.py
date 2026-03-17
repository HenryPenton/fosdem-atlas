"""Tests for application services."""

from src.adapters.persistence.duckdb_repository import DuckDBEventRepository
from src.application.services import (
    AnalyticsService,
    ScheduleService,
    ScrapeService,
    SpeakerService,
)
from src.domain.models import Event
from tests.conftest import SAMPLE_EVENTS


class FakeScheduleFetcher:
    def __init__(self, events: list[Event]) -> None:
        self._events = events

    def fetch_and_parse(self, _url: str) -> list[Event]:
        return self._events


class TestScrapeService:
    def test_run_stores_events(self, repository: DuckDBEventRepository) -> None:
        fetcher = FakeScheduleFetcher(SAMPLE_EVENTS)
        service = ScrapeService(fetcher, repository)

        count = service.run("https://example.com/schedule.xml")

        assert count == 3
        assert repository.get_event_count() == 3

    def test_run_returns_event_count(self, repository: DuckDBEventRepository) -> None:
        fetcher = FakeScheduleFetcher(SAMPLE_EVENTS[:1])
        service = ScrapeService(fetcher, repository)

        count = service.run("https://example.com/schedule.xml")

        assert count == 1

    def test_run_with_no_events(self, repository: DuckDBEventRepository) -> None:
        fetcher = FakeScheduleFetcher([])
        service = ScrapeService(fetcher, repository)

        count = service.run("https://example.com/schedule.xml")

        assert count == 0
        assert repository.get_event_count() == 0


class TestScheduleService:
    def test_get_overview(self, schedule_service: ScheduleService) -> None:
        overview = schedule_service.get_overview()
        assert overview["event_count"] == 3
        assert len(overview["days"]) == 2
        assert len(overview["tracks"]) == 3
        assert len(overview["rooms"]) == 3

    def test_get_grid_data(self, schedule_service: ScheduleService) -> None:
        data = schedule_service.get_grid_data("2026-02-07")
        assert data["selected_day"] == "2026-02-07"
        assert "Room A" in data["rooms"]
        assert "Room B" in data["rooms"]
        assert len(data["time_slots"]) > 0
        assert len(data["grid"]) > 0
        assert "grid_rowspans" in data
        assert "grid_covered" in data

    def test_get_grid_data_rowspan_reflects_duration(
        self, schedule_service: ScheduleService
    ) -> None:
        # "Intro to Rust" in Room A at 10:00 with duration=30 → rowspan 1
        data = schedule_service.get_grid_data("2026-02-07")
        rowspans = data["grid_rowspans"]
        assert rowspans["10:00"]["Room A"] == 1

    def test_get_grid_data_empty_days(self, repository: DuckDBEventRepository) -> None:
        service = ScheduleService(repository)
        data = service.get_grid_data("")
        assert data["days"] == []
        assert data["grid"] == {}
        assert data["grid_rowspans"] == {}
        assert data["grid_covered"] == set()
        assert data["room_tracks"] == {}
        assert data["room_track_changes"] == {}

    def test_get_grid_data_room_tracks_ordered(self, schedule_service: ScheduleService) -> None:
        data = schedule_service.get_grid_data("2026-02-07")
        # Room A has a single event on this day with track "Rust"
        assert data["room_tracks"]["Room A"] == ["Rust"]
        # Room B has a single event with track "Python"
        assert data["room_tracks"]["Room B"] == ["Python"]
        # No changes expected for single-track rooms
        assert data["room_track_changes"]["Room A"] == {}
        assert data["room_track_changes"]["Room B"] == {}

    def test_get_day_detail(self, schedule_service: ScheduleService) -> None:
        data = schedule_service.get_day_detail("2026-02-07")
        assert data["day"] == "2026-02-07"
        assert "Rust" in data["tracks"]
        assert "Python" in data["tracks"]

    def test_get_all_tracks_with_counts(self, schedule_service: ScheduleService) -> None:
        data = schedule_service.get_all_tracks_with_counts()
        assert len(data["tracks"]) == 3
        assert data["track_events"]["Rust"] == 1

    def test_get_event_detail(self, schedule_service: ScheduleService) -> None:
        result = schedule_service.get_event_detail("1")
        assert result is not None
        assert result["title"] == "Intro to Rust"
        assert "speakers" in result

    def test_get_event_detail_not_found(self, schedule_service: ScheduleService) -> None:
        result = schedule_service.get_event_detail("nonexistent")
        assert result is None

    def test_search_events(self, schedule_service: ScheduleService) -> None:
        results = schedule_service.search_events(q="Rust")
        assert len(results) == 1
        assert results[0]["title"] == "Intro to Rust"

    def test_search_events_empty(self, schedule_service: ScheduleService) -> None:
        results = schedule_service.search_events()
        assert results == []

    def test_get_events_by_ids(self, schedule_service: ScheduleService) -> None:
        results = schedule_service.get_events_by_ids(["1", "3"])
        assert len(results) == 2

    def test_build_ical(self, schedule_service: ScheduleService) -> None:
        cal = schedule_service.build_ical(["1", "3"])
        assert "BEGIN:VCALENDAR" in cal
        assert "BEGIN:VEVENT" in cal
        assert "Intro to Rust" in cal
        assert "DuckDB Internals" in cal


class TestAnalyticsService:
    def test_get_analytics(self, analytics_service: AnalyticsService) -> None:
        data = analytics_service.get_analytics()
        assert data["stats"]["total_events"] == 3
        assert "events_per_room" in data
        assert "speaker_stats" in data
        assert "topic_stats" in data
        assert "heatmap_days" in data
        assert "heatmap_hours" in data
        assert "heatmap_grid" in data
        assert "max_heatmap_count" in data


class TestSpeakerService:
    def test_get_all_speakers(self, speaker_service: SpeakerService) -> None:
        speakers = speaker_service.get_all_speakers()
        assert len(speakers) == 1
        assert speakers[0]["name"] == "Mark"

    def test_get_speaker_detail(self, speaker_service: SpeakerService) -> None:
        result = speaker_service.get_speaker_detail("s1")
        assert result is not None
        assert result["name"] == "Mark"
        assert len(result["events"]) == 1

    def test_get_speaker_detail_not_found(self, speaker_service: SpeakerService) -> None:
        result = speaker_service.get_speaker_detail("nonexistent")
        assert result is None
