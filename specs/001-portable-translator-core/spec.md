# Feature Specification: Portable Translator Core (便携式随身翻译核心)

**Feature Branch**: `001-portable-translator-core`
**Created**: 2026-04-17
**Status**: Draft
**Input**: User description: "实现一个便携式随身翻译工具，支持中英日韩实时文本翻译；构建语音翻译功能，用户说话后自动翻译并播放；集成 LLM API 实现智能聊天问答。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time Text Translation (实时文本翻译) (Priority: P1)

用户打开翻译工具，在输入框中键入文本（中文、英文、日文或韩文），选择目标语言后，系统立即显示翻译结果。用户可以随时切换源语言和目标语言方向。翻译过程中系统自动检测输入语言，用户也可以手动指定。翻译结果可一键复制到剪贴板。

**Why this priority**: 文本翻译是翻译工具最基础、最核心的功能。没有它，语音翻译和 LLM 问答都无法运作。它是 MVP 的最小可交付单元，能独立为用户提供完整的翻译价值。

**Independent Test**: 可通过输入一段中文文本并选择英语作为目标语言来完整测试，验证翻译结果的准确性和响应速度。

**Acceptance Scenarios**:

1. **Given** 用户打开翻译工具且处于文本翻译模式, **When** 用户在输入框中输入"你好世界"并选择目标语言为英语, **Then** 系统在输入完成后立即显示英文翻译结果
2. **Given** 用户已输入文本并获得翻译结果, **When** 用户切换目标语言从英语到日语, **Then** 系统自动重新翻译并显示日语结果
3. **Given** 用户输入了混合语言文本（如中英混合）, **When** 系统处理翻译请求, **Then** 系统自动检测主要语言并完成翻译，结果保持语义连贯
4. **Given** 用户获得翻译结果, **When** 用户点击复制按钮, **Then** 翻译结果被复制到系统剪贴板，并显示复制成功提示
5. **Given** 网络连接不可用, **When** 用户尝试翻译, **Then** 系统显示友好的离线提示，并在有离线翻译能力时自动降级使用

---

### User Story 2 - Voice Translation (语音翻译) (Priority: P2)

用户按住语音按钮开始说话，松开后系统自动识别语音内容，将识别出的文本翻译为目标语言，并自动朗读翻译结果。整个过程流畅自然，用户可以在"对话模式"下与外国人交替使用此功能进行双向交流。

**Why this priority**: 语音翻译是"随身翻译工具"的核心差异化功能，使产品在旅行、商务等面对面场景中具有实用价值。它依赖文本翻译引擎（P1），因此排在第二。

**Independent Test**: 可通过对着麦克风说一句中文，验证系统是否正确识别语音、翻译为目标语言并朗读结果。

**Acceptance Scenarios**:

1. **Given** 用户处于语音翻译模式且麦克风权限已授予, **When** 用户按住语音按钮并说"请问附近有餐厅吗", **Then** 系统识别语音文本、翻译为目标语言并自动朗读翻译结果
2. **Given** 语音识别完成, **When** 系统显示识别出的原文, **Then** 用户可以在翻译前确认或编辑识别文本以纠正错误
3. **Given** 用户处于对话模式, **When** 对方用英语说话后用户按住按钮, **Then** 系统自动检测英语输入并翻译为中文朗读
4. **Given** 环境噪音较大导致语音识别置信度低, **When** 系统完成识别, **Then** 系统标注低置信度并提示用户确认或重说

---

### User Story 3 - LLM Intelligent Chat (LLM 智能问答) (Priority: P3)

用户进入聊天模式，通过文本或语音向 LLM 提出问题或请求（如"帮我把这段话翻译成更正式的日语"、"这个韩语单词的用法是什么"），LLM 基于上下文给出智能回答。聊天支持多轮对话，系统保持上下文连贯性。

**Why this priority**: LLM 问答是增值功能，提升翻译工具的智能化水平。它为用户提供超越简单翻译的能力（如语法解释、语境建议、正式/非正式转换），但不是核心翻译功能的前提。

**Independent Test**: 可通过在聊天界面输入"请解释'お疲れ様です'在不同场景下的用法"来验证 LLM 是否给出准确、有上下文的回答。

**Acceptance Scenarios**:

