"""T215 + T216: VoiceTab — push-to-talk single-speaker + split-screen conversation mode.

Two sub-modes:
  * Single-speaker: one mic button, source-language selector, target-language selector.
  * Conversation: split panel (local ⇄ counterpart), each side has its own mic button;
    whichever side speaks, the other side sees the translated text and hears TTS.

Audio capture hardware is wired at the application level (T410 — sounddevice). This
tab accepts a `capture_callback` that, when invoked, returns a snapshot of raw PCM
bytes. In tests we pass a stub that returns canned bytes.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ...exceptions import JimaoError
from ...models.enums import LanguageCode
from ...speech.orchestrator import (
    ConversationOrchestrator,
    VoiceOutcome,
    VoiceTranslationOrchestrator,
)
from ...storage.history import TranslationHistoryRepository
from ..widgets.history_panel import HistoryPanel
from ..widgets.language_selector import LanguageSelector

logger = logging.getLogger(__name__)

AudioProvider = Callable[[], Awaitable[bytes]]


def _default_audio_provider() -> Awaitable[bytes]:
    async def _empty() -> bytes:
        return b""

    return _empty()


class _SpeakerPanel(QWidget):
    """One side of the conversation: language label, recognized text, translated text."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("font-weight: bold;")

        self._recognized = QPlainTextEdit()
        self._recognized.setReadOnly(True)
        self._recognized.setPlaceholderText("识别内容")
        self._recognized.setObjectName("recognized_text")

        self._translated = QPlainTextEdit()
        self._translated.setReadOnly(True)
        self._translated.setPlaceholderText("译文")
        self._translated.setObjectName("translated_text")

        self._mic_btn = QPushButton("🎙 说话")
        self._mic_btn.setObjectName("mic_button")

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(QLabel("识别:"))
        layout.addWidget(self._recognized, 1)
        layout.addWidget(QLabel("译文:"))
        layout.addWidget(self._translated, 1)
        layout.addWidget(self._mic_btn)

    @property
    def mic_button(self) -> QPushButton:
        return self._mic_btn

    def set_recognized(self, text: str) -> None:
        self._recognized.setPlainText(text)

    def set_translated(self, text: str) -> None:
        self._translated.setPlainText(text)

    def recognized_text(self) -> str:
        return self._recognized.toPlainText()

    def translated_text(self) -> str:
        return self._translated.toPlainText()


