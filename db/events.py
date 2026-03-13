"""Event repository - DuckDB operations for events."""

from datetime import datetime

from db.connection import get_connection
from scraper.fosdem import Event


def insert_events(events: list[Event]) -> int:
    """Insert or replace events in the database.

    Returns:
        Number of events inserted.
    """
    conn = get_connection()

    # Clear existing events and insert fresh (simple approach for now)
    conn.execute("DELETE FROM events")

    for event in events:
        conn.execute(
            """
            INSERT INTO events (id, title, start_time, duration_minutes, room, track, day)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                event.id,
                event.title,
                event.start_time,
                event.duration_minutes,
                event.room,
                event.track,
                event.day,
            ],
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
