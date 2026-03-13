"""Ports (interfaces) defining the boundaries of the domain."""

from datetime import datetime
from typing import Protocol

from src.domain.models import Event


class EventRepository(Protocol):
    """Port for event persistence."""

    def insert_events(self, events: list[Event]) -> int: ...

    def get_all_events(self) -> list[dict[str, str | int | datetime]]: ...

    def get_event_count(self) -> int: ...

    def get_events_by_day(self, day: str) -> list[dict[str, str | int | datetime]]: ...

    def get_unique_days(self) -> list[str]: ...

    def get_unique_tracks(self) -> list[str]: ...

    def get_unique_rooms(self) -> list[str]: ...

    def get_speakers_for_event(self, event_id: str) -> list[dict[str, str]]: ...


class ScheduleFetcher(Protocol):
    """Port for fetching the conference schedule."""

    def fetch_and_parse(self, url: str) -> list[Event]: ...
