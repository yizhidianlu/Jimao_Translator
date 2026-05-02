# Jimao Translator (鸡毛翻译器)

便携式桌面翻译器：中 / 英 / 日 / 韩 四语互译 + 语音翻译 + LLM 智能聊天。

## 功能

- **文本翻译** — 输入文本一键翻译，支持 `auto` 识别源语言、目标文本自动拷贝。
- **语音翻译** — 按住说话 → 识别 → 翻译 → 语音播报；对话模式下左右分屏呈现双方语言。
- **LLM 聊天** — 基于通义千问（Qwen3）的多轮对话，流式输出，可讨论翻译/语法/语境问题。
- **历史记录** — 本地 JSON 持久化；面板支持查看 / 复制 / 清空。
- **偏好设置** — 界面偏好、语速、热键、API Key（系统 keyring）统一管理。

## 快速开始

```bash
# 1. 准备 Python 3.11+
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 2. 安装依赖（含开发依赖）
pip install -e ".[dev]" || pip install -e .

# 3. 配置 API Key（运行后在 "偏好设置 …" 中填入，存储到系统 keyring）
export DASHSCOPE_API_KEY=sk-...   # 可选：初次启动前也可通过环境变量注入

# 4. 启动
jimao-translator
# 或
python -m jimao_translator.main
```

详细开发者流程参见 [specs/001-portable-translator-core/quickstart.md](specs/001-portable-translator-core/quickstart.md)。

## 运行测试

```bash
pytest                                         # 全量（单元 + 集成 + GUI + 契约）
pytest -m "not gui"                            # 跳过需要 Qt 事件循环的测试
pytest --cov=jimao_translator --cov-report=term-missing   # 覆盖率
ruff check . && ruff format --check .          # 代码风格
```

目前基线：**186 passed · 86% 覆盖率 · ruff 零违规**。

## 打包

```bash
# Windows / macOS / Linux 通用
pyinstaller packaging/jimao_translator.spec
# 构建产物在 dist/jimao_translator/
```

CI 构建模板见 [.github/workflows/build.yml](.github/workflows/build.yml)。

## 项目状态

✅ MVP 完成（文本 / 语音 / LLM 聊天 / 历史 / 偏好 / 错误 UX）。参见 [tasks.md](specs/001-portable-translator-core/tasks.md)。

## 架构

模块布局与协议契约说明见 [docs/architecture.md](docs/architecture.md)。

## 宪法

本项目遵循 [`.specify/memory/constitution.md`](.specify/memory/constitution.md) 的三大原则：

1. 翻译质量优先
2. 测试优先（TDD，NON-NEGOTIABLE）
3. 模块化架构

合规报告见 [docs/constitution-compliance.md](docs/constitution-compliance.md)。

## 技术栈

Python 3.11+ · PySide6 · httpx · Pydantic · SpeechRecognition · edge-tts · 通义千问 Qwen3（DashScope 兼容 OpenAI 接口） · qasync · keyring

## 许可

MIT
