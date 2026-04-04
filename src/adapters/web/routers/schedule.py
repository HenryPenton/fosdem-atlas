"""Schedule page routes – index, day, track, event, keyword."""

import dataclasses

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.adapters.web.routers.utils import back_link
from src.application.services import ScheduleService


def create_schedule_router(
    schedule_service: ScheduleService,
    templates: Jinja2Templates,
) -> APIRouter:
    router = APIRouter(tags=["schedule-pages"])

    @router.get("/", response_class=HTMLResponse)
    def index(
        request: Request,
        day: str = Query(default="", max_length=20),
    ) -> HTMLResponse:
        overview = schedule_service.get_overview()
        selected_day = day if day in overview.days else (overview.days[0] if overview.days else "")
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "FOSDEM Atlas",
                **dataclasses.asdict(overview),
                "selected_day": selected_day,
            },
        )

    @router.get("/grid", response_class=HTMLResponse)
    def schedule_grid(
        request: Request,
        day: str = Query(default="", max_length=20),
    ) -> HTMLResponse:
        grid_data = schedule_service.get_grid_data(day=day)
        return templates.TemplateResponse(
            request=request,
            name="partials/schedule_grid.html",
            context=dataclasses.asdict(grid_data),
        )

    @router.get("/day/{day}", response_class=HTMLResponse)
    def day_tracks(request: Request, day: str) -> HTMLResponse:
        data = schedule_service.get_day_detail(day)
        return templates.TemplateResponse(
            request=request,
            name="day.html",
            context={
                "title": f"FOSDEM Atlas — {day}",
                **dataclasses.asdict(data),
            },
        )

    @router.get("/day/{day}/track/{track:path}", response_class=HTMLResponse)
    def track_events(request: Request, day: str, track: str) -> HTMLResponse:
        events = schedule_service.get_events_for_day_and_track(day, track)
        if not events:
            url, label = back_link(request, default_url="/tracks", default_label="Back to tracks")
            return templates.TemplateResponse(
                request=request,
                name="404.html",
                context={
                    "title": "FOSDEM Atlas — Not Found",
                    "message": "No events found for that track.",
                    "back_url": url,
                    "back_label": label,
                },
                status_code=404,
            )
        return templates.TemplateResponse(
            request=request,
            name="track.html",
            context={
                "title": f"FOSDEM Atlas — {track}",
                "day": day,
                "track": track,
                "events": events,
            },
        )

    @router.get("/tracks", response_class=HTMLResponse)
    def tracks_browser(request: Request) -> HTMLResponse:
        data = schedule_service.get_all_tracks_with_counts()
        return templates.TemplateResponse(
            request=request,
            name="tracks.html",
            context={
                "title": "FOSDEM Atlas — Tracks",
                **dataclasses.asdict(data),
            },
        )

    @router.get("/track/{track:path}", response_class=HTMLResponse)
    def track_detail(request: Request, track: str) -> HTMLResponse:
        events = schedule_service.get_events_for_track(track)
        if not events:
            url, label = back_link(request, default_url="/tracks", default_label="Back to tracks")
            return templates.TemplateResponse(
                request=request,
                name="404.html",
                context={
                    "title": "FOSDEM Atlas — Not Found",
                    "message": "That track doesn't exist or has no events.",
                    "back_url": url,
                    "back_label": label,
                },
                status_code=404,
            )
        return templates.TemplateResponse(
            request=request,
            name="track.html",
            context={
                "title": f"FOSDEM Atlas — {track}",
                "day": None,
                "track": track,
                "events": events,
            },
        )

    @router.get("/event/{event_id}", response_class=HTMLResponse)
    def event_detail(request: Request, event_id: str) -> HTMLResponse:
        result = schedule_service.get_event_detail(event_id)
        if result is None:
            url, label = back_link(request)
            return templates.TemplateResponse(
                request=request,
                name="404.html",
                context={
                    "title": "FOSDEM Atlas — Not Found",
                    "message": "That event doesn't exist or may have been removed.",
                    "back_url": url,
                    "back_label": label,
                },
                status_code=404,
            )
        return templates.TemplateResponse(
            request=request,
            name="event.html",
            context={
                "title": f"FOSDEM Atlas — {result.title}",
                "event": result,
                "speakers": result.speakers,
            },
        )

    @router.get("/keyword/{term:path}", response_class=HTMLResponse)
    def keyword_events(request: Request, term: str) -> HTMLResponse:
        events = schedule_service.search_events(q=term)
        return templates.TemplateResponse(
            request=request,
            name="keyword.html",
            context={
                "title": f"FOSDEM Atlas — {term}",
                "term": term,
                "events": events,
            },
        )

    @router.get("/my-schedule", response_class=HTMLResponse)
    def my_schedule_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="my_schedule.html",
            context={"title": "FOSDEM Atlas — My Schedule"},
        )

    @router.get("/my-schedule/grid", response_class=HTMLResponse)
    def my_schedule_grid(
        request: Request,
        ids: str = Query(default="", max_length=4096),
    ) -> HTMLResponse:
        event_ids = [i.strip() for i in ids.split(",") if i.strip()]
        grids_by_day = schedule_service.build_grid_for_ids(event_ids) if event_ids else {}
        return templates.TemplateResponse(
            request=request,
            name="partials/my_schedule_grid.html",
            context={"grids_by_day": grids_by_day},
        )

    @router.get("/offline", response_class=HTMLResponse)
    def offline(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="offline.html",
            context={"title": "FOSDEM Atlas — Offline"},
        )

    return router
