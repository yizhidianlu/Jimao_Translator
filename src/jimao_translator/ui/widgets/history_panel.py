"""T400: HistoryPanel — list of recent translations (≤100), re-copy + clear."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...models.translation import TranslationHistoryEntry
from ...storage.history import TranslationHistoryRepository

logger = logging.getLogger(__name__)


def _summarize(entry: TranslationHistoryEntry, max_chars: int = 60) -> str:
    src = entry.request.source_text.strip().replace("\n", " ")
    if len(src) > max_chars:
        src = src[:max_chars] + "…"
    src_lang = entry.request.source_language.value
    tgt_lang = entry.request.target_language.value
    return f"[{src_lang}→{tgt_lang}] {src}"


class HistoryPanel(QWidget):
    """Sidebar listing recent translation entries."""

    entry_selected = Signal(TranslationHistoryEntry)

    def __init__(
        self,
        repo: TranslationHistoryRepository,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._repo = repo

        title = QLabel("最近翻译")
        title.setStyleSheet("font-weight: bold;")

        self._list = QListWidget()
        self._list.setObjectName("history_list")
        self._list.itemActivated.connect(self._on_item_activated)
        self._list.itemDoubleClicked.connect(self._on_item_activated)

        self._refresh_btn = QPushButton("刷新")
        self._refresh_btn.setObjectName("history_refresh")
        self._refresh_btn.clicked.connect(self.refresh)

        self._copy_btn = QPushButton("复制译文")
        self._copy_btn.setObjectName("history_copy")
        self._copy_btn.clicked.connect(self._on_copy_clicked)

        self._clear_btn = QPushButton("清空")
        self._clear_btn.setObjectName("history_clear")
        self._clear_btn.clicked.connect(self._on_clear_clicked)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._refresh_btn)
        btn_row.addWidget(self._copy_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._clear_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self._list, 1)
        layout.addLayout(btn_row)

        self.refresh()

    # ---- public API -----------------------------------------------------------

    def refresh(self) -> None:
        self._list.clear()
        try:
            entries = self._repo.load()
        except Exception as err:  # noqa: BLE001
            logger.warning("failed to load history: %s", err)
            entries = []
        for entry in entries:
            item = QListWidgetItem(_summarize(entry))
            item.setData(Qt.ItemDataRole.UserRole, entry)
            item.setToolTip(f"源: {entry.request.source_text}\n译: {entry.result.translated_text}")
            self._list.addItem(item)

    def selected_entry(self) -> TranslationHistoryEntry | None:
        item = self._list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    # ---- handlers -------------------------------------------------------------

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        entry = item.data(Qt.ItemDataRole.UserRole)
        if entry is not None:
            self.entry_selected.emit(entry)

    def _on_copy_clicked(self) -> None:
        entry = self.selected_entry()
        if entry is None:
            return
        QGuiApplication.clipboard().setText(entry.result.translated_text)

    def _on_clear_clicked(self) -> None:
        reply = QMessageBox.question(
            self,
            "清空历史",
            "确定要清空全部翻译历史吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._repo.clear()
            self.refresh()
