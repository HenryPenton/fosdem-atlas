"""Export routes – CSV and iCal."""

from fastapi import APIRouter

from src.api.routers.export import add_export_routes
from src.application.services import ScheduleService, SpeakerService


def create_export_page_router(
    schedule_service: ScheduleService,
    speaker_service: SpeakerService,
) -> APIRouter:
    router = APIRouter(tags=["export"])
    add_export_routes(
        router,
        schedule_service,
        speaker_service,
        events_csv_path="/export/events.csv",
        speakers_csv_path="/export/speakers.csv",
        ical_path="/my-schedule/export.ics",
    )
    return router
