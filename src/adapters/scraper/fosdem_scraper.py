"""FOSDEM schedule fetcher - adapter implementing the ScheduleFetcher port."""

from datetime import datetime

import httpx
from lxml import etree

from src.domain.models import Event, Link, Speaker


class FosdemScheduleFetcher:
    """Fetches and parses the FOSDEM Pentabarf XML schedule."""

    def fetch_and_parse(self, url: str) -> list[Event]:
        """Fetch the schedule XML and parse it into domain events."""
        xml_content = self._fetch(url)
        return self._parse(xml_content)

    def _fetch(self, url: str) -> bytes:
        response = httpx.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        content: bytes = response.content
        return content

    def _parse(self, xml_content: bytes) -> list[Event]:
        root = etree.fromstring(xml_content)  # noqa: S320
        events: list[Event] = []

        for day in root.findall(".//day"):
            day_date = day.get("date", "")

            for room in day.findall("room"):
                room_name = room.get("name", "")

                for event_elem in room.findall("event"):
                    event_id = event_elem.get("id", "")

                    title = self._text(event_elem, "title")
                    subtitle = self._text(event_elem, "subtitle")
                    abstract = self._text(event_elem, "abstract")
                    track = self._text(event_elem, "track")
                    start_str = self._text(event_elem, "start")
                    duration_str = self._text(event_elem, "duration")

                    start_time = self._parse_datetime(day_date, start_str)
                    duration_minutes = self._parse_duration(duration_str)

                    speakers = [
                        Speaker(id=p.get("id", ""), name=p.text.strip())
                        for p in event_elem.findall(".//person")
                        if p.text and p.text.strip()
                    ]
                    links = [
                        Link(
                            href=lk.get("href", ""),
                            title=lk.text.strip() if lk.text else lk.get("href", ""),
                        )
                        for lk in event_elem.findall(".//link")
                        if lk.get("href")
                    ]

                    events.append(
                        Event(
                            id=event_id,
                            title=title,
                            subtitle=subtitle,
                            abstract=abstract,
                            start_time=start_time,
                            duration_minutes=duration_minutes,
                            room=room_name,
                            track=track,
                            day=day_date,
                            speakers=speakers,
                            links=links,
                        )
                    )

        return events

    @staticmethod
    def _text(element: etree._Element, tag: str) -> str:
        child = element.find(tag)
        if child is not None and child.text:
            return str(child.text).strip()
        return ""

    @staticmethod
    def _parse_datetime(date_str: str, time_str: str) -> datetime:
        if not date_str or not time_str:
            return datetime.min
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return datetime.min

    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        if not duration_str or ":" not in duration_str:
            return 0
        try:
            hours, minutes = duration_str.split(":")
            return int(hours) * 60 + int(minutes)
        except ValueError:
            return 0
