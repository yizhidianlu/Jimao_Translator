"""T043: LlmClient Protocol (see contracts/llm-client.md)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from ..models.chat import ChatConversation


@runtime_checkable
class LlmClient(Protocol):
    """Abstract LLM chat client."""

    def chat(
        self,
        conversation: ChatConversation,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Send the conversation to the LLM and yield assistant text incrementally.

        Args:
            conversation: current chat state; last message MUST have role='user'.
            stream: if True, yield partial deltas; if False, yield a single full string.

        Raises:
            LlmUnavailableError: network/API down or quota exceeded.
            AuthenticationError: invalid API key.
            ContentPolicyViolationError: content filtered by safety policy (FR-015).
        """
        ...

    async def translate_via_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Convenience method: use the LLM to translate text (used by LlmTranslator engine)."""
        ...

    @property
    def provider_name(self) -> str:
        """e.g., 'qwen:qwen-plus'."""
        ...
