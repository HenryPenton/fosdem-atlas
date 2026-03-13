"""FOSDEM Explorer - FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db.connection import close_connection, get_connection
from db.events import get_all_events, get_event_count, get_unique_days
from src.config import settings

# Paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

_scheduler: BackgroundScheduler | None = None


def _run_scrape_job() -> None:
    """Scheduled scrape job."""
    from db.events import insert_events
    from scraper.fosdem import scrape

    print(f"Scheduled scrape: fetching {settings.fosdem_schedule_url}")
    try:
        events = scrape(settings.fosdem_schedule_url)
        count = insert_events(events)
        print(f"Scheduled scrape complete: {count} events stored")
    except Exception as exc:
        print(f"Scheduled scrape failed: {exc}")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    global _scheduler

    # Startup
    print(f"Starting FOSDEM Explorer v{settings.version}")
    print(f"Database: {settings.database_path}")
    get_connection()
    print("Database connected")

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_scrape_job,
        "interval",
        minutes=settings.scrape_interval_minutes,
        id="scrape",
    )
    _scheduler.start()
    print(f"Scheduler started (every {settings.scrape_interval_minutes} minutes)")

    yield

    # Shutdown
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        print("Scheduler stopped")
    print("Shutting down FOSDEM Explorer")
    close_connection()
    print("Database connection closed")


app = FastAPI(
    title="FOSDEM Explorer",
    description="A DuckDB-powered web application for exploring the FOSDEM schedule",
    version=settings.version,
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the main page."""
    event_count = get_event_count()
    days = get_unique_days()
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
    """Return events as HTML partial for HTMX."""
    events = get_all_events()
    return templates.TemplateResponse(
        request=request,
        name="partials/event_list.html",
        context={"events": events},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.version}


def run() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
