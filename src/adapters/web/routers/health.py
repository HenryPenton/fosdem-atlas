"""Health check route."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.api.routers.health import add_health_route
from src.application.services import ScheduleService
from src.config import Settings


def create_health_page_router(
    schedule_service: ScheduleService,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/robots.txt", response_class=PlainTextResponse)
    def robots_txt() -> str:
        return "User-agent: *\nAllow: /\n"

    add_health_route(router, schedule_service, settings)

    return router
