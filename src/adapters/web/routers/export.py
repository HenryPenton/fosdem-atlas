"""Export routes – CSV and iCal."""

import csv
import dataclasses
import io

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from src.application.services import ScheduleService, SpeakerService


def create_export_page_router(
    schedule_service: ScheduleService,
    speaker_service: SpeakerService,
) -> APIRouter:
    router = APIRouter(tags=["export"])

    @router.get("/export/events.csv")
    def export_events_csv() -> StreamingResponse:
        events = schedule_service.get_all_events(sort="time")
        return _csv_response([dataclasses.asdict(e) for e in events], "events.csv")

    @router.get("/export/speakers.csv")
    def export_speakers_csv() -> StreamingResponse:
        speakers = speaker_service.get_all_speakers()
        return _csv_response([dataclasses.asdict(s) for s in speakers], "speakers.csv")

    @router.get("/my-schedule/export.ics")
    def my_schedule_ical(
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


def _sanitise_csv_value(value: str | int | float) -> str | int | float:
    """Prefix string cells that start with formula-trigger characters."""
    if isinstance(value, str) and value and value[0] in ("=", "+", "-", "@"):
        return "\t" + value
    return value


def _csv_response(rows: list[dict[str, str | int | float]], filename: str) -> StreamingResponse:
    if not rows:
        buf = io.StringIO("")
    else:
        buf = io.StringIO()
        sanitised = [{k: _sanitise_csv_value(v) for k, v in row.items()} for row in rows]
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(sanitised)
        buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
