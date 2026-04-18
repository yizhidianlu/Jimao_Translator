"""T026: Unit tests for custom exceptions."""

import pytest

from jimao_translator.exceptions import (
    AuthenticationError,
    ContentPolicyViolationError,
    JimaoError,
    LlmUnavailableError,
    NoSpeechDetectedError,
    RecognitionError,
    TranslationError,
    TtsError,
    UnsupportedLanguageError,
    UnsupportedLanguagePairError,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_jimao_error(self) -> None:
        for cls in (
            TranslationError,
            UnsupportedLanguagePairError,
            RecognitionError,
            NoSpeechDetectedError,
            TtsError,
            UnsupportedLanguageError,
            LlmUnavailableError,
            AuthenticationError,
            ContentPolicyViolationError,
        ):
            assert issubclass(cls, JimaoError)

    def test_subtype_relationships(self) -> None:
        assert issubclass(UnsupportedLanguagePairError, TranslationError)
        assert issubclass(NoSpeechDetectedError, RecognitionError)

    def test_raise_and_catch_as_jimao_error(self) -> None:
        with pytest.raises(JimaoError):
            raise LlmUnavailableError("API down")

    def test_message_preserved(self) -> None:
        try:
            raise AuthenticationError("bad key")
        except AuthenticationError as err:
            assert "bad key" in str(err)