class VoiceTab(QWidget):
    """Push-to-talk voice translation tab with single / conversation modes."""

    def __init__(
        self,
        voice_orchestrator: VoiceTranslationOrchestrator,
        audio_provider: AudioProvider | None = None,
        parent: QWidget | None = None,
        *,
        default_source: LanguageCode = LanguageCode.AUTO,
        default_target: LanguageCode = LanguageCode.EN,
        default_local: LanguageCode = LanguageCode.ZH,
        default_counterpart: LanguageCode = LanguageCode.EN,
        history_repo: TranslationHistoryRepository | None = None,
    ) -> None:
        super().__init__(parent)
        self._voice = voice_orchestrator
        self._audio_provider = audio_provider or (lambda: _default_audio_provider())
        self._history_repo = history_repo
        self._pending_task: asyncio.Task | None = None
        self._convo: ConversationOrchestrator | None = None

        self._mode_toggle = QPushButton("切换到对话模式")
        self._mode_toggle.setObjectName("mode_toggle")
        self._mode_toggle.setCheckable(True)
        self._mode_toggle.clicked.connect(self._on_mode_toggled)

        self._status = QLabel("")
        self._status.setObjectName("voice_status")
        self._status.setAlignment(Qt.AlignmentFlag.AlignRight)

        # ---- single-speaker view --------------------------------------------
        self._single_view = QWidget()
        self._source_selector = LanguageSelector(include_auto=True, initial=default_source)
        self._target_selector = LanguageSelector(include_auto=False, initial=default_target)

        self._recognized_single = QPlainTextEdit()
        self._recognized_single.setReadOnly(True)
        self._recognized_single.setPlaceholderText("识别内容")
        self._recognized_single.setObjectName("recognized_text_single")

        self._translated_single = QPlainTextEdit()
        self._translated_single.setReadOnly(True)
        self._translated_single.setPlaceholderText("译文")
        self._translated_single.setObjectName("translated_text_single")

        self._single_mic = QPushButton("🎙 按下说话")
        self._single_mic.setObjectName("single_mic_button")
        self._single_mic.clicked.connect(lambda: self._run_single())

        single_lang_row = QHBoxLayout()
        single_lang_row.addWidget(QLabel("源语言:"))
        single_lang_row.addWidget(self._source_selector)
        single_lang_row.addSpacing(16)
        single_lang_row.addWidget(QLabel("目标语言:"))
        single_lang_row.addWidget(self._target_selector)
        single_lang_row.addStretch()

        single_layout = QVBoxLayout(self._single_view)
        single_layout.addLayout(single_lang_row)
        single_layout.addWidget(QLabel("识别:"))
        single_layout.addWidget(self._recognized_single, 1)
        single_layout.addWidget(QLabel("译文:"))
        single_layout.addWidget(self._translated_single, 1)
        single_layout.addWidget(self._single_mic)

        # ---- conversation view ----------------------------------------------
        self._convo_view = QWidget()
        self._local_lang_selector = LanguageSelector(include_auto=False, initial=default_local)
        self._counterpart_lang_selector = LanguageSelector(
            include_auto=False, initial=default_counterpart
        )

        self._local_panel = _SpeakerPanel("本端")
        self._counterpart_panel = _SpeakerPanel("对端")
        self._local_panel.mic_button.clicked.connect(lambda: self._run_convo(local=True))
        self._counterpart_panel.mic_button.clicked.connect(lambda: self._run_convo(local=False))

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("conversation_splitter")
        splitter.addWidget(self._local_panel)
        splitter.addWidget(self._counterpart_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        convo_lang_row = QHBoxLayout()
        convo_lang_row.addWidget(QLabel("本端语言:"))
        convo_lang_row.addWidget(self._local_lang_selector)
        convo_lang_row.addSpacing(16)
        convo_lang_row.addWidget(QLabel("对端语言:"))
        convo_lang_row.addWidget(self._counterpart_lang_selector)
        convo_lang_row.addStretch()

        convo_layout = QVBoxLayout(self._convo_view)
        convo_layout.addLayout(convo_lang_row)
        convo_layout.addWidget(splitter, 1)

        # ---- stack both views -----------------------------------------------
        self._stack = QStackedWidget()
        self._stack.addWidget(self._single_view)
        self._stack.addWidget(self._convo_view)

        header = QHBoxLayout()
        header.addWidget(self._mode_toggle)
        header.addStretch()
        header.addWidget(self._status)

        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(header)
        main_layout.addWidget(self._stack, 1)

        self._history_panel: HistoryPanel | None = None
        root = QVBoxLayout(self)
        if self._history_repo is not None:
            self._history_panel = HistoryPanel(self._history_repo)
            root_splitter = QSplitter(Qt.Orientation.Horizontal)
            root_splitter.addWidget(main_content)
            root_splitter.addWidget(self._history_panel)
            root_splitter.setStretchFactor(0, 3)
            root_splitter.setStretchFactor(1, 1)
            root.addWidget(root_splitter)
        else:
            root.addWidget(main_content)

    # ---- public API for tests --------------------------------------------------

    def is_conversation_mode(self) -> bool:
        return self._stack.currentIndex() == 1

    def set_conversation_mode(self, enabled: bool) -> None:
        self._mode_toggle.setChecked(enabled)
        self._apply_mode()

    def recognized_text(self) -> str:
        if self.is_conversation_mode():
            # Whichever side most recently spoke
            return self._counterpart_panel.recognized_text() or self._local_panel.recognized_text()
        return self._recognized_single.toPlainText()

    def translated_text(self) -> str:
        if self.is_conversation_mode():
            return self._local_panel.translated_text() or self._counterpart_panel.translated_text()
        return self._translated_single.toPlainText()

    def trigger_single(self) -> asyncio.Task:
        """For tests — kick off a single-speaker cycle."""
        return self._run_single()

    def trigger_local_speaks(self) -> asyncio.Task:
        return self._run_convo(local=True)

    def trigger_counterpart_speaks(self) -> asyncio.Task:
        return self._run_convo(local=False)

    # ---- mode toggle -----------------------------------------------------------

    def _on_mode_toggled(self) -> None:
        self._apply_mode()

    def _apply_mode(self) -> None:
        if self._mode_toggle.isChecked():
            self._stack.setCurrentIndex(1)
            self._mode_toggle.setText("切回单人模式")
        else:
            self._stack.setCurrentIndex(0)
            self._mode_toggle.setText("切换到对话模式")
            self._convo = None

    def _ensure_convo(self) -> ConversationOrchestrator:
        local = self._local_lang_selector.current_language()
        counterpart = self._counterpart_lang_selector.current_language()
        if (
            self._convo is None
            or self._convo.local_language is not local
            or self._convo.counterpart_language is not counterpart
        ):
            self._convo = ConversationOrchestrator(
                voice=self._voice,
                local_language=local,
                counterpart_language=counterpart,
            )
        return self._convo

    # ---- single-speaker execution ---------------------------------------------

    def _run_single(self) -> asyncio.Task:
        if self._pending_task is not None and not self._pending_task.done():
            self._pending_task.cancel()
        self._status.setText("录音/识别中 …")
        self._single_mic.setEnabled(False)
        loop = asyncio.get_event_loop()
        task = loop.create_task(self._do_single())
        self._pending_task = task
        return task

    async def _do_single(self) -> None:
        try:
            audio = await self._audio_provider()
            source = self._source_selector.current_language()
            target = self._target_selector.current_language()
            outcome = await self._voice.run_once(
                audio_bytes=audio,
                target_language=target,
                source_language=None if source is LanguageCode.AUTO else source,
            )
            self._render_single(outcome)
        except JimaoError as err:
            logger.exception("voice translation failed")
            self._status.setText(f"语音翻译失败: {err}")
        except Exception as err:  # noqa: BLE001 — surface to user
            logger.exception("unexpected voice error")
            self._status.setText(f"错误: {err}")
        finally:
            self._single_mic.setEnabled(True)

    def _render_single(self, outcome: VoiceOutcome) -> None:
        self._recognized_single.setPlainText(outcome.session.recognized_text)
        self._translated_single.setPlainText(outcome.result.translated_text)
        status = f"引擎: {outcome.result.engine}"
        if outcome.low_confidence:
            status += " ⚠ 识别置信度较低"
        self._status.setText(status)
        if self._history_panel is not None:
            self._history_panel.refresh()

    # ---- conversation execution -----------------------------------------------

    def _run_convo(self, *, local: bool) -> asyncio.Task:
        if self._pending_task is not None and not self._pending_task.done():
            self._pending_task.cancel()
        self._status.setText("录音/识别中 …")
        self._local_panel.mic_button.setEnabled(False)
        self._counterpart_panel.mic_button.setEnabled(False)
        loop = asyncio.get_event_loop()
        task = loop.create_task(self._do_convo(local=local))
        self._pending_task = task
        return task

    async def _do_convo(self, *, local: bool) -> None:
        try:
            audio = await self._audio_provider()
            convo = self._ensure_convo()
            outcome = (
                await convo.local_speaks(audio_bytes=audio)
                if local
                else await convo.counterpart_speaks(audio_bytes=audio)
            )
            self._render_convo(outcome, local=local)
        except JimaoError as err:
            logger.exception("conversation voice failed")
            self._status.setText(f"对话翻译失败: {err}")
        except Exception as err:  # noqa: BLE001
            logger.exception("unexpected conversation error")
            self._status.setText(f"错误: {err}")
        finally:
            self._local_panel.mic_button.setEnabled(True)
            self._counterpart_panel.mic_button.setEnabled(True)

    def _render_convo(self, outcome: VoiceOutcome, *, local: bool) -> None:
        if local:
            self._local_panel.set_recognized(outcome.session.recognized_text)
            self._counterpart_panel.set_translated(outcome.result.translated_text)
        else:
            self._counterpart_panel.set_recognized(outcome.session.recognized_text)
            self._local_panel.set_translated(outcome.result.translated_text)
        status = f"引擎: {outcome.result.engine}"
        if outcome.low_confidence:
            status += " ⚠ 识别置信度较低"
        self._status.setText(status)
        if self._history_panel is not None:
            self._history_panel.refresh()
