"""Tests for DuckDBEventsRepository — schedule browsing and search."""

from src.adapters.persistence.duckdb_events_repository import DuckDBEventsRepository
from src.adapters.persistence.duckdb_ingestion_repository import DuckDBIngestionRepository
from src.domain.models import Link


class TestGetAllEvents:
    def test_returns_all_events(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        events = seeded_events_repository.get_all_events()
        assert len(events) == 3

    def test_ordered_by_start_time(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        events = seeded_events_repository.get_all_events()
        times = [e.start_time for e in events]
        assert times == sorted(times)

    def test_empty_when_no_events(self, events_repository: DuckDBEventsRepository) -> None:
        assert events_repository.get_all_events() == []


class TestGetEventsByDay:
    def test_filters_by_day(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        day1 = seeded_events_repository.get_events_by_day("2026-02-07")
        day2 = seeded_events_repository.get_events_by_day("2026-02-08")
        assert len(day1) == 2
        assert len(day2) == 1

    def test_nonexistent_day_returns_empty(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        assert seeded_events_repository.get_events_by_day("2099-01-01") == []


class TestGetUniqueDays:
    def test_returns_sorted_unique_days(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        days = seeded_events_repository.get_unique_days()
        assert days == ["2026-02-07", "2026-02-08"]

    def test_empty_when_no_events(self, events_repository: DuckDBEventsRepository) -> None:
        assert events_repository.get_unique_days() == []


class TestGetUniqueTracks:
    def test_returns_sorted_tracks(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        tracks = seeded_events_repository.get_unique_tracks()
        assert tracks == ["Databases", "Python", "Rust"]

    def test_empty_when_no_events(self, events_repository: DuckDBEventsRepository) -> None:
        assert events_repository.get_unique_tracks() == []


class TestGetUniqueRooms:
    def test_returns_sorted_rooms(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        rooms = seeded_events_repository.get_unique_rooms()
        assert rooms == ["Room A", "Room B", "Room C"]


class TestGetTracksByDay:
    def test_filters_tracks_by_day(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        tracks = seeded_events_repository.get_tracks_by_day("2026-02-07")
        assert set(tracks) == {"Rust", "Python"}

    def test_nonexistent_day_returns_empty(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        assert seeded_events_repository.get_tracks_by_day("2099-01-01") == []


class TestGetEventsByDayAndTrack:
    def test_filters_correctly(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        events = seeded_events_repository.get_events_by_day_and_track("2026-02-07", "Rust")
        assert len(events) == 1
        assert events[0].title == "Intro to Rust"

    def test_no_match_returns_empty(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        assert seeded_events_repository.get_events_by_day_and_track("2026-02-07", "Go") == []


class TestGetSpeakersForEvent:
    def test_returns_speakers(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        speakers = seeded_events_repository.get_speakers_for_event("3")
        assert len(speakers) == 1
        assert speakers[0].name == "Mark"

    def test_no_speakers_returns_empty(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        speakers = seeded_events_repository.get_speakers_for_event("1")
        assert speakers == []

    def test_nonexistent_event_returns_empty(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        assert seeded_events_repository.get_speakers_for_event("999") == []


class TestGetLinksForEvent:
    def test_returns_links(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        events_repository: DuckDBEventsRepository,
    ) -> None:
        from tests.conftest import _make_event

        event = _make_event(
            id="lnk1",
            links=[
                Link(href="https://fosdem.org/2026/schedule/event/lnk1/", title="FOSDEM page"),
                Link(href="https://example.com/slides.pdf", title="Slides"),
            ],
        )
        ingestion_repository.insert_events([event])
        links = events_repository.get_links_for_event("lnk1")
        assert len(links) == 2
        assert links[0].href == "https://fosdem.org/2026/schedule/event/lnk1/"
        assert links[1].title == "Slides"

    def test_no_links_returns_empty(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        assert seeded_events_repository.get_links_for_event("1") == []

    def test_nonexistent_event_returns_empty(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        assert seeded_events_repository.get_links_for_event("999") == []


class TestSearchEvents:
    def test_search_by_title(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        results = seeded_events_repository.search_events("Rust")
        assert len(results) == 1
        assert results[0].title == "Intro to Rust"

    def test_search_by_abstract(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        results = seeded_events_repository.search_events("under the hood")
        assert len(results) == 1
        assert results[0].title == "DuckDB Internals"

    def test_search_case_insensitive(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        results = seeded_events_repository.search_events("rust")
        assert len(results) == 1

    def test_search_no_match(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        assert seeded_events_repository.search_events("nonexistent") == []

    def test_search_partial_match(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        results = seeded_events_repository.search_events("Pack")
        assert len(results) == 1
        assert results[0].title == "Python Packaging"


class TestFilterEvents:
    def test_filter_by_track(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        results = seeded_events_repository.filter_events(track="Rust")
        assert len(results) == 1
        assert results[0].title == "Intro to Rust"

    def test_filter_by_room(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        results = seeded_events_repository.filter_events(room="Room B")
        assert len(results) == 1
        assert results[0].title == "Python Packaging"

    def test_filter_by_day(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        results = seeded_events_repository.filter_events(day="2026-02-08")
        assert len(results) == 1
        assert results[0].title == "DuckDB Internals"

    def test_filter_combines_with_query(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        results = seeded_events_repository.filter_events(q="Rust", day="2026-02-07")
        assert len(results) == 1
        assert results[0].title == "Intro to Rust"

    def test_filter_no_params_returns_all(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        results = seeded_events_repository.filter_events()
        assert len(results) == 3

    def test_filter_no_match(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        results = seeded_events_repository.filter_events(track="NonExistent")
        assert results == []

    def test_filter_mismatched_track_and_day(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        # Rust track is only on 2026-02-07, not 2026-02-08
        results = seeded_events_repository.filter_events(track="Rust", day="2026-02-08")
        assert results == []


class TestGetEventById:
    def test_returns_event(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        event = seeded_events_repository.get_event_by_id("1")
        assert event is not None
        assert event.title == "Intro to Rust"

    def test_returns_none_for_missing_id(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        assert seeded_events_repository.get_event_by_id("nonexistent") is None

    def test_includes_all_fields(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        event = seeded_events_repository.get_event_by_id("1")
        assert event is not None
        for field in (
            "id",
            "title",
            "subtitle",
            "abstract",
            "start_time",
            "duration_minutes",
            "room",
            "track",
            "day",
        ):
            assert hasattr(event, field)


class TestGetEventsByIds:
    def test_returns_matching_events(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        result = seeded_events_repository.get_events_by_ids(["1", "3"])
        assert len(result) == 2
        ids = {e.id for e in result}
        assert ids == {"1", "3"}

    def test_ignores_unknown_ids(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        result = seeded_events_repository.get_events_by_ids(["1", "nonexistent"])
        assert len(result) == 1
        assert result[0].id == "1"

    def test_returns_empty_for_no_ids(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        result = seeded_events_repository.get_events_by_ids([])
        assert result == []

    def test_returns_all_fields(self, seeded_events_repository: DuckDBEventsRepository) -> None:
        result = seeded_events_repository.get_events_by_ids(["1"])
        assert len(result) == 1
        ev = result[0]
        assert ev.title
        assert ev.start_time
        assert ev.duration_minutes
        assert ev.room
        assert ev.track
        assert ev.day

    def test_ordered_by_day_and_time(
        self, seeded_events_repository: DuckDBEventsRepository
    ) -> None:
        result = seeded_events_repository.get_events_by_ids(["3", "1", "2"])
        assert len(result) == 3
        ids = [e.id for e in result]
        # Event 1 and 2 are day 2026-02-07, event 3 is day 2026-02-08
        assert ids == ["1", "2", "3"]
