"""Tests for ScrapeService."""

from src.adapters.persistence.duckdb_events_repository import DuckDBEventsRepository
from src.adapters.persistence.duckdb_ingestion_repository import DuckDBIngestionRepository
from src.application.services import ScrapeService
from src.domain.models import Event
from tests.conftest import SAMPLE_EVENTS


class FakeScheduleFetcher:
    def __init__(self, events: list[Event]) -> None:
        self._events = events

    def fetch_and_parse(self, _url: str) -> list[Event]:
        return self._events


class TestScrapeService:
    def test_run_stores_events(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        events_repository: DuckDBEventsRepository,
    ) -> None:
        fetcher = FakeScheduleFetcher(SAMPLE_EVENTS)
        service = ScrapeService(fetcher, ingestion_repository)

        count = service.run("https://example.com/schedule.xml")

        assert count == 3
        assert events_repository.get_event_count() == 3

    def test_run_returns_event_count(self, ingestion_repository: DuckDBIngestionRepository) -> None:
        fetcher = FakeScheduleFetcher(SAMPLE_EVENTS[:1])
        service = ScrapeService(fetcher, ingestion_repository)

        count = service.run("https://example.com/schedule.xml")

        assert count == 1

    def test_run_with_no_events(
        self,
        ingestion_repository: DuckDBIngestionRepository,
        events_repository: DuckDBEventsRepository,
    ) -> None:
        fetcher = FakeScheduleFetcher([])
        service = ScrapeService(fetcher, ingestion_repository)

        count = service.run("https://example.com/schedule.xml")

        assert count == 0
        assert events_repository.get_event_count() == 0
