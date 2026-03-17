"""Schedule service – browsing and querying the conference schedule."""

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from src.domain.ports import EventRepository


class ScheduleService:
    """Browsing and querying the conference schedule."""

    def __init__(self, repository: EventRepository) -> None:
        self._repo = repository

    def get_event_count(self) -> int:
        return self._repo.get_event_count()

    def get_unique_days(self) -> list[str]:
        return self._repo.get_unique_days()

    def get_unique_tracks(self) -> list[str]:
        return self._repo.get_unique_tracks()

    def get_unique_rooms(self) -> list[str]:
        return self._repo.get_unique_rooms()

    def get_overview(self) -> dict[str, Any]:
        """Home page data."""
        days = self._repo.get_unique_days()
        return {
            "event_count": self._repo.get_event_count(),
            "days": days,
            "day_events": {d: len(self._repo.get_events_by_day(d)) for d in days},
            "tracks": self._repo.get_unique_tracks(),
            "rooms": self._repo.get_unique_rooms(),
        }

    def get_grid_data(self, day: str) -> dict[str, Any]:
        """Build grid structure: rooms × time slots for a day."""
        days = self._repo.get_unique_days()
        if not days:
            return {
                "days": [],
                "selected_day": "",
                "rooms": [],
                "time_slots": [],
                "grid": {},
                "grid_rowspans": {},
                "grid_covered": set(),
            }

        selected_day = day if day in days else days[0]
        rooms = self._repo.get_rooms_by_day(selected_day)
        events = self._repo.get_events_by_day(selected_day)

        starts: list[datetime] = []
        ends: list[datetime] = []
        for ev in events:
            st = ev["start_time"]
            if isinstance(st, datetime):
                starts.append(st)
                ends.append(st + timedelta(minutes=int(ev["duration_minutes"])))  # type: ignore[arg-type]

        time_slots: list[datetime] = []
        if starts:
            slot_start = min(starts).replace(minute=(min(starts).minute // 30) * 30, second=0)
            slot_end = max(ends)
            current = slot_start
            while current < slot_end:
                time_slots.append(current)
                current += timedelta(minutes=30)

        grid: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
        for ev in events:
            st = ev["start_time"]
            if not isinstance(st, datetime):
                continue
            slot_key = st.replace(minute=(st.minute // 30) * 30, second=0).strftime("%H:%M")
            grid[slot_key][str(ev["room"])].append(ev)

        # Compute rowspans and covered cells so the template can render proper rowspan= attrs.
        # A cell is "covered" when a previous row's rowspan extends over it — it must be skipped.
        time_slot_keys = [s.strftime("%H:%M") for s in time_slots]
        grid_rowspans: dict[str, dict[str, int]] = {}
        grid_covered: set[tuple[str, str]] = set()

        for i, slot_key in enumerate(time_slot_keys):
            grid_rowspans[slot_key] = {}
            for room in rooms:
                if (slot_key, room) in grid_covered:
                    grid_rowspans[slot_key][room] = 0  # skip this cell
                    continue
                events_here = grid.get(slot_key, {}).get(room, [])
                if events_here:
                    span = max(
                        1,
                        max(math.ceil(int(ev["duration_minutes"]) / 30) for ev in events_here),
                    )
                    for j in range(1, span):
                        if i + j < len(time_slot_keys):
                            grid_covered.add((time_slot_keys[i + j], room))
                    grid_rowspans[slot_key][room] = span
                else:
                    grid_rowspans[slot_key][room] = 1

        return {
            "days": days,
            "selected_day": selected_day,
            "rooms": rooms,
            "time_slots": time_slots,
            "grid": dict(grid),
            "grid_rowspans": grid_rowspans,
            "grid_covered": grid_covered,
        }

    def get_day_detail(self, day: str) -> dict[str, Any]:
        """Tracks for a day with event counts."""
        tracks = self._repo.get_tracks_by_day(day)
        return {
            "day": day,
            "tracks": tracks,
            "track_events": {
                t: len(self._repo.get_events_by_day_and_track(day, t)) for t in tracks
            },
        }

    def get_events_for_day_and_track(
        self, day: str, track: str
    ) -> list[dict[str, str | int | datetime]]:
        return self._repo.get_events_by_day_and_track(day, track)

    def get_all_tracks_with_counts(self) -> dict[str, Any]:
        """All tracks with their event counts."""
        tracks = self._repo.get_unique_tracks()
        return {
            "tracks": tracks,
            "track_events": {t: len(self._repo.get_events_by_track(t)) for t in tracks},
        }

    def get_events_for_track(self, track: str) -> list[dict[str, str | int | datetime]]:
        return self._repo.get_events_by_track(track)

    def get_event_detail(self, event_id: str) -> dict[str, Any] | None:
        """Event with its speakers, or None if not found."""
        event = self._repo.get_event_by_id(event_id)
        if event is None:
            return None
        speakers = self._repo.get_speakers_for_event(event_id)
        return {**event, "speakers": speakers}

    def search_events(
        self, q: str = "", track: str = "", room: str = "", day: str = ""
    ) -> list[dict[str, str | int | datetime]]:
        q, track, room, day = q.strip(), track.strip(), room.strip(), day.strip()
        if q or track or room or day:
            return self._repo.filter_events(q=q, track=track, room=room, day=day)
        return []

    def get_all_events(self, sort: str = "time") -> list[dict[str, str | int | datetime]]:
        valid_sorts = {"time", "track", "room"}
        sort = sort if sort in valid_sorts else "time"
        return self._repo.get_all_events(sort=sort)

    def get_events_by_ids(self, event_ids: list[str]) -> list[dict[str, str | int | datetime]]:
        return self._repo.get_events_by_ids(event_ids)

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
            start = ev.get("start_time")
            if not isinstance(start, datetime):
                continue
            duration = int(ev.get("duration_minutes", 30))  # type: ignore[arg-type]
            end = start + timedelta(minutes=duration)
            uid = f"{ev['id']}@fosdem-explorer"
            now = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")  # noqa: UP017
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTAMP:{now}",
                    f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
                    f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
                    f"SUMMARY:{_ical_escape(str(ev.get('title', '')))}",
                    f"LOCATION:{_ical_escape(str(ev.get('room', '')))}",
                    f"DESCRIPTION:{_ical_escape(str(ev.get('track', '')))}",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"


def _ical_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
