"""QwenLlmClient — Qwen3 via Alibaba DashScope OpenAI-compatible endpoint.

Replaces the Anthropic backend. Uses the `openai` Python SDK pointed at
`https://dashscope.aliyuncs.com/compatible-mode/v1`, which DashScope
exposes as a drop-in OpenAI Chat Completions API.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from ...exceptions import (
    AuthenticationError,
    ContentPolicyViolationError,
    LlmUnavailableError,
)
from ...models.chat import ChatConversation
from ...models.enums import MessageRole
from ..context import trim_conversation

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen-plus"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_MAX_MESSAGES_WINDOW = 40
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

_TRANSLATION_SYSTEM_PROMPT = (
    "You are a professional translator. Translate the user's text faithfully "
    "from {source_lang} to {target_lang}. Preserve proper nouns. "
    "Respond with ONLY the translation — no explanations, no quotes, no prefixes."
)


class QwenLlmClient:
    """LlmClient implementation backed by DashScope's OpenAI-compatible endpoint."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        system_prompt: str | None = None,
        max_messages_window: int = DEFAULT_MAX_MESSAGES_WINDOW,
        base_url: str = DASHSCOPE_BASE_URL,
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise AuthenticationError("DashScope API key is missing")
        self._model = model
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt
        self._max_messages_window = max_messages_window
        if client is not None:
            self._client = client
        else:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @property
    def provider_name(self) -> str:
        return f"qwen:{self._model}"

    async def translate_via_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        system = _TRANSLATION_SYSTEM_PROMPT.format(source_lang=source_lang, target_lang=target_lang)
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text},
                ],
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

        payload_messages: list[dict[str, str]] = trim_conversation(
            conversation,
            max_messages=self._max_messages_window,
            system_prompt=None,
        )
        if self._system_prompt:
            payload_messages = [
                {"role": "system", "content": self._system_prompt},
                *payload_messages,
            ]

        try:
            if stream:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    messages=payload_messages,
                    stream=True,
                )
                async for chunk in response:
                    delta = self._extract_delta(chunk)
                    if delta:
                        yield delta
            else:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    messages=payload_messages,
                )
                yield self._extract_text(response)
        except Exception as err:  # noqa: BLE001
            self._raise_mapped(err)

    @staticmethod
    def _extract_text(response: Any) -> str:
        choices = getattr(response, "choices", None) or []
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        if message is None:
            return ""
        return getattr(message, "content", "") or ""

    @staticmethod
    def _extract_delta(chunk: Any) -> str:
        choices = getattr(chunk, "choices", None) or []
        if not choices:
            return ""
        delta = getattr(choices[0], "delta", None)
        if delta is None:
            return ""
        return getattr(delta, "content", "") or ""

    @staticmethod
    def _raise_mapped(err: Exception) -> None:
        """Map OpenAI SDK errors (raised by DashScope) to domain exceptions."""
        name = err.__class__.__name__
        message = str(err) or name

        if "Authentication" in name or "ApiKey" in name or "Unauthorized" in name:
            raise AuthenticationError(message) from err
        if "Permission" in name or "ContentPolicy" in name or "content_policy" in message.lower():
            raise ContentPolicyViolationError(message) from err
        raise LlmUnavailableError(message) from err
