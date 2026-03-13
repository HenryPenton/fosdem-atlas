"""DuckDB database connection and schema management."""

import contextlib
import threading
from pathlib import Path

import duckdb

from src.config import settings

_connection: duckdb.DuckDBPyConnection | None = None
_lock = threading.Lock()


def get_connection() -> duckdb.DuckDBPyConnection:
    """Get or create the DuckDB connection.

    Thread-safe: uses a lock to serialize access. DuckDB's Python
    connection is not safe to share across threads without
    synchronization, so all callers go through this single lock.
    """
    global _connection
    with _lock:
        if _connection is None:
            db_path = Path(settings.database_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            _connection = duckdb.connect(str(db_path))
            _init_schema(_connection)
        return _connection


def db_lock() -> threading.Lock:
    """Return the database lock for callers that need to hold it across
    multiple statements (e.g. transactions)."""
    return _lock


def close_connection() -> None:
    """Close the DuckDB connection."""
    global _connection
    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None


def _init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Initialize the database schema."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id VARCHAR PRIMARY KEY,
            title VARCHAR NOT NULL,
            subtitle VARCHAR NOT NULL DEFAULT '',
            abstract VARCHAR NOT NULL DEFAULT '',
            start_time TIMESTAMP NOT NULL,
            duration_minutes INTEGER NOT NULL,
            room VARCHAR NOT NULL,
            track VARCHAR NOT NULL,
            day DATE NOT NULL
        )
    """
    )
    # Add new columns if upgrading from an older schema
    for col, definition in [
        ("subtitle", "VARCHAR NOT NULL DEFAULT ''"),
        ("abstract", "VARCHAR NOT NULL DEFAULT ''"),
    ]:
        with contextlib.suppress(Exception):
            conn.execute(f"ALTER TABLE events ADD COLUMN {col} {definition}")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS speakers (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS event_speakers (
            event_id VARCHAR NOT NULL REFERENCES events(id),
            speaker_id VARCHAR NOT NULL REFERENCES speakers(id),
            PRIMARY KEY (event_id, speaker_id)
        )
    """
    )
