"""Analytics domain models."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DayCount:
    """Event count for a single day."""

    day: str
    count: int


@dataclass(frozen=True)
class TrackCount:
    """Event count for a single track."""

    track: str
    count: int


@dataclass(frozen=True)
class RoomCount:
    """Event count for a single room."""

    room: str
    count: int


@dataclass(frozen=True)
class HeatmapCell:
    """Single cell in the day/hour heatmap."""

    day: str
    hour: int
    count: int


@dataclass(frozen=True)
class RoomStats:
    """Room-level analytics."""

    events_per_room: list[RoomCount] = field(default_factory=list)
    heatmap: list[HeatmapCell] = field(default_factory=list)


@dataclass(frozen=True)
class ConferenceStats:
    """Aggregate conference statistics."""

    total_events: int
    total_speakers: int
    total_tracks: int
    total_rooms: int
    events_per_day: list[DayCount] = field(default_factory=list)
    events_per_track: list[TrackCount] = field(default_factory=list)
