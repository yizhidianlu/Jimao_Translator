"""T100: Contract tests for the TranslationProvider protocol.

Every concrete TranslationProvider implementation (LlmTranslator, Mock, future ones)
MUST pass this test module. The module is parameterized over a fixture `provider`
that each implementation supplies.
"""

from __future__ import annotations

import asyncio
from typing import Callable

import pytest

from jimao_translator.exceptions import TranslationError, UnsupportedLanguagePairError
from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.translation import TranslationRequest
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.provider import TranslationProvider


@pytest.fixture()
def provider() -> TranslationProvider:
    """Default provider fixture — Mock. Override in concrete impl test modules."""
    return MockTranslationProvider()


def _make_request(
    text: str = "你好世界",
    source: LanguageCode = LanguageCode.ZH,
    target: LanguageCode = LanguageCode.EN,
) -> TranslationRequest:
    return TranslationRequest(
        source_text=text,
        source_language=source,
        target_language=target,
        mode=TranslationMode.TEXT,
    )


class TestTranslationProviderContract:
    async def test_translate_returns_result_for_valid_request(
        self, provider: TranslationProvider
    ) -> None:
        result = await provider.translate(_make_request())
        assert result.translated_text
        assert result.engine == provider.name
        assert result.request_id is not None

    async def test_translate_raises_on_empty_source_text(
        self, provider: TranslationProvider
    ) -> None:
        # Bypass the model validator to probe the engine directly.
        request = _make_request("valid")
        object.__setattr__(request, "source_text", "")
        with pytest.raises(ValueError):
            await provider.translate(request)

    async def test_translate_detects_auto_source_language(
        self, provider: TranslationProvider
    ) -> None:
        request = _make_request(source=LanguageCode.AUTO, target=LanguageCode.EN)
        result = await provider.translate(request)
        assert result.detected_source_language is not LanguageCode.AUTO
        assert result.detected_source_language.value in provider.supported_languages

    async def test_translate_respects_timeout(self) -> None:
        slow = MockTranslationProvider(delay_seconds=2.0)
        with pytest.raises((asyncio.TimeoutError, TranslationError)):
            await asyncio.wait_for(slow.translate(_make_request()), timeout=0.1)

    async def test_translate_raises_unsupported_language_pair(self) -> None:
        class NarrowProvider(MockTranslationProvider):
            @property
            def supported_languages(self) -> set[str]:
                return {"en"}

            async def translate(self, request):  # type: ignore[override]
                if request.target_language.value not in self.supported_languages:
                    raise UnsupportedLanguagePairError("target not supported")
                return await super().translate(request)

        narrow = NarrowProvider()
        with pytest.raises(UnsupportedLanguagePairError):
            await narrow.translate(_make_request(target=LanguageCode.JA))

    def test_name_is_non_empty(self, provider: TranslationProvider) -> None:
        assert isinstance(provider.name, str)
        assert len(provider.name) > 0

    def test_supported_languages_is_subset_of_zh_en_ja_ko(
        self, provider: TranslationProvider
    ) -> None:
        assert provider.supported_languages <= {"zh", "en", "ja", "ko"}

    async def test_translate_same_source_and_target_handled_by_caller(
        self, provider: TranslationProvider
    ) -> None:
        """Spec says callers short-circuit; engine still works if called directly."""
        result = await provider.translate(
            _make_request(source=LanguageCode.ZH, target=LanguageCode.ZH)
        )
        # It is acceptable for the engine to either return original text or a translation —
        # the contract only requires that no exception is raised.
        assert result.translated_text
