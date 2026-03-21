"""Shared CSV utilities for export adapters."""

import csv
import io

import nh3
from fastapi.responses import StreamingResponse


def sanitise_csv_value(value: str | int | float) -> str | int | float:
    """Strip HTML and prefix formula-trigger characters for safe CSV output."""
    if isinstance(value, str):
        value = str(nh3.clean(value, tags=set()))  # strip all HTML tags
        if value and value[0] in ("=", "+", "-", "@"):
            return "\t" + value
    return value


def csv_streaming_response(
    rows: list[dict[str, str | int | float]], filename: str
) -> StreamingResponse:
    if not rows:
        buf = io.StringIO("")
    else:
        buf = io.StringIO()
        sanitised = [{k: sanitise_csv_value(v) for k, v in row.items()} for row in rows]
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(sanitised)
        buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
