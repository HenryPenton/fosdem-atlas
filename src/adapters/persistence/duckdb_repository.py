"""DuckDB implementation of the EventRepository port."""

from datetime import datetime

from src.adapters.persistence.duckdb_connection import DuckDBConnection
from src.domain.models import Event


class DuckDBEventRepository:
    """DuckDB-backed event repository."""

    def __init__(self, connection: DuckDBConnection) -> None:
        self._db = connection

    def insert_events(self, events: list[Event]) -> int:
        with self._db.lock:
            conn = self._db.get()

            conn.execute("DELETE FROM event_speakers")
            conn.execute("DELETE FROM events")
            conn.execute("DELETE FROM speakers")

            for event in events:
                conn.execute(
                    """
                    INSERT INTO events
                        (id, title, subtitle, abstract, start_time,
                         duration_minutes, room, track, day)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        event.id,
                        event.title,
                        event.subtitle,
                        event.abstract,
                        event.start_time,
                        event.duration_minutes,
                        event.room,
                        event.track,
                        event.day,
                    ],
                )

                for speaker in event.speakers:
                    conn.execute(
                        "INSERT OR IGNORE INTO speakers (id, name) VALUES (?, ?)",
                        [speaker.id, speaker.name],
                    )
                    conn.execute(
                        "INSERT OR IGNORE INTO event_speakers (event_id, speaker_id) VALUES (?, ?)",
                        [event.id, speaker.id],
                    )

        return len(events)

    def get_all_events(self) -> list[dict[str, str | int | datetime]]:
        conn = self._db.get()
        result = conn.execute(
            """
            SELECT id, title, start_time, duration_minutes, room, track, day
            FROM events
            ORDER BY start_time, room
        """
        ).fetchall()

        return [
            {
                "id": row[0],
                "title": row[1],
                "start_time": row[2],
                "duration_minutes": row[3],
                "room": row[4],
                "track": row[5],
                "day": row[6],
            }
            for row in result
        ]

    def get_event_count(self) -> int:
        conn = self._db.get()
        result = conn.execute("SELECT COUNT(*) FROM events").fetchone()
        return int(result[0]) if result else 0

    def get_events_by_day(self, day: str) -> list[dict[str, str | int | datetime]]:
        conn = self._db.get()
        result = conn.execute(
            """
            SELECT id, title, start_time, duration_minutes, room, track, day
            FROM events
            WHERE day = ?
            ORDER BY start_time, room
            """,
            [day],
        ).fetchall()

        return [
            {
                "id": row[0],
                "title": row[1],
                "start_time": row[2],
                "duration_minutes": row[3],
                "room": row[4],
                "track": row[5],
                "day": row[6],
            }
            for row in result
        ]

    def get_unique_days(self) -> list[str]:
        conn = self._db.get()
        result = conn.execute("SELECT DISTINCT day FROM events ORDER BY day").fetchall()
        return [str(row[0]) for row in result]

    def get_unique_tracks(self) -> list[str]:
        conn = self._db.get()
        result = conn.execute("SELECT DISTINCT track FROM events ORDER BY track").fetchall()
        return [str(row[0]) for row in result]

    def get_unique_rooms(self) -> list[str]:
        conn = self._db.get()
        result = conn.execute("SELECT DISTINCT room FROM events ORDER BY room").fetchall()
        return [str(row[0]) for row in result]

    def get_tracks_by_day(self, day: str) -> list[str]:
        conn = self._db.get()
        result = conn.execute(
            "SELECT DISTINCT track FROM events WHERE day = ? ORDER BY track",
            [day],
        ).fetchall()
        return [str(row[0]) for row in result]

    def get_events_by_day_and_track(
        self, day: str, track: str
    ) -> list[dict[str, str | int | datetime]]:
        conn = self._db.get()
        result = conn.execute(
            """
            SELECT id, title, subtitle, abstract, start_time,
                   duration_minutes, room, track, day
            FROM events
            WHERE day = ? AND track = ?
            ORDER BY start_time, room
            """,
            [day, track],
        ).fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "subtitle": row[2],
                "abstract": row[3],
                "start_time": row[4],
                "duration_minutes": row[5],
                "room": row[6],
                "track": row[7],
                "day": row[8],
            }
            for row in result
        ]

    def get_speakers_for_event(self, event_id: str) -> list[dict[str, str]]:
        conn = self._db.get()
        result = conn.execute(
            """
            SELECT s.id, s.name
            FROM speakers s
            JOIN event_speakers es ON es.speaker_id = s.id
            WHERE es.event_id = ?
            ORDER BY s.name
            """,
            [event_id],
        ).fetchall()
        return [{"id": row[0], "name": row[1]} for row in result]

    def search_events(self, q: str) -> list[dict[str, str | int | datetime]]:
        conn = self._db.get()
        pattern = f"%{q}%"
        result = conn.execute(
            """
            SELECT id, title, abstract, start_time, duration_minutes, room, track, day
            FROM events
            WHERE title ILIKE ? OR abstract ILIKE ?
            ORDER BY start_time, room
            LIMIT 100
            """,
            [pattern, pattern],
        ).fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "abstract": row[2],
                "start_time": row[3],
                "duration_minutes": row[4],
                "room": row[5],
                "track": row[6],
                "day": row[7],
            }
            for row in result
        ]
