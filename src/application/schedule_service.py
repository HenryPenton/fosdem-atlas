"""Schedule service – browsing and querying the conference schedule."""

import dataclasses
import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from src.domain.models import (
    DayDetail,
    EventDetail,
    EventSearchResult,
    EventSummary,
    GridData,
    OverviewData,
    TracksOverview,
)
from src.domain.ports import EventsRepository

logger = logging.getLogger(__name__)


class ScheduleService:
    """Browsing and querying the conference schedule."""

    def __init__(self, repository: EventsRepository) -> None:
        self._repo = repository
        self._overview_cache: OverviewData | None = None
        self._tracks_cache: TracksOverview | None = None
        self._grid_cache: dict[str, GridData] = {}
        self._day_detail_cache: dict[str, DayDetail] = {}
        self._days_cache: list[str] | None = None
        self._unique_tracks_cache: list[str] | None = None
        self._unique_rooms_cache: list[str] | None = None
        self._event_detail_cache: dict[str, EventDetail] = {}

    def invalidate_cache(self) -> None:
        logger.debug("Invalidating schedule caches")
        self._overview_cache = None
        self._tracks_cache = None
        self._grid_cache.clear()
        self._day_detail_cache.clear()
        self._days_cache = None
        self._unique_tracks_cache = None
        self._unique_rooms_cache = None
        self._event_detail_cache.clear()

    @staticmethod
    def parse_event_ids(ids: str, *, limit: int = 200) -> list[str]:
        """Normalise a comma-separated event-ID string into a bounded list."""
        return [i.strip() for i in ids.split(",") if i.strip()][:limit]

    def resolve_selected_day(self, requested: str) -> str:
        """Return *requested* if it is a known day, else the first available day."""
        days = self.get_unique_days()
        if requested in days:
            return requested
        return days[0] if days else ""

    def get_event_count(self) -> int:
        return self._repo.get_event_count()

    def get_unique_days(self) -> list[str]:
        if self._days_cache is not None:
            return self._days_cache
        self._days_cache = self._repo.get_unique_days()
        return self._days_cache

    def get_unique_tracks(self) -> list[str]:
        if self._unique_tracks_cache is not None:
            return self._unique_tracks_cache
        self._unique_tracks_cache = self._repo.get_unique_tracks()
        return self._unique_tracks_cache

    def get_unique_rooms(self) -> list[str]:
        if self._unique_rooms_cache is not None:
            return self._unique_rooms_cache
        self._unique_rooms_cache = self._repo.get_unique_rooms()
        return self._unique_rooms_cache

    def get_overview(self) -> OverviewData:
        """Home page data."""
        if self._overview_cache is not None:
            return self._overview_cache
        days = self._repo.get_unique_days()
        self._overview_cache = OverviewData(
            event_count=self._repo.get_event_count(),
            days=days,
            day_events={d: len(self._repo.get_events_by_day(d)) for d in days},
            tracks=self._repo.get_unique_tracks(),
            rooms=self._repo.get_unique_rooms(),
        )
        return self._overview_cache

    def get_grid_data(self, day: str) -> GridData:
        """Build grid structure: rooms × hourly time slots for a day."""
        if day in self._grid_cache:
            return self._grid_cache[day]
        days = self._repo.get_unique_days()
        if not days:
            return GridData(
                days=[],
                selected_day="",
                rooms=[],
                time_slots=[],
                grid={},
                room_tracks={},
                room_track_changes={},
            )

        selected_day = day if day in days else days[0]
        rooms = self._repo.get_rooms_by_day(selected_day)
        events = self._repo.get_events_by_day(selected_day)

        result = GridData.from_events(
            events,
            days=days,
            selected_day=selected_day,
            rooms=rooms,
        )
        self._grid_cache[day] = result
        return result

    def get_day_detail(self, day: str) -> DayDetail:
        """Tracks for a day with event counts."""
        if day in self._day_detail_cache:
            return self._day_detail_cache[day]
        tracks = self._repo.get_tracks_by_day(day)
        result = DayDetail(
            day=day,
            tracks=tracks,
            track_events={t: len(self._repo.get_events_by_day_and_track(day, t)) for t in tracks},
        )
        self._day_detail_cache[day] = result
        return result

    def get_events_for_day_and_track(self, day: str, track: str) -> list[EventSummary]:
        return self._repo.get_events_by_day_and_track(day, track)

    def get_all_tracks_with_counts(self) -> TracksOverview:
        """All tracks with their event counts."""
        if self._tracks_cache is not None:
            return self._tracks_cache
        tracks = self._repo.get_unique_tracks()
        self._tracks_cache = TracksOverview(
            tracks=tracks,
            track_events={t: len(self._repo.get_events_by_track(t)) for t in tracks},
        )
        return self._tracks_cache

    def get_events_for_track(self, track: str) -> list[EventSummary]:
        return self._repo.get_events_by_track(track)

    def get_event_detail(self, event_id: str) -> EventDetail | None:
        """Event with its speakers, or None if not found."""
        if event_id in self._event_detail_cache:
            return self._event_detail_cache[event_id]
        event = self._repo.get_event_by_id(event_id)
        if event is None:
            return None
        speakers = self._repo.get_speakers_for_event(event_id)
        links = self._repo.get_links_for_event(event_id)
        result = dataclasses.replace(event, speakers=speakers, links=links)
        if len(self._event_detail_cache) >= 256:
            self._event_detail_cache.pop(next(iter(self._event_detail_cache)))
        self._event_detail_cache[event_id] = result
        return result

    def search_events(
        self, q: str = "", track: str = "", room: str = "", day: str = ""
    ) -> list[EventSearchResult]:
        q, track, room, day = q.strip(), track.strip(), room.strip(), day.strip()
        if q or track or room or day:
            return self._repo.filter_events(q=q, track=track, room=room, day=day)
        return []

    def get_all_events(self, sort: str = "time") -> list[EventSummary]:
        valid_sorts = {"time", "track", "room"}
        sort = sort if sort in valid_sorts else "time"
        return self._repo.get_all_events(sort=sort)

    def get_events_by_ids(self, event_ids: list[str]) -> list[EventDetail]:
        return self._repo.get_events_by_ids(event_ids)

    def build_grid_for_ids(self, event_ids: list[str]) -> dict[str, GridData]:
        """Build per-day GridData structures for a specific set of event IDs."""
        events = self._repo.get_events_by_ids(event_ids)

        # Group events by day
        by_day: dict[str, list[EventDetail]] = defaultdict(list)
        for ev in events:
            if isinstance(ev.start_time, datetime):
                by_day[ev.day].append(ev)

        all_days = sorted(by_day.keys())
        result: dict[str, GridData] = {}
        for day, day_events in sorted(by_day.items()):
            summaries = [ev.to_summary() for ev in day_events]
            rooms = sorted({ev.room for ev in day_events})
            result[day] = GridData.from_events(
                summaries,
                days=all_days,
                selected_day=day,
                rooms=rooms,
            )

        return result

    def build_ical(self, event_ids: list[str]) -> str:
        """Build an iCal calendar string for the given event IDs."""
        events = self._repo.get_events_by_ids(event_ids)
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//FOSDEM Atlas//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]
        for ev in events:
            start = ev.start_time
            if not isinstance(start, datetime):
                continue
            duration = ev.duration_minutes
            end = start + timedelta(minutes=duration)
            uid = f"{ev.id}@fosdem-atlas"
            now = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTAMP:{now}",
                    f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
                    f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
                    f"SUMMARY:{_ical_escape(ev.title)}",
                    f"LOCATION:{_ical_escape(ev.room)}",
                    f"DESCRIPTION:{_ical_escape(ev.track)}",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"


def _ical_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
