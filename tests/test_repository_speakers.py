"""Tests for DuckDBSpeakersRepository — speaker queries."""

from datetime import datetime

from src.adapters.persistence.duckdb_ingestion_repository import DuckDBIngestionRepository
from src.adapters.persistence.duckdb_speakers_repository import DuckDBSpeakersRepository
from src.domain.models import Event, Speaker


class TestGetAllSpeakers:
    def test_returns_speakers_with_talk_counts(
        self, seeded_speakers_repository: DuckDBSpeakersRepository
    ) -> None:
        speakers = seeded_speakers_repository.get_all_speakers()
        assert len(speakers) == 1
        assert speakers[0].name == "Mark"
        assert speakers[0].talk_count == 1

    def test_empty_when_no_speakers(self, speakers_repository: DuckDBSpeakersRepository) -> None:
        assert speakers_repository.get_all_speakers() == []

    def test_ordered_by_name(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        speakers_repository: DuckDBSpeakersRepository,
    ) -> None:
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
        ingestion_repository.insert_events(events)
        speakers = speakers_repository.get_all_speakers()
        names = [s.name for s in speakers]
        assert names == sorted(names)


class TestGetSpeakerById:
    def test_returns_speaker(self, seeded_speakers_repository: DuckDBSpeakersRepository) -> None:
        speaker = seeded_speakers_repository.get_speaker_by_id("s1")
        assert speaker is not None
        assert speaker.name == "Mark"
        assert speaker.id == "s1"

    def test_returns_none_for_missing_id(
        self, seeded_speakers_repository: DuckDBSpeakersRepository
    ) -> None:
        assert seeded_speakers_repository.get_speaker_by_id("nonexistent") is None


class TestGetEventsBySpeaker:
    def test_returns_speakers_events(
        self, seeded_speakers_repository: DuckDBSpeakersRepository
    ) -> None:
        events = seeded_speakers_repository.get_events_by_speaker("s1")
        assert len(events) == 1
        assert events[0].title == "DuckDB Internals"

    def test_returns_empty_for_unknown_speaker(
        self, seeded_speakers_repository: DuckDBSpeakersRepository
    ) -> None:
        assert seeded_speakers_repository.get_events_by_speaker("nonexistent") == []

    def test_events_include_expected_fields(
        self, seeded_speakers_repository: DuckDBSpeakersRepository
    ) -> None:
        events = seeded_speakers_repository.get_events_by_speaker("s1")
        assert len(events) == 1
        event = events[0]
        for field in ("id", "title", "start_time", "duration_minutes", "room", "track", "day"):
            assert hasattr(event, field)
