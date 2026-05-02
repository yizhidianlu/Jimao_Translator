# Contract: LlmClient

**Module**: `src/jimao_translator/llm/client.py`

LLM 聊天客户端抽象接口。

## Protocol

```python
from typing import AsyncIterator, Protocol
from jimao_translator.models.chat import ChatConversation, ChatMessage

class LlmClient(Protocol):
    """Abstract LLM chat client."""

    async def chat(
        self,
        conversation: ChatConversation,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Send the conversation to the LLM and yield assistant text incrementally.

        Args:
            conversation: current chat state; last message MUST be role='user'.
            stream: if True, yield partial deltas; if False, yield a single full string.

        Yields:
            text deltas or a single complete response.

        Raises:
            LlmUnavailableError: network down, API down, quota exceeded.
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
        """
        Convenience method: use the LLM to translate text (used by LlmTranslator engine).
        Returns the translated text as a single string.

        Raises the same errors as `chat`.
        """
        ...

    @property
    def provider_name(self) -> str:
        """e.g., 'anthropic-claude'"""
        ...
```

## Behavioral Contract

| Scenario | Expected behavior |
|----------|-------------------|
| 最后一条消息非 user | 抛 `ValueError` |
| API 密钥缺失或无效 | 抛 `AuthenticationError` |
| 网络中断/API 超时 | 抛 `LlmUnavailableError`，上层 UI 提示使用基础翻译功能 |
| 内容违反安全策略 | 抛 `ContentPolicyViolationError`，UI 提示用户调整 |
| `stream=True` | MUST 在首 delta 之前不阻塞 >2s |
| 上下文超长 | MUST 自动窗口化（保留系统提示 + 最近 N 条），不静默丢弃用户消息 |

## Contract Test Cases

`tests/contract/test_llm_client.py`：

1. `test_chat_yields_deltas_when_stream_true`
2. `test_chat_yields_single_string_when_stream_false`
3. `test_chat_raises_when_last_message_not_user`
4. `test_chat_raises_authentication_error_on_invalid_key`
5. `test_chat_raises_unavailable_on_network_failure`
6. `test_chat_respects_content_policy`
7. `test_translate_via_prompt_returns_translation`
8. `test_provider_name_is_non_empty`
9. `test_context_windowing_preserves_system_prompt`
