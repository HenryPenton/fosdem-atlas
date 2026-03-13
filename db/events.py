"""Event repository - DuckDB operations for events."""

from datetime import datetime

from db.connection import db_lock, get_connection
from scraper.fosdem import Event


def insert_events(events: list[Event]) -> int:
    """Insert or replace events in the database.

    Holds the DB lock for the entire operation so readers never see
    a partially-cleared state.

    Returns:
        Number of events inserted.
    """
    with db_lock():
        conn = get_connection()

        conn.execute("DELETE FROM event_speakers")
        conn.execute("DELETE FROM events")
        conn.execute("DELETE FROM speakers")

        for event in events:
            conn.execute(
                """
                INSERT INTO events (id, title, subtitle, abstract, start_time, duration_minutes, room, track, day)
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


def get_all_events() -> list[dict[str, str | int | datetime]]:
    """Get all events ordered by start time."""
    conn = get_connection()
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


def get_event_count() -> int:
    """Get total number of events."""
    conn = get_connection()
    result = conn.execute("SELECT COUNT(*) FROM events").fetchone()
    return int(result[0]) if result else 0


def get_events_by_day(day: str) -> list[dict[str, str | int | datetime]]:
    """Get events for a specific day."""
    conn = get_connection()
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


def get_unique_days() -> list[str]:
    """Get list of unique days in the schedule."""
    conn = get_connection()
    result = conn.execute(
        """
        SELECT DISTINCT day FROM events ORDER BY day
    """
    ).fetchall()
    return [str(row[0]) for row in result]


def get_unique_tracks() -> list[str]:
    """Get list of unique tracks."""
    conn = get_connection()
    result = conn.execute(
        """
        SELECT DISTINCT track FROM events ORDER BY track
    """
    ).fetchall()
    return [str(row[0]) for row in result]


def get_unique_rooms() -> list[str]:
    """Get list of unique rooms."""
    conn = get_connection()
    result = conn.execute(
        """
        SELECT DISTINCT room FROM events ORDER BY room
    """
    ).fetchall()
    return [str(row[0]) for row in result]


def get_speakers_for_event(event_id: str) -> list[dict[str, str]]:
    """Get speakers for a specific event."""
    conn = get_connection()
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
