"""T014: UserPreferences persisted singleton."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .enums import LanguageCode, TranslationMode

Theme = Literal["light", "dark", "system"]


class UserPreferences(BaseModel):
    """Cross-session user settings (stored in preferences.json)."""

    default_source_language: LanguageCode = LanguageCode.AUTO
    default_target_language: LanguageCode = LanguageCode.EN
    ui_theme: Theme = "system"
    voice_speed: float = Field(default=1.0)
    hotkey: str | None = None
    history_enabled: bool = True
    last_active_tab: TranslationMode = TranslationMode.TEXT
    llm_api_key: str | None = None

    @field_validator("voice_speed")
    @classmethod
    def _clamp_voice_speed(cls, value: float) -> float:
        return max(0.5, min(2.0, value))

    @field_validator("default_target_language")
    @classmethod
    def _target_not_auto(cls, value: LanguageCode) -> LanguageCode:
        if value is LanguageCode.AUTO:
            raise ValueError("default_target_language cannot be 'auto'")
        return value
