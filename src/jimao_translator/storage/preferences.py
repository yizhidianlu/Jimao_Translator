"""T031: PreferencesRepository — JSON file + OS keyring for API key."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Protocol

from pydantic import ValidationError

from ..config import KEYRING_SERVICE, KEYRING_USERNAME_LLM, preferences_path
from ..models.preferences import UserPreferences

logger = logging.getLogger(__name__)

_API_KEY_FIELD = "llm_api_key"


class _KeyringBackend(Protocol):
    def get_password(self, service: str, username: str) -> str | None: ...
    def set_password(self, service: str, username: str, password: str) -> None: ...
    def delete_password(self, service: str, username: str) -> None: ...


class PreferencesRepository:
    """Load / save UserPreferences with secrets offloaded to the OS keyring."""

    def __init__(
        self,
        path: Path | None = None,
        keyring_backend: _KeyringBackend | None = None,
    ) -> None:
        self._path = path or preferences_path()
        if keyring_backend is None:
            import keyring as _kr

            self._keyring: _KeyringBackend = _kr
        else:
            self._keyring = keyring_backend

    def load(self) -> UserPreferences:
        data: dict[str, Any] = {}
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    data = {}
            except (json.JSONDecodeError, OSError) as err:
                logger.warning("preferences file unreadable, using defaults: %s", err)
                data = {}

        data.pop(_API_KEY_FIELD, None)
        try:
            prefs = UserPreferences(**data)
        except ValidationError as err:
            logger.warning("preferences invalid, using defaults: %s", err)
            prefs = UserPreferences()

        api_key = self._keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME_LLM)
        if api_key:
            prefs = prefs.model_copy(update={_API_KEY_FIELD: api_key})
        return prefs

    def save(self, prefs: UserPreferences) -> None:
        payload = prefs.model_dump(mode="json", exclude={_API_KEY_FIELD})
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if prefs.llm_api_key:
            self._keyring.set_password(
                KEYRING_SERVICE, KEYRING_USERNAME_LLM, prefs.llm_api_key
            )
        else:
            try:
                self._keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME_LLM)
            except Exception:  # noqa: BLE001 — keyring backends vary widely
                pass
