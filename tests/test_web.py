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

    def test_contains_filter_dropdowns(self, client: TestClient) -> None:
        response = client.get("/")
        assert 'name="track"' in response.text
        assert 'name="room"' in response.text
        assert 'name="day"' in response.text


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

    def test_track_with_slash_in_name(self, client: TestClient) -> None:
        # Tracks like "BOF/Unconference" contain a slash; the route must capture it
        response = client.get("/day/2026-02-07/track/BOF/Unconference")
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

    def test_filter_by_track(self, client: TestClient) -> None:
        response = client.get("/api/events/search?track=Rust")
        assert response.status_code == 200
        assert "Intro to Rust" in response.text
        assert "Python Packaging" not in response.text

    def test_filter_by_room(self, client: TestClient) -> None:
        response = client.get("/api/events/search?room=Room+B")
        assert response.status_code == 200
        assert "Python Packaging" in response.text
        assert "Intro to Rust" not in response.text

    def test_filter_by_day(self, client: TestClient) -> None:
        response = client.get("/api/events/search?day=2026-02-08")
        assert response.status_code == 200
        assert "DuckDB Internals" in response.text
        assert "Intro to Rust" not in response.text

    def test_filter_combined_with_query(self, client: TestClient) -> None:
        response = client.get("/api/events/search?q=Rust&day=2026-02-07")
        assert response.status_code == 200
        assert "Intro to Rust" in response.text

    def test_filter_no_match(self, client: TestClient) -> None:
        response = client.get("/api/events/search?track=NoSuchTrack")
        assert "No events found" in response.text


class TestSchedulePage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/schedule")
        assert response.status_code == 200

    def test_shows_all_events_grouped_by_day(self, client: TestClient) -> None:
        response = client.get("/schedule")
        assert "Intro to Rust" in response.text
        assert "Python Packaging" in response.text
        assert "DuckDB Internals" in response.text
        assert "2026-02-07" in response.text
        assert "2026-02-08" in response.text

    def test_shows_sort_controls(self, client: TestClient) -> None:
        response = client.get("/schedule")
        assert "sort=time" in response.text
        assert "sort=track" in response.text
        assert "sort=room" in response.text

    def test_sort_time_is_active_by_default(self, client: TestClient) -> None:
        response = client.get("/schedule")
        assert "sort-btn--active" in response.text

    def test_sort_by_track(self, client: TestClient) -> None:
        response = client.get("/schedule?sort=track")
        assert response.status_code == 200
        assert "Intro to Rust" in response.text

    def test_sort_by_room(self, client: TestClient) -> None:
        response = client.get("/schedule?sort=room")
        assert response.status_code == 200
        assert "Intro to Rust" in response.text

    def test_invalid_sort_falls_back_to_time(self, client: TestClient) -> None:
        response = client.get("/schedule?sort=invalid")
        assert response.status_code == 200
        assert "Intro to Rust" in response.text


class TestGridPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/grid")
        assert response.status_code == 200

    def test_defaults_to_first_day(self, client: TestClient) -> None:
        response = client.get("/grid")
        assert "2026-02-07" in response.text

    def test_select_specific_day(self, client: TestClient) -> None:
        response = client.get("/grid?day=2026-02-08")
        assert response.status_code == 200
        assert "DuckDB Internals" in response.text

    def test_shows_rooms_as_columns(self, client: TestClient) -> None:
        response = client.get("/grid?day=2026-02-07")
        assert "Room A" in response.text
        assert "Room B" in response.text

    def test_shows_time_slots(self, client: TestClient) -> None:
        response = client.get("/grid?day=2026-02-07")
        assert "10:00" in response.text

    def test_events_link_to_detail(self, client: TestClient) -> None:
        response = client.get("/grid?day=2026-02-07")
        assert "/event/1" in response.text

    def test_shows_day_picker(self, client: TestClient) -> None:
        response = client.get("/grid")
        assert "day=2026-02-07" in response.text
        assert "day=2026-02-08" in response.text

    def test_invalid_day_falls_back_to_first(self, client: TestClient) -> None:
        response = client.get("/grid?day=invalid")
        assert response.status_code == 200
        # Should still show content (falls back to first day)
        assert "Room A" in response.text

    def test_grid_table_present(self, client: TestClient) -> None:
        response = client.get("/grid?day=2026-02-07")
        assert "schedule-grid" in response.text


