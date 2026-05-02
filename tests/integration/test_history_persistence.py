"""T402: history persists across restarts, caps at 100, respects opt-out."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.translation import (
    TranslationHistoryEntry,
    TranslationRequest,
    TranslationResult,
)
from jimao_translator.storage.history import MAX_ENTRIES, TranslationHistoryRepository
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.service import TranslationService


def _entry(i: int) -> TranslationHistoryEntry:
    req = TranslationRequest(
        source_text=f"source-{i}",
        source_language=LanguageCode.ZH,
        target_language=LanguageCode.EN,
        mode=TranslationMode.TEXT,
    )
    result = TranslationResult(
        request_id=req.id,
        translated_text=f"translated-{i}",
        detected_source_language=LanguageCode.ZH,
        confidence=0.9,
        engine="mock",
        completed_at=datetime.now(UTC),
    )
    return TranslationHistoryEntry(request=req, result=result)


class TestHistoryPersistence:
    def test_persists_across_restarts(self, tmp_path: Path) -> None:
        path = tmp_path / "h.json"

        repo1 = TranslationHistoryRepository(path=path)
        repo1.append(_entry(1))
        repo1.append(_entry(2))

        # Simulate restart: new instance, same file
        repo2 = TranslationHistoryRepository(path=path)
        entries = repo2.load()
        assert len(entries) == 2
        # Sorted newest-first
        assert entries[0].request.source_text == "source-2"

    def test_caps_at_100(self, tmp_path: Path) -> None:
        repo = TranslationHistoryRepository(path=tmp_path / "h.json")
        for i in range(150):
            repo.append(_entry(i))
        entries = repo.load()
        assert len(entries) == MAX_ENTRIES

    def test_clear_empties(self, tmp_path: Path) -> None:
        repo = TranslationHistoryRepository(path=tmp_path / "h.json")
        repo.append(_entry(1))
        repo.clear()
        assert repo.load() == []


class TestOptOut:
    async def test_service_with_history_disabled_writes_nothing(self, tmp_path: Path) -> None:
        path = tmp_path / "h.json"
        repo = TranslationHistoryRepository(path=path)
        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=repo,
            history_enabled=False,
        )

        await svc.translate(
            source_text="你好",
            source_language=LanguageCode.ZH,
            target_language=LanguageCode.EN,
            mode=TranslationMode.TEXT,
        )

        assert repo.load() == []
        assert not path.exists()

    async def test_toggling_history_on_off_respected(self, tmp_path: Path) -> None:
        path = tmp_path / "h.json"
        repo = TranslationHistoryRepository(path=path)
        svc = TranslationService(
            provider=MockTranslationProvider(), history_repo=repo, history_enabled=True
        )

        await svc.translate(
            source_text="你好",
            source_language=LanguageCode.ZH,
            target_language=LanguageCode.EN,
            mode=TranslationMode.TEXT,
        )
        assert len(repo.load()) == 1

        svc.set_history_enabled(False)
        await svc.translate(
            source_text="hello",
            source_language=LanguageCode.EN,
            target_language=LanguageCode.ZH,
            mode=TranslationMode.TEXT,
        )
        assert len(repo.load()) == 1  # second call did not persist
