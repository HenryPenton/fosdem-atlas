"""View models for schedule and analytics service results."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeAlias

from src.domain.models.analytics import (
    ConferenceStats,
    RoomCount,
    RoomStats,
    SpeakerStats,
    TopicStats,
)
from src.domain.models.events import EventSummary

# time-slot key → room name → events in that slot/room
ScheduleGrid: TypeAlias = dict[str, dict[str, list[EventSummary]]]
# time-slot key → room name → rowspan count
RowspanGrid: TypeAlias = dict[str, dict[str, int]]
# room name → ordered list of events
RoomEventMap: TypeAlias = dict[str, list[EventSummary]]
# room name → ordered list of track names
RoomTracks: TypeAlias = dict[str, list[str]]
# slot-key → track name (records where a track change occurs)
TrackChanges: TypeAlias = dict[str, str]
# room name → TrackChanges for that room
RoomTrackChanges: TypeAlias = dict[str, TrackChanges]
# day → hour → event count
HeatmapGrid: TypeAlias = dict[str, dict[int, int]]


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
    grid_rowspans: RowspanGrid
    grid_covered: set[tuple[str, str]]
    room_tracks: RoomTracks
    room_track_changes: RoomTrackChanges


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
