"""Tests for the analytics page, analytics API (v1), rooms API, CSV exports, and keyword pages."""

from fastapi.testclient import TestClient


class TestAnalyticsPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/analytics")
        assert response.status_code == 200

    def test_contains_title(self, client: TestClient) -> None:
        response = client.get("/analytics")
        assert "Analytics" in response.text

    def test_shows_total_events(self, client: TestClient) -> None:
        response = client.get("/analytics")
        # 3 sample events seeded
        assert "3" in response.text

    def test_shows_events_per_day(self, client: TestClient) -> None:
        response = client.get("/analytics")
        assert "2026-02-07" in response.text
        assert "2026-02-08" in response.text

    def test_shows_events_per_track(self, client: TestClient) -> None:
        response = client.get("/analytics")
        assert "Rust" in response.text
        assert "Python" in response.text
        assert "Databases" in response.text

    def test_shows_events_per_room(self, client: TestClient) -> None:
        response = client.get("/analytics")
        assert "Room A" in response.text
        assert "Room B" in response.text
        assert "Room C" in response.text

    def test_shows_heatmap_section(self, client: TestClient) -> None:
        response = client.get("/analytics")
        assert "Room Usage Heatmap" in response.text

    def test_heatmap_contains_day_labels(self, client: TestClient) -> None:
        response = client.get("/analytics")
        assert "2026-02-07" in response.text
        assert "2026-02-08" in response.text

    def test_heatmap_contains_hour_labels(self, client: TestClient) -> None:
        response = client.get("/analytics")
        assert "10:00" in response.text
        assert "09:00" in response.text

    def test_shows_tab_navigation(self, client: TestClient) -> None:
        response = client.get("/analytics")
        assert "By Day" in response.text
        assert "By Track" in response.text
        assert "By Room" in response.text
        assert "Heatmap" in response.text


class TestApiV1Analytics:
    def test_returns_analytics(self, client: TestClient) -> None:
        data = client.get("/api/v1/analytics").json()
        assert data["stats"]["total_events"] == 3
        assert "room_stats" in data
        assert "speaker_stats" in data
        assert "topic_stats" in data


class TestApiV1Rooms:
    def test_returns_rooms(self, client: TestClient) -> None:
        data = client.get("/api/v1/rooms").json()
        assert set(data) == {"Room A", "Room B", "Room C"}


class TestAnalyticsExportTab:
    def test_analytics_export_tab(self, client: TestClient) -> None:
        resp = client.get("/analytics")
        assert "Export" in resp.text
        assert "/export/events.csv" in resp.text


class TestExportEventsCSV:
    def test_html_route_returns_csv(self, client: TestClient) -> None:
        resp = client.get("/export/events.csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]
        lines = resp.text.strip().splitlines()
        assert len(lines) == 4  # header + 3 events

    def test_api_route_returns_csv(self, client: TestClient) -> None:
        resp = client.get("/api/v1/export/events.csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        lines = resp.text.strip().splitlines()
        assert "id" in lines[0]
        assert len(lines) == 4


class TestKeywordPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/keyword/Rust")
        assert response.status_code == 200

    def test_shows_keyword_in_heading(self, client: TestClient) -> None:
        response = client.get("/keyword/Rust")
        assert "Rust" in response.text

    def test_shows_matching_events(self, client: TestClient) -> None:
        response = client.get("/keyword/Rust")
        assert "Intro to Rust" in response.text

    def test_no_results_for_unknown_keyword(self, client: TestClient) -> None:
        response = client.get("/keyword/zzzznonexistent")
        assert response.status_code == 200
        assert "No talks found" in response.text

    def test_links_to_event_detail(self, client: TestClient) -> None:
        response = client.get("/keyword/Rust")
        assert "/event/1" in response.text

    def test_breadcrumb_links_to_analytics(self, client: TestClient) -> None:
        response = client.get("/keyword/Rust")
        assert "/analytics" in response.text
