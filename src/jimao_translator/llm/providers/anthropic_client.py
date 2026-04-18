"""T113 + T310: Anthropic LlmClient — Claude-based chat + translation backend.

Phase 3 used `translate_via_prompt` only. Phase 5 US3 adds streaming `chat()`
with automatic context windowing and full domain-error mapping.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from ...exceptions import (
    AuthenticationError,
    ContentPolicyViolationError,
    LlmUnavailableError,
)
from ...models.chat import ChatConversation
from ...models.enums import MessageRole
from ..context import trim_conversation

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_MAX_MESSAGES_WINDOW = 40

_TRANSLATION_SYSTEM_PROMPT = (
    "You are a professional translator. Translate the user's text faithfully "
    "from {source_lang} to {target_lang}. Preserve proper nouns. "
    "Respond with ONLY the translation — no explanations, no quotes, no prefixes."
)


class AnthropicLlmClient:
    """LlmClient implementation backed by the Anthropic Messages API."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        system_prompt: str | None = None,
        max_messages_window: int = DEFAULT_MAX_MESSAGES_WINDOW,
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise AuthenticationError("Anthropic API key is missing")
        self._model = model
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt
        self._max_messages_window = max_messages_window
        if client is not None:
            self._client = client
        else:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return f"anthropic:{self._model}"

    async def translate_via_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        system = _TRANSLATION_SYSTEM_PROMPT.format(
            source_lang=source_lang, target_lang=target_lang
        )
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                messages=[{"role": "user", "content": text}],
            )
        except Exception as err:  # noqa: BLE001
            self._raise_mapped(err)

        return self._extract_text(response).strip()

    async def chat(
        self,
        conversation: ChatConversation,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        if not conversation.messages or conversation.messages[-1].role is not MessageRole.USER:
            raise ValueError("last message must have role='user'")

        payload_messages = trim_conversation(
            conversation,
            max_messages=self._max_messages_window,
            system_prompt=None,  # Anthropic takes `system=` separately.
        )

        kwargs: dict[str, Any] = dict(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=payload_messages,
        )
        if self._system_prompt:
            kwargs["system"] = self._system_prompt

        try:
            if stream:
                async with self._client.messages.stream(**kwargs) as response:
                    async for chunk in response.text_stream:
                        yield chunk
            else:
                response = await self._client.messages.create(**kwargs)
                yield self._extract_text(response)
        except Exception as err:  # noqa: BLE001
            self._raise_mapped(err)

    @staticmethod
    def _extract_text(response: Any) -> str:
        parts = getattr(response, "content", None) or []
        chunks: list[str] = []
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                chunks.append(text)
        return "".join(chunks)

    @staticmethod
    def _raise_mapped(err: Exception) -> None:
        """Map Anthropic SDK errors to our domain exception hierarchy."""
        name = err.__class__.__name__
        message = str(err) or name

        if "Authentication" in name or "ApiKey" in name or "Unauthorized" in name:
            raise AuthenticationError(message) from err
        if "Permission" in name or "ContentPolicy" in name or "content_policy" in message.lower():
            raise ContentPolicyViolationError(message) from err
        raise LlmUnavailableError(message) from err
