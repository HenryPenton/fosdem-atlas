"""FOSDEM Explorer - composition root.

Wires together all adapters and starts the application.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from src.adapters.persistence.duckdb_connection import DuckDBConnection
from src.adapters.persistence.duckdb_repository import DuckDBEventRepository
from src.adapters.scraper.fosdem_scraper import FosdemScheduleFetcher
from src.adapters.web.app import create_app
from src.application.services import ScrapeService
from src.config import settings

# Wire adapters
_db = DuckDBConnection(settings.database_path)
_event_repository = DuckDBEventRepository(_db)
_schedule_fetcher = FosdemScheduleFetcher()
_scrape_service = ScrapeService(_schedule_fetcher, _event_repository)


def _run_scrape() -> None:
    """Scheduled scrape job with error handling."""
    print(f"Scheduled scrape: fetching {settings.fosdem_schedule_url}")
    try:
        count = _scrape_service.run(settings.fosdem_schedule_url)
        print(f"Scheduled scrape complete: {count} events stored")
    except Exception as exc:
        print(f"Scheduled scrape failed: {exc}")


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    print(f"Starting FOSDEM Explorer v{settings.version}")
    print(f"Database: {settings.database_path}")
    _db.get()
    print("Database connected")

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _run_scrape,
        "interval",
        minutes=settings.scrape_interval_minutes,
        id="scrape",
        next_run_time=datetime.now(),
    )
    scheduler.start()
    print(f"Scheduler started (every {settings.scrape_interval_minutes} minutes)")

    yield

    scheduler.shutdown(wait=False)
    print("Scheduler stopped")
    print("Shutting down FOSDEM Explorer")
    _db.close()
    print("Database connection closed")


app = create_app(
    event_repository=_event_repository,
    settings=settings,
    lifespan=_lifespan,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
