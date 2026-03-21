"""Tests for the tracks browser, track detail pages, and the tracks API (v1)."""

from fastapi.testclient import TestClient


class TestTracksBrowserPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/tracks")
        assert response.status_code == 200

    def test_lists_all_tracks(self, client: TestClient) -> None:
        response = client.get("/tracks")
        assert "Rust" in response.text
        assert "Python" in response.text
        assert "Databases" in response.text

    def test_shows_talk_counts(self, client: TestClient) -> None:
        response = client.get("/tracks")
        assert "1 talk" in response.text

    def test_links_to_track_detail(self, client: TestClient) -> None:
        response = client.get("/tracks")
        assert "/track/Rust" in response.text

    def test_has_filter_input(self, client: TestClient) -> None:
        response = client.get("/tracks")
        assert 'id="track-filter"' in response.text


class TestTrackDetailPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/track/Rust")
        assert response.status_code == 200

    def test_shows_events_in_track(self, client: TestClient) -> None:
        response = client.get("/track/Rust")
        assert "Intro to Rust" in response.text

    def test_shows_events_across_days(self, client: TestClient) -> None:
        response = client.get("/track/Databases")
        assert "DuckDB Internals" in response.text
        assert "2026-02-08" in response.text

    def test_breadcrumb_links_to_tracks(self, client: TestClient) -> None:
        response = client.get("/track/Rust")
        assert "/tracks" in response.text

    def test_nonexistent_track_returns_404(self, client: TestClient) -> None:
        response = client.get("/track/NoSuchTrack")
        assert response.status_code == 404
        assert "Not found" in response.text

    def test_404_default_back_link(self, client: TestClient) -> None:
        response = client.get("/track/NoSuchTrack")
        assert "Back to tracks" in response.text

    def test_404_referer_back_link(self, client: TestClient) -> None:
        response = client.get("/track/NoSuchTrack", headers={"Referer": "http://testserver/tracks"})
        assert "Back to tracks" in response.text

    def test_track_with_slash_in_name(self, client: TestClient) -> None:
        response = client.get("/track/BOF/Unconference")
        assert response.status_code == 404


class TestApiV1Tracks:
    def test_returns_tracks_with_counts(self, client: TestClient) -> None:
        data = client.get("/api/v1/tracks").json()
        assert len(data) == 3
        names = {t["name"] for t in data}
        assert names == {"Databases", "Python", "Rust"}
        assert all("event_count" in t for t in data)

    def test_track_detail(self, client: TestClient) -> None:
        data = client.get("/api/v1/tracks/Rust").json()
        assert data["track"] == "Rust"
        assert len(data["events"]) == 1
