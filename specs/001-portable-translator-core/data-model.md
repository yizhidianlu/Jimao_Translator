# Data Model: Portable Translator Core

**Date**: 2026-04-17
**Feature**: 001-portable-translator-core

所有实体使用 Pydantic v2 模型实现（`src/jimao_translator/models/`）。
所有时间戳为 UTC ISO 8601 字符串。

---

## 枚举

### LanguageCode

支持的语言代码（ISO 639-1）。

- `zh` — Chinese (Simplified)
- `en` — English
- `ja` — Japanese
- `ko` — Korean
- `auto` — 自动检测（仅用于源语言输入）

### TranslationMode

- `text` — 文本翻译
- `voice` — 语音翻译（单向）
- `voice_conversation` — 语音对话模式（分屏双向）

### MessageRole

- `user` — 用户消息
- `assistant` — LLM 回复

---

## 核心实体

### TranslationRequest

一次翻译操作的输入。

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `id` | `UUID` | yes | auto | 请求唯一标识 |
| `source_text` | `str` | yes | 1..5000 chars | 待翻译文本 |
| `source_language` | `LanguageCode` | yes | — | 源语言（可为 `auto`） |
| `target_language` | `LanguageCode` | yes | ≠ `auto` | 目标语言 |
| `mode` | `TranslationMode` | yes | — | 翻译模式 |
| `created_at` | `datetime` | yes | UTC | 请求时间戳 |

**规则**:
- `source_language == target_language` 且 `source_language != auto` 时，返回原文（不调用引擎）
- `source_text` 为空/空白时，系统 MUST NOT 发起请求（FR 对应: Edge Cases）

---

### TranslationResult

翻译操作的输出。

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `request_id` | `UUID` | yes | 关联 TranslationRequest.id | 对应请求 |
| `translated_text` | `str` | yes | — | 翻译结果 |
| `detected_source_language` | `LanguageCode` | yes | ≠ `auto` | 实际检测到的源语言 |
| `confidence` | `float` | no | 0.0..1.0 | 翻译置信度（若引擎提供） |
| `engine` | `str` | yes | — | 使用的翻译引擎标识（如 `"claude-sonnet-4-6"`） |
| `completed_at` | `datetime` | yes | UTC | 完成时间戳 |

---

### TranslationHistoryEntry

持久化的翻译历史条目。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request` | `TranslationRequest` | yes | 请求快照 |
| `result` | `TranslationResult` | yes | 结果快照 |

**集合约束** (TranslationHistory):
- 最多 **100** 条（FR-019, FR-021）
- 按 `request.created_at` 降序排序
- 超出上限时 MUST 自动淘汰最旧条目
- 历史保留需用户选择 opt-in（FR-018）

---

### VoiceSession

一次语音交互。

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `id` | `UUID` | yes | auto | 会话标识 |
| `recognized_text` | `str` | yes | — | 识别出的文本（可被用户编辑） |
| `recognition_confidence` | `float` | yes | 0.0..1.0 | 识别置信度（FR-012） |
| `source_language` | `LanguageCode` | yes | — | STT 所用语言 |
| `translation_request_id` | `UUID` | no | — | 触发的翻译请求 id（若已翻译） |
| `tts_played` | `bool` | yes | default=false | 是否已播放 TTS |
| `started_at` | `datetime` | yes | UTC | 语音开始时间 |

**规则**:
- 原始音频 MUST NOT 持久化（FR-016），仅短暂驻留内存
- `recognition_confidence < 0.6` 时 UI MUST 提示低置信度（Acceptance 4）

**State transitions**:

```
recording → recognized → [user_edited?] → translated → played
```

---

### ChatMessage

LLM 对话的单条消息。

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `id` | `UUID` | yes | auto | 消息标识 |
| `role` | `MessageRole` | yes | — | 角色 |
| `content` | `str` | yes | 1..20000 chars | 消息内容 |
| `timestamp` | `datetime` | yes | UTC | 时间戳 |
| `token_usage` | `int` | no | ≥ 0 | token 消耗（仅 assistant） |

---

### ChatConversation

一次 LLM 聊天会话。

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `id` | `UUID` | yes | auto | 会话标识 |
| `messages` | `list[ChatMessage]` | yes | ordered | 消息序列 |
| `created_at` | `datetime` | yes | UTC | 会话创建时间 |
| `last_active_at` | `datetime` | yes | UTC | 最近活跃时间 |

**规则**:
- SC-006: 上下文至少保持 10 轮连贯
- 消息顺序 MUST 按 `timestamp` 升序
- 会话 token 超出提供商上下文限制时，系统 MUST 窗口化最近消息并保留系统提示

---

### UserPreferences

跨会话持久化的用户设置。

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `default_source_language` | `LanguageCode` | yes | `auto` | 默认源语言 |
| `default_target_language` | `LanguageCode` | yes | `en` | 默认目标语言 |
| `ui_theme` | `Literal["light","dark","system"]` | yes | `system` | 主题 |
| `voice_speed` | `float` | yes | 1.0 | TTS 语速（0.5..2.0） |
| `hotkey` | `str` | no | `null` | 全局呼出热键 |
| `history_enabled` | `bool` | yes | `true` | 是否保留翻译历史（FR-018） |
| `last_active_tab` | `TranslationMode` | yes | `text` | 上次激活标签（FR-011a） |
| `llm_api_key` | `str` (encrypted) | no | `null` | LLM API 密钥（使用系统 keyring 存储） |

**规则**:
- `llm_api_key` MUST NOT 明文存储在 JSON；使用 OS keyring（`keyring` 库）
- `voice_speed` 超出范围时自动 clamp 到 [0.5, 2.0]

---

## 关系图

```text
UserPreferences (singleton, local file)

TranslationHistory
  └── TranslationHistoryEntry (×0..100)
        ├── TranslationRequest
        └── TranslationResult

VoiceSession
  └── translation_request_id → TranslationRequest

ChatConversation
  └── messages: ChatMessage (ordered)
```

---

## 存储位置

由 `platformdirs.user_data_dir("JimaoTranslator", "Jimao")` 决定：

- **Windows**: `%APPDATA%\Jimao\JimaoTranslator\`
- **macOS**: `~/Library/Application Support/JimaoTranslator/`
- **Linux**: `~/.local/share/JimaoTranslator/`

文件布局：

```text
<user_data_dir>/
├── preferences.json     # UserPreferences
├── history.json         # TranslationHistory (最多 100 条)
└── logs/
    └── app.log
```

敏感数据（API 密钥）存入操作系统 keyring，而非上述文件。
