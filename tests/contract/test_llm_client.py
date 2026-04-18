"""T300: LlmClient contract tests (verified against MockLlmClient + QwenLlmClient)."""

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
from jimao_translator.llm.providers.mock import MockLlmClient
from jimao_translator.llm.providers.qwen_client import QwenLlmClient
from jimao_translator.models.chat import ChatConversation, ChatMessage
from jimao_translator.models.enums import MessageRole


def _conv(*pairs: tuple[MessageRole, str]) -> ChatConversation:
    return ChatConversation(messages=[ChatMessage(role=r, content=c) for r, c in pairs])


async def _async_iter(items: list[object]):
    for item in items:
        yield item


def _qwen_with_stream(chunks: list[str]) -> QwenLlmClient:
    """Build a QwenLlmClient whose underlying SDK yields OpenAI-style stream chunks."""
    chunk_objs = [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=c))]) for c in chunks
    ]
    non_stream_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="".join(chunks)))]
    )

    async def _create(**kwargs: object):
        if kwargs.get("stream"):
            return _async_iter(chunk_objs)
        return non_stream_response

    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = _create
    return QwenLlmClient(api_key="sk-test", client=client)


class TestLlmClientContract:
    """Full contract surface — verified against MockLlmClient; QwenLlmClient
    also exercised for streaming + error mapping."""

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
        class FakeAuthenticationError(Exception):
            pass

        client = MagicMock()
        client.chat = MagicMock()
        client.chat.completions = MagicMock()
        client.chat.completions.create = AsyncMock(side_effect=FakeAuthenticationError("invalid"))
        llm = QwenLlmClient(api_key="sk-x", client=client)
        conv = _conv((MessageRole.USER, "hi"))
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
        assert QwenLlmClient(api_key="sk-x", client=MagicMock()).provider_name

    async def test_runtime_checkable_protocol(self) -> None:
        assert isinstance(MockLlmClient(), LlmClient)

    async def test_qwen_streams_deltas(self) -> None:
        llm = _qwen_with_stream(["Hel", "lo", " world"])
        conv = _conv((MessageRole.USER, "hi"))
        deltas = [c async for c in llm.chat(conv, stream=True)]
        assert deltas == ["Hel", "lo", " world"]
