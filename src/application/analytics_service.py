"""Analytics service – conference analytics and statistics."""

from typing import Any

from src.domain.ports import EventRepository


class AnalyticsService:
    """Conference analytics and statistics."""

    def __init__(self, repository: EventRepository) -> None:
        self._repo = repository

    def get_analytics(self) -> dict[str, Any]:
        """Full analytics data with computed heatmap."""
        stats = self._repo.get_stats()
        room_stats = self._repo.get_room_stats()
        speaker_stats = self._repo.get_speaker_stats()
        topic_stats = self._repo.get_topic_stats()

        heatmap_raw = room_stats["heatmap"]
        heatmap_days = sorted({str(item["day"]) for item in heatmap_raw})
        heatmap_hours = sorted({int(item["hour"]) for item in heatmap_raw})
        heatmap_grid: dict[str, dict[int, int]] = {
            day: dict.fromkeys(heatmap_hours, 0) for day in heatmap_days
        }
        for item in heatmap_raw:
            heatmap_grid[str(item["day"])][int(item["hour"])] = int(item["count"])
        max_heatmap_count = max((int(item["count"]) for item in heatmap_raw), default=1)

        return {
            "stats": stats,
            "room_stats": room_stats,
            "events_per_room": room_stats["events_per_room"],
            "speaker_stats": speaker_stats,
            "topic_stats": topic_stats,
            "heatmap_days": heatmap_days,
            "heatmap_hours": heatmap_hours,
            "heatmap_grid": heatmap_grid,
            "max_heatmap_count": max_heatmap_count,
        }
