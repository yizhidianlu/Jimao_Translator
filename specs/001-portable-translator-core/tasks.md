---
description: "Task list for portable-translator-core feature implementation"
---

# Tasks: Portable Translator Core

**Input**: Design documents from `/specs/001-portable-translator-core/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: **REQUIRED** — 宪法原则 II (Test-First, NON-NEGOTIABLE) 强制 TDD。
所有实现任务前 MUST 先编写测试（测试任务编号靠前），测试先失败再实现。

**Organization**: Tasks are grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 = Text Translation (P1), US2 = Voice Translation (P2), US3 = LLM Chat (P3)
- 所有路径基于 repo root：`src/jimao_translator/` 或 `tests/`

## Path Conventions

- Single-project desktop app layout
- Source: `src/jimao_translator/<domain>/...`
- Tests: `tests/{contract,integration,unit}/...`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding and dev tooling

- [X] T001 Create project structure (`src/jimao_translator/` 子包目录，`tests/{contract,integration,unit}/` 目录) 按 plan.md 指定布局
- [X] T002 Initialize Python project with `pyproject.toml`、`requirements.txt`、`requirements-dev.txt` at repo root（含 PySide6, httpx, pydantic, SpeechRecognition, sounddevice, edge-tts, anthropic, langdetect, platformdirs, keyring, qasync 依赖）
- [X] T003 [P] Configure Ruff lint/format in `pyproject.toml` (section `[tool.ruff]`) and add `.editorconfig`
- [X] T004 [P] Configure pytest in `pyproject.toml` (section `[tool.pytest.ini_options]`) with asyncio_mode=auto, coverage threshold 80%
- [X] T005 [P] Add `README.md` at repo root stub (项目名、简要描述、指向 quickstart.md)
- [X] T006 [P] Add `.gitignore` entries for `.venv/`, `dist/`, `build/`, `__pycache__/`, `.pytest_cache/`, `*.spec`

**Checkpoint**: `pip install -r requirements-dev.txt` succeeds; `pytest` and `ruff` runnable (no tests yet)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 共享基础设施 — 所有用户故事依赖。

**CRITICAL**: No user-story work starts until this phase completes.

### Enums & Models (Pure data — used by all stories)

- [X] T010 [P] Define `LanguageCode`, `TranslationMode`, `MessageRole` enums in `src/jimao_translator/models/enums.py`
- [X] T011 [P] Define `TranslationRequest` and `TranslationResult` Pydantic models in `src/jimao_translator/models/translation.py`
- [X] T012 [P] Define `VoiceSession` Pydantic model in `src/jimao_translator/models/voice.py`
- [X] T013 [P] Define `ChatMessage` and `ChatConversation` Pydantic models in `src/jimao_translator/models/chat.py`
- [X] T014 [P] Define `UserPreferences` Pydantic model in `src/jimao_translator/models/preferences.py`
- [X] T015 [P] Define `TranslationHistoryEntry` Pydantic model in `src/jimao_translator/models/translation.py`

### Model Tests (Foundational TDD)

- [X] T020 [P] Unit tests for enums in `tests/unit/models/test_enums.py`
- [X] T021 [P] Unit tests for translation models (validation, size limits) in `tests/unit/models/test_translation.py`
- [X] T022 [P] Unit tests for voice model in `tests/unit/models/test_voice.py`
- [X] T023 [P] Unit tests for chat models in `tests/unit/models/test_chat.py`
- [X] T024 [P] Unit tests for preferences (voice_speed clamp, defaults) in `tests/unit/models/test_preferences.py`

### Shared Exceptions

- [X] T025 Define custom exceptions (`TranslationError`, `UnsupportedLanguagePairError`, `RecognitionError`, `NoSpeechDetectedError`, `TtsError`, `LlmUnavailableError`, `AuthenticationError`, `ContentPolicyViolationError`) in `src/jimao_translator/exceptions.py`
- [X] T026 [P] Unit tests for exceptions (message formatting, hierarchy) in `tests/unit/test_exceptions.py`

### Configuration & Storage Primitives

- [X] T030 Implement platform-aware paths helper (`user_data_dir()` via `platformdirs`) in `src/jimao_translator/config.py`
- [X] T031 [P] Implement `PreferencesRepository` (JSON load/save, keyring for API key) in `src/jimao_translator/storage/preferences.py`
- [X] T032 [P] Implement `TranslationHistoryRepository` (JSON, capped at 100 entries, FIFO eviction) in `src/jimao_translator/storage/history.py`
- [X] T033 Unit tests for `PreferencesRepository` (load missing file → defaults; API key via keyring mock) in `tests/unit/storage/test_preferences.py`
- [X] T034 Unit tests for `TranslationHistoryRepository` (cap at 100, eviction order, opt-out) in `tests/unit/storage/test_history.py`

### Protocol Definitions

- [X] T040 [P] Define `TranslationProvider` Protocol in `src/jimao_translator/translation/provider.py`
- [X] T041 [P] Define `SpeechRecognizer` Protocol in `src/jimao_translator/speech/recognizer.py`
- [X] T042 [P] Define `TtsEngine` Protocol in `src/jimao_translator/tts/engine.py`
- [X] T043 [P] Define `LlmClient` Protocol in `src/jimao_translator/llm/client.py`

### Mock Implementations (Needed by all integration tests)

- [X] T050 [P] Implement `MockTranslationProvider` in `src/jimao_translator/translation/engines/mock.py`
- [X] T051 [P] Implement `MockSpeechRecognizer` in `src/jimao_translator/speech/engines/mock.py`
- [X] T052 [P] Implement `MockTtsEngine` in `src/jimao_translator/tts/engines/mock.py`
- [X] T053 [P] Implement `MockLlmClient` in `src/jimao_translator/llm/providers/mock.py`

**Checkpoint**: Foundation ready — user story implementation can proceed.

---

## Phase 3: User Story 1 — Real-time Text Translation (P1) 🎯 MVP

**Goal**: 用户输入中英日韩文本，选择目标语言，立即得到翻译结果，可一键复制。

**Independent Test**: 启动应用 → Text 标签 → 输入 "你好世界" → 选英文 → 500ms 内显示译文；
点击复制按钮后粘贴到其他应用可得到 "Hello, world"。

### Tests for User Story 1 (Write FIRST, ensure FAIL before implementation) ⚠️

- [X] T100 [P] [US1] Contract tests for `TranslationProvider` (8 cases from contracts/translation-provider.md) in `tests/contract/test_translation_provider.py`
- [X] T101 [P] [US1] Integration test: text translation end-to-end (zh→en, auto detect, copy flow) in `tests/integration/test_text_translation_flow.py`
- [X] T102 [P] [US1] Integration test: same-language short-circuit (zh→zh returns original) in `tests/integration/test_text_translation_flow.py`
- [X] T103 [P] [US1] Unit test: empty text rejection in `tests/unit/translation/test_service_validation.py`
- [X] T104 [P] [US1] Unit test: language detection (langdetect wrapper) in `tests/unit/translation/test_language_detection.py`

### Implementation for User Story 1

- [X] T110 [US1] Implement language detection wrapper (`detect_language(text) -> LanguageCode`) in `src/jimao_translator/translation/detection.py`
- [X] T111 [US1] Implement `LlmTranslator` (uses `LlmClient.translate_via_prompt`) in `src/jimao_translator/translation/engines/llm_translator.py`
- [X] T112 [US1] Implement `TranslationService` orchestration (validate → detect → short-circuit → call provider → record history) in `src/jimao_translator/translation/service.py`
- [X] T113 [US1] Implement Anthropic `LlmClient` (translate_via_prompt method only for US1) in `src/jimao_translator/llm/providers/anthropic_client.py`
- [X] T114 [US1] Implement UI widget: `LanguageSelector` in `src/jimao_translator/ui/widgets/language_selector.py`
- [X] T115 [US1] Implement UI tab: `TextTab` (input box, target language selector, translate button, result display, copy button) in `src/jimao_translator/ui/tabs/text_tab.py`
- [X] T116 [US1] Wire `TextTab` into `MainWindow` with tab navigation stub in `src/jimao_translator/ui/main_window.py`
- [X] T117 [US1] Implement app entry point `main()` (qasync + QApplication setup) in `src/jimao_translator/main.py`
- [X] T118 [US1] GUI test: TextTab translate flow via pytest-qt in `tests/integration/test_text_tab_ui.py`

**Checkpoint**: User Story 1 fully functional and testable; application is MVP-ready.

---

## Phase 4: User Story 2 — Voice Translation (P2)

**Goal**: 用户按住按钮说话 → 系统识别 → 翻译 → TTS 播放；对话模式下分屏展示双方语言。

**Independent Test**: 启动应用 → Voice 标签 → 授权麦克风 → 按住按钮说 "请问附近有餐厅吗" → 3s 内听到英文 TTS；切换对话模式后看到分屏布局。

### Tests for User Story 2 (Write FIRST) ⚠️

- [ ] T200 [P] [US2] Contract tests for `SpeechRecognizer` (7 cases from contracts/speech-recognizer.md) in `tests/contract/test_speech_recognizer.py`
- [ ] T201 [P] [US2] Contract tests for `TtsEngine` (6 cases from contracts/tts-engine.md) in `tests/contract/test_tts_engine.py`
- [ ] T202 [P] [US2] Integration test: voice end-to-end (speak mock bytes → recognized → translated → tts output) in `tests/integration/test_voice_end_to_end.py`
- [ ] T203 [P] [US2] Integration test: low-confidence recognition triggers UI warning in `tests/integration/test_voice_end_to_end.py`
- [ ] T204 [P] [US2] Unit test: raw audio bytes never written to disk in `tests/unit/speech/test_no_audio_persistence.py`
- [ ] T205 [P] [US2] Integration test: conversation-mode auto language detection (en speaker → zh playback) in `tests/integration/test_voice_conversation.py`

### Implementation for User Story 2

- [ ] T210 [P] [US2] Implement `SystemSpeechRecognizer` (wraps `SpeechRecognition` + `sounddevice`) in `src/jimao_translator/speech/engines/system_stt.py`
- [ ] T211 [P] [US2] Implement `EdgeTtsEngine` (edge-tts async streaming) in `src/jimao_translator/tts/engines/edge_tts_engine.py`
- [ ] T212 [US2] Implement audio capture helper (push-to-talk buffer, in-memory only, bytes cleared on release) in `src/jimao_translator/speech/capture.py`
- [ ] T213 [US2] Implement audio playback helper (QMediaPlayer with streaming MP3) in `src/jimao_translator/tts/playback.py`
- [ ] T214 [US2] Implement `VoiceTranslationOrchestrator` (capture → recognize → translate → tts playback, error handling) in `src/jimao_translator/speech/orchestrator.py`
- [ ] T215 [US2] Implement UI tab: `VoiceTab` with single-speaker mode (press-to-talk button, recognized text display with edit, confidence indicator) in `src/jimao_translator/ui/tabs/voice_tab.py`
- [ ] T216 [US2] Extend `VoiceTab` with split-screen conversation-mode layout (QSplitter, left=my language, right=counterpart language, scrolling history of both sides) in `src/jimao_translator/ui/tabs/voice_tab.py`
- [ ] T217 [US2] Wire `VoiceTab` into `MainWindow` tab bar in `src/jimao_translator/ui/main_window.py`
- [ ] T218 [US2] GUI test: VoiceTab press-to-talk flow (mock recognizer) via pytest-qt in `tests/integration/test_voice_tab_ui.py`

**Checkpoint**: User Story 1 AND User Story 2 both work independently.

---

## Phase 5: User Story 3 — LLM Intelligent Chat (P3)

**Goal**: 用户与 LLM 多轮对话（文本或语音输入），LLM 基于上下文回答翻译/语法/语境问题。

**Independent Test**: 启动应用 → Chat 标签 → 输入 "帮我把'谢谢'翻译成韩语并解释发音" → LLM 流式回复；追问 "那更礼貌的说法呢" → 验证上下文连贯。

### Tests for User Story 3 (Write FIRST) ⚠️

- [ ] T300 [P] [US3] Contract tests for `LlmClient` chat method (9 cases from contracts/llm-client.md) in `tests/contract/test_llm_client.py`
- [ ] T301 [P] [US3] Integration test: multi-turn chat preserves context ≥10 turns (SC-006) in `tests/integration/test_chat_conversation.py`
- [ ] T302 [P] [US3] Integration test: LLM unavailability shows fallback hint in `tests/integration/test_chat_conversation.py`
- [ ] T303 [P] [US3] Integration test: content policy violation handled gracefully in `tests/integration/test_chat_conversation.py`
- [ ] T304 [P] [US3] Unit test: context windowing preserves system prompt when over token limit in `tests/unit/llm/test_context_window.py`

### Implementation for User Story 3

- [ ] T310 [US3] Extend Anthropic `LlmClient` with full `chat()` streaming method and `ContentPolicyViolationError` mapping in `src/jimao_translator/llm/providers/anthropic_client.py`
- [ ] T311 [US3] Implement context windowing helper (trim oldest messages, keep system prompt) in `src/jimao_translator/llm/context.py`
- [ ] T312 [US3] Implement `ChatService` (maintains conversation state, calls LlmClient, handles errors) in `src/jimao_translator/llm/service.py`
- [ ] T313 [US3] Implement UI tab: `ChatTab` (message list, input box, streaming response rendering, new-conversation button) in `src/jimao_translator/ui/tabs/chat_tab.py`
- [ ] T314 [US3] Wire `ChatTab` into `MainWindow` tab bar in `src/jimao_translator/ui/main_window.py`
- [ ] T315 [US3] GUI test: ChatTab multi-turn flow via pytest-qt (mock LlmClient) in `tests/integration/test_chat_tab_ui.py`

**Checkpoint**: All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finishing touches across all stories.

### History Panel (spans US1/US2)

- [ ] T400 [P] Implement `HistoryPanel` widget (list view of up to 100 entries, re-copy button, clear button) in `src/jimao_translator/ui/widgets/history_panel.py`
- [ ] T401 Integrate `HistoryPanel` into `TextTab` and `VoiceTab` sidebar in `src/jimao_translator/ui/tabs/text_tab.py` and `src/jimao_translator/ui/tabs/voice_tab.py`
- [ ] T402 Integration test: history persists across restarts, caps at 100, respects opt-out in `tests/integration/test_history_persistence.py`

### Preferences UI

- [ ] T410 [P] Implement `PreferencesDialog` (language pair defaults, theme, voice speed, hotkey, history opt-in, API key entry) in `src/jimao_translator/ui/preferences_dialog.py`
- [ ] T411 Wire `PreferencesDialog` into `MainWindow` (menu entry, opens modal) in `src/jimao_translator/ui/main_window.py`
- [ ] T412 Implement "remember last active tab" on close/launch per FR-011a in `src/jimao_translator/ui/main_window.py`
- [ ] T413 GUI test: preferences save/load/reload cycle in `tests/integration/test_preferences_ui.py`

### Error Handling & UX Polish

- [ ] T420 [P] Implement network-offline detection banner + graceful-degradation hint in `src/jimao_translator/ui/widgets/offline_banner.py`
- [ ] T421 [P] Implement global error dialog helper (translates exceptions to user-friendly messages) in `src/jimao_translator/ui/error_dialog.py`
- [ ] T422 Edge-case test: oversized input (>5000 chars) prompts truncation in `tests/integration/test_edge_cases.py`
- [ ] T423 Edge-case test: concurrent translation requests do not interleave results in `tests/integration/test_edge_cases.py`

### Performance & Cross-Platform

- [ ] T430 [P] Performance test: startup <3s on CI (Windows/macOS/Linux) in `tests/integration/test_performance.py`
- [ ] T431 [P] Performance test: text translation latency <500ms with mock provider in `tests/integration/test_performance.py`
- [ ] T432 [P] Performance test: memory <500MB during idle+voice translation in `tests/integration/test_performance.py`

### Documentation & Packaging

- [ ] T440 [P] Update `README.md` with install, run, test, and packaging instructions
- [ ] T441 [P] Add `docs/architecture.md` summarizing module layout and Protocol contracts
- [ ] T442 Create PyInstaller spec file `packaging/jimao_translator.spec` and CI workflow stub `.github/workflows/build.yml`
- [ ] T443 Run `quickstart.md` validation end-to-end on a clean machine; update quickstart if gaps found

### Coverage & Final Validation

- [ ] T450 Run `pytest --cov=jimao_translator --cov-report=term-missing` and ensure ≥80% coverage (宪法原则 II); add missing tests where needed
- [ ] T451 Run `ruff check .` and `ruff format --check .` — no violations
- [ ] T452 Final Constitution compliance review (check all 3 principles, performance, portability) and record results in `docs/constitution-compliance.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — MVP, must ship first
- **User Story 2 (Phase 4)**: Depends on Foundational — may share mocks with US1 but independently testable
- **User Story 3 (Phase 5)**: Depends on Foundational — may extend AnthropicLlmClient from US1
- **Polish (Phase 6)**: Depends on whichever user stories are complete

