"""DuckDB implementation of the EventsRepository port."""

from __future__ import annotations

from src.adapters.persistence.duckdb_connection import DuckDBConnection
from src.domain.models import (
    EventDetail,
    EventSearchResult,
    EventSummary,
    Speaker,
)


class DuckDBEventsRepository:
    """DuckDB implementation of EventsRepository — schedule browsing and search."""

    def __init__(self, connection: DuckDBConnection) -> None:
        self._db = connection

    def get_all_events(self, sort: str = "time") -> list[EventSummary]:
        _order_map = {
            "time": "start_time, room",
            "track": "track, start_time",
            "room": "room, start_time",
        }
        order_by = _order_map.get(sort, "start_time, room")
        conn = self._db.get()
        result = conn.execute(
            f"""
            SELECT id, title, subtitle, abstract, start_time, duration_minutes, room, track, day
            FROM events
            ORDER BY day, {order_by}
            """
        ).fetchall()

        return [
            EventSummary(
                id=str(row[0]),
                title=str(row[1]),
                subtitle=str(row[2]),
                abstract=str(row[3]),
                start_time=row[4],
                duration_minutes=int(row[5]),
                room=str(row[6]),
                track=str(row[7]),
                day=str(row[8]),
            )
            for row in result
        ]

    def get_event_count(self) -> int:
        conn = self._db.get()
        result = conn.execute("SELECT COUNT(*) FROM events").fetchone()
        return int(result[0]) if result else 0

    def get_events_by_day(self, day: str) -> list[EventSummary]:
        conn = self._db.get()
        result = conn.execute(
            """
            SELECT id, title, subtitle, start_time, duration_minutes, room, track, day
            FROM events
            WHERE day = ?
            ORDER BY start_time, room
            """,
            [day],
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

    def get_rooms_by_day(self, day: str) -> list[str]:
        conn = self._db.get()
        result = conn.execute(
            "SELECT DISTINCT room FROM events WHERE day = ? ORDER BY room",
            [day],
        ).fetchall()
        return [str(row[0]) for row in result]

    def get_tracks_by_day(self, day: str) -> list[str]:
        conn = self._db.get()
        result = conn.execute(
            "SELECT DISTINCT track FROM events WHERE day = ? ORDER BY track",
            [day],
        ).fetchall()
        return [str(row[0]) for row in result]

    def get_events_by_day_and_track(self, day: str, track: str) -> list[EventSummary]:
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
            EventSummary(
                id=str(row[0]),
                title=str(row[1]),
                subtitle=str(row[2]),
                abstract=str(row[3]),
                start_time=row[4],
                duration_minutes=int(row[5]),
                room=str(row[6]),
                track=str(row[7]),
                day=str(row[8]),
            )
            for row in result
        ]

    def get_events_by_track(self, track: str) -> list[EventSummary]:
        conn = self._db.get()
        result = conn.execute(
            """
            SELECT id, title, subtitle, abstract, start_time,
                   duration_minutes, room, track, day
            FROM events
            WHERE track = ?
            ORDER BY day, start_time, room
            """,
            [track],
        ).fetchall()
        return [
            EventSummary(
                id=str(row[0]),
                title=str(row[1]),
                subtitle=str(row[2]),
                abstract=str(row[3]),
                start_time=row[4],
                duration_minutes=int(row[5]),
                room=str(row[6]),
                track=str(row[7]),
                day=str(row[8]),
            )
            for row in result
        ]

    def get_speakers_for_event(self, event_id: str) -> list[Speaker]:
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
        return [Speaker(id=str(row[0]), name=str(row[1])) for row in result]

    def get_event_by_id(self, event_id: str) -> EventDetail | None:
        conn = self._db.get()
        row = conn.execute(
            """
            SELECT id, title, subtitle, abstract, start_time,
                   duration_minutes, room, track, day, fosdem_url
            FROM events
            WHERE id = ?
            """,
            [event_id],
        ).fetchone()
        if row is None:
            return None
        return EventDetail(
            id=str(row[0]),
            title=str(row[1]),
            subtitle=str(row[2]),
            abstract=str(row[3]),
            start_time=row[4],
            duration_minutes=int(row[5]),
            room=str(row[6]),
            track=str(row[7]),
            day=str(row[8]),
            fosdem_url=str(row[9]),
        )

    def get_events_by_ids(self, event_ids: list[str]) -> list[EventDetail]:
        if not event_ids:
            return []
        conn = self._db.get()
        placeholders = ", ".join("?" for _ in event_ids)
        result = conn.execute(
            f"""
            SELECT id, title, subtitle, abstract, start_time,
                   duration_minutes, room, track, day, fosdem_url
            FROM events
            WHERE id IN ({placeholders})
            ORDER BY day, start_time, room
            """,
            event_ids,
        ).fetchall()
        return [
            EventDetail(
                id=str(row[0]),
                title=str(row[1]),
                subtitle=str(row[2]),
                abstract=str(row[3]),
                start_time=row[4],
                duration_minutes=int(row[5]),
                room=str(row[6]),
                track=str(row[7]),
                day=str(row[8]),
                fosdem_url=str(row[9]),
            )
            for row in result
        ]

    def filter_events(
        self, q: str = "", track: str = "", room: str = "", day: str = ""
    ) -> list[EventSearchResult]:
        conn = self._db.get()
        conditions: list[str] = []
        params: list[str] = []

        if q:
            conditions.append("(title ILIKE ? OR abstract ILIKE ?)")
            pattern = f"%{q}%"
            params.extend([pattern, pattern])

        if track:
            conditions.append("track = ?")
            params.append(track)

        if room:
            conditions.append("room = ?")
            params.append(room)

        if day:
            conditions.append("day = ?")
            params.append(day)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        result = conn.execute(
            f"""
            SELECT id, title, abstract, start_time, duration_minutes, room, track, day
            FROM events
            {where}
            ORDER BY start_time, room
            LIMIT 200
            """,
            params,
        ).fetchall()
        return [
            EventSearchResult(
                id=str(row[0]),
                title=str(row[1]),
                abstract=str(row[2]),
                start_time=row[3],
                duration_minutes=int(row[4]),
                room=str(row[5]),
                track=str(row[6]),
                day=str(row[7]),
            )
            for row in result
        ]

    def search_events(self, q: str) -> list[EventSearchResult]:
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
            EventSearchResult(
                id=str(row[0]),
                title=str(row[1]),
                abstract=str(row[2]),
                start_time=row[3],
                duration_minutes=int(row[4]),
                room=str(row[5]),
                track=str(row[6]),
                day=str(row[7]),
            )
            for row in result
        ]
