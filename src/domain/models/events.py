"""Event domain models."""

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.models.speakers import Speaker


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
    abstract: str = ""


@dataclass(frozen=True)
class EventSearchResult:
    """Read model: event returned from search or filter queries."""

    id: str
    title: str
    abstract: str
    start_time: datetime
    duration_minutes: int
    room: str
    track: str
    day: str


@dataclass(frozen=True)
class EventDetail:
    """Read model: full event detail including speakers."""

    id: str
    title: str
    subtitle: str
    abstract: str
    start_time: datetime
    duration_minutes: int
    room: str
    track: str
    day: str
    speakers: list[Speaker] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
