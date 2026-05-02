"""T430-T432: Performance smoke tests — startup, translation latency, memory."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import time
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from jimao_translator.models.enums import LanguageCode, TranslationMode
from jimao_translator.storage.history import TranslationHistoryRepository
from jimao_translator.translation.engines.mock import MockTranslationProvider
from jimao_translator.translation.service import TranslationService

pytestmark = pytest.mark.performance


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app  # type: ignore[return-value]


class TestStartupPerformance:
    def test_main_window_construction_under_3s(self, qapp: QApplication, tmp_path: Path) -> None:
        """FR-performance: window construction budget is 3 seconds on CI."""
        from jimao_translator.ui.main_window import MainWindow

        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=TranslationHistoryRepository(path=tmp_path / "h.json"),
            history_enabled=False,
        )
        t0 = time.monotonic()
        MainWindow(translation_service=svc)
        elapsed = time.monotonic() - t0
        assert elapsed < 3.0, f"MainWindow construction took {elapsed:.2f}s (budget 3s)"


class TestTranslationLatency:
    async def test_mock_translation_under_500ms(self, tmp_path: Path) -> None:
        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=TranslationHistoryRepository(path=tmp_path / "h.json"),
            history_enabled=False,
        )
        t0 = time.monotonic()
        await svc.translate(
            source_text="你好",
            source_language=LanguageCode.ZH,
            target_language=LanguageCode.EN,
            mode=TranslationMode.TEXT,
        )
        elapsed_ms = (time.monotonic() - t0) * 1000
        assert elapsed_ms < 500, f"mock translation took {elapsed_ms:.1f}ms (budget 500ms)"

    async def test_batch_of_10_translations_amortized(self, tmp_path: Path) -> None:
        svc = TranslationService(
            provider=MockTranslationProvider(),
            history_repo=TranslationHistoryRepository(path=tmp_path / "h.json"),
            history_enabled=False,
        )
        sources = ["你好", "世界", "晚安", "早上好", "谢谢"] * 2
        t0 = time.monotonic()
        await asyncio.gather(
            *[
                svc.translate(
                    source_text=s,
                    source_language=LanguageCode.ZH,
                    target_language=LanguageCode.EN,
                    mode=TranslationMode.TEXT,
                )
                for s in sources
            ]
        )
        per_call_ms = ((time.monotonic() - t0) * 1000) / len(sources)
        assert per_call_ms < 500, f"amortized {per_call_ms:.1f}ms/call (budget 500ms)"


class TestMemoryUsage:
    def test_process_memory_under_500mb(self) -> None:
        """FR-performance: idle RSS should be comfortably below 500MB.

        Uses psutil if available; otherwise falls back to resource.getrusage on POSIX
        or simply skips on Windows without psutil.
        """
        rss_bytes: int | None = None
        if importlib.util.find_spec("psutil") is not None:
            import psutil  # type: ignore[import-not-found]

            rss_bytes = psutil.Process().memory_info().rss
        elif sys.platform != "win32":
            import resource as _resource

            # ru_maxrss is KB on Linux, bytes on macOS
            factor = 1 if sys.platform == "darwin" else 1024
            rss_bytes = _resource.getrusage(_resource.RUSAGE_SELF).ru_maxrss * factor

        if rss_bytes is None:
            pytest.skip("no memory probe available (psutil missing on Windows)")

        rss_mb = rss_bytes / (1024 * 1024)
        assert rss_mb < 500, f"process RSS is {rss_mb:.0f}MB (budget 500MB)"
