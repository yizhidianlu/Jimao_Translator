"""T413: PreferencesDialog save/load cycle + last-active-tab persistence."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.preferences import UserPreferences
from jimao_translator.storage.preferences import PreferencesRepository
from jimao_translator.ui.preferences_dialog import (
    PreferencesDialog,
    update_last_active_tab,
)

pytestmark = pytest.mark.gui


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app  # type: ignore[return-value]


class FakeKeyring:
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self._store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self._store.pop((service, username), None)


@pytest.fixture()
def repo(tmp_path: Path) -> PreferencesRepository:
    keyring = FakeKeyring()
    return PreferencesRepository(path=tmp_path / "prefs.json", keyring_backend=keyring)


class TestPreferencesDialogCycle:
    def test_open_and_accept_saves_values(
        self, qapp: QApplication, repo: PreferencesRepository
    ) -> None:
        dlg = PreferencesDialog(repo)
        dlg._target_lang.set_language(LanguageCode.JA)  # noqa: SLF001
        dlg._voice_speed.setValue(1.5)  # noqa: SLF001
        dlg._api_key.setText("sk-test-abc")  # noqa: SLF001
        dlg._history_enabled.setChecked(False)  # noqa: SLF001
        dlg._on_accept()  # noqa: SLF001

        saved = dlg.saved_preferences
        assert saved is not None
        assert saved.default_target_language is LanguageCode.JA
        assert saved.voice_speed == 1.5
        assert saved.history_enabled is False
        assert saved.llm_api_key == "sk-test-abc"

        reloaded = repo.load()
        assert reloaded.default_target_language is LanguageCode.JA
        assert reloaded.voice_speed == 1.5
        assert reloaded.history_enabled is False
        assert reloaded.llm_api_key == "sk-test-abc"

    def test_reload_roundtrip_preserves_fields(
        self, qapp: QApplication, repo: PreferencesRepository
    ) -> None:
        repo.save(
            UserPreferences(
                default_source_language=LanguageCode.ZH,
                default_target_language=LanguageCode.KO,
                voice_speed=0.8,
                history_enabled=True,
                llm_api_key="sk-initial",
            )
        )
        dlg = PreferencesDialog(repo)
        assert dlg._voice_speed.value() == pytest.approx(0.8)  # noqa: SLF001
        assert dlg._target_lang.current_language() is LanguageCode.KO  # noqa: SLF001
        assert dlg._api_key.text() == "sk-initial"  # noqa: SLF001

    def test_voice_speed_clamped_even_if_set_out_of_range(
        self, qapp: QApplication, repo: PreferencesRepository
    ) -> None:
        dlg = PreferencesDialog(repo)
        # QDoubleSpinBox itself enforces min/max; verify clamping still holds
        dlg._voice_speed.setValue(3.0)  # noqa: SLF001
        assert dlg._voice_speed.value() == pytest.approx(2.0)  # noqa: SLF001


class TestLastActiveTabPersistence:
    def test_update_last_active_tab(self, repo: PreferencesRepository) -> None:
        update_last_active_tab(repo, TranslationMode.VOICE)
        assert repo.load().last_active_tab is TranslationMode.VOICE

        update_last_active_tab(repo, TranslationMode.TEXT)
        assert repo.load().last_active_tab is TranslationMode.TEXT

    def test_no_write_when_tab_unchanged(self, repo: PreferencesRepository, tmp_path: Path) -> None:
        update_last_active_tab(repo, TranslationMode.VOICE)
        mtime1 = (tmp_path / "prefs.json").stat().st_mtime
        # Call again with same tab — should be a no-op (no rewrite)
        update_last_active_tab(repo, TranslationMode.VOICE)
        mtime2 = (tmp_path / "prefs.json").stat().st_mtime
        assert mtime1 == mtime2
