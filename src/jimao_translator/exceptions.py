"""T025: Custom exception hierarchy for all subsystems."""

from __future__ import annotations


class JimaoError(Exception):
    """Base class for all Jimao Translator domain errors."""


class TranslationError(JimaoError):
    """Translation backend failure."""


class UnsupportedLanguagePairError(TranslationError):
    """The requested source/target language combination is not supported."""


class RecognitionError(JimaoError):
    """Speech-to-text engine failure."""


class NoSpeechDetectedError(RecognitionError):
    """Input audio contained silence or pure noise."""


class TtsError(JimaoError):
    """Text-to-speech engine failure."""


class UnsupportedLanguageError(JimaoError):
    """Engine does not support the requested language."""


class LlmUnavailableError(JimaoError):
    """LLM provider is unreachable, timing out, or over quota."""


class AuthenticationError(JimaoError):
    """API key missing or invalid."""


class ContentPolicyViolationError(JimaoError):
    """Content filtered by provider safety policy (FR-015)."""
