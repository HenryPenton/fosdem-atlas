"""Analytics service – conference analytics and statistics."""

import logging

from src.domain.models import AnalyticsData
from src.domain.ports import AnalyticsRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Conference analytics and statistics."""

    def __init__(self, repository: AnalyticsRepository) -> None:
        self._repo = repository
        self._cache: AnalyticsData | None = None

    def invalidate_cache(self) -> None:
        logger.debug("Invalidating analytics cache")
        self._cache = None

    def get_analytics(self) -> AnalyticsData:
        """Full analytics data with computed heatmap. Results are cached."""
        if self._cache is not None:
            return self._cache

        stats = self._repo.get_stats()
        room_stats = self._repo.get_room_stats()
        speaker_stats = self._repo.get_speaker_stats()
        topic_stats = self._repo.get_topic_stats()

        result = AnalyticsData.from_raw_stats(
            stats=stats,
            room_stats=room_stats,
            speaker_stats=speaker_stats,
            topic_stats=topic_stats,
        )
        self._cache = result
        return result
