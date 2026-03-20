"""Track endpoints."""

from fastapi import APIRouter

from src.api.dtos import TrackDetailDTO, TrackSummaryDTO
from src.api.routers.events import _event_summary_dto
from src.application.services import ScheduleService


def create_tracks_router(schedule_service: ScheduleService) -> APIRouter:
    router = APIRouter(tags=["tracks"])

    @router.get("/tracks")
    def list_tracks() -> list[TrackSummaryDTO]:
        data = schedule_service.get_all_tracks_with_counts()
        return [TrackSummaryDTO(name=t, event_count=data.track_events[t]) for t in data.tracks]

    @router.get("/tracks/{track:path}")
    def get_track_detail(track: str) -> TrackDetailDTO:
        events = schedule_service.get_events_for_track(track)
        return TrackDetailDTO(
            track=track,
            events=[_event_summary_dto(e) for e in events],
        )

    return router
