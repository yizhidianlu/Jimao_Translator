# Contract: TranslationProvider

**Module**: `src/jimao_translator/translation/provider.py`

翻译引擎抽象接口。所有具体翻译引擎（LLM 翻译器、Mock）MUST 实现此 Protocol。

## Protocol

```python
from typing import Protocol
from jimao_translator.models.translation import TranslationRequest, TranslationResult

class TranslationProvider(Protocol):
    """Abstract translation engine. Implementations must be async."""

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        """
        Translate source_text from source_language to target_language.

        Raises:
            TranslationError: when the engine fails (network, auth, quota).
            UnsupportedLanguagePairError: when the requested language pair is not supported.
            TimeoutError: when the request exceeds the engine's deadline (default 10s).
        """
        ...

    @property
    def name(self) -> str:
        """Unique engine identifier (e.g., 'claude-sonnet-4-6')."""
        ...

    @property
    def supported_languages(self) -> set[str]:
        """Set of supported ISO 639-1 language codes."""
        ...
```

## Behavioral Contract

| Scenario | Expected behavior |
|----------|-------------------|
| `source_text` 为空 | 调用方负责预校验；引擎收到空字符串时抛 `ValueError` |
| `source_language == target_language` (非 `auto`) | 调用方短路返回原文，不调用引擎 |
| `source_language == "auto"` | 引擎 MUST 返回检测到的实际源语言于 `detected_source_language` |
| 网络中断 | 抛 `TranslationError("network")` 并允许上层降级 |
| 响应超时 | 10s 内未完成 MUST 抛 `TimeoutError` |
| 语言对不支持 | 抛 `UnsupportedLanguagePairError`，列出可用语言 |

## Contract Test Cases

契约测试位于 `tests/contract/test_translation_provider.py`：

1. `test_translate_returns_result_for_valid_request`
2. `test_translate_same_source_and_target_returns_original` (by caller, not engine)
3. `test_translate_raises_on_empty_source_text`
4. `test_translate_detects_auto_source_language`
5. `test_translate_respects_timeout`
6. `test_translate_raises_unsupported_language_pair`
7. `test_name_is_non_empty`
8. `test_supported_languages_is_subset_of_zh_en_ja_ko`

**所有实现 MUST 通过同一套契约测试。**
