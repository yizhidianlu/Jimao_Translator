"""T313: ChatTab — LLM multi-turn chat with streaming response rendering."""

from __future__ import annotations

import asyncio
import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...exceptions import (
    AuthenticationError,
    ContentPolicyViolationError,
    JimaoError,
    LlmUnavailableError,
)
from ...llm.service import ChatService
from ...models.enums import MessageRole

logger = logging.getLogger(__name__)


def _format_message(role: MessageRole, content: str) -> str:
    prefix = "🧑 你" if role is MessageRole.USER else "🤖 助手"
    return f"{prefix}: {content}"


class ChatTab(QWidget):
    """Chat UI — transcript on top, input + send/new-conversation below."""

    def __init__(
        self,
        chat_service: ChatService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = chat_service
        self._pending_task: asyncio.Task | None = None
        self._streaming_start_pos: int | None = None

        self._transcript = QPlainTextEdit()
        self._transcript.setReadOnly(True)
        self._transcript.setObjectName("chat_transcript")
        self._transcript.setPlaceholderText("与助手对话 …")

        self._input = QPlainTextEdit()
        self._input.setObjectName("chat_input")
        self._input.setPlaceholderText("输入你的问题，按“发送”提交 …")
        self._input.setMaximumBlockCount(200)
        self._input.setMinimumHeight(80)

        self._send_btn = QPushButton("发送")
        self._send_btn.setObjectName("send_button")
        self._send_btn.clicked.connect(self._on_send_clicked)

        self._new_btn = QPushButton("新对话")
        self._new_btn.setObjectName("new_conversation_button")
        self._new_btn.clicked.connect(self._on_new_clicked)

        self._status = QLabel("")
        self._status.setObjectName("chat_status")
        self._status.setAlignment(Qt.AlignmentFlag.AlignRight)

        action_row = QHBoxLayout()
        action_row.addWidget(self._send_btn)
        action_row.addWidget(self._new_btn)
        action_row.addStretch()
        action_row.addWidget(self._status)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("对话历史:"))
        layout.addWidget(self._transcript, 1)
        layout.addWidget(QLabel("输入:"))
        layout.addWidget(self._input)
        layout.addLayout(action_row)

    # ---- public API for tests --------------------------------------------------

    def transcript_text(self) -> str:
        return self._transcript.toPlainText()

    def set_input_text(self, text: str) -> None:
        self._input.setPlainText(text)

    def trigger_send(self) -> asyncio.Task:
        return self._on_send_clicked()

    def trigger_new_conversation(self) -> None:
        self._on_new_clicked()

    # ---- handlers --------------------------------------------------------------

    def _on_send_clicked(self) -> asyncio.Task:
        if self._pending_task is not None and not self._pending_task.done():
            self._pending_task.cancel()

        user_text = self._input.toPlainText().strip()
        self._send_btn.setEnabled(False)
        self._status.setText("等待回复 …")

        loop = asyncio.get_event_loop()
        task = loop.create_task(self._do_send(user_text))
        self._pending_task = task
        return task

    def _on_new_clicked(self) -> None:
        self._service.new_conversation()
        self._transcript.clear()
        self._status.setText("已开启新对话")

    async def _do_send(self, user_text: str) -> None:
        try:
            if not user_text:
                self._status.setText("输入为空")
                return

            self._append_line(_format_message(MessageRole.USER, user_text))
            self._append_line("🤖 助手: ")
            # Remember where the streaming reply starts, so we can append to it.
            cursor = self._transcript.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self._streaming_start_pos = cursor.position()

            self._input.clear()

            collected: list[str] = []
            async for delta in self._service.send(user_text, stream=True):
                collected.append(delta)
                self._append_to_stream(delta)

            self._status.setText("就绪")

        except AuthenticationError as err:
            self._append_line(f"⚠ 认证失败: {err}")
            self._status.setText("认证失败")
        except ContentPolicyViolationError as err:
            self._append_line(f"⚠ 内容策略拒绝: {err}")
            self._status.setText("内容被策略过滤，请调整提问")
        except LlmUnavailableError as err:
            self._append_line(f"⚠ LLM 不可用: {err}")
            self._status.setText("LLM 不可用，可改用基础翻译功能")
        except JimaoError as err:
            logger.exception("chat failed")
            self._append_line(f"⚠ 错误: {err}")
            self._status.setText("错误")
        except ValueError as err:
            self._status.setText(f"输入无效: {err}")
        finally:
            self._send_btn.setEnabled(True)
            self._streaming_start_pos = None

    # ---- rendering helpers ----------------------------------------------------

    def _append_line(self, line: str) -> None:
        self._transcript.appendPlainText(line)

    def _append_to_stream(self, delta: str) -> None:
        """Append a streaming delta to the current assistant line (no newline)."""
        cursor = self._transcript.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(delta)
        self._transcript.setTextCursor(cursor)
