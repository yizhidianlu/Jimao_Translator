"""T022: Unit tests for VoiceSession."""

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from jimao_translator.models.enums import LanguageCode
from jimao_translator.models.voice import VoiceSession


class TestVoiceSession:
    def test_valid_session_defaults(self) -> None:
        session = VoiceSession(
            recognized_text="请问附近有餐厅吗",
            recognition_confidence=0.92,
            source_language=LanguageCode.ZH,
        )
        assert isinstance(session.id, UUID)
        assert session.tts_played is False
        assert session.translation_request_id is None
        assert isinstance(session.started_at, datetime)
        assert session.started_at.tzinfo is not None

    def test_confidence_clamped_to_range(self) -> None:
        with pytest.raises(ValidationError):
            VoiceSession(
                recognized_text="x",
                recognition_confidence=1.1,
                source_language=LanguageCode.ZH,
            )
        with pytest.raises(ValidationError):
            VoiceSession(
                recognized_text="x",
                recognition_confidence=-0.1,
                source_language=LanguageCode.ZH,
            )

    def test_low_confidence_still_accepted(self) -> None:
        """UI flags low confidence, but the model does not reject it."""
        session = VoiceSession(
            recognized_text="unclear",
            recognition_confidence=0.3,
            source_language=LanguageCode.EN,
        )
        assert session.recognition_confidence == 0.3
