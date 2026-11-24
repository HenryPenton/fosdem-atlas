"""Mappers from domain models to API DTOs shared by several routers."""

from src.api.dtos import EventSummaryDTO
from src.domain.models.events import EventSummary


def event_summary_dto(e: EventSummary) -> EventSummaryDTO:
    return EventSummaryDTO(
        id=e.id,
        title=e.title,
        subtitle=e.subtitle,
        start_time=e.start_time,
        duration_minutes=e.duration_minutes,
        room=e.room,
        track=e.track,
        day=e.day,
    )