1. **Given** 用户进入聊天模式, **When** 用户输入"帮我把'谢谢'翻译成韩语，并解释发音", **Then** LLM 返回翻译结果及发音解释
2. **Given** 用户已进行多轮对话, **When** 用户追问"那更礼貌的说法呢", **Then** LLM 基于上下文理解"那"指代上一轮的内容，给出更正式的表达
3. **Given** LLM 服务不可用（网络中断或 API 配额耗尽）, **When** 用户发送消息, **Then** 系统显示友好的错误提示，建议用户使用基础翻译功能
4. **Given** 用户输入包含敏感或不当内容, **When** 系统处理请求, **Then** 系统按照内容安全策略过滤，不返回有害内容

---

### Edge Cases

- 用户输入为空时，系统不发起翻译请求，输入框显示占位提示
- 用户输入超长文本（>5000 字符）时，系统提示截断或分段翻译
- 用户选择不支持的语言对组合时，系统给出明确提示并建议可用的语言对
- 网络中断时，正在进行的翻译请求优雅超时并通知用户
- 语音输入为静音或纯噪音时，系统提示"未检测到语音，请重试"
- 快速连续发送多个翻译请求时，系统正确处理并发，不丢失或混淆结果
- 输入包含特殊字符（emoji、数学符号、代码片段）时，系统合理处理
- LLM 返回异常长响应时，系统分段展示并保持界面可用

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support text translation between Chinese, English, Japanese, and Korean (any direction)
- **FR-002**: System MUST automatically detect the input language when the user does not manually specify it
- **FR-003**: System MUST display translation results within 500ms for text input under 200 characters
- **FR-004**: System MUST provide a one-click copy function for translation results
- **FR-005**: System MUST support voice input via microphone with press-and-hold activation
- **FR-006**: System MUST convert recognized speech to text and display it before translating
- **FR-007**: System MUST automatically read aloud (text-to-speech) the translated result in the target language
- **FR-008**: System MUST allow users to edit recognized speech text before translation to correct recognition errors
- **FR-009**: System MUST integrate with an LLM service for intelligent chat and Q&A
- **FR-010**: System MUST maintain conversation context across multiple chat turns within a session
- **FR-011**: System MUST provide a compact, always-accessible interface that can be quickly invoked (e.g., via hotkey or system tray)
- **FR-012**: System MUST display confidence indicators for voice recognition results
- **FR-013**: System MUST gracefully degrade when network is unavailable, showing clear status and falling back to offline capabilities if available
- **FR-014**: System MUST persist user preferences (preferred language pair, UI settings) across sessions
- **FR-015**: System MUST enforce content safety policies on LLM responses

### Key Entities

- **Translation Request**: Represents a single translation operation; includes source text, detected or specified source language, target language, and request timestamp
- **Translation Result**: The output of a translation; includes translated text, confidence score, alternative translations (if available), and the engine used
- **Voice Session**: A voice interaction cycle; includes raw audio reference, recognized text, recognition confidence, associated translation request, and TTS output status
- **Chat Conversation**: An LLM chat session; includes ordered message history (user and assistant turns), session context, and token usage tracking
- **User Preferences**: Persisted user settings; includes default language pair, UI theme, voice speed, and hotkey configuration

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can obtain a text translation result within 1 second of completing input for texts under 200 characters
- **SC-002**: Voice-to-translation cycle (speak → recognize → translate → playback starts) completes within 3 seconds for utterances under 10 seconds
- **SC-003**: 90% of users can successfully complete a text translation on their first attempt without guidance
- **SC-004**: Translation accuracy for common phrases and sentences achieves a user satisfaction rating of 4/5 or higher
- **SC-005**: The application launches and is ready for input within 3 seconds on supported platforms
- **SC-006**: LLM chat maintains coherent context for at least 10 consecutive turns in a conversation
- **SC-007**: The application uses less than 500MB of memory during normal operation (text and voice translation without local models)

## Assumptions

- Users have internet connectivity for primary functionality; offline mode is a future enhancement limited to basic features
- Target users are travelers, language learners, and professionals who need quick translations in daily scenarios
- The application runs as a lightweight desktop tool on Windows, macOS, and Linux
- Voice features require a working microphone and speakers/headphones on the user's device
- LLM API access requires user-provided API keys; the application does not bundle or resell API access
- Mobile platform support (iOS/Android) is out of scope for this initial version
- The initial supported languages are Chinese (Simplified), English, Japanese, and Korean; additional languages may be added in future iterations
- Chat history is stored locally per session; cloud sync of history is out of scope for v1
