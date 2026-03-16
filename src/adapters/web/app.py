"""FastAPI web adapter."""

import csv
import io
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import StreamingResponse

from src.api.routes import create_api_router
from src.config import Settings
from src.domain.ports import EventRepository

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

CACHE_MAX_AGE = 20


def create_app(
    event_repository: EventRepository,
    settings: Settings,
    lifespan: Any = None,
) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="FOSDEM Explorer",
        description="A DuckDB-powered web application for exploring the FOSDEM schedule",
        version=settings.version,
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def add_cache_control(request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)
        if request.url.path != "/health" and request.method == "GET":
            response.headers["Cache-Control"] = f"public, max-age={CACHE_MAX_AGE}"
        return response

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

    app.include_router(create_api_router(event_repository))

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        event_count = event_repository.get_event_count()
        days = event_repository.get_unique_days()
        day_events = {d: len(event_repository.get_events_by_day(d)) for d in days}
        tracks = event_repository.get_unique_tracks()
        rooms = event_repository.get_unique_rooms()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "FOSDEM Explorer",
                "event_count": event_count,
                "days": days,
                "day_events": day_events,
                "tracks": tracks,
                "rooms": rooms,
            },
        )

    @app.get("/schedule", response_class=HTMLResponse)
    async def schedule(
        request: Request,
        sort: str = Query(default="time", max_length=10),
    ) -> HTMLResponse:
        valid_sorts = {"time", "track", "room"}
        sort = sort if sort in valid_sorts else "time"
        events = event_repository.get_all_events(sort=sort)

        days_events: dict[str, list[dict[str, str | int | datetime]]] = {}
        for event in events:
            days_events.setdefault(str(event["day"]), []).append(event)

        now = datetime.now()
        now_ids: set[str] = set()
        upcoming: list[dict[str, str | int | datetime]] = []
        for event in events:
            start = event["start_time"]
            if not isinstance(start, datetime):
                continue
            end = start + timedelta(minutes=int(event["duration_minutes"]))  # type: ignore[arg-type]
            if start <= now < end:
                now_ids.add(str(event["id"]))
            elif start > now:
                upcoming.append(event)

        next_ids: set[str] = set()
        if upcoming:
            next_start = min(
                e["start_time"] for e in upcoming if isinstance(e["start_time"], datetime)
            )
            next_ids = {str(e["id"]) for e in upcoming if e["start_time"] == next_start}

        return templates.TemplateResponse(
            request=request,
            name="schedule.html",
            context={
                "title": "FOSDEM Explorer — Schedule",
                "days_events": days_events,
                "sort": sort,
                "now_ids": now_ids,
                "next_ids": next_ids,
            },
        )

    @app.get("/grid", response_class=HTMLResponse)
    async def grid(
        request: Request,
        day: str = Query(default="", max_length=20),
    ) -> HTMLResponse:
        days = event_repository.get_unique_days()
        if not days:
            return templates.TemplateResponse(
                request=request,
                name="grid.html",
                context={
                    "title": "FOSDEM Explorer — Grid",
                    "days": [],
                    "selected_day": "",
                    "rooms": [],
                    "time_slots": [],
                    "grid": {},
                },
            )

        selected_day = day if day in days else days[0]
        rooms = event_repository.get_rooms_by_day(selected_day)
        events = event_repository.get_events_by_day(selected_day)

        # Build set of 30-minute time slots spanning the day's events
        starts: list[datetime] = []
        ends: list[datetime] = []
        for ev in events:
            st = ev["start_time"]
            if isinstance(st, datetime):
                starts.append(st)
                dur = ev["duration_minutes"]
                ends.append(st + timedelta(minutes=int(dur)))  # type: ignore[arg-type]

        time_slots: list[datetime] = []
        if starts:
            slot_start = min(starts).replace(minute=(min(starts).minute // 30) * 30, second=0)
            slot_end = max(ends)
            current = slot_start
            while current < slot_end:
                time_slots.append(current)
                current += timedelta(minutes=30)

        # Map (slot, room) → list of events
        grid: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
        for ev in events:
            st = ev["start_time"]
            if not isinstance(st, datetime):
                continue
            slot_key = st.replace(minute=(st.minute // 30) * 30, second=0).strftime("%H:%M")
            grid[slot_key][str(ev["room"])].append(ev)

        return templates.TemplateResponse(
            request=request,
            name="grid.html",
            context={
                "title": f"FOSDEM Explorer — Grid ({selected_day})",
                "days": days,
                "selected_day": selected_day,
                "rooms": rooms,
                "time_slots": time_slots,
                "grid": dict(grid),
            },
        )

    @app.get("/day/{day}", response_class=HTMLResponse)
    async def day_tracks(request: Request, day: str) -> HTMLResponse:
        tracks = event_repository.get_tracks_by_day(day)
        track_events = {
            t: len(event_repository.get_events_by_day_and_track(day, t)) for t in tracks
        }
        return templates.TemplateResponse(
            request=request,
            name="day.html",
            context={
                "title": f"FOSDEM Explorer — {day}",
                "day": day,
                "tracks": tracks,
                "track_events": track_events,
            },
        )

    @app.get("/day/{day}/track/{track:path}", response_class=HTMLResponse)
    async def track_events(request: Request, day: str, track: str) -> HTMLResponse:
        events = event_repository.get_events_by_day_and_track(day, track)
        return templates.TemplateResponse(
            request=request,
            name="track.html",
            context={
                "title": f"FOSDEM Explorer — {track}",
                "day": day,
                "track": track,
                "events": events,
            },
        )

    @app.get("/tracks", response_class=HTMLResponse)
    async def tracks_browser(request: Request) -> HTMLResponse:
        tracks = event_repository.get_unique_tracks()
        track_events = {t: len(event_repository.get_events_by_track(t)) for t in tracks}
        return templates.TemplateResponse(
            request=request,
            name="tracks.html",
            context={
                "title": "FOSDEM Explorer — Tracks",
                "tracks": tracks,
                "track_events": track_events,
            },
        )

    @app.get("/speakers", response_class=HTMLResponse)
    async def speakers_browser(request: Request) -> HTMLResponse:
        speakers = event_repository.get_all_speakers()
        return templates.TemplateResponse(
            request=request,
            name="speakers.html",
            context={
                "title": "FOSDEM Explorer — Speakers",
                "speakers": speakers,
            },
        )

    @app.get("/speaker/{speaker_id}", response_class=HTMLResponse)
    async def speaker_detail(request: Request, speaker_id: str) -> HTMLResponse:
        from fastapi.responses import Response

        speaker = event_repository.get_speaker_by_id(speaker_id)
        if speaker is None:
            return Response(content="Speaker not found", status_code=404)  # type: ignore[return-value]
        events = event_repository.get_events_by_speaker(speaker_id)
        return templates.TemplateResponse(
            request=request,
            name="speaker.html",
            context={
                "title": f"FOSDEM Explorer — {speaker['name']}",
                "speaker": speaker,
                "events": events,
            },
        )

    @app.get("/track/{track:path}", response_class=HTMLResponse)
    async def track_detail(request: Request, track: str) -> HTMLResponse:
        events = event_repository.get_events_by_track(track)
        return templates.TemplateResponse(
            request=request,
            name="track.html",
            context={
                "title": f"FOSDEM Explorer — {track}",
                "day": None,
                "track": track,
                "events": events,
            },
        )

    @app.get("/event/{event_id}", response_class=HTMLResponse)
    async def event_detail(request: Request, event_id: str) -> HTMLResponse:
        from fastapi.responses import Response

        event = event_repository.get_event_by_id(event_id)
        if event is None:
            return Response(content="Event not found", status_code=404)  # type: ignore[return-value]
        speakers = event_repository.get_speakers_for_event(event_id)
        return templates.TemplateResponse(
            request=request,
            name="event.html",
            context={
                "title": f"FOSDEM Explorer — {event['title']}",
                "event": event,
                "speakers": speakers,
            },
        )

    @app.get("/api/events/search", response_class=HTMLResponse)
    async def api_events_search(
        request: Request,
        q: str = Query(default="", max_length=200),
        track: str = Query(default="", max_length=200),
        room: str = Query(default="", max_length=200),
        day: str = Query(default="", max_length=20),
    ) -> HTMLResponse:
        q, track, room, day = q.strip(), track.strip(), room.strip(), day.strip()
        if q or track or room or day:
            events = event_repository.filter_events(q=q, track=track, room=room, day=day)
        else:
            events = []
        return templates.TemplateResponse(
            request=request,
            name="partials/search_results.html",
            context={"events": events, "query": q, "track": track, "room": room, "day": day},
        )

    @app.get("/api/events", response_class=HTMLResponse)
    async def api_events(request: Request) -> HTMLResponse:
        events = event_repository.get_all_events()
        return templates.TemplateResponse(
            request=request,
            name="partials/event_list.html",
            context={"events": events},
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "version": settings.version}

    @app.get("/export/events.csv")
    async def export_events_csv() -> StreamingResponse:
        events = event_repository.get_all_events(sort="time")
        return _csv_response(events, "events.csv")

    @app.get("/export/speakers.csv")
    async def export_speakers_csv() -> StreamingResponse:
        speakers = event_repository.get_all_speakers()
        return _csv_response(speakers, "speakers.csv")

    @app.get("/my-schedule", response_class=HTMLResponse)
    async def my_schedule_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="my_schedule.html",
            context={"title": "FOSDEM Explorer — My Schedule"},
        )

    @app.get("/my-schedule/export.ics")
    async def my_schedule_ical(
        ids: str = Query(default="", max_length=10000),
    ) -> Response:
        event_ids = [i.strip() for i in ids.split(",") if i.strip()][:200]
        events = event_repository.get_events_by_ids(event_ids)
        cal = _build_ical(events)
        return Response(
            content=cal,
            media_type="text/calendar",
            headers={"Content-Disposition": 'attachment; filename="fosdem-schedule.ics"'},
        )

    @app.get("/analytics", response_class=HTMLResponse)
    async def analytics(request: Request) -> HTMLResponse:
        stats = event_repository.get_stats()
        room_stats = event_repository.get_room_stats()
        speaker_stats = event_repository.get_speaker_stats()
        topic_stats = event_repository.get_topic_stats()
        heatmap_raw = room_stats["heatmap"]
        heatmap_days = sorted({str(item["day"]) for item in heatmap_raw})
        heatmap_hours = sorted({int(item["hour"]) for item in heatmap_raw})
        heatmap_grid: dict[str, dict[int, int]] = {
            day: dict.fromkeys(heatmap_hours, 0) for day in heatmap_days
        }
        for item in heatmap_raw:
            heatmap_grid[str(item["day"])][int(item["hour"])] = int(item["count"])
        max_heatmap_count = max((int(item["count"]) for item in heatmap_raw), default=1)
        return templates.TemplateResponse(
            request=request,
            name="analytics.html",
            context={
                "title": "FOSDEM Explorer — Analytics",
                "stats": stats,
                "events_per_room": room_stats["events_per_room"],
                "speaker_stats": speaker_stats,
                "topic_stats": topic_stats,
                "heatmap_days": heatmap_days,
                "heatmap_hours": heatmap_hours,
                "heatmap_grid": heatmap_grid,
                "max_heatmap_count": max_heatmap_count,
            },
        )

    return app


def _csv_response(rows: list[dict[str, Any]], filename: str) -> StreamingResponse:
    if not rows:
        buf = io.StringIO("")
    else:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _ical_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _build_ical(events: list[dict[str, Any]]) -> str:
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
        duration = int(ev.get("duration_minutes", 30))
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
