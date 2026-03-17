"""Domain models for FOSDEM Explorer."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Speaker:
    """A speaker at FOSDEM."""

    id: str
    name: str


@dataclass
class Link:
    """A link associated with an event."""

    href: str
    title: str


@dataclass
class Event:
    """A FOSDEM event/talk."""

    id: str
    title: str
    start_time: datetime
    duration_minutes: int
    room: str
    track: str
    day: str
    subtitle: str = ""
    abstract: str = ""
    speakers: list[Speaker] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)


@dataclass(frozen=True)
class SpeakerSummary:
    """Read model: speaker with talk count for listings."""

    id: str
    name: str
    talk_count: int


@dataclass(frozen=True)
class EventSummary:
    """Read model: event summary."""

    id: str
    title: str
    subtitle: str
    start_time: datetime
    duration_minutes: int
    room: str
    track: str
    day: str


@dataclass(frozen=True)
class SpeakerDetail:
    """Read model: speaker with their events."""

    id: str
    name: str
    events: list[EventSummary]
