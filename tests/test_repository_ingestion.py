"""Tests for DuckDBIngestionRepository — event, speaker, and keyword writes."""

from datetime import datetime

from src.adapters.persistence.duckdb_events_repository import DuckDBEventsRepository
from src.adapters.persistence.duckdb_ingestion_repository import DuckDBIngestionRepository
from src.domain.models import Event, Link, Speaker
from tests.conftest import SAMPLE_EVENTS


class TestInsertEvents:
    def test_insert_and_count(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        events_repository: DuckDBEventsRepository,
    ) -> None:
        count = ingestion_repository.insert_events(SAMPLE_EVENTS)
        assert count == 3
        assert events_repository.get_event_count() == 3

    def test_insert_replaces_previous_data(
        self,
        seeded_ingestion_repository: DuckDBIngestionRepository,
        events_repository: DuckDBEventsRepository,
    ) -> None:
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
        seeded_ingestion_repository.insert_events(new_events)
        assert events_repository.get_event_count() == 1

    def test_insert_stores_speakers(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        events_repository: DuckDBEventsRepository,
    ) -> None:
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
        ingestion_repository.insert_events(events)
        speakers = events_repository.get_speakers_for_event("10")
        assert len(speakers) == 2
        names = {s.name for s in speakers}
        assert names == {"Alice", "Bob"}

    def test_insert_returns_event_count(
        self, ingestion_repository: DuckDBIngestionRepository
    ) -> None:
        count = ingestion_repository.insert_events(SAMPLE_EVENTS[:2])
        assert count == 2

    def test_insert_empty_list(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        events_repository: DuckDBEventsRepository,
    ) -> None:
        count = ingestion_repository.insert_events([])
        assert count == 0
        assert events_repository.get_event_count() == 0

    def test_vtt_link_not_stored_as_video_url(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        events_repository: DuckDBEventsRepository,
    ) -> None:
        """Only recognised video formats (mp4, webm, etc.) are stored as video_url."""
        events = [
            Event(
                id="20",
                title="Talk with Subs",
                start_time=datetime(2026, 2, 7, 10, 0),
                duration_minutes=30,
                room="Room A",
                track="Test",
                day="2026-02-07",
                links=[
                    Link(
                        href="https://video.fosdem.org/2026/h1234/talk.vtt",
                        title="Subtitles",
                    ),
                    Link(
                        href="https://video.fosdem.org/2026/h1234/talk.webm",
                        title="Video recording",
                    ),
                ],
            )
        ]
        ingestion_repository.insert_events(events)
        detail = events_repository.get_event_by_id("20")
        assert detail is not None
        assert detail.video_url == "https://video.fosdem.org/2026/h1234/talk.webm"

    def test_only_vtt_link_results_in_empty_video_url(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        events_repository: DuckDBEventsRepository,
    ) -> None:
        """If no video.fosdem.org link has a known video extension, video_url is empty."""
        events = [
            Event(
                id="21",
                title="Talk Subs Only",
                start_time=datetime(2026, 2, 7, 10, 0),
                duration_minutes=30,
                room="Room A",
                track="Test",
                day="2026-02-07",
                links=[
                    Link(
                        href="https://video.fosdem.org/2026/h1234/talk.vtt",
                        title="Subtitles",
                    ),
                ],
            )
        ]
        ingestion_repository.insert_events(events)
        detail = events_repository.get_event_by_id("21")
        assert detail is not None
        assert detail.video_url == ""
