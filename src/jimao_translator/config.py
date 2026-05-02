"""T030: Platform-aware configuration paths."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "JimaoTranslator"
APP_AUTHOR = "Jimao"
KEYRING_SERVICE = "jimao-translator"
KEYRING_USERNAME_LLM = "dashscope-api-key"


def user_data_path() -> Path:
    """Return the per-user writable data directory, creating it if needed."""
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def preferences_path() -> Path:
    return user_data_path() / "preferences.json"


def history_path() -> Path:
    return user_data_path() / "history.json"


def log_dir() -> Path:
    path = user_data_path() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path
