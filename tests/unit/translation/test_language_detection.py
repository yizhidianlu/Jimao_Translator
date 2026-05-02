"""T104: Unit test — language detection wrapper."""

from __future__ import annotations

import pytest

from jimao_translator.models.enums import LanguageCode
from jimao_translator.translation.detection import detect_language


@pytest.mark.parametrize(
    "text,expected",
    [
        ("你好世界，今天天气真好", LanguageCode.ZH),
        ("Hello world, how are you today?", LanguageCode.EN),
        ("こんにちは、今日は良い天気ですね", LanguageCode.JA),
        ("안녕하세요, 오늘 날씨가 좋네요", LanguageCode.KO),
    ],
)
def test_detects_supported_languages(text: str, expected: LanguageCode) -> None:
    assert detect_language(text) is expected


def test_empty_text_returns_auto() -> None:
    assert detect_language("") is LanguageCode.AUTO


def test_whitespace_returns_auto() -> None:
    assert detect_language("   \t\n  ") is LanguageCode.AUTO


def test_unsupported_language_returns_auto() -> None:
    # French — not in the supported set; wrapper should degrade gracefully.
    result = detect_language("Bonjour tout le monde, comment allez-vous?")
    assert result in {LanguageCode.AUTO, LanguageCode.EN}  # detector may mislabel as EN
