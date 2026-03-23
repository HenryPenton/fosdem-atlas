"""Tests for AnalyticsService."""

from src.application.services import AnalyticsService


class TestAnalyticsService:
    def test_get_analytics(self, analytics_service: AnalyticsService) -> None:
        data = analytics_service.get_analytics()
        assert data.stats.total_events == 3
        assert data.events_per_room is not None
        assert data.speaker_stats is not None
        assert data.topic_stats is not None
        assert data.heatmap_days is not None
        assert data.heatmap_hours is not None
        assert data.heatmap_grid is not None
        assert data.max_heatmap_count is not None
