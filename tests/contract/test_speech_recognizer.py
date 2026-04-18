"""T200: Contract tests for SpeechRecognizer Protocol."""

from __future__ import annotations

import pytest

from jimao_translator.exceptions import NoSpeechDetectedError, UnsupportedLanguageError
from jimao_translator.models.enums import LanguageCode
from jimao_translator.speech.engines.mock import MockSpeechRecognizer
from jimao_translator.speech.recognizer import SpeechRecognizer


@pytest.fixture()
def recognizer() -> SpeechRecognizer:
    return MockSpeechRecognizer()


class TestSpeechRecognizerContract:
    async def test_recognize_returns_voice_session(
        self, recognizer: SpeechRecognizer
    ) -> None:
        session = await recognizer.recognize(b"\x00" * 1024)
        assert session.recognized_text
        assert 0.0 <= session.recognition_confidence <= 1.0

    async def test_recognize_empty_audio_raises_no_speech(self) -> None:
        silent = MockSpeechRecognizer(transcript="", raise_no_speech=True)
        with pytest.raises(NoSpeechDetectedError):
            await silent.recognize(b"")

    async def test_recognize_pure_silence_raises_no_speech(self) -> None:
        silent = MockSpeechRecognizer(raise_no_speech=True)
        with pytest.raises(NoSpeechDetectedError):
            await silent.recognize(b"\x00" * 16_000)

    async def test_recognize_low_confidence_still_returns(self) -> None:
        r = MockSpeechRecognizer(transcript="mumble", confidence=0.35)
        session = await r.recognize(b"audio")
        assert session.recognition_confidence == 0.35
        assert session.recognized_text == "mumble"

    async def test_recognize_auto_detects_language_when_hint_none(
        self, recognizer: SpeechRecognizer
    ) -> None:
        session = await recognizer.recognize(b"audio", language=None)
        assert session.source_language is not LanguageCode.AUTO

    async def test_recognize_does_not_persist_audio_to_disk(
        self, recognizer: SpeechRecognizer, tmp_path, monkeypatch
    ) -> None:
        """FR-016: raw audio bytes MUST NOT be written to disk."""
        import os
        import shutil

        opened_paths: list[str] = []
        real_open = os.open

        def tracking_open(path, *args, **kwargs):
            opened_paths.append(str(path))
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr(os, "open", tracking_open)

        real_copy = shutil.copyfileobj
        copyfile_calls: list[tuple] = []

        def tracking_copy(src, dst, *a, **kw):
            copyfile_calls.append((src, dst))
            return real_copy(src, dst, *a, **kw)

        monkeypatch.setattr(shutil, "copyfileobj", tracking_copy)

        audio = b"\x01\x02\x03" * 2048
        await recognizer.recognize(audio)

        # The only file opens we tolerate are ones not under tmp_path (stdlib caches etc.);
        # none should include our audio bytes.
        for p in opened_paths:
            assert ".wav" not in p.lower()
            assert ".mp3" not in p.lower()
            assert ".pcm" not in p.lower()
            assert "audio" not in p.lower().split(os.sep)[-1]
        assert copyfile_calls == []

    def test_supported_languages_includes_zh_en_ja_ko(
        self, recognizer: SpeechRecognizer
    ) -> None:
        assert {"zh", "en", "ja", "ko"} <= recognizer.supported_languages
