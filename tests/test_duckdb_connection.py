"""Tests for DuckDBConnection — connection lifecycle and recovery."""

from pathlib import Path

from src.adapters.persistence.duckdb_connection import DuckDBConnection


class TestConnectionRecovery:
    def test_returns_working_connection(self, tmp_path: Path) -> None:
        db = DuckDBConnection(str(tmp_path / "test.duckdb"))
        conn = db.get()
        result = conn.execute("SELECT 1").fetchone()
        assert result == (1,)
        db.close()

    def test_recovers_after_broken_connection(self, tmp_path: Path) -> None:
        db = DuckDBConnection(str(tmp_path / "test.duckdb"))

        # Get a good connection and then poison it so the health check fails
        original = db.get()
        original.close()

        # get() should detect the broken connection and return a fresh one
        recovered = db.get()
        result = recovered.execute("SELECT 1").fetchone()
        assert result == (1,)
        db.close()

    def test_same_connection_returned_when_healthy(self, tmp_path: Path) -> None:
        db = DuckDBConnection(str(tmp_path / "test.duckdb"))
        first = db.get()
        second = db.get()
        assert first is second
        db.close()

    def test_broken_connection_removed_from_all_connections(self, tmp_path: Path) -> None:
        db = DuckDBConnection(str(tmp_path / "test.duckdb"))
        original = db.get()
        original.close()

        # After recovery the stale entry should be gone
        db.get()
        assert original not in db._all_connections
        db.close()
