"""DuckDB connection management."""

import threading
from pathlib import Path

import duckdb


class DuckDBConnection:
    """Manages the DuckDB connection lifecycle."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._connection: duckdb.DuckDBPyConnection | None = None
        self._lock = threading.RLock()

    def get(self) -> duckdb.DuckDBPyConnection:
        """Get or create the DuckDB connection (thread-safe)."""
        with self._lock:
            if self._connection is None:
                path = Path(self._db_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                self._connection = duckdb.connect(str(path))
                self._init_schema(self._connection)
            return self._connection

    @property
    def lock(self) -> threading.RLock:
        """Lock for callers needing multi-statement transactions."""
        return self._lock

    def close(self) -> None:
        """Close the DuckDB connection."""
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    def _init_schema(self, conn: duckdb.DuckDBPyConnection) -> None:
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
                day DATE NOT NULL,
                fosdem_url VARCHAR NOT NULL DEFAULT ''
            )
        """
        )
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS keywords (
                term VARCHAR NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (term)
            )
        """
        )
