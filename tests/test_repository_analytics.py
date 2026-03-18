"""Tests for DuckDBAnalyticsRepository — conference stats, room stats, speaker stats, and topics."""

from datetime import datetime

from src.adapters.persistence.duckdb_analytics_repository import DuckDBAnalyticsRepository
from src.adapters.persistence.duckdb_ingestion_repository import DuckDBIngestionRepository
from src.domain.models import Event, Speaker


class TestGetStats:
    def test_returns_total_events(
        self, seeded_analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        stats = seeded_analytics_repository.get_stats()
        assert stats.total_events == 3

    def test_returns_total_speakers(
        self, seeded_analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        stats = seeded_analytics_repository.get_stats()
        assert stats.total_speakers == 1

    def test_returns_total_tracks(
        self, seeded_analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        stats = seeded_analytics_repository.get_stats()
        assert stats.total_tracks == 3

    def test_returns_total_rooms(
        self, seeded_analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        stats = seeded_analytics_repository.get_stats()
        assert stats.total_rooms == 3

    def test_events_per_day(self, seeded_analytics_repository: DuckDBAnalyticsRepository) -> None:
        stats = seeded_analytics_repository.get_stats()
        per_day = {item.day: item.count for item in stats.events_per_day}
        assert per_day["2026-02-07"] == 2
        assert per_day["2026-02-08"] == 1

    def test_events_per_track(self, seeded_analytics_repository: DuckDBAnalyticsRepository) -> None:
        stats = seeded_analytics_repository.get_stats()
        per_track = {item.track: item.count for item in stats.events_per_track}
        assert per_track["Rust"] == 1
        assert per_track["Python"] == 1
        assert per_track["Databases"] == 1

    def test_empty_repository_returns_zeros(
        self, analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        stats = analytics_repository.get_stats()
        assert stats.total_events == 0
        assert stats.total_speakers == 0
        assert stats.events_per_day == []
        assert stats.events_per_track == []


class TestGetRoomStats:
    def test_events_per_room_counts(
        self, seeded_analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        room_stats = seeded_analytics_repository.get_room_stats()
        per_room = {item.room: item.count for item in room_stats.events_per_room}
        assert per_room["Room A"] == 1
        assert per_room["Room B"] == 1
        assert per_room["Room C"] == 1

    def test_events_per_room_ordered_by_count_desc(
        self, seeded_analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        room_stats = seeded_analytics_repository.get_room_stats()
        counts = [item.count for item in room_stats.events_per_room]
        assert counts == sorted(counts, reverse=True)

    def test_heatmap_contains_day_and_hour(
        self, seeded_analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        room_stats = seeded_analytics_repository.get_room_stats()
        heatmap = room_stats.heatmap
        assert len(heatmap) > 0
        days = {item.day for item in heatmap}
        assert "2026-02-07" in days
        assert "2026-02-08" in days

    def test_heatmap_hours_match_event_start_times(
        self, seeded_analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        room_stats = seeded_analytics_repository.get_room_stats()
        hours = {item.hour for item in room_stats.heatmap}
        # SAMPLE_EVENTS start at 10:00, 11:00 on day1 and 09:00 on day2
        assert 10 in hours
        assert 11 in hours
        assert 9 in hours

    def test_empty_repository_returns_empty_lists(
        self, analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        room_stats = analytics_repository.get_room_stats()
        assert room_stats.events_per_room == []
        assert room_stats.heatmap == []


class TestGetSpeakerStats:
    def _seed_multi_speaker_events(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        analytics_repository: DuckDBAnalyticsRepository,
    ) -> DuckDBAnalyticsRepository:
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
        ingestion_repository.insert_events(events)
        return analytics_repository

    def test_top_speakers_ordered_by_talk_count(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        analytics_repository: DuckDBAnalyticsRepository,
    ) -> None:
        repo = self._seed_multi_speaker_events(ingestion_repository, analytics_repository)
        stats = repo.get_speaker_stats()
        top = stats.top_speakers
        assert len(top) == 2
        assert top[0].name == "Alice"
        assert top[0].talk_count == 2
        assert top[1].name == "Bob"
        assert top[1].talk_count == 1

    def test_multi_track_speakers(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        analytics_repository: DuckDBAnalyticsRepository,
    ) -> None:
        repo = self._seed_multi_speaker_events(ingestion_repository, analytics_repository)
        stats = repo.get_speaker_stats()
        multi = stats.multi_track_speakers
        assert len(multi) == 1
        assert multi[0].name == "Alice"
        assert multi[0].track_count == 2
        assert set(multi[0].tracks) == {"Python", "Rust"}

    def test_single_track_speaker_not_in_multi_track(
        self, seeded_analytics_repository: DuckDBAnalyticsRepository
    ) -> None:
        stats = seeded_analytics_repository.get_speaker_stats()
        assert stats.multi_track_speakers == []
        assert len(stats.top_speakers) == 1

    def test_empty_when_no_speakers(self, analytics_repository: DuckDBAnalyticsRepository) -> None:
        stats = analytics_repository.get_speaker_stats()
        assert stats.top_speakers == []
        assert stats.multi_track_speakers == []


class TestGetTopicStats:
    def test_returns_keywords_from_events(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        analytics_repository: DuckDBAnalyticsRepository,
    ) -> None:
        events = [
            Event(
                id="t1",
                title="Rust and WebAssembly",
                abstract="Building WebAssembly modules with Rust for the browser",
                start_time=datetime(2026, 2, 7, 10, 0),
                duration_minutes=30,
                room="Room A",
                track="Rust",
                day="2026-02-07",
            ),
            Event(
                id="t2",
                title="Advanced WebAssembly",
                abstract="Deep dive into WebAssembly runtime internals",
                start_time=datetime(2026, 2, 7, 11, 0),
                duration_minutes=30,
                room="Room B",
                track="Web",
                day="2026-02-07",
            ),
        ]
        ingestion_repository.insert_events(events)
        stats = analytics_repository.get_topic_stats()
        assert len(stats.keywords) > 0
        terms = [kw.term.lower() for kw in stats.keywords]
        assert any("webassembly" in t for t in terms)

    def test_keywords_have_term_and_count(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        analytics_repository: DuckDBAnalyticsRepository,
    ) -> None:
        events = [
            Event(
                id="t1",
                title="Linux kernel hacking",
                abstract="Kernel development with Linux",
                start_time=datetime(2026, 2, 7, 10, 0),
                duration_minutes=30,
                room="Room A",
                track="Kernel",
                day="2026-02-07",
            ),
            Event(
                id="t2",
                title="Linux networking",
                abstract="Linux kernel networking stack",
                start_time=datetime(2026, 2, 7, 11, 0),
                duration_minutes=30,
                room="Room B",
                track="Kernel",
                day="2026-02-07",
            ),
        ]
        ingestion_repository.insert_events(events)
        stats = analytics_repository.get_topic_stats()
        for kw in stats.keywords:
            assert hasattr(kw, "term")
            assert hasattr(kw, "count")
            assert isinstance(kw.count, int)
            assert kw.count >= 2

    def test_empty_when_no_events(self, analytics_repository: DuckDBAnalyticsRepository) -> None:
        stats = analytics_repository.get_topic_stats()
        assert stats.keywords == []

    def test_filters_conference_stopwords(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        analytics_repository: DuckDBAnalyticsRepository,
    ) -> None:
        events = [
            Event(
                id="t1",
                title="Open source Kubernetes",
                abstract="Open source container orchestration with Kubernetes",
                start_time=datetime(2026, 2, 7, 10, 0),
                duration_minutes=30,
                room="Room A",
                track="Cloud",
                day="2026-02-07",
            ),
            Event(
                id="t2",
                title="Kubernetes operators",
                abstract="Building Kubernetes operators for cloud infrastructure",
                start_time=datetime(2026, 2, 7, 11, 0),
                duration_minutes=30,
                room="Room B",
                track="Cloud",
                day="2026-02-07",
            ),
        ]
        ingestion_repository.insert_events(events)
        stats = analytics_repository.get_topic_stats()
        terms_lower = [kw.term.lower() for kw in stats.keywords]
        assert "open source" not in terms_lower
