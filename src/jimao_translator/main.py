"""T117: Application entry point. Bootstraps qasync + Qt + services."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import qasync
from PySide6.QtWidgets import QApplication, QMessageBox

from .llm.providers.qwen_client import QwenLlmClient
from .llm.service import DEFAULT_SYSTEM_PROMPT, ChatService
from .speech.engines.system_stt import SystemSpeechRecognizer
from .speech.orchestrator import VoiceTranslationOrchestrator
from .storage.history import TranslationHistoryRepository
from .storage.preferences import PreferencesRepository
from .translation.engines.llm_translator import LlmTranslator
from .translation.service import TranslationService
from .tts.engines.edge_tts_engine import EdgeTtsEngine
from .ui.main_window import MainWindow


def _setup_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("JIMAO_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _get_api_key(prefs_repo: PreferencesRepository) -> str | None:
    env_key = os.environ.get("DASHSCOPE_API_KEY")
    if env_key:
        return env_key
    return prefs_repo.load().llm_api_key


def main() -> int:
    _setup_logging()
    app = QApplication.instance() or QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    prefs_repo = PreferencesRepository()
    history_repo = TranslationHistoryRepository()
    prefs = prefs_repo.load()

    api_key = _get_api_key(prefs_repo)
    if not api_key:
        QMessageBox.warning(
            None,
            "Jimao Translator",
            "尚未配置通义千问 API 密钥。请设置环境变量 `DASHSCOPE_API_KEY` 或在偏好设置中填入。",
        )
        return 2

    translator_llm = QwenLlmClient(api_key=api_key)
    chat_llm = QwenLlmClient(api_key=api_key, system_prompt=DEFAULT_SYSTEM_PROMPT)
    translator = LlmTranslator(translator_llm)
    service = TranslationService(
        provider=translator,
        history_repo=history_repo,
        history_enabled=prefs.history_enabled,
    )
    chat_service = ChatService(llm_client=chat_llm)

    try:
        stt = SystemSpeechRecognizer()
        tts = EdgeTtsEngine()
        voice = VoiceTranslationOrchestrator(
            recognizer=stt, translation_service=service, tts_engine=tts
        )
    except Exception as err:  # noqa: BLE001 — voice deps optional on first boot
        logging.getLogger(__name__).warning("voice engines unavailable: %s", err)
        voice = None

    window = MainWindow(
        translation_service=service,
        voice_orchestrator=voice,
        chat_service=chat_service,
        history_repo=history_repo if prefs.history_enabled else None,
        prefs_repo=prefs_repo,
    )
    window.select_tab(prefs.last_active_tab)
    window.show()

    with loop:
        return loop.run_forever()


if __name__ == "__main__":
    raise SystemExit(main())
