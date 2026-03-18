"""DuckDB implementation of the SpeakersRepository port."""

from __future__ import annotations

from src.adapters.persistence.duckdb_connection import DuckDBConnection
from src.domain.models import EventSummary, Speaker, SpeakerSummary


class DuckDBSpeakersRepository:
    """DuckDB implementation of SpeakersRepository — speaker queries."""

    def __init__(self, connection: DuckDBConnection) -> None:
        self._db = connection

    def get_all_speakers(self) -> list[SpeakerSummary]:
        conn = self._db.get()
        result = conn.execute(
            """
            SELECT s.id, s.name, COUNT(es.event_id) AS talk_count
            FROM speakers s
            JOIN event_speakers es ON es.speaker_id = s.id
            GROUP BY s.id, s.name
            ORDER BY s.name
            """
        ).fetchall()
        return [
            SpeakerSummary(id=str(row[0]), name=str(row[1]), talk_count=int(row[2]))
            for row in result
        ]

    def get_speaker_by_id(self, speaker_id: str) -> Speaker | None:
        conn = self._db.get()
        row = conn.execute(
            "SELECT id, name FROM speakers WHERE id = ?",
            [speaker_id],
        ).fetchone()
        if row is None:
            return None
        return Speaker(id=str(row[0]), name=str(row[1]))

    def get_events_by_speaker(self, speaker_id: str) -> list[EventSummary]:
        conn = self._db.get()
        result = conn.execute(
            """
            SELECT e.id, e.title, e.subtitle, e.start_time,
                   e.duration_minutes, e.room, e.track, e.day
            FROM events e
            JOIN event_speakers es ON es.event_id = e.id
            WHERE es.speaker_id = ?
            ORDER BY e.day, e.start_time
            """,
            [speaker_id],
        ).fetchall()
        return [
            EventSummary(
                id=str(row[0]),
                title=str(row[1]),
                subtitle=str(row[2]),
                start_time=row[3],
                duration_minutes=int(row[4]),
                room=str(row[5]),
                track=str(row[6]),
                day=str(row[7]),
            )
            for row in result
        ]
