"""Tests for SpeakerService."""

from src.application.services import SpeakerService


class TestSpeakerService:
    def test_get_all_speakers(self, speaker_service: SpeakerService) -> None:
        speakers = speaker_service.get_all_speakers()
        assert len(speakers) == 1
        assert speakers[0].name == "Mark"

    def test_get_speaker_detail(self, speaker_service: SpeakerService) -> None:
        result = speaker_service.get_speaker_detail("s1")
        assert result is not None
        assert result.name == "Mark"
        assert len(result.events) == 1

    def test_get_speaker_detail_not_found(self, speaker_service: SpeakerService) -> None:
        result = speaker_service.get_speaker_detail("nonexistent")
        assert result is None

    def test_get_all_speakers_cached(self, speaker_service: SpeakerService) -> None:
        first = speaker_service.get_all_speakers()
        second = speaker_service.get_all_speakers()
        assert first is second

    def test_get_speaker_detail_cached(self, speaker_service: SpeakerService) -> None:
        first = speaker_service.get_speaker_detail("s1")
        second = speaker_service.get_speaker_detail("s1")
        assert first is second

    def test_invalidate_cache(self, speaker_service: SpeakerService) -> None:
        speaker_service.get_all_speakers()
        speaker_service.get_speaker_detail("s1")
        speaker_service.invalidate_cache()
        # Re-fetch works after invalidation
        speakers = speaker_service.get_all_speakers()
        assert len(speakers) == 1
