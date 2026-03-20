"""Overview endpoint."""

from fastapi import APIRouter

from src.api.dtos import OverviewDTO
from src.application.services import ScheduleService


def create_overview_router(schedule_service: ScheduleService) -> APIRouter:
    router = APIRouter(tags=["overview"])

    @router.get("/overview")
    def get_overview() -> OverviewDTO:
        data = schedule_service.get_overview()
        return OverviewDTO(
            event_count=data.event_count,
            days=data.days,
            day_events=data.day_events,
            tracks=data.tracks,
            rooms=data.rooms,
        )

    return router
