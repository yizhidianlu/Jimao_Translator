"""T111: LlmTranslator — uses LlmClient.translate_via_prompt as the engine."""

from __future__ import annotations

from datetime import UTC, datetime

from ...exceptions import TranslationError, UnsupportedLanguagePairError
from ...llm.client import LlmClient
from ...models.enums import LanguageCode
from ...models.translation import TranslationRequest, TranslationResult

_SUPPORTED = {"zh", "en", "ja", "ko"}


class LlmTranslator:
    """TranslationProvider backed by an LLM chat model."""

    def __init__(self, client: LlmClient) -> None:
        self._client = client

    @property
    def name(self) -> str:
        return f"llm:{self._client.provider_name}"

    @property
    def supported_languages(self) -> set[str]:
        return set(_SUPPORTED)

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        if not request.source_text.strip():
            raise ValueError("source_text must not be empty")

        detected = request.source_language
        if detected is LanguageCode.AUTO:
            from ..detection import detect_language

            detected = detect_language(request.source_text)
            if detected is LanguageCode.AUTO:
                raise TranslationError("could not detect source language")

        if detected.value not in _SUPPORTED or request.target_language.value not in _SUPPORTED:
            raise UnsupportedLanguagePairError(
                f"{detected.value} -> {request.target_language.value} not supported"
            )

        translated = await self._client.translate_via_prompt(
            text=request.source_text,
            source_lang=detected.value,
            target_lang=request.target_language.value,
        )

        return TranslationResult(
            request_id=request.id,
            translated_text=translated,
            detected_source_language=detected,
            engine=self.name,
            completed_at=datetime.now(UTC),
        )
