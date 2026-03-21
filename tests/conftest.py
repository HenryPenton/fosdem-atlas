"""Shared test fixtures."""

import os
from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.adapters.persistence.duckdb_analytics_repository import DuckDBAnalyticsRepository
from src.adapters.persistence.duckdb_connection import DuckDBConnection
from src.adapters.persistence.duckdb_events_repository import DuckDBEventsRepository
from src.adapters.persistence.duckdb_ingestion_repository import DuckDBIngestionRepository
from src.adapters.persistence.duckdb_speakers_repository import DuckDBSpeakersRepository
from src.adapters.web.app import create_app
from src.application.services import AnalyticsService, ScheduleService, SpeakerService
from src.config import Settings
from src.domain.models import Event, Link, Speaker


def _make_event(
    id: str = "1",
    title: str = "Test Event",
    subtitle: str = "",
    abstract: str = "",
    start_time: datetime | None = None,
    duration_minutes: int = 30,
    room: str = "Room A",
    track: str = "Testing",
    day: str = "2026-02-07",
    speakers: list[Speaker] | None = None,
    links: list[Link] | None = None,
) -> Event:
    return Event(
        id=id,
        title=title,
        subtitle=subtitle,
        abstract=abstract,
        start_time=start_time or datetime(2026, 2, 7, 10, 0),
        duration_minutes=duration_minutes,
        room=room,
        track=track,
        day=day,
        speakers=speakers or [],
        links=links or [],
    )


SAMPLE_EVENTS = [
    _make_event(id="1", title="Intro to Rust", abstract="Learn Rust basics", track="Rust"),
    _make_event(
        id="2",
        title="Python Packaging",
        abstract="Modern Python packaging",
        track="Python",
        room="Room B",
        start_time=datetime(2026, 2, 7, 11, 0),
    ),
    _make_event(
        id="3",
        title="DuckDB Internals",
        abstract="How DuckDB works under the hood",
        track="Databases",
        room="Room C",
        day="2026-02-08",
        start_time=datetime(2026, 2, 8, 9, 0),
        speakers=[Speaker(id="s1", name="Mark")],
    ),
]


@pytest.fixture
def db_connection(tmp_path: Path) -> Generator[DuckDBConnection, None, None]:
    """In-memory DuckDB connection for tests."""
    db_path = str(tmp_path / "test.duckdb")
    conn = DuckDBConnection(db_path)
    conn.get()  # initialise schema
    yield conn
    conn.close()
    # Clean up
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def events_repository(db_connection: DuckDBConnection) -> DuckDBEventsRepository:
    """DuckDBEventsRepository backed by a temp database."""
    return DuckDBEventsRepository(db_connection)


@pytest.fixture
def ingestion_repository(db_connection: DuckDBConnection) -> DuckDBIngestionRepository:
    """DuckDBIngestionRepository sharing the same temp database connection."""
    return DuckDBIngestionRepository(db_connection)


@pytest.fixture
def speakers_repository(db_connection: DuckDBConnection) -> DuckDBSpeakersRepository:
    """DuckDBSpeakersRepository sharing the same temp database connection."""
    return DuckDBSpeakersRepository(db_connection)


@pytest.fixture
def analytics_repository(db_connection: DuckDBConnection) -> DuckDBAnalyticsRepository:
    """DuckDBAnalyticsRepository sharing the same temp database connection."""
    return DuckDBAnalyticsRepository(db_connection)


@pytest.fixture
def seeded_ingestion_repository(
    ingestion_repository: DuckDBIngestionRepository,
) -> DuckDBIngestionRepository:
    """Ingestion repository pre-loaded with sample events."""
    ingestion_repository.insert_events(SAMPLE_EVENTS)
    return ingestion_repository


@pytest.fixture
def seeded_events_repository(
    seeded_ingestion_repository: DuckDBIngestionRepository,  # noqa: ARG001
    events_repository: DuckDBEventsRepository,
) -> DuckDBEventsRepository:
    """Events repository after sample events have been inserted via ingestion."""
    # _seeded_ingestion_repository drives the insert; events_repository shares the same db_connection
    return events_repository


@pytest.fixture
def seeded_speakers_repository(
    seeded_ingestion_repository: DuckDBIngestionRepository,  # noqa: ARG001
    speakers_repository: DuckDBSpeakersRepository,
) -> DuckDBSpeakersRepository:
    """Speakers repository after sample events (and their speakers) have been inserted."""
    # _seeded_ingestion_repository drives the insert; speakers_repository shares the same db_connection
    return speakers_repository


@pytest.fixture
def seeded_analytics_repository(
    seeded_ingestion_repository: DuckDBIngestionRepository,  # noqa: ARG001
    analytics_repository: DuckDBAnalyticsRepository,
) -> DuckDBAnalyticsRepository:
    """Analytics repository after sample events have been inserted."""
    # _seeded_ingestion_repository drives the insert; analytics_repository shares the same db_connection
    return analytics_repository


@pytest.fixture
def schedule_service(seeded_events_repository: DuckDBEventsRepository) -> ScheduleService:
    return ScheduleService(seeded_events_repository)


@pytest.fixture
def analytics_service(seeded_analytics_repository: DuckDBAnalyticsRepository) -> AnalyticsService:
    return AnalyticsService(seeded_analytics_repository)


@pytest.fixture
def speaker_service(seeded_speakers_repository: DuckDBSpeakersRepository) -> SpeakerService:
    return SpeakerService(seeded_speakers_repository)


@pytest.fixture
def settings() -> Settings:
    return Settings(database_path=":memory:")


@pytest.fixture
def client(
    schedule_service: ScheduleService,
    analytics_service: AnalyticsService,
    speaker_service: SpeakerService,
    settings: Settings,
) -> TestClient:
    """FastAPI TestClient wired to the seeded repository."""
    app = create_app(
        schedule_service=schedule_service,
        analytics_service=analytics_service,
        speaker_service=speaker_service,
        settings=settings,
    )
    return TestClient(app)
