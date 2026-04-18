"""T050: MockTranslationProvider — deterministic offline stub for tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from ...exceptions import TranslationError, UnsupportedLanguagePairError
from ...models.enums import LanguageCode
from ...models.translation import TranslationRequest, TranslationResult

_SUPPORTED = {"zh", "en", "ja", "ko"}

_DEFAULT_TABLE: dict[tuple[str, str], str] = {
    ("zh", "en"): "Hello",
    ("en", "zh"): "你好",
    ("zh", "ja"): "こんにちは",
    ("zh", "ko"): "안녕하세요",
    ("en", "ja"): "こんにちは",
    ("en", "ko"): "안녕하세요",
    ("ja", "en"): "Hello",
    ("ko", "en"): "Hello",
}


class MockTranslationProvider:
    """Deterministic, in-memory translation engine for contract / integration tests."""

    name: str = "mock-translator"

    def __init__(
        self,
        *,
        table: dict[tuple[str, str], str] | None = None,
        delay_seconds: float = 0.0,
        fail_with: Exception | None = None,
    ) -> None:
        self._table = {**_DEFAULT_TABLE, **(table or {})}
        self._delay = delay_seconds
        self._fail_with = fail_with

    @property
    def supported_languages(self) -> set[str]:
        return set(_SUPPORTED)

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        if self._fail_with is not None:
            raise self._fail_with

        if not request.source_text.strip():
            raise ValueError("source_text must not be empty")

        detected = (
            LanguageCode.ZH
            if request.source_language is LanguageCode.AUTO
            else request.source_language
        )

        if (
            detected.value not in _SUPPORTED
            or request.target_language.value not in _SUPPORTED
        ):
            raise UnsupportedLanguagePairError(
                f"{detected.value} -> {request.target_language.value} not supported"
            )

        if self._delay:
            try:
                await asyncio.wait_for(asyncio.sleep(self._delay), timeout=10)
            except asyncio.TimeoutError as err:
                raise TranslationError("timeout") from err

        key = (detected.value, request.target_language.value)
        translated = self._table.get(key, f"[{detected.value}->{request.target_language.value}] {request.source_text}")

        return TranslationResult(
            request_id=request.id,
            translated_text=translated,
            detected_source_language=detected,
            confidence=0.99,
            engine=self.name,
            completed_at=datetime.now(UTC),
        )
