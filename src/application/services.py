"""Application services (use cases)."""

from src.domain.ports import EventRepository, ScheduleFetcher


class ScrapeService:
    """Orchestrates fetching and storing the FOSDEM schedule."""

    def __init__(self, fetcher: ScheduleFetcher, repository: EventRepository) -> None:
        self._fetcher = fetcher
        self._repository = repository

    def run(self, url: str) -> int:
        """Fetch the schedule and store it. Returns the number of events stored."""
        events = self._fetcher.fetch_and_parse(url)
        return self._repository.insert_events(events)
