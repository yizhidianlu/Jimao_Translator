"""T116 + T217 + T314: MainWindow — full-screen tab host (Text / Voice / Chat)."""

from __future__ import annotations

import contextlib

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QMainWindow, QTabWidget, QWidget

from ..llm.service import ChatService
from ..models.enums import TranslationMode
from ..speech.orchestrator import VoiceTranslationOrchestrator
from ..storage.history import TranslationHistoryRepository
from ..storage.preferences import PreferencesRepository
from ..translation.service import TranslationService
from .preferences_dialog import PreferencesDialog, update_last_active_tab
from .tabs.chat_tab import ChatTab
from .tabs.text_tab import TextTab
from .tabs.voice_tab import AudioProvider, VoiceTab


def _placeholder(text: str) -> QWidget:
    w = QWidget()
    lbl = QLabel(text, w)
    lbl.setStyleSheet("padding: 24px; color: #888;")
    return w


class MainWindow(QMainWindow):
    """Top-level window. Keeps references to tabs so phase-5 can swap placeholders."""

    def __init__(
        self,
        translation_service: TranslationService,
        voice_orchestrator: VoiceTranslationOrchestrator | None = None,
        chat_service: ChatService | None = None,
        history_repo: TranslationHistoryRepository | None = None,
        prefs_repo: PreferencesRepository | None = None,
        audio_provider: AudioProvider | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Jimao Translator")
        self.resize(960, 640)
        self._prefs_repo = prefs_repo

        self._tabs = QTabWidget(self)
        self._tabs.setObjectName("main_tabs")
        self._tabs.currentChanged.connect(self._on_tab_changed)

        self.text_tab = TextTab(service=translation_service, history_repo=history_repo)
        self._tabs.addTab(self.text_tab, "文本翻译")

        if voice_orchestrator is not None:
            self.voice_tab = VoiceTab(
                voice_orchestrator=voice_orchestrator,
                audio_provider=audio_provider,
                history_repo=history_repo,
            )
            self._tabs.addTab(self.voice_tab, "语音翻译")
        else:
            self.voice_tab = None
            self._tabs.addTab(_placeholder("语音翻译 — 未配置"), "语音翻译")

        if chat_service is not None:
            self.chat_tab = ChatTab(chat_service=chat_service)
            self._tabs.addTab(self.chat_tab, "LLM 聊天")
        else:
            self.chat_tab = None
            self._tabs.addTab(_placeholder("LLM 聊天 — 未配置"), "LLM 聊天")

        self.setCentralWidget(self._tabs)
        self._build_menus()

    def _build_menus(self) -> None:
        menubar = self.menuBar()
        app_menu = menubar.addMenu("应用")

        prefs_action = QAction("偏好设置 …", self)
        prefs_action.setShortcut("Ctrl+,")
        prefs_action.triggered.connect(self.open_preferences)
        app_menu.addAction(prefs_action)

        quit_action = QAction("退出", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        app_menu.addAction(quit_action)

    def open_preferences(self) -> PreferencesDialog | None:
        if self._prefs_repo is None:
            return None
        dlg = PreferencesDialog(self._prefs_repo, parent=self)
        dlg.exec()
        return dlg

    def _on_tab_changed(self, _index: int) -> None:
        if self._prefs_repo is None:
            return
        with contextlib.suppress(Exception):  # never break UX on prefs write
            update_last_active_tab(self._prefs_repo, self.active_tab_mode())

    def select_tab(self, mode: TranslationMode) -> None:
        mapping = {
            TranslationMode.TEXT: 0,
            TranslationMode.VOICE: 1,
            TranslationMode.VOICE_CONVERSATION: 1,
        }
        self._tabs.setCurrentIndex(mapping.get(mode, 0))

    def active_tab_mode(self) -> TranslationMode:
        # Tab index 2 (chat) maps to TEXT for last-active-tab persistence
        # since TranslationMode has no CHAT value; restoring chat directly is
        # not supported by select_tab yet.
        return {
            0: TranslationMode.TEXT,
            1: TranslationMode.VOICE,
            2: TranslationMode.TEXT,
        }.get(self._tabs.currentIndex(), TranslationMode.TEXT)
