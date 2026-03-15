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


class TestGetEventById:
    def test_returns_event(self, seeded_repository: DuckDBEventRepository) -> None:
        event = seeded_repository.get_event_by_id("1")
        assert event is not None
        assert event["title"] == "Intro to Rust"

    def test_returns_none_for_missing_id(self, seeded_repository: DuckDBEventRepository) -> None:
        assert seeded_repository.get_event_by_id("nonexistent") is None

    def test_includes_all_fields(self, seeded_repository: DuckDBEventRepository) -> None:
        event = seeded_repository.get_event_by_id("1")
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
            "fosdem_url",
        ):
            assert field in event


class TestGetAllSpeakers:
    def test_returns_speakers_with_talk_counts(
        self, seeded_repository: DuckDBEventRepository
    ) -> None:
        speakers = seeded_repository.get_all_speakers()
        assert len(speakers) == 1
        assert speakers[0]["name"] == "Mark"
        assert speakers[0]["talk_count"] == 1

    def test_empty_when_no_speakers(self, repository: DuckDBEventRepository) -> None:
        assert repository.get_all_speakers() == []

    def test_ordered_by_name(self, repository: DuckDBEventRepository) -> None:
        from datetime import datetime

        from src.domain.models import Event, Speaker

        events = [
            Event(
                id="a",
                title="Talk A",
                start_time=datetime(2026, 2, 7, 10, 0),
                duration_minutes=30,
                room="Room A",
                track="Test",
                day="2026-02-07",
                speakers=[Speaker(id="z1", name="Zelda"), Speaker(id="a1", name="Alice")],
            )
        ]
        repository.insert_events(events)
        speakers = repository.get_all_speakers()
        names = [s["name"] for s in speakers]
        assert names == sorted(names)


class TestGetSpeakerById:
    def test_returns_speaker(self, seeded_repository: DuckDBEventRepository) -> None:
        speaker = seeded_repository.get_speaker_by_id("s1")
        assert speaker is not None
        assert speaker["name"] == "Mark"
        assert speaker["id"] == "s1"

    def test_returns_none_for_missing_id(self, seeded_repository: DuckDBEventRepository) -> None:
        assert seeded_repository.get_speaker_by_id("nonexistent") is None


class TestGetEventsBySpeaker:
    def test_returns_speakers_events(self, seeded_repository: DuckDBEventRepository) -> None:
        events = seeded_repository.get_events_by_speaker("s1")
        assert len(events) == 1
        assert events[0]["title"] == "DuckDB Internals"

    def test_returns_empty_for_unknown_speaker(
        self, seeded_repository: DuckDBEventRepository
    ) -> None:
        assert seeded_repository.get_events_by_speaker("nonexistent") == []

    def test_events_include_expected_fields(self, seeded_repository: DuckDBEventRepository) -> None:
        events = seeded_repository.get_events_by_speaker("s1")
        assert len(events) == 1
        event = events[0]
        for field in ("id", "title", "start_time", "duration_minutes", "room", "track", "day"):
            assert field in event


class TestGetStats:
    def test_returns_total_events(self, seeded_repository: DuckDBEventRepository) -> None:
        stats = seeded_repository.get_stats()
        assert stats["total_events"] == 3

    def test_returns_total_speakers(self, seeded_repository: DuckDBEventRepository) -> None:
        stats = seeded_repository.get_stats()
        assert stats["total_speakers"] == 1

    def test_returns_total_tracks(self, seeded_repository: DuckDBEventRepository) -> None:
        stats = seeded_repository.get_stats()
        assert stats["total_tracks"] == 3

    def test_returns_total_rooms(self, seeded_repository: DuckDBEventRepository) -> None:
        stats = seeded_repository.get_stats()
        assert stats["total_rooms"] == 3

    def test_events_per_day(self, seeded_repository: DuckDBEventRepository) -> None:
        stats = seeded_repository.get_stats()
        per_day = {item["day"]: item["count"] for item in stats["events_per_day"]}  # type: ignore[union-attr]
        assert per_day["2026-02-07"] == 2
        assert per_day["2026-02-08"] == 1

    def test_events_per_track(self, seeded_repository: DuckDBEventRepository) -> None:
        stats = seeded_repository.get_stats()
        per_track = {item["track"]: item["count"] for item in stats["events_per_track"]}  # type: ignore[union-attr]
        assert per_track["Rust"] == 1
        assert per_track["Python"] == 1
        assert per_track["Databases"] == 1

    def test_empty_repository_returns_zeros(self, repository: DuckDBEventRepository) -> None:
        stats = repository.get_stats()
        assert stats["total_events"] == 0
        assert stats["total_speakers"] == 0
        assert stats["events_per_day"] == []
        assert stats["events_per_track"] == []


