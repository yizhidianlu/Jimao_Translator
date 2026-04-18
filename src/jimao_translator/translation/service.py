"""T112: TranslationService — orchestrates validate → detect → short-circuit → engine → history."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from ..models.enums import LanguageCode, TranslationMode
from ..models.translation import (
    TranslationHistoryEntry,
    TranslationRequest,
    TranslationResult,
)
from ..storage.history import TranslationHistoryRepository
from .detection import detect_language
from .provider import TranslationProvider

logger = logging.getLogger(__name__)

_MAX_SOURCE_TEXT = 5000


class TranslationService:
    """User-facing translation orchestration."""

    def __init__(
        self,
        provider: TranslationProvider,
        history_repo: TranslationHistoryRepository,
        history_enabled: bool = True,
    ) -> None:
        self._provider = provider
        self._history_repo = history_repo
        self._history_enabled = history_enabled

    def set_history_enabled(self, enabled: bool) -> None:
        self._history_enabled = enabled

    async def translate(
        self,
        source_text: str,
        source_language: LanguageCode,
        target_language: LanguageCode,
        mode: TranslationMode,
    ) -> TranslationResult:
        if not source_text or not source_text.strip():
            raise ValueError("source_text must not be empty")
        if len(source_text) > _MAX_SOURCE_TEXT:
            raise ValueError(f"source_text exceeds {_MAX_SOURCE_TEXT} chars")
        if target_language is LanguageCode.AUTO:
            raise ValueError("target_language cannot be 'auto'")

        resolved_source = source_language
        if resolved_source is LanguageCode.AUTO:
            resolved_source = detect_language(source_text)

        request = TranslationRequest(
            source_text=source_text,
            source_language=resolved_source,
            target_language=target_language,
            mode=mode,
        )

        if (
            resolved_source is not LanguageCode.AUTO
            and resolved_source is target_language
        ):
            result = TranslationResult(
                request_id=request.id,
                translated_text=source_text,
                detected_source_language=resolved_source,
                confidence=1.0,
                engine="short-circuit",
                completed_at=datetime.now(UTC),
            )
        else:
            result = await self._provider.translate(request)

        if self._history_enabled:
            try:
                self._history_repo.append(
                    TranslationHistoryEntry(request=request, result=result)
                )
            except Exception as err:  # noqa: BLE001 — never block translation on storage
                logger.warning("failed to record history: %s", err)

        return result
