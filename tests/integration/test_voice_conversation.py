"""T205: Conversation-mode auto language detection (bi-directional voice)."""

from __future__ import annotations

from pathlib import Path

import pytest

from jimao_translator.models.enums import LanguageCode
from jimao_translator.speech.engines.mock import MockSpeechRecognizer
from jimao_translator.speech.orchestrator import (
    ConversationOrchestrator,
    VoiceTranslationOrchestrator,
)
from jimao_translator.storage.history import TranslationHistoryRepository
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.service import TranslationService
from jimao_translator.tts.engines.mock import MockTtsEngine


@pytest.fixture()
def history_repo(tmp_path: Path) -> TranslationHistoryRepository:
    return TranslationHistoryRepository(path=tmp_path / "h.json")


class TestConversationMode:
    async def test_english_speaker_produces_chinese_output(
        self, history_repo: TranslationHistoryRepository
    ) -> None:
        stt = MockSpeechRecognizer(
            transcript="hello", confidence=0.9, detected_language=LanguageCode.EN
        )
        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=history_repo,
            history_enabled=False,
        )
        voice = VoiceTranslationOrchestrator(
            recognizer=stt, translation_service=svc, tts_engine=MockTtsEngine()
        )
        convo = ConversationOrchestrator(
            voice=voice,
            local_language=LanguageCode.ZH,
            counterpart_language=LanguageCode.EN,
        )

        outcome = await convo.counterpart_speaks(audio_bytes=b"en-audio")

        assert outcome.session.source_language is LanguageCode.EN
        assert outcome.result.translated_text == "你好"
        assert outcome.target_language is LanguageCode.ZH

    async def test_local_speaker_produces_english_output(
        self, history_repo: TranslationHistoryRepository
    ) -> None:
        stt = MockSpeechRecognizer(
            transcript="你好", confidence=0.9, detected_language=LanguageCode.ZH
        )
        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=history_repo,
            history_enabled=False,
        )
        voice = VoiceTranslationOrchestrator(
            recognizer=stt, translation_service=svc, tts_engine=MockTtsEngine()
        )
        convo = ConversationOrchestrator(
            voice=voice,
            local_language=LanguageCode.ZH,
            counterpart_language=LanguageCode.EN,
        )

        outcome = await convo.local_speaks(audio_bytes=b"zh-audio")

        assert outcome.result.translated_text == "Hello"
        assert outcome.target_language is LanguageCode.EN
