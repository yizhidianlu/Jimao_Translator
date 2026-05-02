"""T053: MockLlmClient — deterministic LLM stub for tests."""

from __future__ import annotations

from collections.abc import AsyncIterator

from ...exceptions import (
    AuthenticationError,
    ContentPolicyViolationError,
    LlmUnavailableError,
)
from ...models.chat import ChatConversation
from ...models.enums import MessageRole


class MockLlmClient:
    """In-memory LLM client with configurable failure modes."""

    provider_name: str = "mock-llm"

    def __init__(
        self,
        *,
        reply: str = "This is a mock reply.",
        chunks: int = 3,
        fail_with: Exception | None = None,
        translations: dict[tuple[str, str, str], str] | None = None,
    ) -> None:
        self._reply = reply
        self._chunks = max(1, chunks)
        self._fail_with = fail_with
        self._translations = translations or {}

    async def chat(
        self,
        conversation: ChatConversation,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        if self._fail_with is not None:
            exc = self._fail_with
            raise exc

        if not conversation.messages or conversation.messages[-1].role is not MessageRole.USER:
            raise ValueError("last message must have role='user'")

        if stream:
            step = max(1, len(self._reply) // self._chunks)
            for i in range(0, len(self._reply), step):
                yield self._reply[i : i + step]
        else:
            yield self._reply

    async def translate_via_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        if self._fail_with is not None:
            raise self._fail_with
        key = (text, source_lang, target_lang)
        if key in self._translations:
            return self._translations[key]
        return f"[{source_lang}->{target_lang}] {text}"


__all__ = [
    "MockLlmClient",
    # re-exports for tests that want to construct failure modes
    "AuthenticationError",
    "ContentPolicyViolationError",
    "LlmUnavailableError",
]
