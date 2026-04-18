"""EdgeTtsEngine unit tests — streaming with a fake Communicate class."""

from __future__ import annotations

import pytest

from jimao_translator.exceptions import TtsError, UnsupportedLanguageError
from jimao_translator.tts.engines.edge_tts_engine import (
    EdgeTtsEngine,
    _clamp_rate,
    _rate_to_edge_str,
)


class _FakeCommunicate:
    last_args: dict | None = None
    raise_on_stream: Exception | None = None

    def __init__(self, text: str, voice: str, rate: str = "+0%") -> None:
        type(self).last_args = {"text": text, "voice": voice, "rate": rate}

    async def stream(self):
        if type(self).raise_on_stream is not None:
            raise type(self).raise_on_stream
        yield {"type": "audio", "data": b"ab"}
        yield {"type": "audio", "data": b"cd"}
        yield {"type": "WordBoundary", "data": b"skipme"}


class TestEdgeTtsEngine:
    def test_rate_clamp_and_format(self) -> None:
        assert _clamp_rate(0.1) == 0.5
        assert _clamp_rate(5.0) == 2.0
        assert _clamp_rate(1.0) == 1.0
        assert _rate_to_edge_str(1.0) == "+0%"
        assert _rate_to_edge_str(1.5) == "+50%"
        assert _rate_to_edge_str(0.75) == "-25%"

    def test_supported_languages(self) -> None:
        tts = EdgeTtsEngine()
        assert {"zh", "en", "ja", "ko"} <= tts.supported_languages

    async def test_synthesize_streams_audio_chunks(self) -> None:
        _FakeCommunicate.raise_on_stream = None
        tts = EdgeTtsEngine(communicate_cls=_FakeCommunicate)
        chunks: list[bytes] = []
        async for c in tts.synthesize("hello", "en", rate=1.5):
            chunks.append(c)
        assert chunks == [b"ab", b"cd"]
        assert _FakeCommunicate.last_args is not None
        assert _FakeCommunicate.last_args["voice"] == "en-US-JennyNeural"
        assert _FakeCommunicate.last_args["rate"] == "+50%"

    async def test_empty_text_rejected(self) -> None:
        tts = EdgeTtsEngine(communicate_cls=_FakeCommunicate)
        with pytest.raises(ValueError):
            async for _ in tts.synthesize("", "en"):
                pass

    async def test_unsupported_language(self) -> None:
        tts = EdgeTtsEngine(communicate_cls=_FakeCommunicate)
        with pytest.raises(UnsupportedLanguageError):
            async for _ in tts.synthesize("hi", "xh"):
                pass

    async def test_backend_error_wrapped_as_tts_error(self) -> None:
        _FakeCommunicate.raise_on_stream = RuntimeError("backend boom")
        tts = EdgeTtsEngine(communicate_cls=_FakeCommunicate)
        try:
            with pytest.raises(TtsError):
                async for _ in tts.synthesize("hi", "en"):
                    pass
        finally:
            _FakeCommunicate.raise_on_stream = None
