"""Export routes – CSV and iCal."""

import dataclasses

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from src.adapters.csv_utils import csv_streaming_response
from src.application.services import ScheduleService, SpeakerService


def create_export_page_router(
    schedule_service: ScheduleService,
    speaker_service: SpeakerService,
) -> APIRouter:
    router = APIRouter(tags=["export"])

    @router.get("/export/events.csv")
    def export_events_csv() -> StreamingResponse:
        events = schedule_service.get_all_events(sort="time")
        return csv_streaming_response([dataclasses.asdict(e) for e in events], "events.csv")

    @router.get("/export/speakers.csv")
    def export_speakers_csv() -> StreamingResponse:
        speakers = speaker_service.get_all_speakers()
        return csv_streaming_response([dataclasses.asdict(s) for s in speakers], "speakers.csv")

    @router.get("/my-schedule/export.ics")
    def my_schedule_ical(
        ids: str = Query(default="", max_length=10000),
    ) -> Response:
        event_ids = schedule_service.parse_event_ids(ids)
        cal = schedule_service.build_ical(event_ids)
        return Response(
            content=cal,
            media_type="text/calendar",
            headers={"Content-Disposition": 'attachment; filename="fosdem-schedule.ics"'},
        )

    return router
