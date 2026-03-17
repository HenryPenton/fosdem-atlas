"""Data Transfer Objects for the JSON API."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SpeakerListItemDTO:
    """Speaker summary for list endpoints."""

    id: str
    name: str
    talk_count: int


@dataclass(frozen=True)
class EventSummaryDTO:
    """Event summary for nested responses."""

    id: str
    title: str
    subtitle: str
    start_time: datetime
    duration_minutes: int
    room: str
    track: str
    day: str


@dataclass(frozen=True)
class SpeakerDetailDTO:
    """Speaker with events for detail endpoint."""

    id: str
    name: str
    events: list[EventSummaryDTO]
