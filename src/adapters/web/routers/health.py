"""Health check route."""

import logging

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from src.api.dtos import HealthDTO
from src.application.services import ScheduleService
from src.config import Settings

logger = logging.getLogger(__name__)


def create_health_page_router(
    schedule_service: ScheduleService,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/robots.txt", response_class=PlainTextResponse)
    def robots_txt() -> str:
        return "User-agent: *\nAllow: /\n"

    @router.get("/health")
    def health(response: Response) -> HealthDTO:
        try:
            event_count = schedule_service.get_event_count()
        except Exception:
            logger.exception("Health check failed")
            response.status_code = 503
            return HealthDTO(status="unhealthy", version=settings.version, events=-1)
        return HealthDTO(status="healthy", version=settings.version, events=event_count)

    return router
