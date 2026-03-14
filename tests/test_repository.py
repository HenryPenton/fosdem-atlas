"""Tests for DuckDBEventRepository."""

from datetime import datetime

from src.adapters.persistence.duckdb_repository import DuckDBEventRepository
from src.domain.models import Event, Speaker
from tests.conftest import SAMPLE_EVENTS


class TestInsertEvents:
    def test_insert_and_count(self, repository: DuckDBEventRepository) -> None:
        count = repository.insert_events(SAMPLE_EVENTS)
        assert count == 3
        assert repository.get_event_count() == 3

    def test_insert_replaces_previous_data(self, seeded_repository: DuckDBEventRepository) -> None:
        new_events = [
            Event(
                id="99",
                title="Only Event",
                start_time=datetime(2026, 2, 7, 10, 0),
                duration_minutes=45,
                room="Room Z",
                track="Solo",
                day="2026-02-07",
            )
        ]
        seeded_repository.insert_events(new_events)
        assert seeded_repository.get_event_count() == 1

    def test_insert_stores_speakers(self, repository: DuckDBEventRepository) -> None:
        events = [
            Event(
                id="10",
                title="Talk",
                start_time=datetime(2026, 2, 7, 10, 0),
                duration_minutes=30,
                room="Room A",
                track="Test",
                day="2026-02-07",
                speakers=[Speaker(id="sp1", name="Alice"), Speaker(id="sp2", name="Bob")],
            )
        ]
        repository.insert_events(events)
        speakers = repository.get_speakers_for_event("10")
        assert len(speakers) == 2
        names = {s["name"] for s in speakers}
        assert names == {"Alice", "Bob"}


class TestGetAllEvents:
    def test_returns_all_events(self, seeded_repository: DuckDBEventRepository) -> None:
        events = seeded_repository.get_all_events()
        assert len(events) == 3

    def test_ordered_by_start_time(self, seeded_repository: DuckDBEventRepository) -> None:
        events = seeded_repository.get_all_events()
        times = [e["start_time"] for e in events]
        assert times == sorted(times)

    def test_empty_when_no_events(self, repository: DuckDBEventRepository) -> None:
        assert repository.get_all_events() == []


class TestGetEventsByDay:
    def test_filters_by_day(self, seeded_repository: DuckDBEventRepository) -> None:
        day1 = seeded_repository.get_events_by_day("2026-02-07")
        day2 = seeded_repository.get_events_by_day("2026-02-08")
        assert len(day1) == 2
        assert len(day2) == 1

    def test_nonexistent_day_returns_empty(self, seeded_repository: DuckDBEventRepository) -> None:
        assert seeded_repository.get_events_by_day("2099-01-01") == []


class TestGetUniqueDays:
    def test_returns_sorted_unique_days(self, seeded_repository: DuckDBEventRepository) -> None:
        days = seeded_repository.get_unique_days()
        assert days == ["2026-02-07", "2026-02-08"]

    def test_empty_when_no_events(self, repository: DuckDBEventRepository) -> None:
        assert repository.get_unique_days() == []


class TestGetUniqueTracks:
    def test_returns_sorted_tracks(self, seeded_repository: DuckDBEventRepository) -> None:
        tracks = seeded_repository.get_unique_tracks()
        assert tracks == ["Databases", "Python", "Rust"]

    def test_empty_when_no_events(self, repository: DuckDBEventRepository) -> None:
        assert repository.get_unique_tracks() == []


class TestGetUniqueRooms:
    def test_returns_sorted_rooms(self, seeded_repository: DuckDBEventRepository) -> None:
        rooms = seeded_repository.get_unique_rooms()
        assert rooms == ["Room A", "Room B", "Room C"]


class TestGetTracksByDay:
    def test_filters_tracks_by_day(self, seeded_repository: DuckDBEventRepository) -> None:
        tracks = seeded_repository.get_tracks_by_day("2026-02-07")
        assert set(tracks) == {"Rust", "Python"}

    def test_nonexistent_day_returns_empty(self, seeded_repository: DuckDBEventRepository) -> None:
        assert seeded_repository.get_tracks_by_day("2099-01-01") == []


