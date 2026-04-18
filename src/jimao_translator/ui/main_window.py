"""T116: MainWindow — full-screen tab host (Text / Voice / Chat).

US1 wires only the Text tab. Voice and Chat tabs land in Phase 4 / Phase 5.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMainWindow, QTabWidget, QWidget

from ..models.enums import TranslationMode
from ..translation.service import TranslationService
from .tabs.text_tab import TextTab


def _placeholder(text: str) -> QWidget:
    w = QWidget()
    lbl = QLabel(text, w)
    lbl.setStyleSheet("padding: 24px; color: #888;")
    return w


class MainWindow(QMainWindow):
    """Top-level window. Keeps references to tabs so phase-4/5 can swap placeholders."""

    def __init__(self, translation_service: TranslationService) -> None:
        super().__init__()
        self.setWindowTitle("Jimao Translator")
        self.resize(960, 640)

        self._tabs = QTabWidget(self)
        self._tabs.setObjectName("main_tabs")

        self.text_tab = TextTab(service=translation_service)
        self._tabs.addTab(self.text_tab, "文本翻译")
        self._tabs.addTab(_placeholder("语音翻译 — Phase 4"), "语音翻译")
        self._tabs.addTab(_placeholder("LLM 聊天 — Phase 5"), "LLM 聊天")

        self.setCentralWidget(self._tabs)

    def select_tab(self, mode: TranslationMode) -> None:
        mapping = {
            TranslationMode.TEXT: 0,
            TranslationMode.VOICE: 1,
            TranslationMode.VOICE_CONVERSATION: 1,
        }
        self._tabs.setCurrentIndex(mapping.get(mode, 0))

    def active_tab_mode(self) -> TranslationMode:
        return {
            0: TranslationMode.TEXT,
            1: TranslationMode.VOICE,
            2: TranslationMode.TEXT,
        }.get(self._tabs.currentIndex(), TranslationMode.TEXT)
