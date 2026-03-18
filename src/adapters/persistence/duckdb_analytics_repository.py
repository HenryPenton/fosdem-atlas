"""DuckDB implementation of the AnalyticsRepository port."""

from __future__ import annotations

from src.adapters.persistence.duckdb_connection import DuckDBConnection
from src.domain.models import (
    ConferenceStats,
    DayCount,
    HeatmapCell,
    KeywordCount,
    MultiTrackSpeaker,
    RoomCount,
    RoomStats,
    SpeakerStats,
    TopicStats,
    TopSpeaker,
    TrackCount,
)


class DuckDBAnalyticsRepository:
    """DuckDB implementation of AnalyticsRepository — conference statistics."""

    def __init__(self, connection: DuckDBConnection) -> None:
        self._db = connection

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

    def get_speaker_stats(self) -> SpeakerStats:
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
        return SpeakerStats(
            top_speakers=[
                TopSpeaker(id=str(row[0]), name=str(row[1]), talk_count=int(row[2]))
                for row in top_speakers
            ],
            multi_track_speakers=[
                MultiTrackSpeaker(
                    id=str(row[0]),
                    name=str(row[1]),
                    track_count=int(row[2]),
                    tracks=list(row[3]),
                )
                for row in multi_track
            ],
        )

    def get_topic_stats(self) -> TopicStats:
        conn = self._db.get()
        rows = conn.execute("SELECT term, count FROM keywords ORDER BY count DESC, term").fetchall()
        return TopicStats(
            keywords=[KeywordCount(term=str(row[0]), count=int(row[1])) for row in rows]
        )
