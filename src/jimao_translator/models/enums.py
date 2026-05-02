"""T010: Core enums shared across all subsystems."""

from __future__ import annotations

from enum import StrEnum


class LanguageCode(StrEnum):
    """Supported ISO 639-1 language codes plus `auto` for source detection."""

    ZH = "zh"
    EN = "en"
    JA = "ja"
    KO = "ko"
    AUTO = "auto"


class TranslationMode(StrEnum):
    """Which UI tab / flow produced a translation."""

    TEXT = "text"
    VOICE = "voice"
    VOICE_CONVERSATION = "voice_conversation"


class MessageRole(StrEnum):
    """Chat participant role."""

    USER = "user"
    ASSISTANT = "assistant"
