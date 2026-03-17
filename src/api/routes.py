"""JSON API v1 endpoints for FOSDEM Explorer."""

import csv
import dataclasses
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.api.dtos import (
    AnalyticsDTO,
    ConferenceStatsDTO,
    DayCountDTO,
    DayDetailDTO,
    DayTrackEventsDTO,
    EventDetailDTO,
    EventSearchResultDTO,
    EventSummaryDTO,
    HeatmapCellDTO,
    KeywordCountDTO,
    MultiTrackSpeakerDTO,
    RoomCountDTO,
    RoomStatsDTO,
    SpeakerDetailDTO,
    SpeakerDTO,
    SpeakerListItemDTO,
    SpeakerStatsDTO,
    TopicStatsDTO,
    TopSpeakerDTO,
    TrackCountDTO,
    TrackDetailDTO,
    TrackSummaryDTO,
)
from src.application.services import AnalyticsService, ScheduleService, SpeakerService
from src.domain.models.events import EventDetail, EventSummary


def create_api_router(
    schedule_service: ScheduleService,
    analytics_service: AnalyticsService,
    speaker_service: SpeakerService,
) -> APIRouter:
    """Create the v1 JSON API router."""
    router = APIRouter(prefix="/api/v1", tags=["api"])

    @router.get("/events")
    async def api_events(
        sort: str = Query(default="time", max_length=10),
    ) -> list[EventSummaryDTO]:
        return [
            EventSummaryDTO(
                id=e.id,
                title=e.title,
                subtitle=e.subtitle,
                start_time=e.start_time,
                duration_minutes=e.duration_minutes,
                room=e.room,
                track=e.track,
                day=e.day,
                abstract=e.abstract,
            )
            for e in schedule_service.get_all_events(sort=sort)
        ]

    @router.get("/events/search")
    async def api_events_search(
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
    async def api_events_by_ids(
        ids: str = Query(default="", max_length=10000),
    ) -> list[EventDetailDTO]:
        event_ids = [i.strip() for i in ids.split(",") if i.strip()][:200]
        return [_event_detail_dto(e) for e in schedule_service.get_events_by_ids(event_ids)]

    @router.get("/events/{event_id}")
    async def api_event_detail(event_id: str) -> EventDetailDTO:
        result = schedule_service.get_event_detail(event_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return _event_detail_dto(result)

    @router.get("/days")
    async def api_days() -> list[str]:
        return schedule_service.get_unique_days()

    @router.get("/days/{day}")
    async def api_day_tracks(day: str) -> DayDetailDTO:
        data = schedule_service.get_day_detail(day)
        return DayDetailDTO(
            day=data.day,
            tracks=data.tracks,
            track_event_counts=data.track_events,
        )

    @router.get("/days/{day}/tracks/{track:path}")
    async def api_day_track_events(day: str, track: str) -> DayTrackEventsDTO:
        events = schedule_service.get_events_for_day_and_track(day, track)
        return DayTrackEventsDTO(
            day=day,
            track=track,
            events=[_event_summary_dto(e) for e in events],
        )

    @router.get("/tracks")
    async def api_tracks() -> list[TrackSummaryDTO]:
        data = schedule_service.get_all_tracks_with_counts()
        return [TrackSummaryDTO(name=t, event_count=data.track_events[t]) for t in data.tracks]

    @router.get("/tracks/{track:path}")
    async def api_track_detail(track: str) -> TrackDetailDTO:
        events = schedule_service.get_events_for_track(track)
        return TrackDetailDTO(
            track=track,
            events=[_event_summary_dto(e) for e in events],
        )

    @router.get("/speakers")
    async def api_speakers() -> list[SpeakerListItemDTO]:
        speakers = speaker_service.get_all_speakers()
        return [SpeakerListItemDTO(id=s.id, name=s.name, talk_count=s.talk_count) for s in speakers]

    @router.get("/speakers/{speaker_id}")
    async def api_speaker_detail(speaker_id: str) -> SpeakerDetailDTO:
        result = speaker_service.get_speaker_detail(speaker_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Speaker not found")
        return SpeakerDetailDTO(
            id=result.id,
            name=result.name,
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

    @router.get("/analytics")
    async def api_analytics() -> AnalyticsDTO:
        data = analytics_service.get_analytics()
        return AnalyticsDTO(
            stats=ConferenceStatsDTO(
                total_events=data.stats.total_events,
                total_speakers=data.stats.total_speakers,
                total_tracks=data.stats.total_tracks,
                total_rooms=data.stats.total_rooms,
                events_per_day=[
                    DayCountDTO(day=d.day, count=d.count) for d in data.stats.events_per_day
                ],
                events_per_track=[
                    TrackCountDTO(track=t.track, count=t.count) for t in data.stats.events_per_track
                ],
            ),
            room_stats=RoomStatsDTO(
                events_per_room=[
                    RoomCountDTO(room=r.room, count=r.count)
                    for r in data.room_stats.events_per_room
                ],
                heatmap=[
                    HeatmapCellDTO(day=h.day, hour=h.hour, count=h.count)
                    for h in data.room_stats.heatmap
                ],
            ),
            speaker_stats=SpeakerStatsDTO(
                top_speakers=[
                    TopSpeakerDTO(id=s.id, name=s.name, talk_count=s.talk_count)
                    for s in data.speaker_stats.top_speakers
                ],
                multi_track_speakers=[
                    MultiTrackSpeakerDTO(
                        id=s.id,
                        name=s.name,
                        track_count=s.track_count,
                        tracks=s.tracks,
                    )
                    for s in data.speaker_stats.multi_track_speakers
                ],
            ),
            topic_stats=TopicStatsDTO(
                keywords=[
                    KeywordCountDTO(term=k.term, count=k.count) for k in data.topic_stats.keywords
                ],
            ),
        )

    @router.get("/rooms")
    async def api_rooms() -> list[str]:
        return schedule_service.get_unique_rooms()

    @router.get("/export/events.csv")
    async def export_events_csv() -> StreamingResponse:
        events = schedule_service.get_all_events(sort="time")
        return _csv_response([dataclasses.asdict(e) for e in events], "events.csv")

    @router.get("/export/speakers.csv")
    async def export_speakers_csv() -> StreamingResponse:
        speakers = speaker_service.get_all_speakers()
        return _csv_response([dataclasses.asdict(s) for s in speakers], "speakers.csv")

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
        fosdem_url=e.fosdem_url,
        speakers=[SpeakerDTO(id=s.id, name=s.name) for s in e.speakers],
    )


def _csv_response(rows: list[dict[str, str | int | float]], filename: str) -> StreamingResponse:
    if not rows:
        buf = io.StringIO("")
    else:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
