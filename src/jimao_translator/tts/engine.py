"""T042: TtsEngine Protocol (see contracts/tts-engine.md)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class TtsEngine(Protocol):
    """Abstract text-to-speech engine."""

    def synthesize(
        self,
        text: str,
        language: str,
        rate: float = 1.0,
    ) -> AsyncIterator[bytes]:
        """Stream synthesized audio bytes (MP3 or PCM).

        Args:
            text: text to speak (1..5000 chars).
            language: ISO 639-1 code (zh / en / ja / ko).
            rate: playback speed, 0.5..2.0. Out-of-range values are clamped.

        Raises:
            TtsError: synthesis failure (network, auth).
            UnsupportedLanguageError: language not supported.
        """
        ...

    @property
    def name(self) -> str: ...

    @property
    def supported_languages(self) -> set[str]: ...
