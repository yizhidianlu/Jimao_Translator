"""T315: GUI test for ChatTab multi-turn flow (pytest-qt + mocked LlmClient)."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from jimao_translator.exceptions import LlmUnavailableError
from jimao_translator.llm.providers.mock import MockLlmClient
from jimao_translator.llm.service import ChatService
from jimao_translator.ui.tabs.chat_tab import ChatTab

pytestmark = pytest.mark.gui


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app  # type: ignore[return-value]


class TestChatTabFlow:
    async def test_send_streams_response_into_transcript(
        self, qapp: QApplication
    ) -> None:
        svc = ChatService(llm_client=MockLlmClient(reply="你好，有什么可以帮你？", chunks=4))
        tab = ChatTab(chat_service=svc)

        tab.set_input_text("翻译 hello 成中文")
        task = tab.trigger_send()
        await task

        transcript = tab.transcript_text()
        assert "翻译 hello 成中文" in transcript
        assert "你好，有什么可以帮你？" in transcript

    async def test_multi_turn_transcript_accumulates(
        self, qapp: QApplication
    ) -> None:
        svc = ChatService(llm_client=MockLlmClient(reply="回答", chunks=1))
        tab = ChatTab(chat_service=svc)

        tab.set_input_text("第一问")
        await tab.trigger_send()
        tab.set_input_text("第二问")
        await tab.trigger_send()

        transcript = tab.transcript_text()
        assert "第一问" in transcript
        assert "第二问" in transcript
        assert transcript.count("回答") == 2
        # Conversation state advanced too
        assert len(svc.conversation.messages) == 4

    async def test_llm_unavailable_shows_fallback_hint(
        self, qapp: QApplication
    ) -> None:
        svc = ChatService(llm_client=MockLlmClient(fail_with=LlmUnavailableError("down")))
        tab = ChatTab(chat_service=svc)

        tab.set_input_text("问一个问题")
        await tab.trigger_send()

        assert "不可用" in tab._status.text() or "LLM" in tab._status.text()  # noqa: SLF001
        assert "基础翻译" in tab._status.text()  # noqa: SLF001

    async def test_new_conversation_clears_transcript(
        self, qapp: QApplication
    ) -> None:
        svc = ChatService(llm_client=MockLlmClient(reply="hi", chunks=1))
        tab = ChatTab(chat_service=svc)
        tab.set_input_text("问题")
        await tab.trigger_send()
        assert "问题" in tab.transcript_text()

        tab.trigger_new_conversation()
        assert tab.transcript_text() == ""
        assert svc.conversation.messages == []

    async def test_empty_input_flagged(self, qapp: QApplication) -> None:
        svc = ChatService(llm_client=MockLlmClient())
        tab = ChatTab(chat_service=svc)
        tab.set_input_text("   ")
        await tab.trigger_send()

        assert "空" in tab._status.text()  # noqa: SLF001
        assert len(svc.conversation.messages) == 0
