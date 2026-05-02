"""T034: Unit tests for TranslationHistoryRepository."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.translation import (
    TranslationHistoryEntry,
    TranslationRequest,
    TranslationResult,
)
from jimao_translator.storage.history import TranslationHistoryRepository


@pytest.fixture()
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def _make_entry(
    offset_seconds: int, target: LanguageCode = LanguageCode.EN
) -> TranslationHistoryEntry:
    created = datetime.now(UTC) + timedelta(seconds=offset_seconds)
    req = TranslationRequest(
        source_text=f"text-{offset_seconds}",
        source_language=LanguageCode.ZH,
        target_language=target,
        mode=TranslationMode.TEXT,
        created_at=created,
    )
    result = TranslationResult(
        request_id=req.id,
        translated_text=f"translated-{offset_seconds}",
        detected_source_language=LanguageCode.ZH,
        engine="mock",
        completed_at=created,
    )
    return TranslationHistoryEntry(request=req, result=result)


class TestTranslationHistoryRepository:
    def test_empty_when_file_missing(self, history_file: Path) -> None:
        repo = TranslationHistoryRepository(path=history_file)
        assert repo.load() == []

    def test_append_persists_entry(self, history_file: Path) -> None:
        repo = TranslationHistoryRepository(path=history_file)
        entry = _make_entry(0)
        repo.append(entry)
        assert len(repo.load()) == 1
        assert repo.load()[0].request.source_text == "text-0"

    def test_cap_at_100_fifo(self, history_file: Path) -> None:
        repo = TranslationHistoryRepository(path=history_file)
        for i in range(105):
            repo.append(_make_entry(i))
        entries = repo.load()
        assert len(entries) == 100
        # Newest first → last-inserted entry (offset 104) on top
        assert entries[0].request.source_text == "text-104"
        # Oldest retained: offset 5 (0..4 evicted)
        assert entries[-1].request.source_text == "text-5"

    def test_clear_removes_all(self, history_file: Path) -> None:
        repo = TranslationHistoryRepository(path=history_file)
        repo.append(_make_entry(0))
        repo.clear()
        assert repo.load() == []

    def test_corrupt_file_recovers_as_empty(self, history_file: Path) -> None:
        history_file.write_text("corrupt!", encoding="utf-8")
        repo = TranslationHistoryRepository(path=history_file)
        assert repo.load() == []

    def test_sorted_descending_by_created_at(self, history_file: Path) -> None:
        repo = TranslationHistoryRepository(path=history_file)
        repo.append(_make_entry(10))
        repo.append(_make_entry(5))
        repo.append(_make_entry(20))
        entries = repo.load()
        timestamps = [e.request.created_at for e in entries]
        assert timestamps == sorted(timestamps, reverse=True)
