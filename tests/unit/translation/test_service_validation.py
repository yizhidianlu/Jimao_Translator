"""T103: Unit test — TranslationService rejects empty input before calling provider."""

from __future__ import annotations

from pathlib import Path

import pytest

from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.storage.history import TranslationHistoryRepository
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.service import TranslationService


@pytest.fixture()
def service(tmp_path: Path) -> TranslationService:
    return TranslationService(
        provider=MockTranslationProvider(),
        history_repo=TranslationHistoryRepository(path=tmp_path / "h.json"),
        history_enabled=False,
    )


class TestEmptyTextValidation:
    async def test_empty_text_raises_value_error(self, service: TranslationService) -> None:
        with pytest.raises(ValueError):
            await service.translate(
                source_text="",
                source_language=LanguageCode.ZH,
                target_language=LanguageCode.EN,
                mode=TranslationMode.TEXT,
            )

    async def test_whitespace_only_raises(self, service: TranslationService) -> None:
        with pytest.raises(ValueError):
            await service.translate(
                source_text="   \n\t",
                source_language=LanguageCode.ZH,
                target_language=LanguageCode.EN,
                mode=TranslationMode.TEXT,
            )

    async def test_oversize_text_is_truncated(self, service: TranslationService) -> None:
        # Per T422: oversized input is truncated to MAX_SOURCE_TEXT, not rejected.
        result = await service.translate(
            source_text="x" * 5500,
            source_language=LanguageCode.EN,
            target_language=LanguageCode.ZH,
            mode=TranslationMode.TEXT,
        )
        assert result.translated_text
