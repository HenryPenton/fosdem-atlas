"""Health check endpoint."""

import logging

from fastapi import APIRouter, Response

from src.api.dtos import HealthDTO
from src.application.services import ScheduleService
from src.config import Settings

logger = logging.getLogger(__name__)


def add_health_route(
    router: APIRouter, schedule_service: ScheduleService, settings: Settings
) -> None:
    """Register ``GET /health`` on *router*."""

    @router.get("/health")
    def health(response: Response) -> HealthDTO:
        try:
            event_count = schedule_service.get_event_count()
        except Exception:
            logger.exception("Health check failed")
            response.status_code = 503
            return HealthDTO(status="unhealthy", version=settings.version, events=-1)
        return HealthDTO(status="healthy", version=settings.version, events=event_count)


def create_health_router(schedule_service: ScheduleService, settings: Settings) -> APIRouter:
    router = APIRouter(tags=["health"])
    add_health_route(router, schedule_service, settings)
    return router