### User Story Dependencies

- US1 (P1) is an MVP checkpoint — ship-ready after Phase 3
- US2 (P2) reuses TranslationService from US1 but its voice flow is isolated
- US3 (P3) reuses AnthropicLlmClient from US1 but chat UI is isolated

### Within Each User Story

- Tests are written FIRST and MUST FAIL before implementation (TDD non-negotiable)
- Models/contracts → services → UI integration (bottom-up within each story)
- Commit after each task or logical group

### Parallel Opportunities

- All `[P]` tasks in Phase 1/2 can run in parallel (disjoint files)
- All test tasks within a user story marked `[P]` can run in parallel
- Mock implementations (T050–T053) can be built in parallel by different contributors
- Docs tasks (T440–T441) can run in parallel with test authoring
- **Cross-story parallelism**: Once Phase 2 done, US1/US2/US3 can be staffed in parallel by 3 contributors

---

## Parallel Example: User Story 1 kickoff

```bash
# After Phase 2 completes, spin up US1 tests in parallel:
Task: "T100 Contract tests for TranslationProvider in tests/contract/test_translation_provider.py"
Task: "T101 Integration test: text translation end-to-end in tests/integration/test_text_translation_flow.py"
Task: "T103 Unit test: empty text rejection in tests/unit/translation/test_service_validation.py"
Task: "T104 Unit test: language detection in tests/unit/translation/test_language_detection.py"
```

