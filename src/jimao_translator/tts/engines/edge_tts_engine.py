"""T211: EdgeTtsEngine — Microsoft Edge free TTS via `edge-tts` (async streaming)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from ...exceptions import TtsError, UnsupportedLanguageError

logger = logging.getLogger(__name__)

_VOICE_MAP = {
    "zh": "zh-CN-XiaoxiaoNeural",
    "en": "en-US-JennyNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
}

_SUPPORTED = set(_VOICE_MAP)


def _clamp_rate(rate: float) -> float:
    return max(0.5, min(2.0, rate))


def _rate_to_edge_str(rate: float) -> str:
    pct = int(round((rate - 1.0) * 100))
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"


class EdgeTtsEngine:
    """Streaming TTS backed by edge-tts."""

    name: str = "edge-tts"

    def __init__(
        self, voice_map: dict[str, str] | None = None, communicate_cls: Any | None = None
    ) -> None:
        self._voice_map = voice_map or _VOICE_MAP
        self._communicate_cls = communicate_cls

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

        clamped = _clamp_rate(rate)
        voice = self._voice_map[language]

        if self._communicate_cls is None:
            from edge_tts import Communicate

            communicate_cls = Communicate
        else:
            communicate_cls = self._communicate_cls

        try:
            communicate = communicate_cls(text, voice, rate=_rate_to_edge_str(clamped))
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio" and chunk.get("data"):
                    yield chunk["data"]
        except UnsupportedLanguageError:
            raise
        except Exception as err:  # noqa: BLE001
            raise TtsError(str(err)) from err
