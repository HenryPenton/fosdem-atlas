"""Speaker endpoints."""

from fastapi import APIRouter, HTTPException

from src.api.dtos import EventSummaryDTO, SpeakerDetailDTO, SpeakerListItemDTO
from src.application.services import SpeakerService


def create_speakers_router(speaker_service: SpeakerService) -> APIRouter:
    router = APIRouter(tags=["speakers"])

    @router.get("/speakers")
    def list_speakers() -> list[SpeakerListItemDTO]:
        speakers = speaker_service.get_all_speakers()
        return [SpeakerListItemDTO(id=s.id, name=s.name, talk_count=s.talk_count) for s in speakers]

    @router.get("/speakers/{speaker_id}")
    def get_speaker_detail(speaker_id: str) -> SpeakerDetailDTO:
        result = speaker_service.get_speaker_detail(speaker_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Speaker not found")
        return SpeakerDetailDTO(
            id=result.id,
            name=result.name,
            bio=result.bio,
            events=[
                EventSummaryDTO(
                    id=e.id,
                    title=e.title,
                    subtitle=e.subtitle,
                    start_time=e.start_time,
                    duration_minutes=e.duration_minutes,
                    room=e.room,
                    track=e.track,
                    day=e.day,
                )
                for e in result.events
            ],
        )

    return router
