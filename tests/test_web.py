"""Tests for the FastAPI web app endpoints."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_returns_healthy_status(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_includes_version(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "version" in data


class TestIndexPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200

    def test_contains_title(self, client: TestClient) -> None:
        response = client.get("/")
        assert "FOSDEM Explorer" in response.text

    def test_shows_event_count(self, client: TestClient) -> None:
        response = client.get("/")
        # 3 sample events seeded
        assert "3" in response.text

    def test_shows_day_links(self, client: TestClient) -> None:
        response = client.get("/")
        assert "2026-02-07" in response.text
        assert "2026-02-08" in response.text

    def test_contains_search_bar(self, client: TestClient) -> None:
        response = client.get("/")
        assert 'name="q"' in response.text
        assert "/api/events/search" in response.text


class TestDayPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/day/2026-02-07")
        assert response.status_code == 200

    def test_shows_tracks_for_day(self, client: TestClient) -> None:
        response = client.get("/day/2026-02-07")
        assert "Rust" in response.text
        assert "Python" in response.text

    def test_nonexistent_day_shows_no_tracks(self, client: TestClient) -> None:
        response = client.get("/day/2099-01-01")
        assert response.status_code == 200


class TestTrackPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/day/2026-02-07/track/Rust")
        assert response.status_code == 200

    def test_shows_events_in_track(self, client: TestClient) -> None:
        response = client.get("/day/2026-02-07/track/Rust")
        assert "Intro to Rust" in response.text

    def test_nonexistent_track_returns_200(self, client: TestClient) -> None:
        response = client.get("/day/2026-02-07/track/Go")
        assert response.status_code == 200


class TestApiEvents:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/events")
        assert response.status_code == 200

    def test_returns_html_partial(self, client: TestClient) -> None:
        response = client.get("/api/events")
        assert "Intro to Rust" in response.text


class TestApiEventsSearch:
    def test_search_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/events/search?q=Rust")
        assert response.status_code == 200

    def test_search_finds_matching_events(self, client: TestClient) -> None:
        response = client.get("/api/events/search?q=Rust")
        assert "Intro to Rust" in response.text

    def test_search_no_results(self, client: TestClient) -> None:
        response = client.get("/api/events/search?q=nonexistent")
        assert response.status_code == 200
        assert "No events found" in response.text

    def test_search_empty_query_returns_empty(self, client: TestClient) -> None:
        response = client.get("/api/events/search?q=")
        assert response.status_code == 200
        # Empty query should not show results
        assert "Intro to Rust" not in response.text

    def test_search_by_abstract(self, client: TestClient) -> None:
        response = client.get("/api/events/search?q=under+the+hood")
        assert "DuckDB Internals" in response.text
