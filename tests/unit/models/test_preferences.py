"""T024: Unit tests for UserPreferences (defaults, voice_speed clamp)."""

import pytest
from pydantic import ValidationError

from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.preferences import UserPreferences


class TestUserPreferences:
    def test_defaults(self) -> None:
        prefs = UserPreferences()
        assert prefs.default_source_language is LanguageCode.AUTO
        assert prefs.default_target_language is LanguageCode.EN
        assert prefs.ui_theme == "system"
        assert prefs.voice_speed == 1.0
        assert prefs.hotkey is None
        assert prefs.history_enabled is True
        assert prefs.last_active_tab is TranslationMode.TEXT
        assert prefs.llm_api_key is None

    def test_voice_speed_clamp_low(self) -> None:
        prefs = UserPreferences(voice_speed=0.1)
        assert prefs.voice_speed == 0.5

    def test_voice_speed_clamp_high(self) -> None:
        prefs = UserPreferences(voice_speed=5.0)
        assert prefs.voice_speed == 2.0

    def test_voice_speed_in_range_unchanged(self) -> None:
        prefs = UserPreferences(voice_speed=1.25)
        assert prefs.voice_speed == 1.25

    def test_invalid_theme_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UserPreferences(ui_theme="fancy")  # type: ignore[arg-type]

    def test_target_language_cannot_be_auto(self) -> None:
        with pytest.raises(ValidationError):
            UserPreferences(default_target_language=LanguageCode.AUTO)
