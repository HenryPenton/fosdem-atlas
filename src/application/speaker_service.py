"""Speaker service – speaker queries and detail views."""

import logging

from src.domain.models import SpeakerDetail, SpeakerSummary
from src.domain.ports import SpeakersRepository

logger = logging.getLogger(__name__)


class SpeakerService:
    """Speaker queries and detail views."""

    def __init__(self, repository: SpeakersRepository) -> None:
        self._repo = repository
        self._speakers_cache: list[SpeakerSummary] | None = None
        self._speaker_detail_cache: dict[str, SpeakerDetail] = {}

    def invalidate_cache(self) -> None:
        logger.debug("Invalidating speaker caches")
        self._speakers_cache = None
        self._speaker_detail_cache.clear()

    def get_all_speakers(self) -> list[SpeakerSummary]:
        if self._speakers_cache is not None:
            return self._speakers_cache
        self._speakers_cache = self._repo.get_all_speakers()
        return self._speakers_cache

    def get_speaker_detail(self, speaker_id: str) -> SpeakerDetail | None:
        """Speaker with their events, or None if not found."""
        if speaker_id in self._speaker_detail_cache:
            return self._speaker_detail_cache[speaker_id]
        speaker = self._repo.get_speaker_by_id(speaker_id)
        if speaker is None:
            return None
        events = self._repo.get_events_by_speaker(speaker_id)
        result = SpeakerDetail(id=speaker.id, name=speaker.name, bio=speaker.bio, events=events)
        if len(self._speaker_detail_cache) >= 256:
            self._speaker_detail_cache.pop(next(iter(self._speaker_detail_cache)))
        self._speaker_detail_cache[speaker_id] = result
        return result
