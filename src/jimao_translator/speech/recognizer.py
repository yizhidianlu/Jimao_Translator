"""T041: SpeechRecognizer Protocol (see contracts/speech-recognizer.md)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models.voice import VoiceSession


@runtime_checkable
class SpeechRecognizer(Protocol):
    """Abstract speech-to-text engine."""

    async def recognize(
        self,
        audio_bytes: bytes,
        language: str | None = None,
    ) -> VoiceSession:
        """Recognize speech from in-memory audio bytes (WAV/PCM 16kHz preferred).

        Args:
            audio_bytes: raw audio payload. MUST NOT be persisted to disk.
            language: optional ISO 639-1 hint; None triggers auto-detect.

        Raises:
            NoSpeechDetectedError: audio is silence or pure noise.
            RecognitionError: network or engine failure.
            UnsupportedLanguageError: hint language is not supported.
        """
        ...

    @property
    def name(self) -> str:
        """Engine identifier."""
        ...

    @property
    def supported_languages(self) -> set[str]: ...
