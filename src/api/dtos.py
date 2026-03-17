"""Data Transfer Objects for the JSON API."""

from dataclasses import dataclass, field
from datetime import datetime

# ── Event DTOs ──────────────────────────────────────────────


@dataclass(frozen=True)
class EventSummaryDTO:
    """Event summary for list endpoints."""

    id: str
    title: str
    subtitle: str
    start_time: datetime
    duration_minutes: int
    room: str
    track: str
    day: str
    abstract: str = ""


@dataclass(frozen=True)
class EventSearchResultDTO:
    """Event returned from search or filter queries."""

    id: str
    title: str
    abstract: str
    start_time: datetime
    duration_minutes: int
    room: str
    track: str
    day: str


@dataclass(frozen=True)
class LinkDTO:
    """A link associated with an event."""

    href: str
    title: str


@dataclass(frozen=True)
class SpeakerDTO:
    """Speaker nested inside an event detail."""

    id: str
    name: str


@dataclass(frozen=True)
class EventDetailDTO:
    """Full event detail including speakers."""

    id: str
    title: str
    subtitle: str
    abstract: str
    start_time: datetime
    duration_minutes: int
    room: str
    track: str
    day: str
    fosdem_url: str
    speakers: list[SpeakerDTO] = field(default_factory=list)


# ── Speaker DTOs ────────────────────────────────────────────


@dataclass(frozen=True)
class SpeakerListItemDTO:
    """Speaker summary for list endpoints."""

    id: str
    name: str
    talk_count: int


@dataclass(frozen=True)
class SpeakerDetailDTO:
    """Speaker with events for detail endpoint."""

    id: str
    name: str
    events: list[EventSummaryDTO]


# ── Schedule DTOs ───────────────────────────────────────────


@dataclass(frozen=True)
class DayDetailDTO:
    """Tracks for a day with event counts."""

    day: str
    tracks: list[str]
    track_event_counts: dict[str, int]


@dataclass(frozen=True)
class DayTrackEventsDTO:
    """Events for a specific day and track."""

    day: str
    track: str
    events: list[EventSummaryDTO]


@dataclass(frozen=True)
class TrackSummaryDTO:
    """Track name with event count."""

    name: str
    event_count: int


@dataclass(frozen=True)
class TrackDetailDTO:
    """Track with its events."""

    track: str
    events: list[EventSummaryDTO]


# ── Analytics DTOs ──────────────────────────────────────────


@dataclass(frozen=True)
class DayCountDTO:
    day: str
    count: int


@dataclass(frozen=True)
class TrackCountDTO:
    track: str
    count: int


@dataclass(frozen=True)
class RoomCountDTO:
    room: str
    count: int


@dataclass(frozen=True)
class HeatmapCellDTO:
    day: str
    hour: int
    count: int


@dataclass(frozen=True)
class RoomStatsDTO:
    events_per_room: list[RoomCountDTO] = field(default_factory=list)
    heatmap: list[HeatmapCellDTO] = field(default_factory=list)


@dataclass(frozen=True)
class TopSpeakerDTO:
    id: str
    name: str
    talk_count: int


@dataclass(frozen=True)
class MultiTrackSpeakerDTO:
    id: str
    name: str
    track_count: int
    tracks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SpeakerStatsDTO:
    top_speakers: list[TopSpeakerDTO] = field(default_factory=list)
    multi_track_speakers: list[MultiTrackSpeakerDTO] = field(default_factory=list)


@dataclass(frozen=True)
class KeywordCountDTO:
    term: str
    count: int


@dataclass(frozen=True)
class TopicStatsDTO:
    keywords: list[KeywordCountDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ConferenceStatsDTO:
    total_events: int
    total_speakers: int
    total_tracks: int
    total_rooms: int
    events_per_day: list[DayCountDTO] = field(default_factory=list)
    events_per_track: list[TrackCountDTO] = field(default_factory=list)


@dataclass(frozen=True)
class AnalyticsDTO:
    stats: ConferenceStatsDTO
    room_stats: RoomStatsDTO
    speaker_stats: SpeakerStatsDTO
    topic_stats: TopicStatsDTO


# ── Health DTO ──────────────────────────────────────────────


@dataclass(frozen=True)
class HealthDTO:
    status: str
    version: str
    events: int