class TestGetRoomStats:
    def test_events_per_room_counts(self, seeded_repository: DuckDBEventRepository) -> None:
        room_stats = seeded_repository.get_room_stats()
        per_room = {item["room"]: item["count"] for item in room_stats["events_per_room"]}
        assert per_room["Room A"] == 1
        assert per_room["Room B"] == 1
        assert per_room["Room C"] == 1

    def test_events_per_room_ordered_by_count_desc(
        self, seeded_repository: DuckDBEventRepository
    ) -> None:
        room_stats = seeded_repository.get_room_stats()
        counts = [item["count"] for item in room_stats["events_per_room"]]
        assert counts == sorted(counts, reverse=True)

    def test_heatmap_contains_day_and_hour(self, seeded_repository: DuckDBEventRepository) -> None:
        room_stats = seeded_repository.get_room_stats()
        heatmap = room_stats["heatmap"]
        assert len(heatmap) > 0
        days = {item["day"] for item in heatmap}
        assert "2026-02-07" in days
        assert "2026-02-08" in days

    def test_heatmap_hours_match_event_start_times(
        self, seeded_repository: DuckDBEventRepository
    ) -> None:
        room_stats = seeded_repository.get_room_stats()
        hours = {item["hour"] for item in room_stats["heatmap"]}
        # SAMPLE_EVENTS start at 10:00, 11:00 on day1 and 09:00 on day2
        assert 10 in hours
        assert 11 in hours
        assert 9 in hours

    def test_empty_repository_returns_empty_lists(self, repository: DuckDBEventRepository) -> None:
        room_stats = repository.get_room_stats()
        assert room_stats["events_per_room"] == []
        assert room_stats["heatmap"] == []


class TestGetSpeakerStats:
    def _events_with_speakers(self, repository: DuckDBEventRepository) -> DuckDBEventRepository:
        from datetime import datetime

        from src.domain.models import Event, Speaker

        events = [
            Event(
                id="a",
                title="Talk 1",
                start_time=datetime(2026, 2, 7, 10, 0),
                duration_minutes=30,
                room="Room A",
                track="Rust",
                day="2026-02-07",
                speakers=[Speaker(id="sp1", name="Alice")],
            ),
            Event(
                id="b",
                title="Talk 2",
                start_time=datetime(2026, 2, 7, 11, 0),
                duration_minutes=30,
                room="Room B",
                track="Python",
                day="2026-02-07",
                speakers=[Speaker(id="sp1", name="Alice")],
            ),
            Event(
                id="c",
                title="Talk 3",
                start_time=datetime(2026, 2, 7, 12, 0),
                duration_minutes=30,
                room="Room C",
                track="Go",
                day="2026-02-07",
                speakers=[Speaker(id="sp2", name="Bob")],
            ),
        ]
        repository.insert_events(events)
        return repository

    def test_top_speakers_ordered_by_talk_count(self, repository: DuckDBEventRepository) -> None:
        repo = self._events_with_speakers(repository)
        stats = repo.get_speaker_stats()
        top = stats["top_speakers"]
        assert len(top) == 2
        assert top[0]["name"] == "Alice"
        assert top[0]["talk_count"] == 2
        assert top[1]["name"] == "Bob"
        assert top[1]["talk_count"] == 1

    def test_multi_track_speakers(self, repository: DuckDBEventRepository) -> None:
        repo = self._events_with_speakers(repository)
        stats = repo.get_speaker_stats()
        multi = stats["multi_track_speakers"]
        assert len(multi) == 1
        assert multi[0]["name"] == "Alice"
        assert multi[0]["track_count"] == 2
        assert set(multi[0]["tracks"]) == {"Python", "Rust"}  # type: ignore[arg-type]

    def test_single_track_speaker_not_in_multi_track(
        self, seeded_repository: DuckDBEventRepository
    ) -> None:
        stats = seeded_repository.get_speaker_stats()
        assert stats["multi_track_speakers"] == []
        assert len(stats["top_speakers"]) == 1

    def test_empty_when_no_speakers(self, repository: DuckDBEventRepository) -> None:
        stats = repository.get_speaker_stats()
        assert stats["top_speakers"] == []
        assert stats["multi_track_speakers"] == []
