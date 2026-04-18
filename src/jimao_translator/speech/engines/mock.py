"""T051: MockSpeechRecognizer — deterministic STT stub for tests."""

from __future__ import annotations

from ...exceptions import NoSpeechDetectedError, UnsupportedLanguageError
from ...models.enums import LanguageCode
from ...models.voice import VoiceSession

_SUPPORTED = {"zh", "en", "ja", "ko"}


class MockSpeechRecognizer:
    """In-memory STT that echoes a preset transcript; never writes to disk."""

    name: str = "mock-stt"

    def __init__(
        self,
        transcript: str = "你好世界",
        confidence: float = 0.9,
        detected_language: LanguageCode = LanguageCode.ZH,
        raise_no_speech: bool = False,
    ) -> None:
        self._transcript = transcript
        self._confidence = confidence
        self._detected_language = detected_language
        self._raise_no_speech = raise_no_speech

    @property
    def supported_languages(self) -> set[str]:
        return set(_SUPPORTED)

    async def recognize(
        self,
        audio_bytes: bytes,
        language: str | None = None,
    ) -> VoiceSession:
        # Contract: never persist audio — we simply drop our reference.
        del audio_bytes

        if self._raise_no_speech or len(self._transcript.strip()) == 0:
            raise NoSpeechDetectedError("no speech detected in audio")

        if language is not None and language not in _SUPPORTED:
            raise UnsupportedLanguageError(language)

        source_lang = (
            LanguageCode(language) if language in _SUPPORTED else self._detected_language
        )

        return VoiceSession(
            recognized_text=self._transcript,
            recognition_confidence=self._confidence,
            source_language=source_lang,
        )
