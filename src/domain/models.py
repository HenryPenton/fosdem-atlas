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
