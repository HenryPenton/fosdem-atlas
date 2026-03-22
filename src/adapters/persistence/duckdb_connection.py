"""DuckDB connection management."""

import contextlib
import threading
from pathlib import Path

import duckdb


class DuckDBConnection:
    """Manages DuckDB connections with per-thread isolation.

    DuckDB connections are not thread-safe.  Returning a single shared
    connection to multiple threads causes
    "Attempting to execute an unsuccessful or closed pending query result"
    under concurrent load.  Each OS/asyncio worker thread therefore gets
    its own connection via threading.local().
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()
        self._local = threading.local()
        self._all_connections: list[duckdb.DuckDBPyConnection] = []

    def get(self) -> duckdb.DuckDBPyConnection:
        """Return the calling thread's DuckDB connection, creating it if needed."""
        conn: duckdb.DuckDBPyConnection | None = getattr(self._local, "connection", None)
        if conn is not None:
            try:
                conn.execute("SELECT 1")
            except Exception:
                with contextlib.suppress(Exception):
                    conn.close()
                with self._lock:
                    if conn in self._all_connections:
                        self._all_connections.remove(conn)
                self._local.connection = None
                conn = None
        if conn is None:
            path = Path(self._db_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            conn = duckdb.connect(str(path))
            # Hold the lock during schema init so concurrent new threads don't
            # race on DDL (CREATE TABLE IF NOT EXISTS causes a catalog
            # write-write conflict when multiple connections run it in parallel).
            with self._lock:
                self._init_schema(conn)
                self._all_connections.append(conn)
            self._local.connection = conn
        return conn

    @property
    def lock(self) -> threading.RLock:
        """Lock for callers needing exclusive multi-statement transactions."""
        return self._lock

    def close(self) -> None:
        """Close all open per-thread connections."""
        with self._lock:
            for conn in self._all_connections:
                with contextlib.suppress(Exception):
                    conn.close()

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
                day DATE NOT NULL
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS speakers (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                bio VARCHAR NOT NULL DEFAULT ''
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS event_speakers (
                event_id VARCHAR NOT NULL,
                speaker_id VARCHAR NOT NULL,
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

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS event_links (
                event_id VARCHAR NOT NULL,
                href VARCHAR NOT NULL,
                title VARCHAR NOT NULL DEFAULT '',
                PRIMARY KEY (event_id, href)
            )
        """
        )
