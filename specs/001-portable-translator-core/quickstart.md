# Quickstart: Portable Translator Core

**Feature**: 001-portable-translator-core
**Audience**: 开发者首次运行/调试本项目

## 前置条件

- Python 3.11 或更高版本
- Git
- 可访问互联网（用于翻译/STT/TTS/LLM API）
- Anthropic API 密钥（用于 LLM 和翻译后端）

## 初始化

```bash
git clone <repo-url>
cd Jimao_Translator
git checkout 001-portable-translator-core

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -e .
# 可选（开发者）：
pip install pytest pytest-asyncio pytest-cov pytest-qt ruff psutil
```

## 配置 API 密钥

首次启动时，应用会提示配置 Anthropic API 密钥。
或预先通过环境变量设置：

```bash
# Windows (PowerShell):
$env:ANTHROPIC_API_KEY = "sk-ant-..."
# macOS / Linux:
export ANTHROPIC_API_KEY="sk-ant-..."
```

密钥首次使用后会被保存至系统 keyring，之后无需重复输入。

## 启动应用

```bash
jimao-translator
# 或直接运行入口脚本：
python -m jimao_translator.main
```

启动后：

1. 默认进入 **Text Translation** 标签页
2. 输入中文文本，选择目标语言为英语 → 立即看到译文
3. 切换到 **Voice Translation** 标签页 → 按住麦克风按钮说话
4. 切换到 **LLM Chat** 标签页 → 与 Claude 对话

## 运行测试

```bash
# 运行全部测试
pytest

# 按分层运行
pytest tests/contract     # 契约测试
pytest tests/integration  # 集成测试
pytest tests/unit         # 单元测试

# 覆盖率
pytest --cov=jimao_translator --cov-report=term-missing
```

目标覆盖率 >= 80%（见宪法原则 II）。

## 代码风格

```bash
ruff check .
ruff format .
```

## 验收场景演示（按规范 spec.md）

### 文本翻译 (P1)

1. 启动应用
2. 输入 "你好世界"
3. 目标语言选择 "English"
4. **预期**: 500ms 内显示 "Hello, world"
5. 点击复制按钮 → 粘贴到其他窗口验证

### 语音翻译 (P2)

1. 切换到 Voice 标签，授予麦克风权限
2. 按住语音按钮并说 "请问附近有餐厅吗"
3. **预期**: 3 秒内识别原文、翻译为英文、播放英文 TTS
4. 切换到"对话模式" → 分屏显示，左侧中文、右侧英文

### LLM 聊天 (P3)

1. 切换到 Chat 标签
2. 输入 "帮我把'谢谢'翻译成韩语，并解释发音"
3. **预期**: LLM 流式返回答复，包含翻译和发音说明
4. 追问 "那更礼貌的说法呢" → 验证上下文连贯性

## 打包

```bash
pyinstaller packaging/jimao_translator.spec
```

输出位于 `dist/jimao_translator/`，可直接分发。

## 故障排查

| 症状 | 可能原因 | 解决 |
|------|---------|------|
| 启动时报 "ANTHROPIC_API_KEY missing" | 密钥未配置 | 通过 UI 配置或设置环境变量 |
| 语音按钮无反应 | 系统未授予麦克风权限 | 在系统设置中授权 |
| 翻译速度慢 (>1s) | 网络延迟 | 检查网络；未来版本将支持本地缓存 |
| TTS 无声音 | 系统音量/输出设备问题 | 检查音频输出 |

## 下一步

运行 `/speckit-tasks` 生成实现任务列表。
