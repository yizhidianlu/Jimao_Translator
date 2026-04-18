"""T012: VoiceSession model (STT + optional TTS playback state)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .enums import LanguageCode


def _utcnow() -> datetime:
    return datetime.now(UTC)


class VoiceSession(BaseModel):
    """A single voice-translation interaction."""

    id: UUID = Field(default_factory=uuid4)
    recognized_text: str
    recognition_confidence: float = Field(ge=0.0, le=1.0)
    source_language: LanguageCode
    translation_request_id: UUID | None = None
    tts_played: bool = False
    started_at: datetime = Field(default_factory=_utcnow)
