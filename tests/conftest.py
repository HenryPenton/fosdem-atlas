"""Shared test fixtures."""

import os
from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.adapters.persistence.duckdb_connection import DuckDBConnection
from src.adapters.persistence.duckdb_repository import DuckDBEventRepository
from src.adapters.web.app import create_app
from src.config import Settings
from src.domain.models import Event, Speaker


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
def repository(db_connection: DuckDBConnection) -> DuckDBEventRepository:
    """DuckDBEventRepository backed by a temp database."""
    return DuckDBEventRepository(db_connection)


@pytest.fixture
def seeded_repository(repository: DuckDBEventRepository) -> DuckDBEventRepository:
    """Repository pre-loaded with sample events."""
    repository.insert_events(SAMPLE_EVENTS)
    return repository


@pytest.fixture
def settings() -> Settings:
    return Settings(database_path=":memory:")


@pytest.fixture
def client(seeded_repository: DuckDBEventRepository, settings: Settings) -> TestClient:
    """FastAPI TestClient wired to the seeded repository."""
    app = create_app(event_repository=seeded_repository, settings=settings)
    return TestClient(app)
