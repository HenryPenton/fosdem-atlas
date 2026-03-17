"""DuckDB implementation of the EventRepository port."""

from __future__ import annotations

from datetime import datetime

import duckdb
import yake

from src.adapters.persistence.duckdb_connection import DuckDBConnection
from src.domain.models import (
    ConferenceStats,
    DayCount,
    Event,
    EventDetail,
    EventSummary,
    HeatmapCell,
    RoomCount,
    RoomStats,
    Speaker,
    SpeakerSummary,
    TrackCount,
)

_TOPIC_STOPWORDS = {
    # Conference-specific
    "open source",
    "fosdem",
    "lightning talk",
    "bof",
    "devroom",
    # Presentation terms
    "talk",
    "session",
    "presentation",
    "overview",
    "introduction",
    "update",
    "status update",
    "case study",
    # Too generic for a tech conference
    "software",
    "free software",
    "development",
    "developer",
    "developers",
    "community",
    "application",
    "applications",
    "project",
    "projects",
    "tool",
    "tools",
    "approach",
    "system",
    "systems",
    "user",
    "users",
    "code",
    "data",
    "feature",
    "features",
    "real world",
    "open",
    "source",
    "based",
    "world",
}


class DuckDBEventRepository:
    """DuckDB-backed event repository."""

    def __init__(self, connection: DuckDBConnection) -> None:
        self._db = connection

    def insert_events(self, events: list[Event]) -> int:
        with self._db.lock:
            conn = self._db.get()

            conn.execute("DELETE FROM event_speakers")
            conn.execute("DELETE FROM keywords")
            conn.execute("DELETE FROM events")
            conn.execute("DELETE FROM speakers")

            for event in events:
                fosdem_url = next((lk.href for lk in event.links if "fosdem.org" in lk.href), "")
                conn.execute(
                    """
                    INSERT INTO events
                        (id, title, subtitle, abstract, start_time,
                         duration_minutes, room, track, day, fosdem_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        fosdem_url,
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

            self._extract_keywords(conn, events)

        return len(events)

    def _extract_keywords(self, conn: duckdb.DuckDBPyConnection, events: list[Event]) -> None:
        if not events:
            return

        full_text = ". ".join(f"{e.title}. {e.abstract}" for e in events)
        extractor = yake.KeywordExtractor(lan="en", n=2, top=60, dedupLim=0.5)
        raw_keywords = extractor.extract_keywords(full_text)

        candidates = [
            kw for kw, _ in raw_keywords if kw.lower() not in _TOPIC_STOPWORDS and len(kw) > 2
        ]

        docs = [f"{e.title} {e.abstract}".lower() for e in events]
        results: list[tuple[str, int]] = []
        for term in candidates:
            count = sum(1 for doc in docs if term.lower() in doc)
            if count >= 2:
                results.append((term, count))

        seen_lower: set[str] = set()
        for term, count in sorted(results, key=lambda x: (-x[1], x[0])):
            low = term.lower()
            if low not in seen_lower:
                seen_lower.add(low)
                conn.execute(
                    "INSERT INTO keywords (term, count) VALUES (?, ?)",
                    [term, count],
                )
                if len(seen_lower) >= 30:
                    break

    def get_all_events(self, sort: str = "time") -> list[dict[str, str | int | datetime]]:
        _order_map = {
            "time": "start_time, room",
            "track": "track, start_time",
            "room": "room, start_time",
        }
        order_by = _order_map.get(sort, "start_time, room")
        conn = self._db.get()
        result = conn.execute(
            f"""
            SELECT id, title, start_time, duration_minutes, room, track, day
            FROM events
            ORDER BY day, {order_by}
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

    def get_events_by_track(self, track: str) -> list[dict[str, str | int | datetime]]:
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

    def get_events_by_ids(self, event_ids: list[str]) -> list[dict[str, str | int | datetime]]:
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
                "fosdem_url": row[9],
            }
            for row in result
        ]

    def filter_events(
        self, q: str = "", track: str = "", room: str = "", day: str = ""
    ) -> list[dict[str, str | int | datetime]]:
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

    def get_room_stats(self) -> RoomStats:
        conn = self._db.get()
        events_per_room = conn.execute(
            "SELECT room, COUNT(*) FROM events GROUP BY room ORDER BY COUNT(*) DESC"
        ).fetchall()
        heatmap_rows = conn.execute(
            """
            SELECT day, EXTRACT(hour FROM start_time) AS hour, COUNT(*) AS count
            FROM events
            GROUP BY day, hour
            ORDER BY day, hour
            """
        ).fetchall()
        return RoomStats(
            events_per_room=[
                RoomCount(room=str(row[0]), count=int(row[1])) for row in events_per_room
            ],
            heatmap=[
                HeatmapCell(day=str(row[0]), hour=int(row[1]), count=int(row[2]))
                for row in heatmap_rows
            ],
        )

    def get_stats(self) -> ConferenceStats:
        conn = self._db.get()
        total_events = int((conn.execute("SELECT COUNT(*) FROM events").fetchone() or (0,))[0])
        total_speakers = int((conn.execute("SELECT COUNT(*) FROM speakers").fetchone() or (0,))[0])
        total_tracks = int(
            (conn.execute("SELECT COUNT(DISTINCT track) FROM events").fetchone() or (0,))[0]
        )
        total_rooms = int(
            (conn.execute("SELECT COUNT(DISTINCT room) FROM events").fetchone() or (0,))[0]
        )

        events_per_day = conn.execute(
            "SELECT day, COUNT(*) FROM events GROUP BY day ORDER BY day"
        ).fetchall()
        events_per_track = conn.execute(
            "SELECT track, COUNT(*) FROM events GROUP BY track ORDER BY COUNT(*) DESC"
        ).fetchall()

        return ConferenceStats(
            total_events=total_events,
            total_speakers=total_speakers,
            total_tracks=total_tracks,
            total_rooms=total_rooms,
            events_per_day=[DayCount(day=str(row[0]), count=int(row[1])) for row in events_per_day],
            events_per_track=[
                TrackCount(track=str(row[0]), count=int(row[1])) for row in events_per_track
            ],
        )

    def get_speaker_stats(self) -> dict[str, list[dict[str, str | int | list[str]]]]:
        conn = self._db.get()
        top_speakers = conn.execute(
            """
            SELECT s.id, s.name, COUNT(es.event_id) AS talk_count
            FROM speakers s
            JOIN event_speakers es ON es.speaker_id = s.id
            GROUP BY s.id, s.name
            ORDER BY talk_count DESC, s.name
            LIMIT 20
            """
        ).fetchall()
        multi_track = conn.execute(
            """
            SELECT s.id, s.name, COUNT(DISTINCT e.track) AS track_count,
                   LIST(DISTINCT e.track ORDER BY e.track) AS tracks
            FROM speakers s
            JOIN event_speakers es ON es.speaker_id = s.id
            JOIN events e ON e.id = es.event_id
            GROUP BY s.id, s.name
            HAVING COUNT(DISTINCT e.track) > 1
            ORDER BY track_count DESC, s.name
            """
        ).fetchall()
        return {
            "top_speakers": [
                {"id": str(row[0]), "name": str(row[1]), "talk_count": int(row[2])}
                for row in top_speakers
            ],
            "multi_track_speakers": [
                {
                    "id": str(row[0]),
                    "name": str(row[1]),
                    "track_count": int(row[2]),
                    "tracks": list(row[3]),
                }
                for row in multi_track
            ],
        }

    def get_topic_stats(self) -> dict[str, list[dict[str, str | int]]]:
        conn = self._db.get()
        rows = conn.execute("SELECT term, count FROM keywords ORDER BY count DESC, term").fetchall()
        return {"keywords": [{"term": row[0], "count": int(row[1])} for row in rows]}
