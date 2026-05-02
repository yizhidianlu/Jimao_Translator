"""T115: TextTab — input, target-language selector, translate + copy buttons."""

from __future__ import annotations

import asyncio
import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ...exceptions import JimaoError
from ...models.enums import LanguageCode, TranslationMode
from ...models.translation import TranslationHistoryEntry
from ...storage.history import TranslationHistoryRepository
from ...translation.service import TranslationService
from ..widgets.history_panel import HistoryPanel
from ..widgets.language_selector import LanguageSelector

logger = logging.getLogger(__name__)


class TextTab(QWidget):
    """Text translation tab — Phase 3 US1 MVP."""

    def __init__(
        self,
        service: TranslationService,
        parent: QWidget | None = None,
        *,
        default_source: LanguageCode = LanguageCode.AUTO,
        default_target: LanguageCode = LanguageCode.EN,
        history_repo: TranslationHistoryRepository | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._history_repo = history_repo
        self._pending_task: asyncio.Task | None = None

        self._source_selector = LanguageSelector(include_auto=True, initial=default_source)
        self._target_selector = LanguageSelector(include_auto=False, initial=default_target)

        self._input = QPlainTextEdit()
        self._input.setPlaceholderText("输入要翻译的文本 …")
        self._input.setObjectName("source_text")

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("译文将显示在这里")
        self._output.setObjectName("translated_text")

        self._translate_btn = QPushButton("翻译")
        self._translate_btn.setObjectName("translate_button")
        self._translate_btn.clicked.connect(self._on_translate_clicked)

        self._copy_btn = QPushButton("复制译文")
        self._copy_btn.setObjectName("copy_button")
        self._copy_btn.clicked.connect(self._on_copy_clicked)
        self._copy_btn.setEnabled(False)

        self._status_label = QLabel("")
        self._status_label.setObjectName("status_label")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("源语言:"))
        lang_row.addWidget(self._source_selector)
        lang_row.addSpacing(16)
        lang_row.addWidget(QLabel("目标语言:"))
        lang_row.addWidget(self._target_selector)
        lang_row.addStretch()

        action_row = QHBoxLayout()
        action_row.addWidget(self._translate_btn)
        action_row.addWidget(self._copy_btn)
        action_row.addStretch()
        action_row.addWidget(self._status_label)

        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(lang_row)
        main_layout.addWidget(self._input, 1)
        main_layout.addLayout(action_row)
        main_layout.addWidget(self._output, 1)

        self._history_panel: HistoryPanel | None = None
        outer_layout = QVBoxLayout(self)
        if self._history_repo is not None:
            self._history_panel = HistoryPanel(self._history_repo)
            self._history_panel.entry_selected.connect(self._on_history_selected)
            splitter = QSplitter(Qt.Orientation.Horizontal)
            splitter.addWidget(main_content)
            splitter.addWidget(self._history_panel)
            splitter.setStretchFactor(0, 3)
            splitter.setStretchFactor(1, 1)
            outer_layout.addWidget(splitter)
        else:
            outer_layout.addWidget(main_content)

    # ---- public API for tests ---------------------------------------------

    def set_input_text(self, text: str) -> None:
        self._input.setPlainText(text)

    def output_text(self) -> str:
        return self._output.toPlainText()

    def trigger_translate(self) -> asyncio.Task:
        """Run translation against the current state; returns the scheduled task."""
        return self._on_translate_clicked()

    # ---- event handlers ---------------------------------------------------

    def _on_translate_clicked(self) -> asyncio.Task:
        if self._pending_task is not None and not self._pending_task.done():
            self._pending_task.cancel()

        source_text = self._input.toPlainText()
        source_lang = self._source_selector.current_language()
        target_lang = self._target_selector.current_language()

        self._translate_btn.setEnabled(False)
        self._status_label.setText("翻译中 …")

        loop = asyncio.get_event_loop()
        task = loop.create_task(self._run_translation(source_text, source_lang, target_lang))
        self._pending_task = task
        return task

    async def _run_translation(
        self,
        source_text: str,
        source_lang: LanguageCode,
        target_lang: LanguageCode,
    ) -> None:
        try:
            result = await self._service.translate(
                source_text=source_text,
                source_language=source_lang,
                target_language=target_lang,
                mode=TranslationMode.TEXT,
            )
            self._output.setPlainText(result.translated_text)
            self._status_label.setText(f"引擎: {result.engine}")
            self._copy_btn.setEnabled(bool(result.translated_text))
            if self._history_panel is not None:
                self._history_panel.refresh()
        except ValueError as err:
            self._status_label.setText(f"输入无效: {err}")
            self._copy_btn.setEnabled(False)
        except JimaoError as err:
            logger.exception("translation failed")
            self._status_label.setText(f"翻译失败: {err}")
            self._copy_btn.setEnabled(False)
        finally:
            self._translate_btn.setEnabled(True)

    def _on_copy_clicked(self) -> None:
        text = self._output.toPlainText()
        if text:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            self._status_label.setText("已复制")

    def _on_history_selected(self, entry: TranslationHistoryEntry) -> None:
        """Populate input from a history entry — the user can edit and re-translate."""
        self._input.setPlainText(entry.request.source_text)
        self._output.setPlainText(entry.result.translated_text)
        self._source_selector.set_language(entry.request.source_language)
        self._target_selector.set_language(entry.request.target_language)
        self._copy_btn.setEnabled(bool(entry.result.translated_text))
        self._status_label.setText(f"历史 · 引擎: {entry.result.engine}")
