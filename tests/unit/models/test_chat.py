"""T023: Unit tests for ChatMessage and ChatConversation."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from jimao_translator.models.chat import ChatConversation, ChatMessage
from jimao_translator.models.enums import MessageRole


def _now() -> datetime:
    return datetime.now(UTC)


class TestChatMessage:
    def test_valid_user_message(self) -> None:
        msg = ChatMessage(role=MessageRole.USER, content="hello")
        assert isinstance(msg.id, UUID)
        assert msg.timestamp.tzinfo is not None
        assert msg.token_usage is None

    def test_assistant_message_with_tokens(self) -> None:
        msg = ChatMessage(role=MessageRole.ASSISTANT, content="hi", token_usage=42)
        assert msg.token_usage == 42

    def test_empty_content_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ChatMessage(role=MessageRole.USER, content="")

    def test_content_over_20000_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ChatMessage(role=MessageRole.USER, content="x" * 20001)

    def test_content_exactly_20000_accepted(self) -> None:
        msg = ChatMessage(role=MessageRole.USER, content="x" * 20000)
        assert len(msg.content) == 20000

    def test_negative_token_usage_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ChatMessage(role=MessageRole.ASSISTANT, content="x", token_usage=-1)


class TestChatConversation:
    def test_empty_conversation(self) -> None:
        convo = ChatConversation()
        assert convo.messages == []
        assert isinstance(convo.id, UUID)
        assert convo.created_at <= convo.last_active_at

    def test_append_message(self) -> None:
        convo = ChatConversation()
        convo.messages.append(ChatMessage(role=MessageRole.USER, content="hi"))
        assert len(convo.messages) == 1

    def test_messages_preserved_in_order(self) -> None:
        m1 = ChatMessage(role=MessageRole.USER, content="q1", timestamp=_now())
        m2 = ChatMessage(role=MessageRole.ASSISTANT, content="a1", timestamp=_now())
        convo = ChatConversation(messages=[m1, m2])
        assert convo.messages[0].role is MessageRole.USER
        assert convo.messages[1].role is MessageRole.ASSISTANT
