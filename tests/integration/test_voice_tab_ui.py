"""T218: GUI test for VoiceTab — single-speaker + conversation mode."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from jimao_translator.models.enums import LanguageCode
from jimao_translator.speech.engines.mock import MockSpeechRecognizer
from jimao_translator.speech.orchestrator import VoiceTranslationOrchestrator
from jimao_translator.storage.history import TranslationHistoryRepository
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.service import TranslationService
from jimao_translator.tts.engines.mock import MockTtsEngine
from jimao_translator.ui.tabs.voice_tab import VoiceTab

pytestmark = pytest.mark.gui


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app  # type: ignore[return-value]


@pytest.fixture()
def service(tmp_path: Path) -> TranslationService:
    return TranslationService(
        provider=MockTranslationProvider(),
        history_repo=TranslationHistoryRepository(path=tmp_path / "h.json"),
        history_enabled=False,
    )


def _make_audio_provider(payload: bytes = b"fake-pcm"):
    async def _provider() -> bytes:
        return payload
    return _provider


class TestVoiceTabSingleSpeaker:
    async def test_single_speaker_translates_and_renders(
        self, qapp: QApplication, service: TranslationService
    ) -> None:
        stt = MockSpeechRecognizer(
            transcript="你好", confidence=0.9, detected_language=LanguageCode.ZH
        )
        voice = VoiceTranslationOrchestrator(
            recognizer=stt, translation_service=service, tts_engine=MockTtsEngine()
        )
        tab = VoiceTab(voice_orchestrator=voice, audio_provider=_make_audio_provider())
        tab._source_selector.set_language(LanguageCode.ZH)  # noqa: SLF001
        tab._target_selector.set_language(LanguageCode.EN)  # noqa: SLF001

        task = tab.trigger_single()
        await task

        assert tab._recognized_single.toPlainText() == "你好"  # noqa: SLF001
        assert tab._translated_single.toPlainText() == "Hello"  # noqa: SLF001

    async def test_low_confidence_shows_warning(
        self, qapp: QApplication, service: TranslationService
    ) -> None:
        stt = MockSpeechRecognizer(
            transcript="mumble", confidence=0.3, detected_language=LanguageCode.EN
        )
        voice = VoiceTranslationOrchestrator(
            recognizer=stt, translation_service=service, tts_engine=MockTtsEngine()
        )
        tab = VoiceTab(voice_orchestrator=voice, audio_provider=_make_audio_provider())
        tab._source_selector.set_language(LanguageCode.EN)  # noqa: SLF001
        tab._target_selector.set_language(LanguageCode.ZH)  # noqa: SLF001

        task = tab.trigger_single()
        await task

        assert "低" in tab._status.text()  # noqa: SLF001


class TestVoiceTabConversationMode:
    async def test_mode_toggle_switches_view(
        self, qapp: QApplication, service: TranslationService
    ) -> None:
        stt = MockSpeechRecognizer(transcript="你好", detected_language=LanguageCode.ZH)
        voice = VoiceTranslationOrchestrator(
            recognizer=stt, translation_service=service, tts_engine=MockTtsEngine()
        )
        tab = VoiceTab(voice_orchestrator=voice, audio_provider=_make_audio_provider())

        assert tab.is_conversation_mode() is False
        tab.set_conversation_mode(True)
        assert tab.is_conversation_mode() is True

    async def test_counterpart_speaks_renders_translation_on_local_side(
        self, qapp: QApplication, service: TranslationService
    ) -> None:
        stt = MockSpeechRecognizer(
            transcript="hello", confidence=0.9, detected_language=LanguageCode.EN
        )
        voice = VoiceTranslationOrchestrator(
            recognizer=stt, translation_service=service, tts_engine=MockTtsEngine()
        )
        tab = VoiceTab(voice_orchestrator=voice, audio_provider=_make_audio_provider())
        tab._local_lang_selector.set_language(LanguageCode.ZH)  # noqa: SLF001
        tab._counterpart_lang_selector.set_language(LanguageCode.EN)  # noqa: SLF001
        tab.set_conversation_mode(True)

        task = tab.trigger_counterpart_speaks()
        await task

        assert tab._counterpart_panel.recognized_text() == "hello"  # noqa: SLF001
        assert tab._local_panel.translated_text() == "你好"  # noqa: SLF001

    async def test_local_speaks_renders_translation_on_counterpart_side(
        self, qapp: QApplication, service: TranslationService
    ) -> None:
        stt = MockSpeechRecognizer(
            transcript="你好", confidence=0.9, detected_language=LanguageCode.ZH
        )
        voice = VoiceTranslationOrchestrator(
            recognizer=stt, translation_service=service, tts_engine=MockTtsEngine()
        )
        tab = VoiceTab(voice_orchestrator=voice, audio_provider=_make_audio_provider())
        tab._local_lang_selector.set_language(LanguageCode.ZH)  # noqa: SLF001
        tab._counterpart_lang_selector.set_language(LanguageCode.EN)  # noqa: SLF001
        tab.set_conversation_mode(True)

        task = tab.trigger_local_speaks()
        await task

        assert tab._local_panel.recognized_text() == "你好"  # noqa: SLF001
        assert tab._counterpart_panel.translated_text() == "Hello"  # noqa: SLF001
