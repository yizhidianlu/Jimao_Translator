"""T040: TranslationProvider Protocol (see contracts/translation-provider.md)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models.translation import TranslationRequest, TranslationResult


@runtime_checkable
class TranslationProvider(Protocol):
    """Abstract translation engine. Implementations must be async."""

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        """Translate source_text from source_language to target_language.

        Raises:
            TranslationError: engine failure (network, auth, quota).
            UnsupportedLanguagePairError: language pair not supported.
            TimeoutError: request exceeds deadline.
        """
        ...

    @property
    def name(self) -> str:
        """Unique engine identifier (e.g., 'qwen-plus')."""
        ...

    @property
    def supported_languages(self) -> set[str]:
        """Set of supported ISO 639-1 language codes."""
        ...
