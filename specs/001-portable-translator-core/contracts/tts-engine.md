# Contract: TtsEngine

**Module**: `src/jimao_translator/tts/engine.py`

文本转语音（TTS）抽象接口。

## Protocol

```python
from typing import AsyncIterator, Protocol

class TtsEngine(Protocol):
    """Abstract text-to-speech engine."""

    async def synthesize(
        self,
        text: str,
        language: str,
        rate: float = 1.0,
    ) -> AsyncIterator[bytes]:
        """
        Stream synthesized audio bytes (MP3 or PCM).

        Args:
            text: text to speak (1..5000 chars).
            language: ISO 639-1 code (zh / en / ja / ko).
            rate: playback speed, 0.5..2.0. Out-of-range values MUST be clamped.

        Yields:
            audio chunks (bytes). The consumer plays them in order.

        Raises:
            TtsError: for synthesis failures (network, auth).
            UnsupportedLanguageError: when `language` is not supported.
        """
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def supported_languages(self) -> set[str]:
        ...
```

## Behavioral Contract

| Scenario | Expected behavior |
|----------|-------------------|
| 空文本 | 调用方预校验；引擎收到空字符串 MUST 抛 `ValueError` |
| `rate < 0.5` 或 `> 2.0` | 引擎 MUST clamp 到合法范围，不抛异常 |
| 不支持的语言 | 抛 `UnsupportedLanguageError` |
| 流式输出 | 首个 chunk MUST 在 500ms 内产生（低延迟播放） |
| 网络失败 | 抛 `TtsError`，允许上层降级（如使用系统 TTS 后备） |

## Contract Test Cases

`tests/contract/test_tts_engine.py`：

1. `test_synthesize_yields_audio_chunks`
2. `test_synthesize_empty_text_raises_value_error`
3. `test_synthesize_clamps_out_of_range_rate`
4. `test_synthesize_raises_unsupported_language`
5. `test_first_chunk_within_500ms` (实现可用 mock 以测试契约，真实引擎性能测试单独)
6. `test_supported_languages_includes_zh_en_ja_ko`
