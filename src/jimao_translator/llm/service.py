"""T312: ChatService — multi-turn conversation state + LLM streaming.

Append the user message first, then stream the assistant response. If the LLM
call fails, the user message is retained so the user can see what they sent and
optionally retry; no partial assistant message is persisted.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from ..models.chat import ChatConversation, ChatMessage
from ..models.enums import MessageRole
from .client import LlmClient

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful bilingual assistant. Help the user translate, "
    "explain grammar, and clarify cultural context. Reply concisely in the "
    "language of the user's most recent message unless they ask otherwise."
)


class ChatService:
    """Conversation state holder + LLM invocation glue."""

    def __init__(
        self,
        llm_client: LlmClient,
        system_prompt: str | None = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._llm = llm_client
        self._system_prompt = system_prompt
        self._conversation = ChatConversation()

    @property
    def conversation(self) -> ChatConversation:
        return self._conversation

    @property
    def system_prompt(self) -> str | None:
        return self._system_prompt

    def new_conversation(self) -> None:
        self._conversation = ChatConversation()

    async def send(
        self,
        user_text: str,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        if not user_text or not user_text.strip():
            raise ValueError("user_text must not be empty")

        user_msg = ChatMessage(role=MessageRole.USER, content=user_text)
        self._conversation.messages.append(user_msg)

        collected: list[str] = []
        try:
            async for delta in self._llm.chat(self._conversation, stream=stream):
                collected.append(delta)
                yield delta
        except Exception:
            # Keep user message in history, but do NOT persist a partial assistant reply.
            raise

        assistant_content = "".join(collected).strip()
        if assistant_content:
            self._conversation.messages.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=assistant_content)
            )
