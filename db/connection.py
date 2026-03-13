"""DuckDB database connection and schema management."""

from pathlib import Path

import duckdb

from src.config import settings

# Global connection (singleton for embedded DuckDB)
_connection: duckdb.DuckDBPyConnection | None = None


def get_connection() -> duckdb.DuckDBPyConnection:
    """Get or create the DuckDB connection."""
    global _connection
    if _connection is None:
        # Ensure data directory exists
        db_path = Path(settings.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        _connection = duckdb.connect(str(db_path))
        _init_schema(_connection)
    return _connection


def close_connection() -> None:
    """Close the DuckDB connection."""
    global _connection
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
            start_time TIMESTAMP NOT NULL,
            duration_minutes INTEGER NOT NULL,
            room VARCHAR NOT NULL,
            track VARCHAR NOT NULL,
            day DATE NOT NULL
        )
    """
    )