class TestEventDetailPage:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert response.status_code == 200

    def test_shows_event_title(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert "Intro to Rust" in response.text

    def test_shows_abstract(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert "Learn Rust basics" in response.text

    def test_shows_speaker(self, client: TestClient) -> None:
        response = client.get("/event/3")
        assert "Mark" in response.text

    def test_shows_track_and_room(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert "Rust" in response.text
        assert "Room A" in response.text

    def test_shows_back_link(self, client: TestClient) -> None:
        response = client.get("/event/1")
        assert "/day/2026-02-07/track/Rust" in response.text

    def test_returns_404_for_unknown_event(self, client: TestClient) -> None:
        response = client.get("/event/nonexistent")
        assert response.status_code == 404


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

    def test_nonexistent_track_returns_200(self, client: TestClient) -> None:
        response = client.get("/track/NoSuchTrack")
        assert response.status_code == 200


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

    def test_track_with_slash_in_name(self, client: TestClient) -> None:
        response = client.get("/track/BOF/Unconference")
        assert response.status_code == 200


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


class TestCacheControl:
    def test_page_has_cache_header(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.headers["Cache-Control"] == "public, max-age=20"

    def test_api_has_cache_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/events")
        assert response.headers["Cache-Control"] == "public, max-age=20"

    def test_health_has_no_cache_header(self, client: TestClient) -> None:
        response = client.get("/health")
        assert "Cache-Control" not in response.headers


class TestApiV1Events:
    def test_returns_json(self, client: TestClient) -> None:
        response = client.get("/api/v1/events")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_event_has_expected_fields(self, client: TestClient) -> None:
        data = client.get("/api/v1/events").json()
        event = data[0]
        for field in ("id", "title", "start_time", "duration_minutes", "room", "track", "day"):
            assert field in event

    def test_sort_by_track(self, client: TestClient) -> None:
        data = client.get("/api/v1/events?sort=track").json()
        assert len(data) == 3


class TestApiV1EventsSearch:
    def test_search_returns_results(self, client: TestClient) -> None:
        data = client.get("/api/v1/events/search?q=Rust").json()
        assert len(data) == 1
        assert data[0]["title"] == "Intro to Rust"

    def test_filter_by_track(self, client: TestClient) -> None:
        data = client.get("/api/v1/events/search?track=Python").json()
        assert len(data) == 1
        assert data[0]["title"] == "Python Packaging"

    def test_empty_query_returns_empty(self, client: TestClient) -> None:
        data = client.get("/api/v1/events/search").json()
        assert data == []


class TestApiV1EventDetail:
    def test_returns_event(self, client: TestClient) -> None:
        data = client.get("/api/v1/events/1").json()
        assert data["title"] == "Intro to Rust"

    def test_includes_speakers(self, client: TestClient) -> None:
        data = client.get("/api/v1/events/3").json()
        assert "speakers" in data
        assert data["speakers"][0]["name"] == "Mark"

    def test_404_for_unknown(self, client: TestClient) -> None:
        response = client.get("/api/v1/events/nonexistent")
        assert response.status_code == 404


class TestApiV1Days:
    def test_returns_days(self, client: TestClient) -> None:
        data = client.get("/api/v1/days").json()
        assert data == ["2026-02-07", "2026-02-08"]

    def test_day_detail_returns_tracks(self, client: TestClient) -> None:
        data = client.get("/api/v1/days/2026-02-07").json()
        assert data["day"] == "2026-02-07"
        assert set(data["tracks"]) == {"Python", "Rust"}
        assert "track_event_counts" in data


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


class TestApiV1Speakers:
    def test_returns_speakers(self, client: TestClient) -> None:
        data = client.get("/api/v1/speakers").json()
        assert len(data) == 1
        assert data[0]["name"] == "Mark"

    def test_speaker_detail(self, client: TestClient) -> None:
        data = client.get("/api/v1/speakers/s1").json()
        assert data["name"] == "Mark"
        assert len(data["events"]) == 1

    def test_speaker_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/speakers/nonexistent")
        assert response.status_code == 404


class TestApiV1Rooms:
    def test_returns_rooms(self, client: TestClient) -> None:
        data = client.get("/api/v1/rooms").json()
        assert set(data) == {"Room A", "Room B", "Room C"}


class TestApiV1Analytics:
    def test_returns_analytics(self, client: TestClient) -> None:
        data = client.get("/api/v1/analytics").json()
        assert data["stats"]["total_events"] == 3
        assert "room_stats" in data
        assert "speaker_stats" in data
        assert "topic_stats" in data


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


class TestAnalyticsExportTab:
    def test_analytics_export_tab(self, client: TestClient) -> None:
        resp = client.get("/analytics")
        assert "Export" in resp.text
        assert "/export/events.csv" in resp.text
