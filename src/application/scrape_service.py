"""Scrape service – orchestrates fetching and storing the FOSDEM schedule."""

import logging

from src.domain.ports import IngestionRepository, ScheduleFetcher

logger = logging.getLogger(__name__)


class ScrapeService:
    """Orchestrates fetching and storing the FOSDEM schedule."""

    def __init__(self, fetcher: ScheduleFetcher, repository: IngestionRepository) -> None:
        self._fetcher = fetcher
        self._repository = repository

    def run(self, url: str) -> int:
        """Fetch the schedule and store it. Returns the number of events stored."""
        logger.info("Fetching schedule from %s", url)
        events = self._fetcher.fetch_and_parse(url)
        logger.debug("Parsed %d events from feed", len(events))
        count = self._repository.insert_events(events)
        logger.info("Stored %d events", count)
        return count
