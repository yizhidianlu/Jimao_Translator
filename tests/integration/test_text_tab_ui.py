"""T118: GUI test for TextTab translation flow (pytest-qt + pytest-asyncio)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from jimao_translator.models.enums import LanguageCode
from jimao_translator.storage.history import TranslationHistoryRepository
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.service import TranslationService
from jimao_translator.ui.tabs.text_tab import TextTab

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


class TestTextTabFlow:
    async def test_translate_populates_output(
        self, qapp: QApplication, service: TranslationService
    ) -> None:
        tab = TextTab(service=service, default_target=LanguageCode.EN)
        tab.set_input_text("你好")
        tab._source_selector.set_language(LanguageCode.ZH)  # noqa: SLF001
        task = tab.trigger_translate()
        await task

        assert tab.output_text() == "Hello"
        assert tab._copy_btn.isEnabled()  # noqa: SLF001

    async def test_empty_input_flagged_to_status(
        self, qapp: QApplication, service: TranslationService
    ) -> None:
        tab = TextTab(service=service)
        tab.set_input_text("")
        task = tab.trigger_translate()
        await task

        assert tab.output_text() == ""
        assert "输入无效" in tab._status_label.text() or "empty" in tab._status_label.text().lower()  # noqa: SLF001

    async def test_copy_button_disabled_before_success(
        self, qapp: QApplication, service: TranslationService
    ) -> None:
        tab = TextTab(service=service)
        assert not tab._copy_btn.isEnabled()  # noqa: SLF001
