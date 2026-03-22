"""Event endpoints."""

from fastapi import APIRouter, HTTPException, Query

from src.api.dtos import (
    EventDetailDTO,
    EventSearchResultDTO,
    EventSummaryDTO,
    LinkDTO,
    SpeakerDTO,
)
from src.application.services import ScheduleService
from src.domain.models.events import EventDetail, EventSummary


def create_events_router(schedule_service: ScheduleService) -> APIRouter:
    router = APIRouter(tags=["events"])

    @router.get("/events")
    def list_events(
        sort: str = Query(default="time", max_length=10),
    ) -> list[EventSummaryDTO]:
        return [_event_summary_dto(e) for e in schedule_service.get_all_events(sort=sort)]

    @router.get("/events/search")
    def search_events(
        q: str = Query(default="", max_length=200),
        track: str = Query(default="", max_length=200),
        room: str = Query(default="", max_length=200),
        day: str = Query(default="", max_length=20),
    ) -> list[EventSearchResultDTO]:
        return [
            EventSearchResultDTO(
                id=e.id,
                title=e.title,
                abstract=e.abstract,
                start_time=e.start_time,
                duration_minutes=e.duration_minutes,
                room=e.room,
                track=e.track,
                day=e.day,
            )
            for e in schedule_service.search_events(q=q, track=track, room=room, day=day)
        ]

    @router.get("/events/by-ids")
    def get_events_by_ids(
        ids: str = Query(default="", max_length=10000),
    ) -> list[EventDetailDTO]:
        event_ids = [i.strip() for i in ids.split(",") if i.strip()][:200]
        return [_event_detail_dto(e) for e in schedule_service.get_events_by_ids(event_ids)]

    @router.get("/events/{event_id}")
    def get_event_detail(event_id: str) -> EventDetailDTO:
        result = schedule_service.get_event_detail(event_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return _event_detail_dto(result)

    return router


def _event_summary_dto(e: EventSummary) -> EventSummaryDTO:
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


def _event_detail_dto(e: EventDetail) -> EventDetailDTO:
    return EventDetailDTO(
        id=e.id,
        title=e.title,
        subtitle=e.subtitle,
        abstract=e.abstract,
        start_time=e.start_time,
        duration_minutes=e.duration_minutes,
        room=e.room,
        track=e.track,
        day=e.day,
        speakers=[SpeakerDTO(id=s.id, name=s.name) for s in e.speakers],
        links=[LinkDTO(href=lk.href, title=lk.title) for lk in e.links],
    )
