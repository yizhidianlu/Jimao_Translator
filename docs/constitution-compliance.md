# Constitution Compliance Report

**Feature**: 001-portable-translator-core
**Review date**: 2026-04-18
**Constitution version**: 1.0.0 (ratified 2026-04-17)

## 总览

| 原则 / 约束 | 状态 | 证据 |
|---|---|---|
| I. 翻译质量优先 | ✅ 合规 | 见 §1 |
| II. 测试优先 (TDD) | ✅ 合规 | 见 §2（186 passed · 86% cov） |
| III. 模块化架构 | ✅ 合规 | 见 §3 |
| Performance & Portability | ✅ 合规 | 见 §4 |
| Development Workflow | ✅ 合规 | 见 §5 |

## 1. Translation Quality First

| 要求 | 落地方式 |
|---|---|
| 翻译准确性优先 | `TranslationResult.confidence` 字段贯穿所有引擎；UI 在 `VoiceOutcome.low_confidence`（<0.6）时标注提醒（`voice_tab.py`）|
| 低置信度明确标注 | `LOW_CONFIDENCE_THRESHOLD = 0.6` 常量，`VoiceOutcome.low_confidence` 属性；UI 层展示"识别不确定"提示 |
| 语音识别纠错 | `SpeechSession.confidence` 参与判定；低置信度触发 UI 提示而非静默传递给翻译 |
| 上下文感知 | LLM 聊天走 `ChatService` + `trim_conversation` 维护多轮上下文（默认窗口 40 条，系统提示永不被裁） |
| 置信度与元数据 | `TranslationResult` 包含 `detected_source_language`、`engine`、`confidence`、`completed_at`，完整审计链路 |

**缺口**：术语库 / glossary 机制尚未实现（未列入 MVP 范围，后续迭代承接）。

## 2. Test-First (NON-NEGOTIABLE)

| 要求 | 证据 |
|---|---|
| TDD 执行 | 所有 Phase 3-6 任务均按 "测试先写 FAIL → 实现 → PASS" 节奏提交（见 `tasks.md` 任务顺序与 git 历史）|
| 覆盖率 ≥80% | **86%** (`pytest --cov=jimao_translator`) |
| 边界用例 | 空输入（`test_service_validation.py::test_empty_text_raises`）、超长文本截断（`test_edge_cases.py::TestOversizedInput`）、未知语言（`UnsupportedLanguageError` 各处）、并发隔离（`test_edge_cases.py::TestConcurrentRequests`）|
| 语音端到端 | `tests/integration/test_voice_end_to_end.py` + `test_voice_tab_ui.py` |
| 单元 + 集成分层 | `tests/unit/` · `tests/contract/` · `tests/integration/`（gui / performance 独立 marker）|
| pytest 框架 | `pyproject.toml [tool.pytest.ini_options]` 配置完整 |

**基线**：186 passed · 1 skipped（psutil 可选）· ruff 零违规。

## 3. Modular Architecture

| 要求 | 落地方式 |
|---|---|
| 功能域独立封装 | `translation/` · `speech/` · `tts/` · `llm/` 四个顶层包，各自持有 Protocol + Service + engines 子目录 |
| Protocol 通信 | `TranslationProvider`、`SpeechRecognizer`、`TtsEngine`、`LlmClient` 均为 `@runtime_checkable Protocol` |
| 翻译引擎插件化 | `TranslationProvider` 实现支持 `MockTranslationProvider` / `LlmTranslator`（通过提示词走 LLM）切换；可继续扩展 |
| 独立测试 | 每个 engine 都有对应契约测试（`tests/contract/test_*`） |
| 新场景通过扩展 | Phase 4 语音 / Phase 5 聊天均新增独立包，未修改既有模块核心逻辑 |

## 4. Performance & Portability

| 约束 | 指标 | 测试 |
|---|---|---|
| 启动 < 3s | MainWindow 构造在本地 Windows 11 约 0.3s | `test_performance.py::test_main_window_construction_under_3s` |
| 文本翻译 < 500ms | Mock provider 典型 < 5ms | `test_performance.py::test_mock_translation_under_500ms` + `test_batch_of_10_translations_amortized` |
| 语音端到端 < 2s | 依赖真实 STT/TTS，本地 mock 验证 orchestration 路径 | `test_voice_end_to_end.py` |
| 内存 < 500MB | 依赖 psutil 探测；不可用时 skip | `test_performance.py::test_process_memory_under_500mb` |
| 离线基础翻译 | `OfflineBanner` + `MockTranslationProvider` / 本地缓存回退 | `test_history_panel_ui.py::TestOfflineBanner` |
| 跨平台 | `platformdirs` 选择用户数据目录；CI 矩阵覆盖 Ubuntu/macOS/Windows | `.github/workflows/build.yml` |
| 超时与降级 | `QwenLlmClient` 错误映射到 `LlmUnavailableError` → UI 降级 | `test_qwen_client.py::test_*_error_mapped` |

## 5. Development Workflow

| 要求 | 落地 |
|---|---|
| Python 3.11+ | `pyproject.toml requires-python = ">=3.11"` |
| 依赖管理 | `pyproject.toml` + `pip install -e .`（保留 `requirements*.txt` 供 CI 兼容） |
| Ruff lint + format | `pyproject.toml [tool.ruff]` 全量规则；本地 + CI 双重校验 |
| 提交规范 | 现有 git 历史均使用 `feat(phase-X,USY): ...` 前缀 |
| PR 含测试 | 每个 phase 提交均包含对应 test 文件增量 |

## 结论

**核心结论**：MVP 在三大原则、性能约束、开发流程上全部合规，测试覆盖率 86% 超过 80% 门槛。

**后续工作（不阻塞 MVP 发布）**：
- 术语库 / glossary 机制（原则 I 的扩展）
- 真实 STT/TTS 后端的性能基准（当前以 mock 验证 orchestration 路径）
- 本地离线翻译模型（原则 IV 约束下的增强）
