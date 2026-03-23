"""Tests for ScheduleService."""

from datetime import datetime

from src.adapters.persistence.duckdb_events_repository import DuckDBEventsRepository
from src.adapters.persistence.duckdb_ingestion_repository import DuckDBIngestionRepository
from src.application.services import ScheduleService
from tests.conftest import _make_event


class TestScheduleService:
    def test_get_overview(self, schedule_service: ScheduleService) -> None:
        overview = schedule_service.get_overview()
        assert overview.event_count == 3
        assert len(overview.days) == 2
        assert len(overview.tracks) == 3
        assert len(overview.rooms) == 3

    def test_get_grid_data(self, schedule_service: ScheduleService) -> None:
        data = schedule_service.get_grid_data("2026-02-07")
        assert data.selected_day == "2026-02-07"
        assert "Room A" in data.rooms
        assert "Room B" in data.rooms
        assert len(data.time_slots) > 0
        assert len(data.grid) > 0

    def test_get_grid_data_events_placed_in_hour(self, schedule_service: ScheduleService) -> None:
        # "Intro to Rust" in Room A at 10:00 → appears in "10:00" hour slot
        data = schedule_service.get_grid_data("2026-02-07")
        assert "Room A" in data.grid.get("10:00", {})
        events = data.grid["10:00"]["Room A"]
        assert any(ev.title == "Intro to Rust" for ev in events)

    def test_get_grid_data_empty_days(self, events_repository: DuckDBEventsRepository) -> None:
        service = ScheduleService(events_repository)
        data = service.get_grid_data("")
        assert data.days == []
        assert data.grid == {}
        assert data.room_tracks == {}
        assert data.room_track_changes == {}

    def test_get_grid_data_room_tracks_ordered(self, schedule_service: ScheduleService) -> None:
        data = schedule_service.get_grid_data("2026-02-07")
        # Room A has a single event on this day with track "Rust"
        assert data.room_tracks["Room A"] == ["Rust"]
        # Room B has a single event with track "Python"
        assert data.room_tracks["Room B"] == ["Python"]
        # No changes expected for single-track rooms
        assert data.room_track_changes["Room A"] == {}
        assert data.room_track_changes["Room B"] == {}

    def test_get_grid_data_track_changes(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        events_repository: DuckDBEventsRepository,
    ) -> None:
        ingestion_repository.insert_events(
            [
                _make_event(
                    id="t1",
                    title="First Talk",
                    track="Track A",
                    room="Room A",
                    day="2026-02-07",
                    start_time=datetime(2026, 2, 7, 10, 0),
                ),
                _make_event(
                    id="t2",
                    title="Second Talk",
                    track="Track B",
                    room="Room A",
                    day="2026-02-07",
                    start_time=datetime(2026, 2, 7, 11, 0),
                ),
            ]
        )
        service = ScheduleService(events_repository)
        data = service.get_grid_data("2026-02-07")
        assert data.room_tracks["Room A"] == ["Track A", "Track B"]
        assert data.room_track_changes["Room A"].get("11:00") == "Track B"

    def test_get_grid_data_unknown_day_falls_back(self, schedule_service: ScheduleService) -> None:
        data = schedule_service.get_grid_data("9999-01-01")
        assert data.selected_day in ["2026-02-07", "2026-02-08"]

    def test_get_grid_data_cached(self, schedule_service: ScheduleService) -> None:
        first = schedule_service.get_grid_data("2026-02-07")
        second = schedule_service.get_grid_data("2026-02-07")
        assert first is second

    def test_get_day_detail(self, schedule_service: ScheduleService) -> None:
        data = schedule_service.get_day_detail("2026-02-07")
        assert data.day == "2026-02-07"
        assert "Rust" in data.tracks
        assert "Python" in data.tracks

    def test_get_day_detail_cached(self, schedule_service: ScheduleService) -> None:
        first = schedule_service.get_day_detail("2026-02-07")
        second = schedule_service.get_day_detail("2026-02-07")
        assert first is second

    def test_get_all_tracks_with_counts(self, schedule_service: ScheduleService) -> None:
        data = schedule_service.get_all_tracks_with_counts()
        assert len(data.tracks) == 3
        assert data.track_events["Rust"] == 1

    def test_get_all_tracks_with_counts_cached(self, schedule_service: ScheduleService) -> None:
        first = schedule_service.get_all_tracks_with_counts()
        second = schedule_service.get_all_tracks_with_counts()
        assert first is second

    def test_get_event_detail(self, schedule_service: ScheduleService) -> None:
        result = schedule_service.get_event_detail("1")
        assert result is not None
        assert result.title == "Intro to Rust"
        assert hasattr(result, "speakers")

    def test_get_event_detail_not_found(self, schedule_service: ScheduleService) -> None:
        result = schedule_service.get_event_detail("nonexistent")
        assert result is None

    def test_get_event_detail_cached(self, schedule_service: ScheduleService) -> None:
        first = schedule_service.get_event_detail("1")
        second = schedule_service.get_event_detail("1")
        assert first is second

    def test_search_events(self, schedule_service: ScheduleService) -> None:
        results = schedule_service.search_events(q="Rust")
        assert len(results) == 1
        assert results[0].title == "Intro to Rust"

    def test_search_events_empty(self, schedule_service: ScheduleService) -> None:
        results = schedule_service.search_events()
        assert results == []

    def test_search_events_whitespace_only_returns_empty(
        self, schedule_service: ScheduleService
    ) -> None:
        assert schedule_service.search_events(q="   ") == []

    def test_get_event_count(self, schedule_service: ScheduleService) -> None:
        assert schedule_service.get_event_count() == 3

    def test_get_unique_days(self, schedule_service: ScheduleService) -> None:
        days = schedule_service.get_unique_days()
        assert len(days) == 2
        assert schedule_service.get_unique_days() == days  # cache hit

    def test_get_unique_tracks(self, schedule_service: ScheduleService) -> None:
        tracks = schedule_service.get_unique_tracks()
        assert len(tracks) == 3
        assert schedule_service.get_unique_tracks() == tracks  # cache hit

    def test_get_unique_rooms(self, schedule_service: ScheduleService) -> None:
        rooms = schedule_service.get_unique_rooms()
        assert len(rooms) == 3
        assert schedule_service.get_unique_rooms() == rooms  # cache hit

    def test_get_overview_cached(self, schedule_service: ScheduleService) -> None:
        first = schedule_service.get_overview()
        second = schedule_service.get_overview()
        assert first is second

    def test_get_all_events_default_sort(self, schedule_service: ScheduleService) -> None:
        events = schedule_service.get_all_events()
        assert len(events) == 3

    def test_get_all_events_invalid_sort_falls_back_to_time(
        self, schedule_service: ScheduleService
    ) -> None:
        events = schedule_service.get_all_events(sort="invalid")
        assert len(events) == 3

    def test_get_events_for_day_and_track(self, schedule_service: ScheduleService) -> None:
        events = schedule_service.get_events_for_day_and_track("2026-02-07", "Rust")
        assert len(events) == 1
        assert events[0].title == "Intro to Rust"

    def test_get_events_for_track(self, schedule_service: ScheduleService) -> None:
        events = schedule_service.get_events_for_track("Databases")
        assert len(events) == 1
        assert events[0].title == "DuckDB Internals"

    def test_get_events_by_ids(self, schedule_service: ScheduleService) -> None:
        results = schedule_service.get_events_by_ids(["1", "3"])
        assert len(results) == 2

    def test_build_ical(self, schedule_service: ScheduleService) -> None:
        cal = schedule_service.build_ical(["1", "3"])
        assert "BEGIN:VCALENDAR" in cal
        assert "BEGIN:VEVENT" in cal
        assert "Intro to Rust" in cal
        assert "DuckDB Internals" in cal

    def test_build_grid_for_ids(self, schedule_service: ScheduleService) -> None:
        grid = schedule_service.build_grid_for_ids(["1", "3"])
        assert set(grid.keys()) == {"2026-02-07", "2026-02-08"}
        assert grid["2026-02-07"].selected_day == "2026-02-07"
        assert "Room A" in grid["2026-02-07"].rooms
        assert grid["2026-02-08"].selected_day == "2026-02-08"

    def test_build_grid_for_ids_empty(self, schedule_service: ScheduleService) -> None:
        assert schedule_service.build_grid_for_ids([]) == {}

    def test_invalidate_cache(self, schedule_service: ScheduleService) -> None:
        # Populate all caches
        schedule_service.get_overview()
        schedule_service.get_grid_data("2026-02-07")
        schedule_service.get_day_detail("2026-02-07")
        schedule_service.get_all_tracks_with_counts()
        schedule_service.get_event_detail("1")
        schedule_service.get_unique_days()
        schedule_service.get_unique_tracks()
        schedule_service.get_unique_rooms()
        # Invalidate and verify re-fetch still works correctly
        schedule_service.invalidate_cache()
        assert schedule_service.get_event_count() == 3
        assert schedule_service.get_overview().event_count == 3
