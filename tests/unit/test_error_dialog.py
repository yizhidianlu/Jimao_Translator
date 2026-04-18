"""T421: Unit tests for format_error — domain error → user-friendly text."""

from __future__ import annotations

from jimao_translator.exceptions import (
    AuthenticationError,
    ContentPolicyViolationError,
    JimaoError,
    LlmUnavailableError,
    NoSpeechDetectedError,
    RecognitionError,
    TranslationError,
    TtsError,
    UnsupportedLanguageError,
)
from jimao_translator.ui.error_dialog import format_error


class TestFormatError:
    def test_authentication_error_prompts_to_update_api_key(self) -> None:
        title, body = format_error(AuthenticationError("bad key"))
        assert "认证" in title
        assert "密钥" in body

    def test_content_policy_error_prompts_to_rephrase(self) -> None:
        title, body = format_error(ContentPolicyViolationError("filtered"))
        assert "内容" in title
        assert "策略" in body

    def test_llm_unavailable_mentions_fallback(self) -> None:
        title, body = format_error(LlmUnavailableError("timeout"))
        assert "LLM" in title
        assert "基础翻译" in body
        assert "timeout" in body  # include raw detail for troubleshooting

    def test_no_speech_detected_has_mic_hint(self) -> None:
        title, body = format_error(NoSpeechDetectedError("silence"))
        assert "语音" in title
        assert "麦克风" in body

    def test_recognition_error(self) -> None:
        title, _ = format_error(RecognitionError("net"))
        assert "识别" in title

    def test_tts_error(self) -> None:
        title, _ = format_error(TtsError("boom"))
        assert "合成" in title

    def test_unsupported_language_error(self) -> None:
        title, body = format_error(UnsupportedLanguageError("xh"))
        assert "语言" in title
        assert "xh" in body

    def test_translation_error(self) -> None:
        title, _ = format_error(TranslationError("bad"))
        assert "翻译" in title

    def test_generic_jimao_error(self) -> None:
        title, body = format_error(JimaoError("something"))
        assert title
        assert "something" in body

    def test_unknown_exception(self) -> None:
        title, body = format_error(RuntimeError("whoops"))
        assert "意外" in title
        assert "RuntimeError" in body
        assert "whoops" in body
