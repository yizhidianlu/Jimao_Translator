"""T420: Offline banner — surfaces network-offline state and fallback hint."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class OfflineBanner(QWidget):
    """Thin yellow bar shown when network features are unavailable.

    Consumers toggle visibility via `set_offline(True/False)`. The banner always
    shows the fallback hint (local-only operations remain available).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("offline_banner")
        self.setStyleSheet(
            "#offline_banner { background-color: #fff3cd; border-bottom: 1px solid #ffe69c; }"
            "#offline_banner QLabel { color: #664d03; padding: 4px 8px; }"
        )

        self._label = QLabel(
            "⚠ 网络不可用 · LLM / 在线语音不可用，基础翻译仍可离线使用（如本地缓存）。"
        )
        self._label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self._dismiss = QPushButton("隐藏")
        self._dismiss.setFlat(True)
        self._dismiss.clicked.connect(self.hide)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label, 1)
        layout.addWidget(self._dismiss)

        self._offline = False
        self.hide()

    def set_offline(self, offline: bool) -> None:
        """Show the banner when offline, hide when online."""
        self._offline = bool(offline)
        self.setVisible(self._offline)

    def is_offline(self) -> bool:
        return self._offline
