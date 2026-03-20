"""HTMX partial routes."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.application.services import ScheduleService


def create_partials_router(
    schedule_service: ScheduleService,
    templates: Jinja2Templates,
) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["partials"])

    @router.get("/events/search", response_class=HTMLResponse)
    def search_events(
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

    @router.get("/events", response_class=HTMLResponse)
    def list_events(request: Request) -> HTMLResponse:
        events = schedule_service.get_all_events()
        return templates.TemplateResponse(
            request=request,
            name="partials/event_list.html",
            context={"events": events},
        )

    return router
