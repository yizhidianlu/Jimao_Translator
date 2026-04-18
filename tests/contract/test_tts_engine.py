"""T201: Contract tests for TtsEngine Protocol."""

from __future__ import annotations

import pytest

from jimao_translator.exceptions import UnsupportedLanguageError
from jimao_translator.tts.engine import TtsEngine
from jimao_translator.tts.engines.mock import MockTtsEngine


@pytest.fixture()
def engine() -> TtsEngine:
    return MockTtsEngine(chunks=3, chunk_size=16)


class TestTtsEngineContract:
    async def test_synthesize_yields_audio_chunks(self, engine: TtsEngine) -> None:
        chunks: list[bytes] = []
        async for chunk in engine.synthesize("hello", language="en"):
            chunks.append(chunk)
        assert len(chunks) == 3
        assert all(isinstance(c, bytes) and len(c) > 0 for c in chunks)

    async def test_synthesize_empty_text_raises_value_error(
        self, engine: TtsEngine
    ) -> None:
        with pytest.raises(ValueError):
            async for _ in engine.synthesize("", language="en"):
                pass

    async def test_synthesize_clamps_out_of_range_rate(self, engine: TtsEngine) -> None:
        # No exception for rates outside [0.5, 2.0]; engine clamps internally.
        async for _ in engine.synthesize("hi", language="en", rate=10.0):
            pass
        async for _ in engine.synthesize("hi", language="en", rate=-5.0):
            pass

    async def test_synthesize_raises_unsupported_language(self, engine: TtsEngine) -> None:
        with pytest.raises(UnsupportedLanguageError):
            async for _ in engine.synthesize("hi", language="fr"):
                pass

    async def test_first_chunk_within_500ms(self, engine: TtsEngine) -> None:
        import asyncio
        import time

        start = time.perf_counter()
        it = engine.synthesize("hi", language="en").__aiter__()
        await asyncio.wait_for(it.__anext__(), timeout=0.5)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5

    def test_supported_languages_includes_zh_en_ja_ko(self, engine: TtsEngine) -> None:
        assert {"zh", "en", "ja", "ko"} <= engine.supported_languages
