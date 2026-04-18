# Jimao Translator (鸡毛翻译器)

便携式桌面翻译器：中 / 英 / 日 / 韩 四语互译 + 语音翻译 + LLM 智能聊天。

## 功能

- **文本翻译**：输入文本一键翻译，支持自动识别源语言。
- **语音翻译**：按住说话 → 识别 → 翻译 → 语音播报；对话模式下分屏展示双方语言。
- **LLM 聊天**：基于 Anthropic Claude 的多轮对话，可处理翻译、语法、语境问题。

## 快速开始

开发者请参阅 [specs/001-portable-translator-core/quickstart.md](specs/001-portable-translator-core/quickstart.md)。

## 项目状态

🚧 开发中（Phase 1 Setup）。参见 [tasks.md](specs/001-portable-translator-core/tasks.md) 了解进度。

## 宪法

本项目遵循 [`.specify/memory/constitution.md`](.specify/memory/constitution.md) 的三大原则：

1. 翻译质量优先
2. 测试优先（TDD，NON-NEGOTIABLE）
3. 模块化架构

## 技术栈

Python 3.11+ · PySide6 · httpx · Pydantic · SpeechRecognition · edge-tts · Anthropic Claude · qasync

## 许可

MIT
