"""T021: Unit tests for TranslationRequest, TranslationResult, TranslationHistoryEntry."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.translation import (
    TranslationHistoryEntry,
    TranslationRequest,
    TranslationResult,
)


def _now() -> datetime:
    return datetime.now(UTC)


class TestTranslationRequest:
    def test_valid_request_defaults(self) -> None:
        req = TranslationRequest(
            source_text="你好",
            source_language=LanguageCode.ZH,
            target_language=LanguageCode.EN,
            mode=TranslationMode.TEXT,
        )
        assert isinstance(req.id, UUID)
        assert isinstance(req.created_at, datetime)
        assert req.created_at.tzinfo is not None

    def test_empty_text_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TranslationRequest(
                source_text="",
                source_language=LanguageCode.ZH,
                target_language=LanguageCode.EN,
                mode=TranslationMode.TEXT,
            )

    def test_whitespace_only_text_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TranslationRequest(
                source_text="   \n\t  ",
                source_language=LanguageCode.ZH,
                target_language=LanguageCode.EN,
                mode=TranslationMode.TEXT,
            )

    def test_text_over_5000_chars_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TranslationRequest(
                source_text="a" * 5001,
                source_language=LanguageCode.ZH,
                target_language=LanguageCode.EN,
                mode=TranslationMode.TEXT,
            )

    def test_text_exactly_5000_chars_accepted(self) -> None:
        req = TranslationRequest(
            source_text="a" * 5000,
            source_language=LanguageCode.ZH,
            target_language=LanguageCode.EN,
            mode=TranslationMode.TEXT,
        )
        assert len(req.source_text) == 5000

    def test_target_language_cannot_be_auto(self) -> None:
        with pytest.raises(ValidationError):
            TranslationRequest(
                source_text="hello",
                source_language=LanguageCode.EN,
                target_language=LanguageCode.AUTO,
                mode=TranslationMode.TEXT,
            )

    def test_source_language_may_be_auto(self) -> None:
        req = TranslationRequest(
            source_text="hello",
            source_language=LanguageCode.AUTO,
            target_language=LanguageCode.EN,
            mode=TranslationMode.TEXT,
        )
        assert req.source_language is LanguageCode.AUTO


class TestTranslationResult:
    def test_valid_result(self) -> None:
        result = TranslationResult(
            request_id=uuid4(),
            translated_text="Hello",
            detected_source_language=LanguageCode.ZH,
            engine="claude-sonnet-4-6",
            completed_at=_now(),
        )
        assert result.confidence is None

    def test_confidence_in_range(self) -> None:
        result = TranslationResult(
            request_id=uuid4(),
            translated_text="Hello",
            detected_source_language=LanguageCode.ZH,
            confidence=0.87,
            engine="claude-sonnet-4-6",
            completed_at=_now(),
        )
        assert result.confidence == 0.87

    def test_confidence_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TranslationResult(
                request_id=uuid4(),
                translated_text="Hello",
                detected_source_language=LanguageCode.ZH,
                confidence=1.5,
                engine="x",
                completed_at=_now(),
            )

    def test_detected_source_language_cannot_be_auto(self) -> None:
        with pytest.raises(ValidationError):
            TranslationResult(
                request_id=uuid4(),
                translated_text="Hello",
                detected_source_language=LanguageCode.AUTO,
                engine="x",
                completed_at=_now(),
            )


class TestTranslationHistoryEntry:
    def test_pairs_request_and_result(self) -> None:
        req = TranslationRequest(
            source_text="你好",
            source_language=LanguageCode.ZH,
            target_language=LanguageCode.EN,
            mode=TranslationMode.TEXT,
        )
        result = TranslationResult(
            request_id=req.id,
            translated_text="Hello",
            detected_source_language=LanguageCode.ZH,
            engine="x",
            completed_at=_now(),
        )
        entry = TranslationHistoryEntry(request=req, result=result)
        assert entry.request.id == entry.result.request_id
