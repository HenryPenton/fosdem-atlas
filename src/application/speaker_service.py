"""Speaker service – speaker queries and detail views."""

from src.domain.models import SpeakerDetail, SpeakerSummary
from src.domain.ports import SpeakersRepository


class SpeakerService:
    """Speaker queries and detail views."""

    def __init__(self, repository: SpeakersRepository) -> None:
        self._repo = repository

    def get_all_speakers(self) -> list[SpeakerSummary]:
        return self._repo.get_all_speakers()

    def get_speaker_detail(self, speaker_id: str) -> SpeakerDetail | None:
        """Speaker with their events, or None if not found."""
        speaker = self._repo.get_speaker_by_id(speaker_id)
        if speaker is None:
            return None
        events = self._repo.get_events_by_speaker(speaker_id)
        return SpeakerDetail(id=speaker.id, name=speaker.name, events=events)
