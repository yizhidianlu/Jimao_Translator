"""T214: Voice translation orchestrators.

`VoiceTranslationOrchestrator` runs a single push-to-talk cycle:
    audio bytes → recognize → translate → synthesize TTS chunks.

`ConversationOrchestrator` wraps the above for bi-directional conversation mode
where each side has a fixed language; the speaker is identified by which side's
button was pressed, and we route translation to the *other* side's language.

Neither class touches disk — audio bytes flow in-memory only (FR-016).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..models.enums import LanguageCode, TranslationMode
from ..models.translation import TranslationResult
from ..models.voice import VoiceSession

if TYPE_CHECKING:
    from ..translation.service import TranslationService
    from .recognizer import SpeechRecognizer
    from ..tts.engine import TtsEngine

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.6


@dataclass
class VoiceOutcome:
    """Result of one voice-translation cycle."""

    session: VoiceSession
    result: TranslationResult
    audio_chunks: list[bytes] = field(default_factory=list)
    target_language: LanguageCode | None = None

    @property
    def low_confidence(self) -> bool:
        return self.session.recognition_confidence < LOW_CONFIDENCE_THRESHOLD


class VoiceTranslationOrchestrator:
    """Run one STT → translate → TTS cycle for a single speaker."""

    def __init__(
        self,
        recognizer: "SpeechRecognizer",
        translation_service: "TranslationService",
        tts_engine: "TtsEngine",
    ) -> None:
        self._recognizer = recognizer
        self._translation_service = translation_service
        self._tts_engine = tts_engine

    async def run_once(
        self,
        audio_bytes: bytes,
        target_language: LanguageCode,
        source_language: LanguageCode | None = None,
        mode: TranslationMode = TranslationMode.TEXT,
    ) -> VoiceOutcome:
        """Recognize speech → translate → synthesize TTS chunks."""
        stt_hint = source_language.value if source_language else None
        session = await self._recognizer.recognize(audio_bytes, language=stt_hint)

        resolved_source = source_language or session.source_language

        result = await self._translation_service.translate(
            source_text=session.recognized_text,
            source_language=resolved_source,
            target_language=target_language,
            mode=mode,
        )

        audio_chunks: list[bytes] = []
        if result.translated_text:
            try:
                async for chunk in self._tts_engine.synthesize(
                    text=result.translated_text,
                    language=target_language.value,
                ):
                    audio_chunks.append(chunk)
            except Exception as err:  # noqa: BLE001 — TTS failure is non-fatal
                logger.warning("TTS synthesis failed: %s", err)

        return VoiceOutcome(
            session=session,
            result=result,
            audio_chunks=audio_chunks,
            target_language=target_language,
        )


class ConversationOrchestrator:
    """Bi-directional conversation mode.

    Each side is assigned a fixed language. Whoever speaks gets their audio
    translated into the *other* side's language and played back there.
    """

    def __init__(
        self,
        voice: VoiceTranslationOrchestrator,
        local_language: LanguageCode,
        counterpart_language: LanguageCode,
    ) -> None:
        if local_language is LanguageCode.AUTO or counterpart_language is LanguageCode.AUTO:
            raise ValueError("conversation-mode languages must be concrete, not 'auto'")
        if local_language is counterpart_language:
            raise ValueError("local and counterpart languages must differ")
        self._voice = voice
        self._local_language = local_language
        self._counterpart_language = counterpart_language

    @property
    def local_language(self) -> LanguageCode:
        return self._local_language

    @property
    def counterpart_language(self) -> LanguageCode:
        return self._counterpart_language

    async def local_speaks(self, audio_bytes: bytes) -> VoiceOutcome:
        """Local side spoke — translate into the counterpart's language."""
        return await self._voice.run_once(
            audio_bytes=audio_bytes,
            source_language=self._local_language,
            target_language=self._counterpart_language,
        )

    async def counterpart_speaks(self, audio_bytes: bytes) -> VoiceOutcome:
        """Counterpart spoke — translate into the local language."""
        return await self._voice.run_once(
            audio_bytes=audio_bytes,
            source_language=self._counterpart_language,
            target_language=self._local_language,
        )
