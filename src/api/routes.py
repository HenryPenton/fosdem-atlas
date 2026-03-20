"""JSON API v1 – combines all sub-routers."""

from fastapi import APIRouter

from src.api.routers.analytics import create_analytics_router
from src.api.routers.days import create_days_router
from src.api.routers.events import create_events_router
from src.api.routers.export import create_export_router
from src.api.routers.health import create_health_router
from src.api.routers.overview import create_overview_router
from src.api.routers.speakers import create_speakers_router
from src.api.routers.tracks import create_tracks_router
from src.application.services import AnalyticsService, ScheduleService, SpeakerService
from src.config import Settings


def create_api_router(
    schedule_service: ScheduleService,
    analytics_service: AnalyticsService,
    speaker_service: SpeakerService,
    settings: Settings,
) -> APIRouter:
    """Create the v1 JSON API router by combining all sub-routers."""
    router = APIRouter(prefix="/api/v1", tags=["api"])

    router.include_router(create_events_router(schedule_service))
    router.include_router(create_speakers_router(speaker_service))
    router.include_router(create_tracks_router(schedule_service))
    router.include_router(create_days_router(schedule_service))
    router.include_router(create_analytics_router(analytics_service))
    router.include_router(create_export_router(schedule_service, speaker_service))
    router.include_router(create_health_router(schedule_service, settings))
    router.include_router(create_overview_router(schedule_service))

    return router
