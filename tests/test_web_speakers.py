"""Tests for the speakers browser, speaker detail pages, speakers API (v1), and speaker CSV export."""

from fastapi.testclient import TestClient


class TestSpeakersBrowserPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/speakers")
        assert response.status_code == 200

    def test_lists_speakers(self, client: TestClient) -> None:
        response = client.get("/speakers")
        assert "Mark" in response.text

    def test_shows_talk_count(self, client: TestClient) -> None:
        response = client.get("/speakers")
        assert "1 talk" in response.text

    def test_links_to_speaker_detail(self, client: TestClient) -> None:
        response = client.get("/speakers")
        assert "/speaker/s1" in response.text

    def test_shows_speaker_count(self, client: TestClient) -> None:
        response = client.get("/speakers")
        assert "1 speaker" in response.text


class TestSpeakerDetailPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/speaker/s1")
        assert response.status_code == 200

    def test_shows_speaker_name(self, client: TestClient) -> None:
        response = client.get("/speaker/s1")
        assert "Mark" in response.text

    def test_shows_their_talks(self, client: TestClient) -> None:
        response = client.get("/speaker/s1")
        assert "DuckDB Internals" in response.text

    def test_returns_404_for_unknown_speaker(self, client: TestClient) -> None:
        response = client.get("/speaker/nonexistent")
        assert response.status_code == 404

    def test_links_back_to_speakers(self, client: TestClient) -> None:
        response = client.get("/speaker/s1")
        assert "/speakers" in response.text

    def test_event_links_to_detail(self, client: TestClient) -> None:
        response = client.get("/speaker/s1")
        assert "/event/3" in response.text


class TestApiV1Speakers:
    def test_returns_speakers(self, client: TestClient) -> None:
        data = client.get("/api/v1/speakers").json()
        assert len(data) == 1
        assert data[0]["name"] == "Mark"

    def test_speaker_detail(self, client: TestClient) -> None:
        data = client.get("/api/v1/speakers/s1").json()
        assert data["name"] == "Mark"
        assert len(data["events"]) == 1
        assert "bio" in data

    def test_speaker_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/speakers/nonexistent")
        assert response.status_code == 404


class TestExportSpeakersCSV:
    def test_html_route_returns_csv(self, client: TestClient) -> None:
        resp = client.get("/export/speakers.csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        lines = resp.text.strip().splitlines()
        assert len(lines) >= 2  # header + at least 1 speaker

    def test_api_route_returns_csv(self, client: TestClient) -> None:
        resp = client.get("/api/v1/export/speakers.csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
