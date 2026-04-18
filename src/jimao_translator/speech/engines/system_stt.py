"""T210: SystemSpeechRecognizer — wraps `SpeechRecognition` + Google's free STT.

Audio bytes are WAV-framed in memory before being handed to the backend; the
raw payload is never touched by disk I/O (see `recognize()`).
"""

from __future__ import annotations

import asyncio
import io
import logging
import wave
from typing import Any

from ...exceptions import NoSpeechDetectedError, RecognitionError, UnsupportedLanguageError
from ...models.enums import LanguageCode
from ...models.voice import VoiceSession

logger = logging.getLogger(__name__)

_SUPPORTED_MAP = {
    "zh": "zh-CN",
    "en": "en-US",
    "ja": "ja-JP",
    "ko": "ko-KR",
}


class SystemSpeechRecognizer:
    """Production STT backed by Google's free endpoint via the SpeechRecognition package."""

    name: str = "speech_recognition:google"

    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        sample_width: int = 2,
        channels: int = 1,
        backend: Any | None = None,
    ) -> None:
        self._sample_rate = sample_rate
        self._sample_width = sample_width
        self._channels = channels
        if backend is None:
            import speech_recognition as sr  # lazy import

            self._sr = sr
            self._recognizer = sr.Recognizer()
        else:
            self._sr = backend["module"]
            self._recognizer = backend["recognizer"]

    @property
    def supported_languages(self) -> set[str]:
        return set(_SUPPORTED_MAP)

    async def recognize(
        self,
        audio_bytes: bytes,
        language: str | None = None,
    ) -> VoiceSession:
        if not audio_bytes:
            raise NoSpeechDetectedError("empty audio buffer")

        if language is not None and language not in _SUPPORTED_MAP:
            raise UnsupportedLanguageError(language)

        hint_lang = language or "zh"
        locale = _SUPPORTED_MAP[hint_lang]

        wav_bytes = _frame_as_wav(
            audio_bytes, self._sample_rate, self._sample_width, self._channels
        )

        def _do_recognize() -> tuple[str, LanguageCode]:
            audio_data = self._sr.AudioData(wav_bytes, self._sample_rate, self._sample_width)
            try:
                text = self._recognizer.recognize_google(audio_data, language=locale)
            except self._sr.UnknownValueError as err:
                raise NoSpeechDetectedError("no speech detected") from err
            except self._sr.RequestError as err:
                raise RecognitionError(str(err)) from err
            return text, LanguageCode(hint_lang)

        text, detected = await asyncio.to_thread(_do_recognize)

        return VoiceSession(
            recognized_text=text,
            recognition_confidence=0.8,  # Google's free endpoint does not return a score
            source_language=detected,
        )


def _frame_as_wav(pcm_bytes: bytes, sample_rate: int, sample_width: int, channels: int) -> bytes:
    """Wrap raw PCM bytes with a WAV header in memory (no disk writes)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(sample_rate)
        w.writeframes(pcm_bytes)
    return buf.getvalue()
