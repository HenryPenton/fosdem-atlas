"""Day and room endpoints."""

from fastapi import APIRouter

from src.api.dtos import DayDetailDTO, DayTrackEventsDTO
from src.api.mappers import event_summary_dto
from src.application.services import ScheduleService


def create_days_router(schedule_service: ScheduleService) -> APIRouter:
    router = APIRouter(tags=["days"])

    @router.get("/days")
    def list_days() -> list[str]:
        return schedule_service.get_unique_days()

    @router.get("/days/{day}")
    def get_day_tracks(day: str) -> DayDetailDTO:
        data = schedule_service.get_day_detail(day)
        return DayDetailDTO(
            day=data.day,
            tracks=data.tracks,
            track_event_counts=data.track_events,
        )

    @router.get("/days/{day}/tracks/{track:path}")
    def get_day_track_events(day: str, track: str) -> DayTrackEventsDTO:
        events = schedule_service.get_events_for_day_and_track(day, track)
        return DayTrackEventsDTO(
            day=day,
            track=track,
            events=[event_summary_dto(e) for e in events],
        )

    @router.get("/rooms")
    def list_rooms() -> list[str]:
        return schedule_service.get_unique_rooms()

    return router
