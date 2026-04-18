"""T033: Unit tests for PreferencesRepository."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.preferences import UserPreferences
from jimao_translator.storage.preferences import PreferencesRepository


@pytest.fixture()
def prefs_file(tmp_path: Path) -> Path:
    return tmp_path / "preferences.json"


@pytest.fixture()
def keyring_stub() -> MagicMock:
    stub = MagicMock()
    stub.store = {}
    stub.get_password.side_effect = lambda svc, user: stub.store.get((svc, user))
    stub.set_password.side_effect = lambda svc, user, pw: stub.store.__setitem__((svc, user), pw)
    stub.delete_password.side_effect = lambda svc, user: stub.store.pop((svc, user), None)
    return stub


class TestPreferencesRepository:
    def test_load_missing_file_returns_defaults(
        self, prefs_file: Path, keyring_stub: MagicMock
    ) -> None:
        repo = PreferencesRepository(path=prefs_file, keyring_backend=keyring_stub)
        prefs = repo.load()
        assert prefs == UserPreferences()
        assert prefs.default_source_language is LanguageCode.AUTO

    def test_save_and_reload_round_trip(self, prefs_file: Path, keyring_stub: MagicMock) -> None:
        repo = PreferencesRepository(path=prefs_file, keyring_backend=keyring_stub)
        prefs = UserPreferences(
            default_target_language=LanguageCode.JA,
            ui_theme="dark",
            voice_speed=1.4,
            last_active_tab=TranslationMode.VOICE,
        )
        repo.save(prefs)
        reloaded = repo.load()
        assert reloaded.default_target_language is LanguageCode.JA
        assert reloaded.ui_theme == "dark"
        assert reloaded.voice_speed == 1.4
        assert reloaded.last_active_tab is TranslationMode.VOICE

    def test_api_key_goes_to_keyring_not_json(
        self, prefs_file: Path, keyring_stub: MagicMock
    ) -> None:
        repo = PreferencesRepository(path=prefs_file, keyring_backend=keyring_stub)
        prefs = UserPreferences(llm_api_key="sk-ant-secret")
        repo.save(prefs)

        raw = prefs_file.read_text(encoding="utf-8")
        assert "sk-ant-secret" not in raw

        keyring_stub.set_password.assert_called_once()
        svc, user, pw = keyring_stub.set_password.call_args.args
        assert pw == "sk-ant-secret"

        reloaded = repo.load()
        assert reloaded.llm_api_key == "sk-ant-secret"

    def test_clearing_api_key_removes_from_keyring(
        self, prefs_file: Path, keyring_stub: MagicMock
    ) -> None:
        repo = PreferencesRepository(path=prefs_file, keyring_backend=keyring_stub)
        repo.save(UserPreferences(llm_api_key="sk-ant-secret"))
        repo.save(UserPreferences(llm_api_key=None))
        assert keyring_stub.delete_password.called
        assert repo.load().llm_api_key is None

    def test_corrupt_file_falls_back_to_defaults(
        self, prefs_file: Path, keyring_stub: MagicMock
    ) -> None:
        prefs_file.write_text("{not valid json", encoding="utf-8")
        repo = PreferencesRepository(path=prefs_file, keyring_backend=keyring_stub)
        assert repo.load() == UserPreferences()
