# Contract: SpeechRecognizer

**Module**: `src/jimao_translator/speech/recognizer.py`

语音识别（STT）抽象接口。

## Protocol

```python
from typing import Protocol
from pathlib import Path
from jimao_translator.models.voice import VoiceSession

class SpeechRecognizer(Protocol):
    """Abstract speech-to-text engine."""

    async def recognize(
        self,
        audio_bytes: bytes,
        language: str | None = None,
    ) -> VoiceSession:
        """
        Recognize speech from in-memory audio bytes (WAV/PCM 16kHz preferred).

        Args:
            audio_bytes: raw audio payload. MUST NOT be persisted to disk.
            language: optional ISO 639-1 hint; None triggers auto-detect.

        Returns:
            VoiceSession with recognized_text and recognition_confidence.

        Raises:
            NoSpeechDetectedError: when audio is silence/pure noise.
            RecognitionError: for network or engine failures.
            UnsupportedLanguageError: when hint language is not supported.
        """
        ...

    @property
    def name(self) -> str:
        """Engine identifier."""
        ...

    @property
    def supported_languages(self) -> set[str]:
        ...
```

## Behavioral Contract

| Scenario | Expected behavior |
|----------|-------------------|
| 静音/纯噪音输入 | 抛 `NoSpeechDetectedError`，UI 显示"未检测到语音，请重试" |
| 置信度 < 0.6 | 正常返回，UI 负责标注低置信度 |
| 输入非法格式 | 抛 `RecognitionError("invalid_audio_format")` |
| 原始音频字节 | MUST 在函数返回前被释放，MUST NOT 写入磁盘（FR-016） |
| `language=None` | 引擎 MUST 尝试自动检测并在 `source_language` 字段返回结果 |

## Contract Test Cases

`tests/contract/test_speech_recognizer.py`：

1. `test_recognize_returns_voice_session`
2. `test_recognize_empty_audio_raises_no_speech`
3. `test_recognize_pure_silence_raises_no_speech`
4. `test_recognize_low_confidence_still_returns`
5. `test_recognize_auto_detects_language_when_hint_none`
6. `test_recognize_does_not_persist_audio_to_disk`
7. `test_supported_languages_includes_zh_en_ja_ko`

Mock 实现 MUST 通过相同的契约测试集。
