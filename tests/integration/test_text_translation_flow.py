"""T101 + T102: Integration tests for the text-translation end-to-end flow."""

from __future__ import annotations

from pathlib import Path

import pytest

from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.translation import TranslationRequest
from jimao_translator.storage.history import TranslationHistoryRepository
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.service import TranslationService


@pytest.fixture()
def history_repo(tmp_path: Path) -> TranslationHistoryRepository:
    return TranslationHistoryRepository(path=tmp_path / "history.json")


@pytest.fixture()
def service(history_repo: TranslationHistoryRepository) -> TranslationService:
    return TranslationService(
        provider=MockTranslationProvider(),
        history_repo=history_repo,
        history_enabled=True,
    )


class TestTextTranslationFlow:
    async def test_zh_to_en_end_to_end(self, service: TranslationService) -> None:
        """T101: user enters Chinese, picks English, gets translation and copyable result."""
        result = await service.translate(
            source_text="你好",
            source_language=LanguageCode.ZH,
            target_language=LanguageCode.EN,
            mode=TranslationMode.TEXT,
        )
        assert result.translated_text == "Hello"
        assert result.detected_source_language is LanguageCode.ZH

    async def test_auto_detect_source(self, service: TranslationService) -> None:
        result = await service.translate(
            source_text="hello",
            source_language=LanguageCode.AUTO,
            target_language=LanguageCode.ZH,
            mode=TranslationMode.TEXT,
        )
        assert result.detected_source_language in {
            LanguageCode.EN,
            LanguageCode.ZH,
            LanguageCode.JA,
            LanguageCode.KO,
        }

    async def test_history_persisted_when_enabled(
        self, service: TranslationService, history_repo: TranslationHistoryRepository
    ) -> None:
        await service.translate(
            source_text="hello",
            source_language=LanguageCode.EN,
            target_language=LanguageCode.ZH,
            mode=TranslationMode.TEXT,
        )
        entries = history_repo.load()
        assert len(entries) == 1
        assert entries[0].request.source_text == "hello"

    async def test_history_skipped_when_disabled(
        self, history_repo: TranslationHistoryRepository
    ) -> None:
        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=history_repo,
            history_enabled=False,
        )
        await svc.translate(
            source_text="hello",
            source_language=LanguageCode.EN,
            target_language=LanguageCode.ZH,
            mode=TranslationMode.TEXT,
        )
        assert history_repo.load() == []


class TestSameLanguageShortCircuit:
    async def test_zh_to_zh_returns_original_without_engine(
        self, history_repo: TranslationHistoryRepository
    ) -> None:
        """T102: same-language translation returns original text without invoking provider."""

        class CountingProvider(MockTranslationProvider):
            def __init__(self) -> None:
                super().__init__()
                self.call_count = 0

            async def translate(self, request: TranslationRequest):  # type: ignore[override]
                self.call_count += 1
                return await super().translate(request)

        provider = CountingProvider()
        svc = TranslationService(
            provider=provider,
            history_repo=history_repo,
            history_enabled=False,
        )
        result = await svc.translate(
            source_text="你好",
            source_language=LanguageCode.ZH,
            target_language=LanguageCode.ZH,
            mode=TranslationMode.TEXT,
        )
        assert result.translated_text == "你好"
        assert provider.call_count == 0
