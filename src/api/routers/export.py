"""Export endpoints (CSV, iCal)."""

import dataclasses

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from src.adapters.csv_utils import csv_streaming_response
from src.application.services import ScheduleService, SpeakerService


def add_export_routes(
    router: APIRouter,
    schedule_service: ScheduleService,
    speaker_service: SpeakerService,
    *,
    events_csv_path: str,
    speakers_csv_path: str,
    ical_path: str,
) -> None:
    """Register the CSV and iCal export handlers on *router* at the given paths."""

    @router.get(events_csv_path)
    def export_events_csv() -> StreamingResponse:
        events = schedule_service.get_all_events(sort="time")
        return csv_streaming_response([dataclasses.asdict(e) for e in events], "events.csv")

    @router.get(speakers_csv_path)
    def export_speakers_csv() -> StreamingResponse:
        speakers = speaker_service.get_all_speakers()
        return csv_streaming_response([dataclasses.asdict(s) for s in speakers], "speakers.csv")

    @router.get(ical_path)
    def export_schedule_ical(
        ids: str = Query(default="", max_length=10000),
    ) -> Response:
        event_ids = schedule_service.parse_event_ids(ids)
        cal = schedule_service.build_ical(event_ids)
        return Response(
            content=cal,
            media_type="text/calendar",
            headers={"Content-Disposition": 'attachment; filename="fosdem-schedule.ics"'},
        )


def create_export_router(
    schedule_service: ScheduleService,
    speaker_service: SpeakerService,
) -> APIRouter:
    router = APIRouter(prefix="/export", tags=["export"])
    add_export_routes(
        router,
        schedule_service,
        speaker_service,
        events_csv_path="/events.csv",
        speakers_csv_path="/speakers.csv",
        ical_path="/schedule.ics",
    )
    return router
