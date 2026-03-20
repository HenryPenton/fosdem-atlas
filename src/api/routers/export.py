"""Export endpoints (CSV, iCal)."""

import csv
import dataclasses
import io

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from src.application.services import ScheduleService, SpeakerService


def create_export_router(
    schedule_service: ScheduleService,
    speaker_service: SpeakerService,
) -> APIRouter:
    router = APIRouter(prefix="/export", tags=["export"])

    @router.get("/events.csv")
    def export_events_csv() -> StreamingResponse:
        events = schedule_service.get_all_events(sort="time")
        return _csv_response([dataclasses.asdict(e) for e in events], "events.csv")

    @router.get("/speakers.csv")
    def export_speakers_csv() -> StreamingResponse:
        speakers = speaker_service.get_all_speakers()
        return _csv_response([dataclasses.asdict(s) for s in speakers], "speakers.csv")

    @router.get("/schedule.ics")
    def export_schedule_ical(
        ids: str = Query(default="", max_length=10000),
    ) -> Response:
        event_ids = [i.strip() for i in ids.split(",") if i.strip()][:200]
        cal = schedule_service.build_ical(event_ids)
        return Response(
            content=cal,
            media_type="text/calendar",
            headers={"Content-Disposition": 'attachment; filename="fosdem-schedule.ics"'},
        )

    return router


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
