"""FOSDEM schedule scraper - fetches and parses the Pentabarf XML feed."""

from dataclasses import dataclass
from datetime import datetime

import httpx
from lxml import etree


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


def fetch_schedule_xml(url: str) -> bytes:
    """Fetch the FOSDEM schedule XML."""
    response = httpx.get(url, timeout=30.0, follow_redirects=True)
    response.raise_for_status()
    content: bytes = response.content
    return content


def parse_schedule(xml_content: bytes) -> list[Event]:
    """Parse the Pentabarf XML schedule into Event objects."""
    root = etree.fromstring(xml_content)
    events: list[Event] = []

    for day in root.findall(".//day"):
        day_date = day.get("date", "")

        for room in day.findall("room"):
            room_name = room.get("name", "")

            for event_elem in room.findall("event"):
                event_id = event_elem.get("id", "")

                # Extract text fields
                title = _get_text(event_elem, "title")
                track = _get_text(event_elem, "track")
                start_str = _get_text(event_elem, "start")
                duration_str = _get_text(event_elem, "duration")

                # Parse start time
                start_time = _parse_datetime(day_date, start_str)

                # Parse duration (format: HH:MM)
                duration_minutes = _parse_duration(duration_str)

                events.append(
                    Event(
                        id=event_id,
                        title=title,
                        start_time=start_time,
                        duration_minutes=duration_minutes,
                        room=room_name,
                        track=track,
                        day=day_date,
                    )
                )

    return events


def _get_text(element: etree._Element, tag: str) -> str:
    """Get text content of a child element."""
    child = element.find(tag)
    if child is not None and child.text:
        return str(child.text).strip()
    return ""


def _parse_datetime(date_str: str, time_str: str) -> datetime:
    """Parse date and time strings into datetime."""
    if not date_str or not time_str:
        return datetime.min
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        return datetime.min


def _parse_duration(duration_str: str) -> int:
    """Parse duration string (HH:MM) into minutes."""
    if not duration_str or ":" not in duration_str:
        return 0
    try:
        hours, minutes = duration_str.split(":")
        return int(hours) * 60 + int(minutes)
    except ValueError:
        return 0


def scrape(url: str | None = None) -> list[Event]:
    """Fetch and parse the FOSDEM schedule.

    Args:
        url: Schedule XML URL. Defaults to FOSDEM 2026.

    Returns:
        List of parsed events.
    """
    if url is None:
        url = "https://fosdem.org/2026/schedule/xml"

    xml_content = fetch_schedule_xml(url)
    return parse_schedule(xml_content)