class TestGetEventsByDayAndTrack:
    def test_filters_correctly(self, seeded_repository: DuckDBEventRepository) -> None:
        events = seeded_repository.get_events_by_day_and_track("2026-02-07", "Rust")
        assert len(events) == 1
        assert events[0]["title"] == "Intro to Rust"

    def test_no_match_returns_empty(self, seeded_repository: DuckDBEventRepository) -> None:
        assert seeded_repository.get_events_by_day_and_track("2026-02-07", "Go") == []


class TestGetSpeakersForEvent:
    def test_returns_speakers(self, seeded_repository: DuckDBEventRepository) -> None:
        speakers = seeded_repository.get_speakers_for_event("3")
        assert len(speakers) == 1
        assert speakers[0]["name"] == "Mark"

    def test_no_speakers_returns_empty(self, seeded_repository: DuckDBEventRepository) -> None:
        speakers = seeded_repository.get_speakers_for_event("1")
        assert speakers == []

    def test_nonexistent_event_returns_empty(
        self, seeded_repository: DuckDBEventRepository
    ) -> None:
        assert seeded_repository.get_speakers_for_event("999") == []


class TestSearchEvents:
    def test_search_by_title(self, seeded_repository: DuckDBEventRepository) -> None:
        results = seeded_repository.search_events("Rust")
        assert len(results) == 1
        assert results[0]["title"] == "Intro to Rust"

    def test_search_by_abstract(self, seeded_repository: DuckDBEventRepository) -> None:
        results = seeded_repository.search_events("under the hood")
        assert len(results) == 1
        assert results[0]["title"] == "DuckDB Internals"

    def test_search_case_insensitive(self, seeded_repository: DuckDBEventRepository) -> None:
        results = seeded_repository.search_events("rust")
        assert len(results) == 1

    def test_search_no_match(self, seeded_repository: DuckDBEventRepository) -> None:
        assert seeded_repository.search_events("nonexistent") == []

    def test_search_partial_match(self, seeded_repository: DuckDBEventRepository) -> None:
        results = seeded_repository.search_events("Pack")
        assert len(results) == 1
        assert results[0]["title"] == "Python Packaging"


class TestFilterEvents:
    def test_filter_by_track(self, seeded_repository: DuckDBEventRepository) -> None:
        results = seeded_repository.filter_events(track="Rust")
        assert len(results) == 1
        assert results[0]["title"] == "Intro to Rust"

    def test_filter_by_room(self, seeded_repository: DuckDBEventRepository) -> None:
        results = seeded_repository.filter_events(room="Room B")
        assert len(results) == 1
        assert results[0]["title"] == "Python Packaging"

    def test_filter_by_day(self, seeded_repository: DuckDBEventRepository) -> None:
        results = seeded_repository.filter_events(day="2026-02-08")
        assert len(results) == 1
        assert results[0]["title"] == "DuckDB Internals"

    def test_filter_combines_with_query(self, seeded_repository: DuckDBEventRepository) -> None:
        results = seeded_repository.filter_events(q="Rust", day="2026-02-07")
        assert len(results) == 1
        assert results[0]["title"] == "Intro to Rust"

    def test_filter_no_params_returns_all(self, seeded_repository: DuckDBEventRepository) -> None:
        results = seeded_repository.filter_events()
        assert len(results) == 3

    def test_filter_no_match(self, seeded_repository: DuckDBEventRepository) -> None:
        results = seeded_repository.filter_events(track="NonExistent")
        assert results == []

    def test_filter_mismatched_track_and_day(
        self, seeded_repository: DuckDBEventRepository
    ) -> None:
        # Rust track is only on 2026-02-07, not 2026-02-08
        results = seeded_repository.filter_events(track="Rust", day="2026-02-08")
        assert results == []
