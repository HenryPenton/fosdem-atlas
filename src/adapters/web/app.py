"""FastAPI web adapter."""

from __future__ import annotations

import csv
import dataclasses
import io
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from pathlib import Path

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import StreamingResponse

from src.api.dtos import HealthDTO
from src.api.routes import create_api_router
from src.application.services import AnalyticsService, ScheduleService, SpeakerService
from src.config import Settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

CACHE_MAX_AGE = 20
RATE_LIMIT = "200/minute"

limiter = Limiter(
    key_func=lambda *_args, **_kwargs: "global",
    default_limits=[RATE_LIMIT],
    headers_enabled=True,
)


def create_app(
    schedule_service: ScheduleService,
    analytics_service: AnalyticsService,
    speaker_service: SpeakerService,
    settings: Settings,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
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

    def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
        accept = request.headers.get("accept", "")
        response: Response
        if "text/html" in accept:
            response = HTMLResponse(
                content=templates.get_template("rate_limit.html").render(
                    {"request": request, "title": "FOSDEM Explorer — Too Many Requests"}
                ),
                status_code=429,
            )
        else:
            response = JSONResponse(
                {"error": f"Rate limit exceeded: {exc.detail}"}, status_code=429
            )
        return request.app.state.limiter._inject_headers(response, request.state.view_rate_limit)  # type: ignore[no-any-return]

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.middleware("http")
    async def add_cache_control(request: Request, call_next: RequestResponseEndpoint) -> Response:
        response: Response = await call_next(request)
        if request.url.path != "/health" and request.method == "GET":
            response.headers["Cache-Control"] = f"public, max-age={CACHE_MAX_AGE}"
        return response

    app.include_router(create_api_router(schedule_service, analytics_service, speaker_service))

    @app.get("/", response_class=HTMLResponse)
    async def index(
        request: Request,
        day: str = Query(default="", max_length=20),
    ) -> HTMLResponse:
        overview = schedule_service.get_overview()
        grid_data = schedule_service.get_grid_data(day=day)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "FOSDEM Explorer",
                **dataclasses.asdict(overview),
                **dataclasses.asdict(grid_data),
            },
        )

    @app.get("/day/{day}", response_class=HTMLResponse)
    async def day_tracks(request: Request, day: str) -> HTMLResponse:
        data = schedule_service.get_day_detail(day)
        return templates.TemplateResponse(
            request=request,
            name="day.html",
            context={
                "title": f"FOSDEM Explorer — {day}",
                **dataclasses.asdict(data),
            },
        )

    @app.get("/day/{day}/track/{track:path}", response_class=HTMLResponse)
    async def track_events(request: Request, day: str, track: str) -> HTMLResponse:
        events = schedule_service.get_events_for_day_and_track(day, track)
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
        data = schedule_service.get_all_tracks_with_counts()
        return templates.TemplateResponse(
            request=request,
            name="tracks.html",
            context={
                "title": "FOSDEM Explorer — Tracks",
                **dataclasses.asdict(data),
            },
        )

    @app.get("/speakers", response_class=HTMLResponse)
    async def speakers_browser(request: Request) -> HTMLResponse:
        speakers = speaker_service.get_all_speakers()
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
        result = speaker_service.get_speaker_detail(speaker_id)
        if result is None:
            return Response(content="Speaker not found", status_code=404)  # type: ignore[return-value]
        return templates.TemplateResponse(
            request=request,
            name="speaker.html",
            context={
                "title": f"FOSDEM Explorer — {result.name}",
                "speaker": result,
                "events": result.events,
            },
        )

    @app.get("/track/{track:path}", response_class=HTMLResponse)
    async def track_detail(request: Request, track: str) -> HTMLResponse:
        events = schedule_service.get_events_for_track(track)
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
        result = schedule_service.get_event_detail(event_id)
        if result is None:
            return Response(content="Event not found", status_code=404)  # type: ignore[return-value]
        return templates.TemplateResponse(
            request=request,
            name="event.html",
            context={
                "title": f"FOSDEM Explorer — {result.title}",
                "event": result,
                "speakers": result.speakers,
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
        events = schedule_service.search_events(q=q, track=track, room=room, day=day)
        return templates.TemplateResponse(
            request=request,
            name="partials/search_results.html",
            context={
                "events": events,
                "query": q.strip(),
                "track": track.strip(),
                "room": room.strip(),
                "day": day.strip(),
            },
        )

    @app.get("/api/events", response_class=HTMLResponse)
    async def api_events(request: Request) -> HTMLResponse:
        events = schedule_service.get_all_events()
        return templates.TemplateResponse(
            request=request,
            name="partials/event_list.html",
            context={"events": events},
        )

    @app.get("/health")
    async def health(response: Response) -> HealthDTO:
        try:
            event_count = schedule_service.get_event_count()
        except Exception:
            response.status_code = 503
            return HealthDTO(status="unhealthy", version=settings.version, events=-1)
        return HealthDTO(status="healthy", version=settings.version, events=event_count)

    @app.get("/export/events.csv")
    async def export_events_csv() -> StreamingResponse:
        events = schedule_service.get_all_events(sort="time")
        return _csv_response([dataclasses.asdict(e) for e in events], "events.csv")

    @app.get("/export/speakers.csv")
    async def export_speakers_csv() -> StreamingResponse:
        speakers = speaker_service.get_all_speakers()
        return _csv_response([dataclasses.asdict(s) for s in speakers], "speakers.csv")

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
        cal = schedule_service.build_ical(event_ids)
        return Response(
            content=cal,
            media_type="text/calendar",
            headers={"Content-Disposition": 'attachment; filename="fosdem-schedule.ics"'},
        )

    @app.get("/analytics", response_class=HTMLResponse)
    async def analytics(request: Request) -> HTMLResponse:
        data = analytics_service.get_analytics()
        return templates.TemplateResponse(
            request=request,
            name="analytics.html",
            context={
                "title": "FOSDEM Explorer — Analytics",
                **dataclasses.asdict(data),
            },
        )

    @app.get("/keyword/{term:path}", response_class=HTMLResponse)
    async def keyword_events(request: Request, term: str) -> HTMLResponse:
        events = schedule_service.search_events(q=term)
        return templates.TemplateResponse(
            request=request,
            name="keyword.html",
            context={
                "title": f"FOSDEM Explorer — {term}",
                "term": term,
                "events": events,
            },
        )

    @app.get("/offline", response_class=HTMLResponse)
    async def offline(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="offline.html",
            context={"title": "FOSDEM Explorer — Offline"},
        )

    return app


def _csv_response(rows: list[dict[str, str | int | float]], filename: str) -> StreamingResponse:
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
