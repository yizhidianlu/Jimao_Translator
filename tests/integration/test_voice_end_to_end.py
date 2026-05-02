"""T202 + T203: Voice translation end-to-end + low-confidence warning."""

from __future__ import annotations

from pathlib import Path

import pytest

from jimao_translator.models.enums import LanguageCode
from jimao_translator.speech.engines.mock import MockSpeechRecognizer
from jimao_translator.speech.orchestrator import VoiceTranslationOrchestrator
from jimao_translator.storage.history import TranslationHistoryRepository
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.service import TranslationService
from jimao_translator.tts.engines.mock import MockTtsEngine


@pytest.fixture()
def history_repo(tmp_path: Path) -> TranslationHistoryRepository:
    return TranslationHistoryRepository(path=tmp_path / "h.json")


class TestVoiceEndToEnd:
    async def test_speak_zh_get_english_tts(
        self, history_repo: TranslationHistoryRepository
    ) -> None:
        """T202: audio bytes → recognize → translate → tts produces audio chunks."""
        stt = MockSpeechRecognizer(
            transcript="你好", confidence=0.95, detected_language=LanguageCode.ZH
        )
        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=history_repo,
            history_enabled=False,
        )
        orchestrator = VoiceTranslationOrchestrator(
            recognizer=stt,
            translation_service=svc,
            tts_engine=MockTtsEngine(chunks=4, chunk_size=8),
        )

        outcome = await orchestrator.run_once(
            audio_bytes=b"fake-audio",
            target_language=LanguageCode.EN,
        )

        assert outcome.session.recognized_text == "你好"
        assert outcome.result.translated_text == "Hello"
        assert outcome.session.source_language is LanguageCode.ZH
        assert len(outcome.audio_chunks) == 4

    async def test_low_confidence_flagged(self, history_repo: TranslationHistoryRepository) -> None:
        """T203: confidence < 0.6 surfaced as low_confidence=True."""
        stt = MockSpeechRecognizer(transcript="mumble", confidence=0.35)
        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=history_repo,
            history_enabled=False,
        )
        orchestrator = VoiceTranslationOrchestrator(
            recognizer=stt,
            translation_service=svc,
            tts_engine=MockTtsEngine(),
        )
        outcome = await orchestrator.run_once(audio_bytes=b"a", target_language=LanguageCode.EN)
        assert outcome.low_confidence is True
