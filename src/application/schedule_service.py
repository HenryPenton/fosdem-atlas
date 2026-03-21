"""Schedule service – browsing and querying the conference schedule."""

import dataclasses
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from src.domain.models import (
    DayDetail,
    EventDetail,
    EventSearchResult,
    EventSummary,
    GridData,
    OverviewData,
    RoomEventMap,
    RoomTrackChanges,
    RoomTracks,
    ScheduleGrid,
    TrackChanges,
    TracksOverview,
)
from src.domain.ports import EventsRepository


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
        self._overview_cache = None
        self._tracks_cache = None
        self._grid_cache.clear()
        self._day_detail_cache.clear()
        self._days_cache = None
        self._unique_tracks_cache = None
        self._unique_rooms_cache = None
        self._event_detail_cache.clear()

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

        starts: list[datetime] = []
        ends: list[datetime] = []
        for ev in events:
            st = ev.start_time
            if isinstance(st, datetime):
                starts.append(st)
                ends.append(st + timedelta(minutes=ev.duration_minutes))

        time_slots: list[datetime] = []
        if starts:
            slot_start = min(starts).replace(minute=0, second=0)
            slot_end = max(ends)
            current = slot_start
            while current < slot_end:
                time_slots.append(current)
                current += timedelta(hours=1)

        # Place each event in the hour of its start time
        grid: ScheduleGrid = defaultdict(lambda: defaultdict(list))
        for ev in events:
            st = ev.start_time
            if not isinstance(st, datetime):
                continue
            slot_key = st.replace(minute=0, second=0).strftime("%H:%M")
            grid[slot_key][ev.room].append(ev)

        # Sort events within each cell by start time
        for slot_key in grid:
            for room in grid[slot_key]:
                grid[slot_key][room].sort(key=lambda e: e.start_time)

        # Build per-room ordered track list and change-point markers
        room_events_by_room: RoomEventMap = defaultdict(list)
        for ev in events:
            if isinstance(ev.start_time, datetime):
                room_events_by_room[ev.room].append(ev)

        room_tracks: RoomTracks = {}
        room_track_changes: RoomTrackChanges = {}

        for room in rooms:
            sorted_evs = sorted(room_events_by_room.get(room, []), key=lambda e: e.start_time)
            seen: list[str] = []
            current_track: str | None = None
            changes: TrackChanges = {}
            for ev in sorted_evs:
                track = ev.track
                if not track or track == current_track:
                    continue
                st = ev.start_time
                if not isinstance(st, datetime):
                    continue
                slot_key = st.replace(minute=0, second=0).strftime("%H:%M")
                if current_track is not None:
                    changes[slot_key] = track
                if track not in seen:
                    seen.append(track)
                current_track = track
            room_tracks[room] = seen
            room_track_changes[room] = changes

        result = GridData(
            days=days,
            selected_day=selected_day,
            rooms=rooms,
            time_slots=time_slots,
            grid=dict(grid),
            room_tracks=room_tracks,
            room_track_changes=room_track_changes,
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
        result = dataclasses.replace(event, speakers=speakers)
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

        result: dict[str, GridData] = {}
        for day, day_events in sorted(by_day.items()):
            rooms = sorted({ev.room for ev in day_events})

            starts = [ev.start_time for ev in day_events if isinstance(ev.start_time, datetime)]
            ends = [
                ev.start_time + timedelta(minutes=ev.duration_minutes)
                for ev in day_events
                if isinstance(ev.start_time, datetime)
            ]

            time_slots: list[datetime] = []
            if starts:
                slot_start = min(starts).replace(minute=0, second=0)
                slot_end = max(ends)
                current = slot_start
                while current < slot_end:
                    time_slots.append(current)
                    current += timedelta(hours=1)

            grid: ScheduleGrid = defaultdict(lambda: defaultdict(list))
            for ev in day_events:
                st = ev.start_time
                if not isinstance(st, datetime):
                    continue
                slot_key = st.replace(minute=0, second=0).strftime("%H:%M")
                # EventDetail is not an EventSummary, build a compatible summary
                summary = EventSummary(
                    id=ev.id,
                    title=ev.title,
                    subtitle=ev.subtitle,
                    start_time=ev.start_time,
                    duration_minutes=ev.duration_minutes,
                    room=ev.room,
                    track=ev.track,
                    day=ev.day,
                    abstract=ev.abstract,
                )
                grid[slot_key][ev.room].append(summary)

            for slot_key in grid:
                for room in grid[slot_key]:
                    grid[slot_key][room].sort(key=lambda e: e.start_time)

            room_events_by_room: RoomEventMap = defaultdict(list)
            for ev in day_events:
                if isinstance(ev.start_time, datetime):
                    summary = EventSummary(
                        id=ev.id,
                        title=ev.title,
                        subtitle=ev.subtitle,
                        start_time=ev.start_time,
                        duration_minutes=ev.duration_minutes,
                        room=ev.room,
                        track=ev.track,
                        day=ev.day,
                        abstract=ev.abstract,
                    )
                    room_events_by_room[ev.room].append(summary)

            room_tracks: RoomTracks = {}
            room_track_changes: RoomTrackChanges = {}
            for room in rooms:
                sorted_evs = sorted(room_events_by_room.get(room, []), key=lambda e: e.start_time)
                seen: list[str] = []
                current_track: str | None = None
                changes: TrackChanges = {}
                for sevt in sorted_evs:
                    track = sevt.track
                    if not track or track == current_track:
                        continue
                    st = sevt.start_time
                    if not isinstance(st, datetime):
                        continue
                    slot_key = st.replace(minute=0, second=0).strftime("%H:%M")
                    if current_track is not None:
                        changes[slot_key] = track
                    if track not in seen:
                        seen.append(track)
                    current_track = track
                room_tracks[room] = seen
                room_track_changes[room] = changes

            result[day] = GridData(
                days=sorted(by_day.keys()),
                selected_day=day,
                rooms=rooms,
                time_slots=time_slots,
                grid=dict(grid),
                room_tracks=room_tracks,
                room_track_changes=room_track_changes,
            )

        return result

    def build_ical(self, event_ids: list[str]) -> str:
        """Build an iCal calendar string for the given event IDs."""
        events = self._repo.get_events_by_ids(event_ids)
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//FOSDEM Explorer//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]
        for ev in events:
            start = ev.start_time
            if not isinstance(start, datetime):
                continue
            duration = ev.duration_minutes
            end = start + timedelta(minutes=duration)
            uid = f"{ev.id}@fosdem-explorer"
            now = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")  # noqa: UP017
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
