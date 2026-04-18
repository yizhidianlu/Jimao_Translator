"""LlmTranslator unit tests — engine adapter over LlmClient.translate_via_prompt."""

from __future__ import annotations

from jimao_translator.llm.providers.mock import MockLlmClient
from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.translation import TranslationRequest
from jimao_translator.translation.engines.llm_translator import LlmTranslator


def _req(
    source_lang: LanguageCode, target_lang: LanguageCode, text: str = "hello"
) -> TranslationRequest:
    return TranslationRequest(
        source_text=text,
        source_language=source_lang,
        target_language=target_lang,
        mode=TranslationMode.TEXT,
    )


class TestLlmTranslator:
    async def test_translate_uses_llm_client(self) -> None:
        llm = MockLlmClient(translations={("hello", "en", "zh"): "你好"})
        translator = LlmTranslator(llm)
        req = _req(LanguageCode.EN, LanguageCode.ZH, text="hello")
        result = await translator.translate(req)
        assert result.translated_text == "你好"
        assert result.detected_source_language is LanguageCode.EN
        assert (
            result.engine.startswith("anthropic")
            or "llm" in result.engine
            or "mock" in result.engine
        )

    async def test_supported_languages_is_non_empty(self) -> None:
        translator = LlmTranslator(MockLlmClient())
        assert len(translator.supported_languages) > 0

    async def test_completed_at_is_utc(self) -> None:
        translator = LlmTranslator(MockLlmClient())
        result = await translator.translate(_req(LanguageCode.ZH, LanguageCode.EN, "你好"))
        assert result.completed_at.utcoffset() is not None

    async def test_request_id_threaded_to_result(self) -> None:
        translator = LlmTranslator(MockLlmClient())
        req = _req(LanguageCode.EN, LanguageCode.JA, "hi")
        result = await translator.translate(req)
        assert result.request_id == req.id
