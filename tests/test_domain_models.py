"""Tests for domain models – pure logic, no I/O."""

from datetime import datetime

from src.domain.models import (
    AnalyticsData,
    ConferenceStats,
    EventDetail,
    EventSummary,
    GridData,
    HeatmapCell,
    RoomCount,
    RoomStats,
    Speaker,
    SpeakerStats,
    TopicStats,
)


def _summary(
    *,
    id: str = "1",
    title: str = "Talk",
    track: str = "Track",
    room: str = "Room A",
    day: str = "2026-02-07",
    start_time: datetime = datetime(2026, 2, 7, 10, 0),
    duration_minutes: int = 30,
) -> EventSummary:
    return EventSummary(
        id=id,
        title=title,
        subtitle="",
        start_time=start_time,
        duration_minutes=duration_minutes,
        room=room,
        track=track,
        day=day,
    )


class TestEventDetailToSummary:
    def test_projects_all_fields(self) -> None:
        detail = EventDetail(
            id="1",
            title="Intro to Rust",
            subtitle="A primer",
            abstract="Learn Rust basics",
            start_time=datetime(2026, 2, 7, 10, 0),
            duration_minutes=30,
            room="Room A",
            track="Rust",
            day="2026-02-07",
            speakers=[Speaker(id="s1", name="Alice")],
        )
        summary = detail.to_summary()
        assert isinstance(summary, EventSummary)
        assert summary.id == "1"
        assert summary.title == "Intro to Rust"
        assert summary.subtitle == "A primer"
        assert summary.abstract == "Learn Rust basics"
        assert summary.start_time == datetime(2026, 2, 7, 10, 0)
        assert summary.duration_minutes == 30
        assert summary.room == "Room A"
        assert summary.track == "Rust"
        assert summary.day == "2026-02-07"


class TestGridDataFromEvents:
    def test_basic_grid(self) -> None:
        events = [
            _summary(id="1", title="Intro to Rust", room="Room A", track="Rust"),
            _summary(
                id="2",
                title="Python Packaging",
                room="Room B",
                track="Python",
                start_time=datetime(2026, 2, 7, 11, 0),
            ),
        ]
        data = GridData.from_events(
            events,
            days=["2026-02-07"],
            selected_day="2026-02-07",
            rooms=["Room A", "Room B"],
        )
        assert data.selected_day == "2026-02-07"
        assert "Room A" in data.rooms
        assert "Room B" in data.rooms
        assert len(data.time_slots) > 0
        assert len(data.grid) > 0

    def test_events_placed_in_hour(self) -> None:
        events = [
            _summary(
                id="1",
                title="Intro to Rust",
                room="Room A",
                start_time=datetime(2026, 2, 7, 10, 0),
            ),
        ]
        data = GridData.from_events(
            events,
            days=["2026-02-07"],
            selected_day="2026-02-07",
            rooms=["Room A"],
        )
        assert "Room A" in data.grid.get("10:00", {})
        cell_events = data.grid["10:00"]["Room A"]
        assert any(ev.title == "Intro to Rust" for ev in cell_events)

    def test_empty_events(self) -> None:
        data = GridData.from_events(
            [],
            days=["2026-02-07"],
            selected_day="2026-02-07",
            rooms=[],
        )
        assert data.grid == {}
        assert data.time_slots == []
        assert data.room_tracks == {}
        assert data.room_track_changes == {}

    def test_room_tracks_ordered(self) -> None:
        events = [
            _summary(id="1", room="Room A", track="Rust"),
            _summary(
                id="2",
                room="Room B",
                track="Python",
                start_time=datetime(2026, 2, 7, 11, 0),
            ),
        ]
        data = GridData.from_events(
            events,
            days=["2026-02-07"],
            selected_day="2026-02-07",
            rooms=["Room A", "Room B"],
        )
        assert data.room_tracks["Room A"] == ["Rust"]
        assert data.room_tracks["Room B"] == ["Python"]
        assert data.room_track_changes["Room A"] == {}
        assert data.room_track_changes["Room B"] == {}

    def test_track_changes(self) -> None:
        events = [
            _summary(
                id="t1",
                title="First Talk",
                track="Track A",
                room="Room A",
                start_time=datetime(2026, 2, 7, 10, 0),
            ),
            _summary(
                id="t2",
                title="Second Talk",
                track="Track B",
                room="Room A",
                start_time=datetime(2026, 2, 7, 11, 0),
            ),
        ]
        data = GridData.from_events(
            events,
            days=["2026-02-07"],
            selected_day="2026-02-07",
            rooms=["Room A"],
        )
        assert data.room_tracks["Room A"] == ["Track A", "Track B"]
        assert data.room_track_changes["Room A"].get("11:00") == "Track B"

    def test_time_slots_cover_range(self) -> None:
        events = [
            _summary(
                id="1",
                start_time=datetime(2026, 2, 7, 10, 15),
                duration_minutes=90,
                room="Room A",
            ),
        ]
        data = GridData.from_events(
            events,
            days=["2026-02-07"],
            selected_day="2026-02-07",
            rooms=["Room A"],
        )
        hours = [ts.hour for ts in data.time_slots]
        assert 10 in hours
        assert 11 in hours


class TestAnalyticsDataFromRawStats:
    def test_computes_heatmap_grid(self) -> None:
        room_stats = RoomStats(
            events_per_room=[RoomCount(room="Room A", count=5)],
            heatmap=[
                HeatmapCell(day="2026-02-07", hour=10, count=3),
                HeatmapCell(day="2026-02-07", hour=11, count=2),
                HeatmapCell(day="2026-02-08", hour=10, count=1),
            ],
        )
        stats = ConferenceStats(total_events=6, total_speakers=2, total_tracks=1, total_rooms=1)
        data = AnalyticsData.from_raw_stats(
            stats=stats,
            room_stats=room_stats,
            speaker_stats=SpeakerStats(),
            topic_stats=TopicStats(),
        )
        assert data.heatmap_days == ["2026-02-07", "2026-02-08"]
        assert data.heatmap_hours == [10, 11]
        assert data.heatmap_grid["2026-02-07"][10] == 3
        assert data.heatmap_grid["2026-02-07"][11] == 2
        assert data.heatmap_grid["2026-02-08"][10] == 1
        assert data.heatmap_grid["2026-02-08"][11] == 0  # zero-filled
        assert data.max_heatmap_count == 3

    def test_empty_heatmap(self) -> None:
        room_stats = RoomStats()
        stats = ConferenceStats(total_events=0, total_speakers=0, total_tracks=0, total_rooms=0)
        data = AnalyticsData.from_raw_stats(
            stats=stats,
            room_stats=room_stats,
            speaker_stats=SpeakerStats(),
            topic_stats=TopicStats(),
        )
        assert data.heatmap_days == []
        assert data.heatmap_hours == []
        assert data.heatmap_grid == {}
        assert data.max_heatmap_count == 1  # default

    def test_events_per_room_forwarded(self) -> None:
        room_counts = [RoomCount(room="Room A", count=5)]
        room_stats = RoomStats(events_per_room=room_counts)
        stats = ConferenceStats(total_events=5, total_speakers=1, total_tracks=1, total_rooms=1)
        data = AnalyticsData.from_raw_stats(
            stats=stats,
            room_stats=room_stats,
            speaker_stats=SpeakerStats(),
            topic_stats=TopicStats(),
        )
        assert data.events_per_room == room_counts
