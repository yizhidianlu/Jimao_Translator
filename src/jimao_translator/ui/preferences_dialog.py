"""T410: PreferencesDialog — modal form for UserPreferences."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from ..models.enums import LanguageCode, TranslationMode
from ..models.preferences import UserPreferences
from ..storage.preferences import PreferencesRepository
from .widgets.language_selector import LanguageSelector

logger = logging.getLogger(__name__)


_THEMES = [("跟随系统", "system"), ("亮色", "light"), ("暗色", "dark")]


class PreferencesDialog(QDialog):
    """Modal to edit and persist `UserPreferences`."""

    def __init__(
        self,
        repo: PreferencesRepository,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("偏好设置")
        self.setModal(True)
        self._repo = repo
        self._prefs = repo.load()

        self._source_lang = LanguageSelector(
            include_auto=True, initial=self._prefs.default_source_language
        )
        self._target_lang = LanguageSelector(
            include_auto=False, initial=self._prefs.default_target_language
        )

        self._theme = QComboBox()
        for label, value in _THEMES:
            self._theme.addItem(label, value)
        theme_values = [v for _, v in _THEMES]
        if self._prefs.ui_theme in theme_values:
            self._theme.setCurrentIndex(theme_values.index(self._prefs.ui_theme))

        self._voice_speed = QDoubleSpinBox()
        self._voice_speed.setRange(0.5, 2.0)
        self._voice_speed.setSingleStep(0.1)
        self._voice_speed.setDecimals(2)
        self._voice_speed.setValue(self._prefs.voice_speed)

        self._hotkey = QLineEdit()
        self._hotkey.setPlaceholderText("如 Ctrl+Alt+Space（可选）")
        if self._prefs.hotkey:
            self._hotkey.setText(self._prefs.hotkey)

        self._history_enabled = QCheckBox("记录翻译历史（最近 100 条）")
        self._history_enabled.setChecked(self._prefs.history_enabled)

        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key.setPlaceholderText("sk-ant-… (保存至系统 keyring)")
        if self._prefs.llm_api_key:
            self._api_key.setText(self._prefs.llm_api_key)

        form = QFormLayout()
        form.addRow("默认源语言", self._source_lang)
        form.addRow("默认目标语言", self._target_lang)
        form.addRow("主题", self._theme)
        form.addRow("语音速率", self._voice_speed)
        form.addRow("全局热键", self._hotkey)
        form.addRow("", self._history_enabled)
        form.addRow("通义千问 API 密钥", self._api_key)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._saved_prefs: UserPreferences | None = None

    @property
    def saved_preferences(self) -> UserPreferences | None:
        """Populated after accept(); None if cancelled."""
        return self._saved_prefs

    def _collect(self) -> UserPreferences:
        api_key = self._api_key.text().strip() or None
        source = self._source_lang.current_language()
        target = self._target_lang.current_language()
        if target is LanguageCode.AUTO:
            target = self._prefs.default_target_language
        return UserPreferences(
            default_source_language=source,
            default_target_language=target,
            ui_theme=self._theme.currentData(),
            voice_speed=self._voice_speed.value(),
            hotkey=self._hotkey.text().strip() or None,
            history_enabled=self._history_enabled.isChecked(),
            last_active_tab=self._prefs.last_active_tab,
            llm_api_key=api_key,
        )

    def _on_accept(self) -> None:
        prefs = self._collect()
        try:
            self._repo.save(prefs)
        except Exception as err:  # noqa: BLE001
            logger.exception("failed to save preferences: %s", err)
            return
        self._saved_prefs = prefs
        self.accept()


def update_last_active_tab(repo: PreferencesRepository, tab: TranslationMode) -> None:
    """T412 helper: persist last active tab without touching other fields."""
    prefs = repo.load()
    if prefs.last_active_tab is tab:
        return
    repo.save(prefs.model_copy(update={"last_active_tab": tab}))
