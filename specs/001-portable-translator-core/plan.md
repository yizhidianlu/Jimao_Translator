# Implementation Plan: Portable Translator Core

**Branch**: `001-portable-translator-core` | **Date**: 2026-04-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-portable-translator-core/spec.md`

## Summary

构建便携式随身翻译工具，包含三个模式：实时文本翻译（中英日韩互译）、
语音翻译（按住说话 → 识别 → 翻译 → 朗读，支持分屏对话模式）、
LLM 智能问答（单一提供商，多轮对话）。采用全屏沉浸式桌面 UI，通过标签页切换三个模式。
技术方案以 Python 3.11+ 为核心，PySide6 构建跨平台 GUI，模块化架构支持未来扩展。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: PySide6 (GUI), httpx (HTTP 客户端), pydantic (数据模型), SpeechRecognition + sounddevice (语音采集), edge-tts (TTS), anthropic SDK (LLM), langdetect (语言检测)
**Storage**: 本地 JSON 文件（用户偏好、翻译历史，上限 100 条）；无远程存储
**Testing**: pytest + pytest-qt（GUI 测试）+ pytest-asyncio（异步测试）
**Target Platform**: Windows / macOS / Linux 桌面
**Project Type**: Desktop app (single project)
**Performance Goals**: 文本翻译结果 <500ms；语音端到端（说话→播放开始）<3s；启动 <3s
**Constraints**: 内存占用 <500MB（不含本地模型）；支持离线降级提示；原始语音数据不持久化
**Scale/Scope**: 单用户本地桌面应用；4 种语言互译（中英日韩）；最多 100 条历史记录；10+ 轮对话上下文

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

基于宪法 v1.0.0 的合规检查：

### I. Translation Quality First (翻译质量优先)

- ✅ 计划使用上下文感知的翻译 API（非逐词映射），符合"上下文感知"要求
- ✅ 语音识别置信度会标注并允许用户修正（FR-008、FR-012）
- ✅ LLM 回答提供置信度说明（通过显式标注"可能不准确"）
- ⚠ 术语库（glossary）机制在 v1 范围内未实现 —
  **理由**: v1 聚焦于核心翻译与 LLM 问答场景，术语库属于专业翻译增强功能，将在 v2 规划

### II. Test-First (测试优先, NON-NEGOTIABLE)

- ✅ pytest 框架，覆盖率目标 >= 80%
- ✅ 翻译质量测试集：边界用例（空输入、超长、特殊字符、混合语言）
- ✅ 语音端到端集成测试（mock 麦克风输入 → 验证识别/翻译/TTS 输出）
- ✅ 每个模块独立单元测试

### III. Modular Architecture (模块化架构)

- ✅ 功能域独立封装：`translation/`、`speech/` (STT)、`tts/`、`llm/`、`storage/`、`ui/`
- ✅ 模块间通过 Protocol/ABC 通信（如 `TranslationEngine` 接口）
- ✅ 翻译引擎插件化：抽象 `TranslationProvider` 允许后续切换
  （注: 尽管 v1 LLM 锁定单提供商，但接口抽象保留扩展性）
- ✅ 新场景通过新增模块扩展，不修改核心模块

### Performance & Portability Constraints

- ✅ 启动 <3s（Python + PySide6 可达）
- ✅ 内存 <500MB（纯 API 模式，无本地模型）
- ✅ 跨平台（PySide6 支持 Win/macOS/Linux）
- ✅ 所有外部 API 调用使用 httpx 异步客户端，含超时控制

### Development Workflow

- ✅ Python 3.11+
- ✅ Ruff lint/format
- ✅ Conventional Commits（已在提交中遵循）
- ✅ Feature branch 工作流

**Gate Result**: ✅ PASS（无违规，无需复杂度追踪表）

## Project Structure

### Documentation (this feature)

```text
specs/001-portable-translator-core/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (module interface contracts)
│   ├── translation-provider.md
│   ├── speech-recognizer.md
│   ├── tts-engine.md
│   └── llm-client.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── jimao_translator/
│   ├── __init__.py
│   ├── main.py                    # App entry point (launches PySide6 window)
│   ├── config.py                  # Settings/env loading
│   ├── translation/               # Text translation domain
│   │   ├── __init__.py
│   │   ├── provider.py            # TranslationProvider Protocol
│   │   ├── engines/
│   │   │   ├── llm_translator.py  # Default: use LLM as translator
│   │   │   └── mock.py            # For tests
│   │   └── service.py             # Translation orchestration
│   ├── speech/                    # Speech-to-text (STT)
│   │   ├── __init__.py
│   │   ├── recognizer.py          # SpeechRecognizer Protocol
│   │   └── engines/
│   │       ├── system_stt.py      # SpeechRecognition library wrapper
│   │       └── mock.py
│   ├── tts/                       # Text-to-speech
│   │   ├── __init__.py
│   │   ├── engine.py              # TtsEngine Protocol
│   │   └── engines/
│   │       ├── edge_tts_engine.py
│   │       └── mock.py
│   ├── llm/                       # LLM chat integration
│   │   ├── __init__.py
│   │   ├── client.py              # LlmClient Protocol
│   │   └── providers/
│   │       ├── anthropic_client.py
│   │       └── mock.py
│   ├── storage/                   # Local persistence
│   │   ├── __init__.py
│   │   ├── preferences.py         # UserPreferences repo
│   │   └── history.py             # TranslationHistory repo (max 100)
│   ├── models/                    # Pydantic data models
│   │   ├── __init__.py
│   │   ├── translation.py
│   │   ├── voice.py
│   │   ├── chat.py
│   │   └── preferences.py
│   └── ui/                        # PySide6 UI
│       ├── __init__.py
│       ├── main_window.py         # Full-screen window with tabs
│       ├── tabs/
│       │   ├── text_tab.py        # Text translation tab
│       │   ├── voice_tab.py       # Voice translation (split-screen)
│       │   └── chat_tab.py        # LLM chat
│       └── widgets/
│           ├── language_selector.py
│           └── history_panel.py

tests/
├── contract/                      # Module contract tests (Protocol compliance)
│   ├── test_translation_provider.py
│   ├── test_speech_recognizer.py
│   ├── test_tts_engine.py
│   └── test_llm_client.py
├── integration/                   # Cross-module tests
│   ├── test_voice_end_to_end.py
│   ├── test_text_translation_flow.py
│   └── test_chat_conversation.py
└── unit/                          # Per-module unit tests
    ├── translation/
    ├── speech/
    ├── tts/
    ├── llm/
    ├── storage/
    └── models/
```

**Structure Decision**: 采用 **Option 1: Single project**。应用是单体桌面应用，
所有模块共享同一代码库。顶层 `src/jimao_translator/` 按功能域分包，
每个域包含 Protocol 定义（`provider.py`/`engine.py`/`client.py`）和具体实现（`engines/` 或 `providers/`），
实现模块化架构原则。`tests/` 按测试类型组织（contract/integration/unit），
以支持宪法 II 所要求的 TDD 工作流。

## Complexity Tracking

> 无需填写 — Constitution Check 全部通过（除 glossary 机制已在原则 I 下注明为 v2 范围）。
