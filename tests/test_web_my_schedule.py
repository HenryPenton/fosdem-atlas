"""Tests for the My Schedule page, iCal export, and the events-by-ids API used by the schedule."""

from fastapi.testclient import TestClient


class TestMySchedulePage:
    def test_renders(self, client: TestClient) -> None:
        resp = client.get("/my-schedule")
        assert resp.status_code == 200
        assert "My Schedule" in resp.text

    def test_contains_js_reference(self, client: TestClient) -> None:
        resp = client.get("/my-schedule")
        assert "my-schedule.js" in resp.text

    def test_transfer_section_present(self, client: TestClient) -> None:
        resp = client.get("/my-schedule")
        assert "transfer-details" in resp.text
        assert "Transfer Schedule" in resp.text

    def test_export_copy_button_present(self, client: TestClient) -> None:
        resp = client.get("/my-schedule")
        assert "transfer-copy-btn" in resp.text
        assert "Copy to Clipboard" in resp.text

    def test_import_merge_and_overwrite_buttons_present(self, client: TestClient) -> None:
        resp = client.get("/my-schedule")
        assert "transfer-merge-btn" in resp.text
        assert "transfer-overwrite-btn" in resp.text
        assert "Merge" in resp.text
        assert "Overwrite" in resp.text

    def test_import_textarea_present(self, client: TestClient) -> None:
        resp = client.get("/my-schedule")
        assert "transfer-import-text" in resp.text

    def test_export_textarea_present(self, client: TestClient) -> None:
        resp = client.get("/my-schedule")
        assert "transfer-export-text" in resp.text


class TestMyScheduleIcalExport:
    def test_returns_ical_with_events(self, client: TestClient) -> None:
        resp = client.get("/my-schedule/export.ics?ids=1,3")
        assert resp.status_code == 200
        assert "text/calendar" in resp.headers["content-type"]
        body = resp.text
        assert "BEGIN:VCALENDAR" in body
        assert "BEGIN:VEVENT" in body
        assert "END:VCALENDAR" in body
        assert "Intro to Rust" in body
        assert "DuckDB Internals" in body

    def test_returns_empty_calendar_no_ids(self, client: TestClient) -> None:
        resp = client.get("/my-schedule/export.ics")
        assert resp.status_code == 200
        body = resp.text
        assert "BEGIN:VCALENDAR" in body
        assert "BEGIN:VEVENT" not in body

    def test_returns_empty_calendar_invalid_ids(self, client: TestClient) -> None:
        resp = client.get("/my-schedule/export.ics?ids=nope,fake")
        assert resp.status_code == 200
        body = resp.text
        assert "BEGIN:VEVENT" not in body

    def test_ical_has_required_fields(self, client: TestClient) -> None:
        resp = client.get("/my-schedule/export.ics?ids=1")
        body = resp.text
        assert "DTSTART:" in body
        assert "DTEND:" in body
        assert "SUMMARY:" in body
        assert "LOCATION:" in body
        assert "UID:" in body


class TestApiV1EventsByIds:
    def test_returns_events(self, client: TestClient) -> None:
        resp = client.get("/api/v1/events/by-ids?ids=1,3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        ids = {e["id"] for e in data}
        assert "1" in ids
        assert "3" in ids

    def test_empty_ids(self, client: TestClient) -> None:
        resp = client.get("/api/v1/events/by-ids")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_unknown_ids(self, client: TestClient) -> None:
        resp = client.get("/api/v1/events/by-ids?ids=nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []
