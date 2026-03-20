"""Analytics endpoints."""

from fastapi import APIRouter

from src.api.dtos import (
    AnalyticsDTO,
    ConferenceStatsDTO,
    DayCountDTO,
    HeatmapCellDTO,
    KeywordCountDTO,
    MultiTrackSpeakerDTO,
    RoomCountDTO,
    RoomStatsDTO,
    SpeakerStatsDTO,
    TopicStatsDTO,
    TopSpeakerDTO,
    TrackCountDTO,
)
from src.application.services import AnalyticsService


def create_analytics_router(analytics_service: AnalyticsService) -> APIRouter:
    router = APIRouter(tags=["analytics"])

    @router.get("/analytics")
    def get_analytics() -> AnalyticsDTO:
        data = analytics_service.get_analytics()
        return AnalyticsDTO(
            stats=ConferenceStatsDTO(
                total_events=data.stats.total_events,
                total_speakers=data.stats.total_speakers,
                total_tracks=data.stats.total_tracks,
                total_rooms=data.stats.total_rooms,
                events_per_day=[
                    DayCountDTO(day=d.day, count=d.count) for d in data.stats.events_per_day
                ],
                events_per_track=[
                    TrackCountDTO(track=t.track, count=t.count) for t in data.stats.events_per_track
                ],
            ),
            room_stats=RoomStatsDTO(
                events_per_room=[
                    RoomCountDTO(room=r.room, count=r.count)
                    for r in data.room_stats.events_per_room
                ],
                heatmap=[
                    HeatmapCellDTO(day=h.day, hour=h.hour, count=h.count)
                    for h in data.room_stats.heatmap
                ],
            ),
            speaker_stats=SpeakerStatsDTO(
                top_speakers=[
                    TopSpeakerDTO(id=s.id, name=s.name, talk_count=s.talk_count)
                    for s in data.speaker_stats.top_speakers
                ],
                multi_track_speakers=[
                    MultiTrackSpeakerDTO(
                        id=s.id,
                        name=s.name,
                        track_count=s.track_count,
                        tracks=s.tracks,
                    )
                    for s in data.speaker_stats.multi_track_speakers
                ],
            ),
            topic_stats=TopicStatsDTO(
                keywords=[
                    KeywordCountDTO(term=k.term, count=k.count) for k in data.topic_stats.keywords
                ],
            ),
        )

    return router
