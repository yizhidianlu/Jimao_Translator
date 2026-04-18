# Architecture

## 分层

```
UI (PySide6)
    │  signals / asyncSlot
    ▼
Services (orchestration)
    │  依赖 Protocol（可注入 mock / real 实现）
    ▼
Engines (provider adapters)
    │  → 外部 SDK / HTTP / 本地后端
    ▼
Storage (JSON + keyring)
```

目标：**UI 不直接依赖外部 SDK**。每一层只依赖下一层定义的 Protocol。

## 模块布局

| 包 | 职责 |
|---|---|
| `models/` | Pydantic 数据模型与枚举，零业务逻辑 |
| `config.py` | `platformdirs` 驱动的路径 / 常量 |
| `exceptions.py` | 所有领域异常继承自 `JimaoError` |
| `storage/` | `TranslationHistoryRepository`、`PreferencesRepository`（JSON + keyring） |
| `translation/` | `TranslationProvider` Protocol + `TranslationService` + `engines/`（mock / llm_translator） |
| `speech/` | `SpeechRecognizer` Protocol + `VoiceTranslationOrchestrator` + `engines/`（mock / system_stt） |
| `tts/` | `TtsEngine` Protocol + `playback.play_stream` + `engines/`（mock / edge_tts） |
| `llm/` | `LlmClient` Protocol + `ChatService`（上下文窗口裁剪 + 流式） + `providers/`（mock / anthropic） |
| `ui/` | `MainWindow` + 各 Tab + 独立 widgets（`history_panel`、`offline_banner`、`language_selector`） |

## Protocol 契约

运行时可检查（`@runtime_checkable`），可直接 `isinstance(obj, Protocol)` 验证。

| Protocol | 关键方法 | 测试基准 |
|---|---|---|
| `TranslationProvider` | `translate(request) -> TranslationResult` | `tests/contract/test_translation_provider.py` |
| `SpeechRecognizer` | `recognize(audio_bytes, language=None) -> SpeechSession` | `tests/contract/test_speech_recognizer.py` |
| `TtsEngine` | `synthesize(text, language, rate=1.0) -> AsyncIterator[bytes]` | `tests/contract/test_tts_engine.py` |
| `LlmClient` | `chat(messages) -> AsyncIterator[str]` · `translate_via_prompt(...)` | `tests/contract/test_llm_client.py` |

新增后端时：先让 `tests/contract/` 针对该实现通过，再写 service-level 集成测试。

## 异步模型

- 入口：`qasync.QEventLoop` 将 asyncio 挂载到 Qt 事件循环。
- UI 事件处理器用 `@asyncSlot`（通过 `qasync`）启动协程。
- 所有 provider / service 方法均为 `async`，不在 GUI 线程里做阻塞 IO。
- `TtsEngine.synthesize` 返回 `AsyncIterator[bytes]`，支持边合成边播放（流式 TTS）。

## 数据持久化

| 文件 | 内容 |
|---|---|
| `{user_data_dir}/history.json` | 翻译历史条目（`TranslationHistoryEntry` 列表，最大保留 N 条） |
| `{user_data_dir}/preferences.json` | 语言 / 主题 / 语速 / 热键 / 历史开关（不含 API Key） |
| OS keyring (`JIMAO_SERVICE`) | LLM API Key，明文永不写盘 |

`{user_data_dir}` 由 `platformdirs` 选择，跨平台（Windows `%LOCALAPPDATA%`、macOS `~/Library/Application Support`、Linux `~/.local/share`）。

## 错误策略

1. **领域异常层** — `exceptions.py` 定义 `JimaoError` 及其子类（`AuthenticationError`、`LlmUnavailableError`、`ContentPolicyViolationError`、`NoSpeechDetectedError`、`RecognitionError`、`TtsError`、`UnsupportedLanguageError`、`TranslationError`）。
2. **Provider 适配** — 外部 SDK 异常按类名 / 消息映射到领域异常（见 `AnthropicLlmClient._raise_mapped`）。
3. **UI 呈现** — `ui/error_dialog.format_error(err)` 将领域异常翻译为中文用户消息；`show_error(err, parent)` 弹出 `QMessageBox`。
4. **优雅降级** — 网络不可用时显示 `OfflineBanner`，基础翻译（mock / 本地缓存）仍可用。

## 测试金字塔

- **单元测试** (`tests/unit/`)：纯逻辑，无 Qt / 无网络。
- **契约测试** (`tests/contract/`)：对每个 Protocol 实现断言同一组行为。
- **集成测试** (`tests/integration/`)：服务 + 存储组合；带 `gui` 标记的使用 `QApplication` 单例。
- **性能 smoke** (`tests/integration/test_performance.py`，`performance` 标记)：启动 / 延迟 / 内存预算。

覆盖率门槛 **≥ 80%**，在 `pyproject.toml` 的 `[tool.coverage.run]` omit 了 `main.py`（纯 bootstrap，无逻辑）。
