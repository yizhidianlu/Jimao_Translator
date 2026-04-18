"""T301–T303: ChatService integration tests (multi-turn, unavailability, policy)."""

from __future__ import annotations

import pytest

from jimao_translator.exceptions import ContentPolicyViolationError, LlmUnavailableError
from jimao_translator.llm.providers.mock import MockLlmClient
from jimao_translator.llm.service import ChatService
from jimao_translator.models.enums import MessageRole


class TestMultiTurnContext:
    async def test_preserves_context_over_ten_turns(self) -> None:
        """T301 SC-006: 10 turns, each reply references prior."""
        llm = MockLlmClient(reply="ok", chunks=1)
        svc = ChatService(llm_client=llm)

        for i in range(10):
            reply_chunks = [c async for c in svc.send(f"question {i}", stream=True)]
            assert "".join(reply_chunks) == "ok"

        # 10 user messages + 10 assistant messages = 20
        assert len(svc.conversation.messages) == 20
        assert svc.conversation.messages[0].role is MessageRole.USER
        assert svc.conversation.messages[-1].role is MessageRole.ASSISTANT

    async def test_new_conversation_resets_state(self) -> None:
        llm = MockLlmClient(reply="hi", chunks=1)
        svc = ChatService(llm_client=llm)
        async for _ in svc.send("first"):
            pass
        assert len(svc.conversation.messages) == 2
        svc.new_conversation()
        assert svc.conversation.messages == []


class TestLlmUnavailability:
    async def test_unavailability_raises_and_leaves_user_message(self) -> None:
        """T302: network down — user message should still be recorded; assistant not."""
        llm = MockLlmClient(fail_with=LlmUnavailableError("down"))
        svc = ChatService(llm_client=llm)

        with pytest.raises(LlmUnavailableError):
            async for _ in svc.send("help"):
                pass

        msgs = svc.conversation.messages
        assert len(msgs) == 1
        assert msgs[0].role is MessageRole.USER
        assert msgs[0].content == "help"


class TestContentPolicy:
    async def test_content_policy_violation_surfaced(self) -> None:
        """T303: policy error must bubble, user msg kept, assistant msg absent."""
        llm = MockLlmClient(fail_with=ContentPolicyViolationError("filtered"))
        svc = ChatService(llm_client=llm)

        with pytest.raises(ContentPolicyViolationError):
            async for _ in svc.send("something"):
                pass

        assert len(svc.conversation.messages) == 1
        assert svc.conversation.messages[0].role is MessageRole.USER
