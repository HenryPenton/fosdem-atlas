"""FOSDEM Atlas - composition root.

Wires together all adapters and starts the application.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from src.adapters.persistence.duckdb_analytics_repository import DuckDBAnalyticsRepository
from src.adapters.persistence.duckdb_connection import DuckDBConnection
from src.adapters.persistence.duckdb_events_repository import DuckDBEventsRepository
from src.adapters.persistence.duckdb_ingestion_repository import DuckDBIngestionRepository
from src.adapters.persistence.duckdb_speakers_repository import DuckDBSpeakersRepository
from src.adapters.scraper.fosdem_scraper import FosdemScheduleFetcher
from src.adapters.web.app import create_app
from src.application.services import (
    AnalyticsService,
    ScheduleService,
    ScrapeService,
    SpeakerService,
)
from src.config import configure_logging, settings

configure_logging()
logger = logging.getLogger(__name__)

# Wire adapters
_db = DuckDBConnection(settings.database_path)
_events_repository = DuckDBEventsRepository(_db)
_speakers_repository = DuckDBSpeakersRepository(_db)
_analytics_repository = DuckDBAnalyticsRepository(_db)
_ingestion_repository = DuckDBIngestionRepository(_db)
_schedule_fetcher = FosdemScheduleFetcher()
_scrape_service = ScrapeService(_schedule_fetcher, _ingestion_repository)

# Wire application services
_schedule_service = ScheduleService(_events_repository)
_analytics_service = AnalyticsService(_analytics_repository)
_speaker_service = SpeakerService(_speakers_repository)


def _run_scrape() -> None:
    """Scheduled scrape job with error handling."""
    logger.info("Scheduled scrape: fetching %s", settings.fosdem_schedule_url)
    try:
        count = _scrape_service.run(settings.fosdem_schedule_url)
        logger.info("Scheduled scrape complete: %d events stored", count)
        _analytics_service.invalidate_cache()
        _schedule_service.invalidate_cache()
        _speaker_service.invalidate_cache()
    except Exception:
        logger.exception("Scheduled scrape failed")


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting FOSDEM Atlas v%s", settings.version)
    logger.info("Database: %s", settings.database_path)
    _db.get()
    logger.info("Database connected")

    _run_scrape()

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _run_scrape,
        "interval",
        minutes=settings.scrape_interval_minutes,
        id="scrape",
    )
    scheduler.start()
    logger.info("Scheduler started (every %d minutes)", settings.scrape_interval_minutes)

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
    logger.info("Shutting down FOSDEM Atlas")
    _db.close()
    logger.info("Database connection closed")


app = create_app(
    schedule_service=_schedule_service,
    analytics_service=_analytics_service,
    speaker_service=_speaker_service,
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
