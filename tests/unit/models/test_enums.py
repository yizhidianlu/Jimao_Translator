"""T020: Unit tests for LanguageCode, TranslationMode, MessageRole enums."""

import pytest

from jimao_translator.models.enums import LanguageCode, MessageRole, TranslationMode


class TestLanguageCode:
    def test_members(self) -> None:
        assert LanguageCode.ZH.value == "zh"
        assert LanguageCode.EN.value == "en"
        assert LanguageCode.JA.value == "ja"
        assert LanguageCode.KO.value == "ko"
        assert LanguageCode.AUTO.value == "auto"

    def test_all_supported_codes_present(self) -> None:
        values = {m.value for m in LanguageCode}
        assert {"zh", "en", "ja", "ko", "auto"} <= values

    def test_from_string(self) -> None:
        assert LanguageCode("zh") is LanguageCode.ZH
        assert LanguageCode("en") is LanguageCode.EN

    def test_invalid_code_raises(self) -> None:
        with pytest.raises(ValueError):
            LanguageCode("fr")


class TestTranslationMode:
    def test_members(self) -> None:
        assert TranslationMode.TEXT.value == "text"
        assert TranslationMode.VOICE.value == "voice"
        assert TranslationMode.VOICE_CONVERSATION.value == "voice_conversation"


class TestMessageRole:
    def test_members(self) -> None:
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
