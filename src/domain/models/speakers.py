"""Speaker domain models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.models.events import EventSummary


@dataclass
class Speaker:
    """A speaker at FOSDEM."""

    id: str
    name: str
    bio: str = ""


@dataclass(frozen=True)
class SpeakerSummary:
    """Read model: speaker with talk count for listings."""

    id: str
    name: str
    talk_count: int


@dataclass(frozen=True)
class SpeakerDetail:
    """Read model: speaker with their events."""

    id: str
    name: str
    bio: str
    events: list[EventSummary]
