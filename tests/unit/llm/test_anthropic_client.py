"""Unit test for AnthropicLlmClient: translate_via_prompt returns content and maps errors."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from jimao_translator.exceptions import (
    AuthenticationError,
    ContentPolicyViolationError,
    LlmUnavailableError,
)
from jimao_translator.llm.providers.anthropic_client import AnthropicLlmClient


def _make_mock_client(text: str = "Hello") -> MagicMock:
    response = SimpleNamespace(content=[SimpleNamespace(text=text)])
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(return_value=response)
    return client


class TestTranslateViaPrompt:
    async def test_returns_stripped_text(self) -> None:
        client = _make_mock_client("  Hello  ")
        llm = AnthropicLlmClient(api_key="sk-test", client=client)
        result = await llm.translate_via_prompt("你好", "zh", "en")
        assert result == "Hello"
        client.messages.create.assert_awaited_once()

    async def test_rejects_missing_api_key(self) -> None:
        with pytest.raises(AuthenticationError):
            AnthropicLlmClient(api_key="", client=_make_mock_client())

    async def test_sdk_authentication_error_mapped(self) -> None:
        class AuthenticationError_sdk(Exception):
            pass

        client = MagicMock()
        client.messages = MagicMock()
        client.messages.create = AsyncMock(
            side_effect=AuthenticationError_sdk("invalid api key")
        )
        llm = AnthropicLlmClient(api_key="sk-x", client=client)
        with pytest.raises(AuthenticationError):
            await llm.translate_via_prompt("hi", "en", "zh")

    async def test_sdk_content_policy_error_mapped(self) -> None:
        class PermissionDeniedError(Exception):
            pass

        client = MagicMock()
        client.messages = MagicMock()
        client.messages.create = AsyncMock(
            side_effect=PermissionDeniedError("blocked by content_policy")
        )
        llm = AnthropicLlmClient(api_key="sk-x", client=client)
        with pytest.raises(ContentPolicyViolationError):
            await llm.translate_via_prompt("hi", "en", "zh")

    async def test_generic_sdk_error_mapped_to_unavailable(self) -> None:
        client = MagicMock()
        client.messages = MagicMock()
        client.messages.create = AsyncMock(side_effect=RuntimeError("connection reset"))
        llm = AnthropicLlmClient(api_key="sk-x", client=client)
        with pytest.raises(LlmUnavailableError):
            await llm.translate_via_prompt("hi", "en", "zh")

    def test_provider_name_includes_model(self) -> None:
        llm = AnthropicLlmClient(api_key="sk-x", model="claude-sonnet-4-5", client=_make_mock_client())
        assert "claude-sonnet-4-5" in llm.provider_name
