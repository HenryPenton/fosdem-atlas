"""FastAPI web adapter."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
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
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "FOSDEM Explorer",
                "event_count": event_count,
                "days": days,
            },
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
