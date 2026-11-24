"""View models for schedule and analytics service results."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from src.domain.models.analytics import (
    ConferenceStats,
    RoomCount,
    RoomStats,
    SpeakerStats,
    TopicStats,
)
from src.domain.models.events import EventSummary

# time-slot key → room name → events in that slot/room
type ScheduleGrid = dict[str, dict[str, list[EventSummary]]]
# room name → ordered list of events
type RoomEventMap = dict[str, list[EventSummary]]
# room name → ordered list of track names
type RoomTracks = dict[str, list[str]]
# slot-key → track name (records where a track change occurs)
type TrackChanges = dict[str, str]
# room name → TrackChanges for that room
type RoomTrackChanges = dict[str, TrackChanges]
# day → hour → event count
type HeatmapGrid = dict[str, dict[int, int]]


@dataclass(frozen=True)
class OverviewData:
    """Home page overview data."""

    event_count: int
    days: list[str]
    day_events: dict[str, int]
    tracks: list[str]
    rooms: list[str]


@dataclass(frozen=True)
class GridData:
    """Schedule grid structure for a single day."""

    days: list[str]
    selected_day: str
    rooms: list[str]
    time_slots: list[datetime]
    grid: ScheduleGrid
    room_tracks: RoomTracks
    room_track_changes: RoomTrackChanges

    @classmethod
    def from_events(
        cls,
        events: list[EventSummary],
        *,
        days: list[str],
        selected_day: str,
        rooms: list[str],
    ) -> GridData:
        """Build a grid by placing *events* into hourly room×time cells."""
        starts: list[datetime] = []
        ends: list[datetime] = []
        for ev in events:
            st = ev.start_time
            if isinstance(st, datetime):
                starts.append(st)
                ends.append(st + timedelta(minutes=ev.duration_minutes))

        time_slots: list[datetime] = []
        if starts:
            slot_start = min(starts).replace(minute=0, second=0)
            slot_end = max(ends)
            current = slot_start
            while current < slot_end:
                time_slots.append(current)
                current += timedelta(hours=1)

        grid: ScheduleGrid = defaultdict(lambda: defaultdict(list))
        for ev in events:
            st = ev.start_time
            if not isinstance(st, datetime):
                continue
            slot_key = st.replace(minute=0, second=0).strftime("%H:%M")
            grid[slot_key][ev.room].append(ev)

        for slot_key in grid:
            for room in grid[slot_key]:
                grid[slot_key][room].sort(key=lambda e: e.start_time)

        room_events_by_room: RoomEventMap = defaultdict(list)
        for ev in events:
            if isinstance(ev.start_time, datetime):
                room_events_by_room[ev.room].append(ev)

        room_tracks_map: RoomTracks = {}
        room_track_changes_map: RoomTrackChanges = {}
        for room in rooms:
            sorted_evs = sorted(room_events_by_room.get(room, []), key=lambda e: e.start_time)
            seen: list[str] = []
            current_track: str | None = None
            changes: TrackChanges = {}
            for ev in sorted_evs:
                track = ev.track
                if not track or track == current_track:
                    continue
                st = ev.start_time
                if not isinstance(st, datetime):
                    continue
                slot_key = st.replace(minute=0, second=0).strftime("%H:%M")
                if current_track is not None:
                    changes[slot_key] = track
                if track not in seen:
                    seen.append(track)
                current_track = track
            room_tracks_map[room] = seen
            room_track_changes_map[room] = changes

        return cls(
            days=days,
            selected_day=selected_day,
            rooms=rooms,
            time_slots=time_slots,
            grid=dict(grid),
            room_tracks=room_tracks_map,
            room_track_changes=room_track_changes_map,
        )


@dataclass(frozen=True)
class DayDetail:
    """Tracks for a day with event counts."""

    day: str
    tracks: list[str]
    track_events: dict[str, int]


@dataclass(frozen=True)
class TracksOverview:
    """All tracks with event counts."""

    tracks: list[str]
    track_events: dict[str, int]


@dataclass(frozen=True)
class AnalyticsData:
    """Full analytics result with computed heatmap."""

    stats: ConferenceStats
    room_stats: RoomStats
    events_per_room: list[RoomCount]
    speaker_stats: SpeakerStats
    topic_stats: TopicStats
    heatmap_days: list[str]
    heatmap_hours: list[int]
    heatmap_grid: HeatmapGrid
    max_heatmap_count: int = field(default=1)

    @classmethod
    def from_raw_stats(
        cls,
        *,
        stats: ConferenceStats,
        room_stats: RoomStats,
        speaker_stats: SpeakerStats,
        topic_stats: TopicStats,
    ) -> AnalyticsData:
        """Build analytics data, computing the heatmap grid from raw cells."""
        heatmap_raw = room_stats.heatmap
        heatmap_days = sorted({item.day for item in heatmap_raw})
        heatmap_hours = sorted({item.hour for item in heatmap_raw})
        heatmap_grid: HeatmapGrid = {day: dict.fromkeys(heatmap_hours, 0) for day in heatmap_days}
        for item in heatmap_raw:
            heatmap_grid[item.day][item.hour] = item.count
        max_heatmap_count = max((item.count for item in heatmap_raw), default=1)

        return cls(
            stats=stats,
            room_stats=room_stats,
            events_per_room=room_stats.events_per_room,
            speaker_stats=speaker_stats,
            topic_stats=topic_stats,
            heatmap_days=heatmap_days,
            heatmap_hours=heatmap_hours,
            heatmap_grid=heatmap_grid,
            max_heatmap_count=max_heatmap_count,
        )
