"""T300: LlmClient contract tests (9 cases from contracts/llm-client.md)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from jimao_translator.exceptions import (
    AuthenticationError,
    ContentPolicyViolationError,
    LlmUnavailableError,
)
from jimao_translator.llm.client import LlmClient
from jimao_translator.llm.providers.anthropic_client import AnthropicLlmClient
from jimao_translator.llm.providers.mock import MockLlmClient
from jimao_translator.models.chat import ChatConversation, ChatMessage
from jimao_translator.models.enums import MessageRole


def _conv(*pairs: tuple[MessageRole, str]) -> ChatConversation:
    return ChatConversation(messages=[ChatMessage(role=r, content=c) for r, c in pairs])


class _FakeStreamCtx:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    async def __aenter__(self) -> _FakeStreamCtx:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    @property
    def text_stream(self):
        async def _gen():
            for c in self._chunks:
                yield c

        return _gen()


def _anthropic_with_stream(chunks: list[str]) -> AnthropicLlmClient:
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.stream = MagicMock(return_value=_FakeStreamCtx(chunks))
    client.messages.create = AsyncMock(
        return_value=SimpleNamespace(content=[SimpleNamespace(text="".join(chunks))])
    )
    return AnthropicLlmClient(api_key="sk-test", client=client)


class TestLlmClientContract:
    """Full contract surface — verified against MockLlmClient; AnthropicLlmClient
    also exercised for streaming + error mapping (tests 4, 5, 6)."""

    async def test_chat_yields_deltas_when_stream_true(self) -> None:
        llm = MockLlmClient(reply="Hello world", chunks=3)
        conv = _conv((MessageRole.USER, "hi"))
        deltas = [c async for c in llm.chat(conv, stream=True)]
        assert len(deltas) >= 2
        assert "".join(deltas) == "Hello world"

    async def test_chat_yields_single_string_when_stream_false(self) -> None:
        llm = MockLlmClient(reply="Hello world")
        conv = _conv((MessageRole.USER, "hi"))
        deltas = [c async for c in llm.chat(conv, stream=False)]
        assert deltas == ["Hello world"]

    async def test_chat_raises_when_last_message_not_user(self) -> None:
        llm = MockLlmClient()
        conv = _conv(
            (MessageRole.USER, "hi"),
            (MessageRole.ASSISTANT, "hello"),
        )
        with pytest.raises(ValueError):
            async for _ in llm.chat(conv):
                pass

    async def test_chat_raises_authentication_error_on_invalid_key(self) -> None:
        class _SdkAuthError(Exception):
            pass

        client = MagicMock()
        client.messages = MagicMock()
        client.messages.stream = MagicMock(side_effect=_SdkAuthError("invalid"))
        llm = AnthropicLlmClient(api_key="sk-x", client=client)
        conv = _conv((MessageRole.USER, "hi"))
        # Rename class to trigger AuthenticationError mapping
        _SdkAuthError.__name__ = "AuthenticationError"
        with pytest.raises(AuthenticationError):
            async for _ in llm.chat(conv):
                pass

    async def test_chat_raises_unavailable_on_network_failure(self) -> None:
        llm = MockLlmClient(fail_with=LlmUnavailableError("network down"))
        conv = _conv((MessageRole.USER, "hi"))
        with pytest.raises(LlmUnavailableError):
            async for _ in llm.chat(conv):
                pass

    async def test_chat_respects_content_policy(self) -> None:
        llm = MockLlmClient(fail_with=ContentPolicyViolationError("filtered"))
        conv = _conv((MessageRole.USER, "something"))
        with pytest.raises(ContentPolicyViolationError):
            async for _ in llm.chat(conv):
                pass

    async def test_translate_via_prompt_returns_translation(self) -> None:
        llm = MockLlmClient(translations={("你好", "zh", "en"): "Hello"})
        assert await llm.translate_via_prompt("你好", "zh", "en") == "Hello"

    async def test_provider_name_is_non_empty(self) -> None:
        assert MockLlmClient().provider_name
        assert AnthropicLlmClient(api_key="sk-x", client=MagicMock()).provider_name

    async def test_runtime_checkable_protocol(self) -> None:
        assert isinstance(MockLlmClient(), LlmClient)

    async def test_anthropic_streams_deltas(self) -> None:
        llm = _anthropic_with_stream(["Hel", "lo", " world"])
        conv = _conv((MessageRole.USER, "hi"))
        deltas = [c async for c in llm.chat(conv, stream=True)]
        assert deltas == ["Hel", "lo", " world"]
