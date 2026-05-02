"""T011 + T015: Translation request/result models and history entry."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from .enums import LanguageCode, TranslationMode


def _utcnow() -> datetime:
    return datetime.now(UTC)


class TranslationRequest(BaseModel):
    """Input for a single translation operation."""

    id: UUID = Field(default_factory=uuid4)
    source_text: str = Field(min_length=1, max_length=5000)
    source_language: LanguageCode
    target_language: LanguageCode
    mode: TranslationMode
    created_at: datetime = Field(default_factory=_utcnow)

    @field_validator("source_text")
    @classmethod
    def _reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_text must not be blank")
        return value

    @field_validator("target_language")
    @classmethod
    def _target_not_auto(cls, value: LanguageCode) -> LanguageCode:
        if value is LanguageCode.AUTO:
            raise ValueError("target_language cannot be 'auto'")
        return value


class TranslationResult(BaseModel):
    """Output of a translation operation."""

    request_id: UUID
    translated_text: str
    detected_source_language: LanguageCode
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    engine: str
    completed_at: datetime

    @field_validator("detected_source_language")
    @classmethod
    def _detected_not_auto(cls, value: LanguageCode) -> LanguageCode:
        if value is LanguageCode.AUTO:
            raise ValueError("detected_source_language must be a concrete language")
        return value


class TranslationHistoryEntry(BaseModel):
    """A paired request/result persisted to history."""

    request: TranslationRequest
    result: TranslationResult
