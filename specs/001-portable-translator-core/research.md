# Research: Portable Translator Core

**Date**: 2026-04-17
**Feature**: 001-portable-translator-core

本文档记录 Phase 0 技术调研的决策、理由与备选方案。所有 NEEDS CLARIFICATION
已在 `spec.md` 的 Clarifications 段解决，此处专注技术选型。

---

## 1. GUI 框架

- **Decision**: PySide6 (Qt for Python, LGPL)
- **Rationale**:
  - 跨平台（Windows/macOS/Linux）原生外观，启动时间可控在 3 秒内
  - 成熟稳定，PySide6 使用 LGPL 许可证，商业友好
  - 支持全屏沉浸式布局、标签页、分屏（QSplitter 原生支持对话模式）
  - 与 Python 生态深度集成，pytest-qt 提供 GUI 测试支持
- **Alternatives considered**:
  - **Tkinter**: 标准库但 UI 粗糙，无法实现沉浸式现代 UI
  - **Electron + Python 后端**: 启动慢、内存占用超出 500MB 限制
  - **Flet**: 新兴且有依赖 Flutter 运行时，跨平台打包复杂
  - **Kivy**: 更偏移动/触控，桌面体验次于 Qt

## 2. 翻译引擎

- **Decision**: 以 LLM（Anthropic Claude）作为默认翻译后端，通过 `TranslationProvider` 抽象
- **Rationale**:
  - 宪法原则 I 要求"上下文感知翻译"，LLM 天然具备此能力
  - 与 LLM 聊天模块复用同一客户端，降低依赖
  - 质量优于传统 MT API（如 Google Translate）在口语化/文化语境场景
  - 模块化接口允许未来接入 DeepL / 本地模型 / Google Translate
- **Alternatives considered**:
  - **Google Cloud Translation**: 需额外 API 凭证，上下文能力弱
  - **DeepL API**: 质量好但不支持韩语（v1 需求）
  - **本地模型 (NLLB / Marian)**: 下载体积大，违反 500MB 内存限制

## 3. 语音识别 (STT)

- **Decision**: `SpeechRecognition` 库 + Google Web Speech API（默认）+ `sounddevice` 录音
- **Rationale**:
  - `SpeechRecognition` 提供统一接口，未来可切换 whisper / Vosk 本地引擎
  - Google Web Speech API 免费且覆盖 4 种目标语言，延迟 <1s
  - `sounddevice` 跨平台实现按键录音
  - 识别结果包含 `confidence`，满足 FR-012
- **Alternatives considered**:
  - **whisper.cpp 本地**: 模型 >1GB 违反内存约束，启动慢
  - **Azure/AWS STT**: 需额外付费 API 密钥，增加用户配置负担
  - **Vosk**: 模型需下载，首次体验差

## 4. 文本转语音 (TTS)

- **Decision**: `edge-tts`（基于 Microsoft Edge 的免费 TTS）
- **Rationale**:
  - 免费、无需 API 密钥
  - 支持中英日韩所有 4 种目标语言且音质自然
  - 异步 API，与 httpx/asyncio 架构契合
  - 输出标准音频流（MP3），可直接用 QMediaPlayer 播放
- **Alternatives considered**:
  - **pyttsx3**: 使用系统 TTS，韩语/日语发音质量差
  - **Google Cloud TTS**: 收费且需凭证
  - **Coqui TTS 本地**: 模型体积大，违反内存约束

## 5. LLM 提供商

- **Decision**: Anthropic Claude (claude-sonnet-4-6)，通过官方 `anthropic` Python SDK
- **Rationale**:
  - 澄清确认"单一 LLM 提供商"策略
  - Claude 在中英日韩翻译质量和文化语境理解上表现优秀
  - 官方 SDK 支持流式响应、工具调用，扩展性好
  - 用户提供 API 密钥，符合 FR-009
- **Alternatives considered**:
  - **OpenAI GPT**: 质量相当，但项目已在 Anthropic 生态（Claude Code）
  - **本地模型 (Llama)**: 违反内存/启动约束
  - **多提供商聚合**: 澄清阶段已明确 v1 仅单一提供商

## 6. 语言检测

- **Decision**: `langdetect`（基于 Google language-detection 的 Python 移植）
- **Rationale**:
  - 轻量（<1MB），无需联网
  - 对中英日韩四语言识别准确率 >95%
  - 满足 FR-002 自动检测输入语言
- **Alternatives considered**:
  - **langid**: 相似但社区活跃度较低
  - **fastText**: 需下载模型（>100MB）

## 7. 本地存储

- **Decision**: JSON 文件存储（`platformdirs` 确定用户数据目录），不使用数据库
- **Rationale**:
  - 数据量小（<100 条历史 + 少量偏好），JSON 完全够用
  - 避免 SQLite 启动/文件锁开销
  - 用户可直接查看/备份/迁移文件（可调试性好）
  - 符合宪法"YAGNI"精神（简洁至上）
- **Alternatives considered**:
  - **SQLite**: 杀鸡用牛刀，增加复杂度
  - **shelve**: 平台兼容性差
  - **TOML 配置文件**: 适合偏好但不适合历史列表

## 8. 异步并发模型

- **Decision**: `asyncio` + `httpx.AsyncClient`，UI 通过 `qasync` 桥接 Qt 事件循环
- **Rationale**:
  - LLM/STT/TTS 均为 I/O 密集，asyncio 避免阻塞 UI
  - `qasync` 是社区标准 Qt+asyncio 集成库，稳定
  - 支持并发翻译请求（用户快速切换目标语言时）
- **Alternatives considered**:
  - **线程池 (QThreadPool)**: 更复杂，调试困难
  - **纯同步**: UI 会冻结，违反用户体验

## 9. 打包与分发

- **Decision**: PyInstaller 生成单文件可执行包，每平台独立构建
- **Rationale**:
  - 用户无需安装 Python 环境
  - PyInstaller 成熟支持 PySide6 及所有依赖
  - 可在 CI 中自动化构建
- **Alternatives considered**:
  - **Nuitka**: 编译慢，调试体验差
  - **Briefcase**: 较新，PySide6 支持不完善
  - **pip install 方式**: 不符合"便携式"定位

## 10. 测试策略

- **Decision**:
  - **Contract tests**: 验证每个 Protocol 的 mock 与真实实现行为一致
  - **Integration tests**: 跨模块（例：voice → STT → translation → TTS）
  - **Unit tests**: 纯函数、数据验证
  - **GUI tests**: 使用 `pytest-qt` 触发控件事件
  - **Mock 外部服务**: 所有网络调用在测试中使用 `respx`（httpx 的 mock 库）
- **Rationale**:
  - 满足宪法"TDD 强制执行"和"覆盖率 >= 80%"
  - 集成测试保证模块协作，契约测试保证接口稳定
  - 不依赖真实 API 密钥，CI 可稳定运行
- **Alternatives considered**: N/A（测试层次是标准实践）

---

## 总结

所有技术决策已覆盖宪法的 3 个核心原则和性能约束。无遗留 NEEDS CLARIFICATION。
下一步：生成 `data-model.md`、`contracts/`、`quickstart.md`。
