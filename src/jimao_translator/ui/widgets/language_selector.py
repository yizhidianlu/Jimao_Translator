"""T114: LanguageSelector — dropdown bound to LanguageCode enum."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QWidget

from ...models.enums import LanguageCode

_DISPLAY = {
    LanguageCode.AUTO: "自动检测 (Auto)",
    LanguageCode.ZH: "中文 (Chinese)",
    LanguageCode.EN: "English",
    LanguageCode.JA: "日本語 (Japanese)",
    LanguageCode.KO: "한국어 (Korean)",
}


class LanguageSelector(QComboBox):
    """Combo box for picking a LanguageCode. `include_auto=False` for target field."""

    language_changed = Signal(LanguageCode)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        include_auto: bool = True,
        initial: LanguageCode | None = None,
    ) -> None:
        super().__init__(parent)
        self._codes: list[LanguageCode] = []
        for code in LanguageCode:
            if code is LanguageCode.AUTO and not include_auto:
                continue
            self._codes.append(code)
            self.addItem(_DISPLAY[code], code)

        if initial and initial in self._codes:
            self.setCurrentIndex(self._codes.index(initial))

        self.currentIndexChanged.connect(self._emit_language_changed)

    def current_language(self) -> LanguageCode:
        data = self.currentData()
        if isinstance(data, LanguageCode):
            return data
        return LanguageCode(data)

    def set_language(self, code: LanguageCode) -> None:
        if code in self._codes:
            self.setCurrentIndex(self._codes.index(code))

    def _emit_language_changed(self, _: int) -> None:
        self.language_changed.emit(self.current_language())
