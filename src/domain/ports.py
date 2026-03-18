"""Ports (interfaces) defining the boundaries of the domain."""

from typing import Protocol

from src.domain.models import (
    ConferenceStats,
    Event,
    EventDetail,
    EventSearchResult,
    EventSummary,
    RoomStats,
    Speaker,
    SpeakerStats,
    SpeakerSummary,
    TopicStats,
)


class IngestionRepository(Protocol):
    """Port for writing events, speakers, and keywords to persistence."""

    def insert_events(self, events: list[Event]) -> int: ...


class EventsRepository(Protocol):
    """Port for event schedule browsing and search."""

    def get_all_events(self, sort: str = "time") -> list[EventSummary]: ...

    def get_event_count(self) -> int: ...

    def get_events_by_day(self, day: str) -> list[EventSummary]: ...

    def get_unique_days(self) -> list[str]: ...

    def get_unique_tracks(self) -> list[str]: ...

    def get_unique_rooms(self) -> list[str]: ...

    def get_rooms_by_day(self, day: str) -> list[str]: ...

    def get_tracks_by_day(self, day: str) -> list[str]: ...

    def get_events_by_day_and_track(self, day: str, track: str) -> list[EventSummary]: ...

    def get_events_by_track(self, track: str) -> list[EventSummary]: ...

    def get_event_by_id(self, event_id: str) -> EventDetail | None: ...

    def get_events_by_ids(self, event_ids: list[str]) -> list[EventDetail]: ...

    def get_speakers_for_event(self, event_id: str) -> list[Speaker]: ...

    def filter_events(
        self, q: str = "", track: str = "", room: str = "", day: str = ""
    ) -> list[EventSearchResult]: ...

    def search_events(self, q: str) -> list[EventSearchResult]: ...


class SpeakersRepository(Protocol):
    """Port for speaker queries."""

    def get_all_speakers(self) -> list[SpeakerSummary]: ...

    def get_speaker_by_id(self, speaker_id: str) -> Speaker | None: ...

    def get_events_by_speaker(self, speaker_id: str) -> list[EventSummary]: ...


class AnalyticsRepository(Protocol):
    """Port for conference analytics and statistics."""

    def get_stats(self) -> ConferenceStats: ...

    def get_room_stats(self) -> RoomStats: ...

    def get_speaker_stats(self) -> SpeakerStats: ...

    def get_topic_stats(self) -> TopicStats: ...


class ScheduleFetcher(Protocol):
    """Port for fetching the conference schedule."""

    def fetch_and_parse(self, url: str) -> list[Event]: ...
