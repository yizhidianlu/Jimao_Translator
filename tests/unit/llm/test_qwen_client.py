"""Unit test for QwenLlmClient: translate_via_prompt returns content and maps errors."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from jimao_translator.exceptions import (
    AuthenticationError,
    ContentPolicyViolationError,
    LlmUnavailableError,
)
from jimao_translator.llm.providers.qwen_client import QwenLlmClient


def _make_mock_client(text: str = "Hello") -> MagicMock:
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=response)
    return client


class TestTranslateViaPrompt:
    async def test_returns_stripped_text(self) -> None:
        client = _make_mock_client("  Hello  ")
        llm = QwenLlmClient(api_key="sk-test", client=client)
        result = await llm.translate_via_prompt("你好", "zh", "en")
        assert result == "Hello"
        client.chat.completions.create.assert_awaited_once()

    async def test_rejects_missing_api_key(self) -> None:
        with pytest.raises(AuthenticationError):
            QwenLlmClient(api_key="", client=_make_mock_client())

    async def test_sdk_authentication_error_mapped(self) -> None:
        class FakeAuthenticationError(Exception):
            pass

        client = MagicMock()
        client.chat = MagicMock()
        client.chat.completions = MagicMock()
        client.chat.completions.create = AsyncMock(
            side_effect=FakeAuthenticationError("invalid api key")
        )
        llm = QwenLlmClient(api_key="sk-x", client=client)
        with pytest.raises(AuthenticationError):
            await llm.translate_via_prompt("hi", "en", "zh")

    async def test_sdk_content_policy_error_mapped(self) -> None:
        class PermissionDeniedError(Exception):
            pass

        client = MagicMock()
        client.chat = MagicMock()
        client.chat.completions = MagicMock()
        client.chat.completions.create = AsyncMock(
            side_effect=PermissionDeniedError("blocked by content_policy")
        )
        llm = QwenLlmClient(api_key="sk-x", client=client)
        with pytest.raises(ContentPolicyViolationError):
            await llm.translate_via_prompt("hi", "en", "zh")

    async def test_generic_sdk_error_mapped_to_unavailable(self) -> None:
        client = MagicMock()
        client.chat = MagicMock()
        client.chat.completions = MagicMock()
        client.chat.completions.create = AsyncMock(side_effect=RuntimeError("connection reset"))
        llm = QwenLlmClient(api_key="sk-x", client=client)
        with pytest.raises(LlmUnavailableError):
            await llm.translate_via_prompt("hi", "en", "zh")

    def test_provider_name_includes_model(self) -> None:
        llm = QwenLlmClient(api_key="sk-x", model="qwen-max", client=_make_mock_client())
        assert "qwen-max" in llm.provider_name
        assert llm.provider_name.startswith("qwen:")
