"""JSON API v1 endpoints for FOSDEM Explorer."""

import csv
import io
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.domain.ports import EventRepository


def create_api_router(event_repository: EventRepository) -> APIRouter:
    """Create the v1 JSON API router."""
    router = APIRouter(prefix="/api/v1", tags=["api"])

    @router.get("/events")
    async def api_events(
        sort: str = Query(default="time", max_length=10),
    ) -> list[dict[str, Any]]:
        valid_sorts = {"time", "track", "room"}
        sort = sort if sort in valid_sorts else "time"
        return event_repository.get_all_events(sort=sort)

    @router.get("/events/search")
    async def api_events_search(
        q: str = Query(default="", max_length=200),
        track: str = Query(default="", max_length=200),
        room: str = Query(default="", max_length=200),
        day: str = Query(default="", max_length=20),
    ) -> list[dict[str, Any]]:
        q, track, room, day = q.strip(), track.strip(), room.strip(), day.strip()
        if q or track or room or day:
            return event_repository.filter_events(q=q, track=track, room=room, day=day)
        return []

    @router.get("/events/{event_id}")
    async def api_event_detail(event_id: str) -> dict[str, Any]:
        event = event_repository.get_event_by_id(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        speakers = event_repository.get_speakers_for_event(event_id)
        return {**event, "speakers": speakers}

    @router.get("/days")
    async def api_days() -> list[str]:
        return event_repository.get_unique_days()

    @router.get("/days/{day}")
    async def api_day_tracks(day: str) -> dict[str, Any]:
        tracks = event_repository.get_tracks_by_day(day)
        return {
            "day": day,
            "tracks": tracks,
            "track_event_counts": {
                t: len(event_repository.get_events_by_day_and_track(day, t)) for t in tracks
            },
        }

    @router.get("/days/{day}/tracks/{track:path}")
    async def api_day_track_events(day: str, track: str) -> dict[str, Any]:
        events = event_repository.get_events_by_day_and_track(day, track)
        return {"day": day, "track": track, "events": events}

    @router.get("/tracks")
    async def api_tracks() -> list[dict[str, Any]]:
        tracks = event_repository.get_unique_tracks()
        return [
            {"name": t, "event_count": len(event_repository.get_events_by_track(t))} for t in tracks
        ]

    @router.get("/tracks/{track:path}")
    async def api_track_detail(track: str) -> dict[str, Any]:
        events = event_repository.get_events_by_track(track)
        return {"track": track, "events": events}

    @router.get("/speakers")
    async def api_speakers() -> list[dict[str, Any]]:
        return event_repository.get_all_speakers()

    @router.get("/speakers/{speaker_id}")
    async def api_speaker_detail(speaker_id: str) -> dict[str, Any]:
        speaker = event_repository.get_speaker_by_id(speaker_id)
        if speaker is None:
            raise HTTPException(status_code=404, detail="Speaker not found")
        events = event_repository.get_events_by_speaker(speaker_id)
        return {**speaker, "events": events}

    @router.get("/analytics")
    async def api_analytics() -> dict[str, Any]:
        stats = event_repository.get_stats()
        room_stats = event_repository.get_room_stats()
        speaker_stats = event_repository.get_speaker_stats()
        topic_stats = event_repository.get_topic_stats()
        return {
            "stats": stats,
            "room_stats": room_stats,
            "speaker_stats": speaker_stats,
            "topic_stats": topic_stats,
        }

    @router.get("/rooms")
    async def api_rooms() -> list[str]:
        return event_repository.get_unique_rooms()

    @router.get("/export/events.csv")
    async def export_events_csv() -> StreamingResponse:
        events = event_repository.get_all_events(sort="time")
        return _csv_response(events, "events.csv")

    @router.get("/export/speakers.csv")
    async def export_speakers_csv() -> StreamingResponse:
        speakers = event_repository.get_all_speakers()
        return _csv_response(speakers, "speakers.csv")

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
