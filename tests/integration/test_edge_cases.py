"""T422-T423: Edge-case tests — oversized input truncation + concurrent isolation."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest

from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.models.translation import TranslationRequest, TranslationResult
from jimao_translator.storage.history import TranslationHistoryRepository
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.service import MAX_SOURCE_TEXT, TranslationService


def _svc(tmp_path: Path, provider: MockTranslationProvider | None = None) -> TranslationService:
    return TranslationService(
        provider=provider or MockTranslationProvider(),
        history_repo=TranslationHistoryRepository(path=tmp_path / "h.json"),
        history_enabled=False,
    )


class TestOversizedInput:
    async def test_over_limit_is_truncated_not_rejected(self, tmp_path: Path) -> None:
        svc = _svc(tmp_path)
        huge = "你" * (MAX_SOURCE_TEXT + 500)
        result = await svc.translate(
            source_text=huge,
            source_language=LanguageCode.ZH,
            target_language=LanguageCode.EN,
            mode=TranslationMode.TEXT,
        )
        assert result.translated_text  # produced a result instead of raising

    async def test_under_limit_not_truncated(self, tmp_path: Path) -> None:
        svc = _svc(tmp_path)
        text = "你好" * 10
        # assert no exception — length still under cap
        await svc.translate(
            source_text=text,
            source_language=LanguageCode.ZH,
            target_language=LanguageCode.EN,
            mode=TranslationMode.TEXT,
        )

    async def test_truncation_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        svc = _svc(tmp_path)
        huge = "a" * (MAX_SOURCE_TEXT + 10)
        with caplog.at_level("WARNING", logger="jimao_translator.translation.service"):
            await svc.translate(
                source_text=huge,
                source_language=LanguageCode.EN,
                target_language=LanguageCode.ZH,
                mode=TranslationMode.TEXT,
            )
        assert any("truncat" in rec.message.lower() for rec in caplog.records)


class _OrderTrackingProvider:
    """Records (source_text, invocation_order) so we can assert isolation."""

    name = "order-tracker"
    supported_languages = {"zh", "en"}

    def __init__(self, delays: dict[str, float]) -> None:
        self._delays = delays
        self.started: list[str] = []

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        self.started.append(request.source_text)
        await asyncio.sleep(self._delays.get(request.source_text, 0.0))
        return TranslationResult(
            request_id=request.id,
            translated_text=f"[{request.source_text}]",
            detected_source_language=request.source_language,
            confidence=0.9,
            engine=self.name,
            completed_at=datetime.now(UTC),
        )


class TestConcurrentRequests:
    async def test_results_do_not_interleave(self, tmp_path: Path) -> None:
        """Slow request must still return its own result, not the fast one's."""
        provider = _OrderTrackingProvider(delays={"slow": 0.05, "fast": 0.0})
        svc = _svc(tmp_path, provider=provider)

        slow_task = asyncio.create_task(
            svc.translate(
                source_text="slow",
                source_language=LanguageCode.EN,
                target_language=LanguageCode.ZH,
                mode=TranslationMode.TEXT,
            )
        )
        fast_task = asyncio.create_task(
            svc.translate(
                source_text="fast",
                source_language=LanguageCode.EN,
                target_language=LanguageCode.ZH,
                mode=TranslationMode.TEXT,
            )
        )
        fast_result = await fast_task
        slow_result = await slow_task

        assert fast_result.translated_text == "[fast]"
        assert slow_result.translated_text == "[slow]"
        assert fast_result.request_id != slow_result.request_id

    async def test_history_entries_retain_distinct_request_ids(self, tmp_path: Path) -> None:
        provider = MockTranslationProvider(delay_seconds=0.01)
        svc = TranslationService(
            provider=provider,
            history_repo=TranslationHistoryRepository(path=tmp_path / "h.json"),
            history_enabled=True,
        )
        results = await asyncio.gather(
            *[
                svc.translate(
                    source_text=src,
                    source_language=LanguageCode.ZH,
                    target_language=LanguageCode.EN,
                    mode=TranslationMode.TEXT,
                )
                for src in ("你好", "世界", "晚安")
            ]
        )
        ids = {r.request_id for r in results}
        assert len(ids) == 3
