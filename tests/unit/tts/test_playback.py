"""Unit test for play_stream — consumes async audio chunks into a single buffer."""

from __future__ import annotations

from collections.abc import AsyncIterator

from jimao_translator.tts.playback import play_stream


async def _chunks(parts: list[bytes]) -> AsyncIterator[bytes]:
    for p in parts:
        yield p


class TestPlayStream:
    async def test_concatenates_chunks(self) -> None:
        result = await play_stream(_chunks([b"abc", b"def", b"ghi"]))
        assert result == b"abcdefghi"

    async def test_empty_stream_yields_empty_bytes(self) -> None:
        result = await play_stream(_chunks([]))
        assert result == b""
