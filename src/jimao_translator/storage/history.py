"""T032: TranslationHistoryRepository — JSON file capped at 100, FIFO eviction."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from ..config import history_path
from ..models.translation import TranslationHistoryEntry

logger = logging.getLogger(__name__)

MAX_ENTRIES = 100

_entries_adapter: TypeAdapter[list[TranslationHistoryEntry]] = TypeAdapter(
    list[TranslationHistoryEntry]
)


class TranslationHistoryRepository:
    """Persisted, capped list of translation history entries."""

    def __init__(self, path: Path | None = None, max_entries: int = MAX_ENTRIES) -> None:
        self._path = path or history_path()
        self._max = max_entries

    def load(self) -> list[TranslationHistoryEntry]:
        if not self._path.exists():
            return []
        try:
            raw = self._path.read_text(encoding="utf-8")
            entries = _entries_adapter.validate_json(raw)
        except (json.JSONDecodeError, ValidationError, OSError) as err:
            logger.warning("history file unreadable, treating as empty: %s", err)
            return []
        return sorted(entries, key=lambda e: e.request.created_at, reverse=True)

    def append(self, entry: TranslationHistoryEntry) -> None:
        entries = self.load()
        entries.insert(0, entry)
        if len(entries) > self._max:
            entries = entries[: self._max]
        self._write(entries)

    def clear(self) -> None:
        self._write([])

    def _write(self, entries: list[TranslationHistoryEntry]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = _entries_adapter.dump_json(entries, indent=2).decode("utf-8")
        self._path.write_text(payload, encoding="utf-8")
