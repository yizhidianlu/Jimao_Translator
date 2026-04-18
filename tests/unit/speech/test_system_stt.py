"""SystemSpeechRecognizer unit tests with a fake SpeechRecognition backend."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from jimao_translator.exceptions import (
    NoSpeechDetectedError,
    RecognitionError,
    UnsupportedLanguageError,
)
from jimao_translator.models.enums import LanguageCode
from jimao_translator.speech.engines.system_stt import SystemSpeechRecognizer


class _FakeSR:
    class UnknownValueError(Exception):
        pass

    class RequestError(Exception):
        pass

    class AudioData:
        def __init__(self, data: bytes, sample_rate: int, sample_width: int) -> None:
            self.data = data
            self.sample_rate = sample_rate
            self.sample_width = sample_width


def _make_backend(recognize_result: str | Exception) -> dict:
    recognizer = MagicMock()
    if isinstance(recognize_result, Exception):
        recognizer.recognize_google.side_effect = recognize_result
    else:
        recognizer.recognize_google.return_value = recognize_result
    return {"module": _FakeSR, "recognizer": recognizer}


class TestSystemSpeechRecognizer:
    def test_supported_languages(self) -> None:
        rec = SystemSpeechRecognizer(backend=_make_backend("ok"))
        assert {"zh", "en", "ja", "ko"} <= rec.supported_languages

    async def test_recognizes_audio_to_text(self) -> None:
        backend = _make_backend("你好")
        rec = SystemSpeechRecognizer(backend=backend)
        session = await rec.recognize(b"\x00\x01" * 100, language="zh")
        assert session.recognized_text == "你好"
        assert session.source_language is LanguageCode.ZH
        backend["recognizer"].recognize_google.assert_called_once()

    async def test_rejects_empty_audio(self) -> None:
        rec = SystemSpeechRecognizer(backend=_make_backend("x"))
        with pytest.raises(NoSpeechDetectedError):
            await rec.recognize(b"", language="zh")

    async def test_unsupported_language(self) -> None:
        rec = SystemSpeechRecognizer(backend=_make_backend("x"))
        with pytest.raises(UnsupportedLanguageError):
            await rec.recognize(b"\x00\x01", language="xh")

    async def test_unknown_value_maps_to_no_speech(self) -> None:
        backend = _make_backend(_FakeSR.UnknownValueError("silence"))
        rec = SystemSpeechRecognizer(backend=backend)
        with pytest.raises(NoSpeechDetectedError):
            await rec.recognize(b"\x00\x01" * 50, language="en")

    async def test_request_error_maps_to_recognition_error(self) -> None:
        backend = _make_backend(_FakeSR.RequestError("quota"))
        rec = SystemSpeechRecognizer(backend=backend)
        with pytest.raises(RecognitionError):
            await rec.recognize(b"\x00\x01" * 50, language="en")

    async def test_default_language_is_zh(self) -> None:
        """No language hint → default 'zh'."""
        backend = _make_backend("你好")
        rec = SystemSpeechRecognizer(backend=backend)
        session = await rec.recognize(b"\x00\x01" * 50)
        assert session.source_language is LanguageCode.ZH
