"""JSON API v1 endpoints for FOSDEM Explorer."""

import csv
import dataclasses
import io
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.api.dtos import EventSummaryDTO, SpeakerDetailDTO, SpeakerListItemDTO
from src.application.services import AnalyticsService, ScheduleService, SpeakerService


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
    ) -> list[dict[str, Any]]:
        return [dataclasses.asdict(e) for e in schedule_service.get_all_events(sort=sort)]

    @router.get("/events/search")
    async def api_events_search(
        q: str = Query(default="", max_length=200),
        track: str = Query(default="", max_length=200),
        room: str = Query(default="", max_length=200),
        day: str = Query(default="", max_length=20),
    ) -> list[Any]:
        return [
            dataclasses.asdict(e)
            for e in schedule_service.search_events(q=q, track=track, room=room, day=day)
        ]

    @router.get("/events/by-ids")
    async def api_events_by_ids(
        ids: str = Query(default="", max_length=10000),
    ) -> list[dict[str, Any]]:
        event_ids = [i.strip() for i in ids.split(",") if i.strip()][:200]
        return [dataclasses.asdict(e) for e in schedule_service.get_events_by_ids(event_ids)]

    @router.get("/events/{event_id}")
    async def api_event_detail(event_id: str) -> Any:
        result = schedule_service.get_event_detail(event_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return dataclasses.asdict(result)

    @router.get("/days")
    async def api_days() -> list[str]:
        return schedule_service.get_unique_days()

    @router.get("/days/{day}")
    async def api_day_tracks(day: str) -> dict[str, Any]:
        data = schedule_service.get_day_detail(day)
        return {
            "day": data["day"],
            "tracks": data["tracks"],
            "track_event_counts": data["track_events"],
        }

    @router.get("/days/{day}/tracks/{track:path}")
    async def api_day_track_events(day: str, track: str) -> dict[str, Any]:
        events = schedule_service.get_events_for_day_and_track(day, track)
        return {
            "day": day,
            "track": track,
            "events": [dataclasses.asdict(e) for e in events],
        }

    @router.get("/tracks")
    async def api_tracks() -> list[dict[str, Any]]:
        data = schedule_service.get_all_tracks_with_counts()
        return [{"name": t, "event_count": data["track_events"][t]} for t in data["tracks"]]

    @router.get("/tracks/{track:path}")
    async def api_track_detail(track: str) -> dict[str, Any]:
        events = schedule_service.get_events_for_track(track)
        return {
            "track": track,
            "events": [dataclasses.asdict(e) for e in events],
        }

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
    async def api_analytics() -> dict[str, Any]:
        data = analytics_service.get_analytics()
        return {
            "stats": data["stats"],
            "room_stats": data["room_stats"],
            "speaker_stats": data["speaker_stats"],
            "topic_stats": data["topic_stats"],
        }

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


def _csv_response(rows: list[dict[str, Any]], filename: str) -> StreamingResponse:
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
