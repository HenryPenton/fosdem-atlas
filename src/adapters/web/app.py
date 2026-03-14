"""FastAPI web adapter."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import Settings
from src.domain.ports import EventRepository

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


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

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        event_count = event_repository.get_event_count()
        days = event_repository.get_unique_days()
        day_events = {d: len(event_repository.get_events_by_day(d)) for d in days}
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "FOSDEM Explorer",
                "event_count": event_count,
                "days": days,
                "day_events": day_events,
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

    @app.get("/day/{day}/track/{track}", response_class=HTMLResponse)
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

    @app.get("/api/events/search", response_class=HTMLResponse)
    async def api_events_search(
        request: Request, q: str = Query(default="", max_length=200)
    ) -> HTMLResponse:
        events = event_repository.search_events(q.strip()) if q.strip() else []
        return templates.TemplateResponse(
            request=request,
            name="partials/search_results.html",
            context={"events": events, "query": q.strip()},
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

    return app