Once tests fail, implement in dependency order: T110 (detection) → T111 (engine) → T112 (service) → T113 (LLM client) → T114–T117 (UI).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) — tooling in place
2. Complete Phase 2 (Foundational) — models, protocols, mocks, storage
3. Complete Phase 3 (US1) — text translation end-to-end
4. **STOP and VALIDATE**: Run `quickstart.md` text-translation scenario
5. Ship MVP (可演示给利益相关方)

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add US1 → test → **demo MVP**
3. Add US2 → test → demo voice translation
4. Add US3 → test → demo LLM chat
5. Polish phase → production-grade release candidate

### Parallel Team Strategy

- Developer A: US1 (text translation + UI skeleton)
- Developer B: US2 (voice translation + audio infra)
- Developer C: US3 (LLM chat + context management)
- Everyone contributes to Phase 6 polish after their story lands

---

## Notes

- `[P]` tasks = different files, no dependencies on incomplete work
- `[Story]` label maps each task to its user story for traceability
- 宪法要求 **Test-First (NON-NEGOTIABLE)** — 每个实现任务前 MUST 先完成对应测试且测试失败
- Commit boundaries: after each task group or logical checkpoint
- Stop at any Checkpoint to validate the story independently
- 避免跨故事的隐式依赖：每个故事的完成不得打断其他故事的独立可测性
