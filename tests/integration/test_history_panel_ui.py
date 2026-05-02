"""GUI tests for HistoryPanel + OfflineBanner + MainWindow smoke."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from jimao_translator.llm.providers.mock import MockLlmClient
from jimao_translator.llm.service import ChatService
from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.translation import (
    TranslationHistoryEntry,
    TranslationRequest,
    TranslationResult,
)
from jimao_translator.speech.engines.mock import MockSpeechRecognizer
from jimao_translator.speech.orchestrator import VoiceTranslationOrchestrator
from jimao_translator.storage.history import TranslationHistoryRepository
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.service import TranslationService
from jimao_translator.tts.engines.mock import MockTtsEngine
from jimao_translator.ui.main_window import MainWindow
from jimao_translator.ui.widgets.history_panel import HistoryPanel
from jimao_translator.ui.widgets.offline_banner import OfflineBanner

pytestmark = pytest.mark.gui


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app  # type: ignore[return-value]


def _entry(src: str, tgt: str) -> TranslationHistoryEntry:
    req = TranslationRequest(
        source_text=src,
        source_language=LanguageCode.ZH,
        target_language=LanguageCode.EN,
        mode=TranslationMode.TEXT,
    )
    result = TranslationResult(
        request_id=req.id,
        translated_text=tgt,
        detected_source_language=LanguageCode.ZH,
        confidence=0.9,
        engine="mock",
        completed_at=datetime.now(UTC),
    )
    return TranslationHistoryEntry(request=req, result=result)


class TestHistoryPanel:
    def test_refresh_shows_entries(self, qapp: QApplication, tmp_path: Path) -> None:
        repo = TranslationHistoryRepository(path=tmp_path / "h.json")
        repo.append(_entry("你好", "Hello"))
        repo.append(_entry("世界", "World"))

        panel = HistoryPanel(repo)
        assert panel._list.count() == 2  # noqa: SLF001

    def test_selected_entry_returned(self, qapp: QApplication, tmp_path: Path) -> None:
        repo = TranslationHistoryRepository(path=tmp_path / "h.json")
        repo.append(_entry("你好", "Hello"))
        panel = HistoryPanel(repo)
        panel._list.setCurrentRow(0)  # noqa: SLF001
        selected = panel.selected_entry()
        assert selected is not None
        assert selected.result.translated_text == "Hello"

    def test_entry_selected_signal_fires(self, qapp: QApplication, tmp_path: Path) -> None:
        repo = TranslationHistoryRepository(path=tmp_path / "h.json")
        repo.append(_entry("你好", "Hello"))
        panel = HistoryPanel(repo)
        captured: list[TranslationHistoryEntry] = []
        panel.entry_selected.connect(lambda e: captured.append(e))
        item = panel._list.item(0)  # noqa: SLF001
        panel._on_item_activated(item)  # noqa: SLF001
        assert len(captured) == 1
        assert captured[0].result.translated_text == "Hello"


class TestOfflineBanner:
    def test_hidden_by_default(self, qapp: QApplication) -> None:
        banner = OfflineBanner()
        banner.show()  # parentless widget — explicit show needed for isVisible semantics
        assert banner.is_offline() is False

    def test_set_offline_shows_and_hides(self, qapp: QApplication) -> None:
        banner = OfflineBanner()
        banner.set_offline(True)
        assert banner.is_offline() is True
        banner.set_offline(False)
        assert banner.is_offline() is False


class TestMainWindowSmoke:
    def test_constructs_with_all_services(self, qapp: QApplication, tmp_path: Path) -> None:
        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=TranslationHistoryRepository(path=tmp_path / "h.json"),
            history_enabled=False,
        )
        voice = VoiceTranslationOrchestrator(
            recognizer=MockSpeechRecognizer(),
            translation_service=svc,
            tts_engine=MockTtsEngine(),
        )
        chat = ChatService(llm_client=MockLlmClient())
        win = MainWindow(
            translation_service=svc,
            voice_orchestrator=voice,
            chat_service=chat,
        )
        assert win.text_tab is not None
        assert win.voice_tab is not None
        assert win.chat_tab is not None

    def test_tab_mapping(self, qapp: QApplication, tmp_path: Path) -> None:
        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=TranslationHistoryRepository(path=tmp_path / "h.json"),
            history_enabled=False,
        )
        win = MainWindow(translation_service=svc)
        win.select_tab(TranslationMode.VOICE)
        assert win.active_tab_mode() is TranslationMode.VOICE
        win.select_tab(TranslationMode.TEXT)
        assert win.active_tab_mode() is TranslationMode.TEXT
