"""T052: MockTtsEngine — deterministic TTS stub for tests."""

from __future__ import annotations

from collections.abc import AsyncIterator

from ...exceptions import UnsupportedLanguageError

_SUPPORTED = {"zh", "en", "ja", "ko"}


def _clamp_rate(rate: float) -> float:
    return max(0.5, min(2.0, rate))


class MockTtsEngine:
    """In-memory TTS that streams a single bytes chunk per invocation."""

    name: str = "mock-tts"

    def __init__(
        self,
        *,
        chunk_size: int = 16,
        chunks: int = 3,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunks = chunks

    @property
    def supported_languages(self) -> set[str]:
        return set(_SUPPORTED)

    async def synthesize(
        self,
        text: str,
        language: str,
        rate: float = 1.0,
    ) -> AsyncIterator[bytes]:
        if not text:
            raise ValueError("text must not be empty")
        if language not in _SUPPORTED:
            raise UnsupportedLanguageError(language)

        _clamp_rate(rate)

        for i in range(self._chunks):
            yield bytes([i % 256]) * self._chunk_size
