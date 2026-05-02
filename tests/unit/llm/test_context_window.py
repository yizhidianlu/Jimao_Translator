"""T304: context windowing preserves system prompt when over token limit."""

from __future__ import annotations

from jimao_translator.llm.context import trim_conversation
from jimao_translator.models.chat import ChatConversation, ChatMessage
from jimao_translator.models.enums import MessageRole


def _long_conv(n: int) -> ChatConversation:
    """Build a conversation of length n ending on a USER turn (invariant before send)."""
    msgs = []
    for i in range(n):
        # Pattern: user, assistant, user, assistant, ... user at the end.
        role = MessageRole.ASSISTANT if i % 2 == 1 and i != n - 1 else MessageRole.USER
        if i == n - 1:
            role = MessageRole.USER
        else:
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
        msgs.append(ChatMessage(role=role, content=f"message-{i}"))
    # Force last to USER
    msgs[-1] = ChatMessage(role=MessageRole.USER, content=f"message-{n - 1}")
    return ChatConversation(messages=msgs)


class TestTrimConversation:
    def test_no_trim_when_under_limit(self) -> None:
        conv = _long_conv(4)
        trimmed = trim_conversation(conv, max_messages=20, system_prompt="sys")
        assert trimmed[0]["role"] == "system"
        assert trimmed[0]["content"] == "sys"
        assert len(trimmed) == 5  # system + 4

    def test_trims_oldest_preserves_most_recent(self) -> None:
        conv = _long_conv(30)
        trimmed = trim_conversation(conv, max_messages=6, system_prompt="sys")
        # system + 6 most recent = 7
        assert trimmed[0]["role"] == "system"
        assert len(trimmed) == 7
        # Must keep the newest
        assert trimmed[-1]["content"] == "message-29"

    def test_preserves_system_prompt_when_trimming_heavily(self) -> None:
        conv = _long_conv(100)
        trimmed = trim_conversation(conv, max_messages=4, system_prompt="critical-sys")
        assert trimmed[0]["role"] == "system"
        assert trimmed[0]["content"] == "critical-sys"

    def test_no_system_prompt_when_none(self) -> None:
        conv = _long_conv(4)
        trimmed = trim_conversation(conv, max_messages=20, system_prompt=None)
        roles = [m["role"] for m in trimmed]
        assert "system" not in roles
        assert len(trimmed) == 4

    def test_does_not_silently_drop_user_message_about_to_send(self) -> None:
        """Last message must always be preserved regardless of trim."""
        conv = _long_conv(50)
        trimmed = trim_conversation(conv, max_messages=2, system_prompt="sys")
        assert trimmed[-1]["content"] == "message-49"
        assert trimmed[-1]["role"] == "user"
